"""
Acoustic Feature Extraction Pipeline (LFCC, Mel-Spectrogram, Spectral Flux, Jitter/Shimmer)
for SENTRY Anti-Spoofing & Deepfake Detection.
"""

from typing import Dict, Any, Tuple
import numpy as np
import scipy.signal as signal
import scipy.fft as fft
import torch
import torchaudio.transforms as T

from sentry.core.config import settings


class AcousticFeatureExtractor:
    """Extracts spectro-temporal and vocoder-artifact features for voice authenticity detection."""

    def __init__(
        self,
        sample_rate: int = 16000,
        n_fft: int = 512,
        hop_length: int = 160,
        n_mels: int = 80,
        n_lfcc: int = 40
    ):
        self.sample_rate = sample_rate
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.n_mels = n_mels
        self.n_lfcc = n_lfcc

        # Torchaudio MelSpectrogram transform
        self.mel_transform = T.MelSpectrogram(
            sample_rate=sample_rate,
            n_fft=n_fft,
            win_length=int(sample_rate * 0.025),  # 25ms
            hop_length=hop_length,                # 10ms
            n_mels=n_mels,
            power=2.0
        )

        # Torchaudio LFCC transform (Linear Frequency Cepstral Coefficients - ASVspoof standard)
        self.lfcc_transform = T.LFCC(
            sample_rate=sample_rate,
            n_filter=60,
            n_lfcc=n_lfcc,
            speckwargs={
                "n_fft": n_fft,
                "win_length": int(sample_rate * 0.025),
                "hop_length": hop_length
            }
        )

    def extract_mel_spectrogram(self, audio_tensor: torch.Tensor) -> np.ndarray:
        """Computes normalized Log-Mel Spectrogram (80 x Time)."""
        if audio_tensor.ndim == 1:
            audio_tensor = audio_tensor.unsqueeze(0)
        mel_spec = self.mel_transform(audio_tensor)
        log_mel = torch.log(torch.clamp(mel_spec, min=1e-5)).squeeze(0)
        # Normalize to [0, 1] range for visual and CNN ingestion
        log_mel_np = log_mel.detach().cpu().numpy()
        min_v = np.min(log_mel_np)
        max_v = np.max(log_mel_np)
        if max_v - min_v > 1e-6:
            normalized = (log_mel_np - min_v) / (max_v - min_v)
        else:
            normalized = np.zeros_like(log_mel_np)
        return normalized

    def extract_lfcc(self, audio_tensor: torch.Tensor) -> np.ndarray:
        """Computes Linear Frequency Cepstral Coefficients (40 x Time)."""
        if audio_tensor.ndim == 1:
            audio_tensor = audio_tensor.unsqueeze(0)
        lfcc = self.lfcc_transform(audio_tensor).squeeze(0)
        return lfcc.detach().cpu().numpy()

    def compute_vocoder_artifacts(self, audio: np.ndarray) -> Dict[str, float]:
        """
        Calculates physical acoustic metrics that differentiate biological human vocal tract
        acoustics from synthetic vocoders (HiFi-GAN, WaveGlow, Tacotron/ElevenLabs/VALL-E):
        - High-Frequency Spectral Cutoff / Attenuation ratio
        - Spectral Centroid & Spectral Flux
        - Pitch Period Jitter (Perturbation quotient)
        - Amplitude Shimmer
        """
        if len(audio) < self.n_fft * 2:
            return {
                "hf_attenuation_ratio": 0.5,
                "spectral_flux": 0.05,
                "spectral_centroid_hz": 2000.0,
                "pitch_jitter": 0.01,
                "amplitude_shimmer": 0.02,
                "vocoder_artifact_score": 0.5
            }

        # 1. FFT Frequency Spectrum Analysis
        freqs = np.fft.rfftfreq(len(audio), 1.0 / self.sample_rate)
        fft_mag = np.abs(np.fft.rfft(audio))

        # Energy below 4kHz vs Energy 4kHz - 8kHz
        low_band_mask = (freqs >= 100) & (freqs < 3800)
        high_band_mask = (freqs >= 4000) & (freqs <= 7800)

        low_energy = np.sum(fft_mag[low_band_mask]**2) + 1e-9
        high_energy = np.sum(fft_mag[high_band_mask]**2) + 1e-9

        # Synthetic vocoders often exhibit abnormal high-frequency spectral rolloff or harmonic gaps
        hf_ratio = float(high_energy / (low_energy + high_energy))

        # 2. Spectral Centroid
        centroid = float(np.sum(freqs * fft_mag) / (np.sum(fft_mag) + 1e-9))

        # 3. Spectral Flux (frame to frame variation in spectral magnitude)
        stft = np.abs(signal.stft(audio, fs=self.sample_rate, nperseg=self.n_fft, noverlap=self.n_fft - self.hop_length)[2])
        if stft.shape[1] > 1:
            diff = np.diff(stft, axis=1)
            flux = float(np.mean(np.sqrt(np.sum(diff**2, axis=0))))
        else:
            flux = 0.05

        # 4. Approximate Pitch Jitter & Shimmer via Autocorrelation Peak Tracking
        corr = signal.correlate(audio, audio, mode="full")
        corr = corr[len(corr) // 2:]
        # Find fundamental frequency peak (70Hz - 400Hz range)
        min_lag = int(self.sample_rate / 400)
        max_lag = int(self.sample_rate / 70)
        if len(corr) > max_lag:
            peak_lag = min_lag + np.argmax(corr[min_lag:max_lag])
            peak_height = corr[peak_lag] / (corr[0] + 1e-9)
            # In synthetic audio, pitch track often lacks biological micro-jitter
            pitch_jitter = float(np.clip(1.0 - peak_height, 0.001, 0.2))
        else:
            pitch_jitter = 0.02

        # Amplitude Shimmer approximation
        frame_energies = np.array([np.mean(audio[i:i+self.hop_length]**2) for i in range(0, len(audio)-self.hop_length, self.hop_length)])
        if len(frame_energies) > 1:
            shimmer = float(np.mean(np.abs(np.diff(frame_energies))) / (np.mean(frame_energies) + 1e-9))
        else:
            shimmer = 0.02

        # Synthetic vocoder artifact anomaly score
        # Biological voices have natural jitter (0.015-0.06), balanced HF ratio, smooth flux
        # Overly clean / static pitch or harsh vocoder discontinuities yield high artifact score
        is_too_clean_pitch = 1.0 if pitch_jitter < 0.008 else 0.0
        abnormal_hf = 1.0 if (hf_ratio < 0.03 or hf_ratio > 0.35) else 0.0
        vocoder_score = float(np.clip(0.3 * abnormal_hf + 0.4 * is_too_clean_pitch + 0.3 * (1.0 if flux < 0.02 else 0.0), 0.0, 1.0))

        return {
            "hf_attenuation_ratio": round(hf_ratio, 4),
            "spectral_flux": round(flux, 4),
            "spectral_centroid_hz": round(centroid, 1),
            "pitch_jitter": round(pitch_jitter, 4),
            "amplitude_shimmer": round(shimmer, 4),
            "vocoder_artifact_score": round(vocoder_score, 3)
        }


feature_extractor = AcousticFeatureExtractor()
