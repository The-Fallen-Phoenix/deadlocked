"""
Audio Augmentation & Telephony Codec Simulation Pipeline for SENTRY.
Simulates real-world acoustic conditions: G.711 Telephony, 8kHz downsampling,
ambient noise, room reverberation (RIR), and SpecAugment.
"""

import random
from typing import Tuple, Optional
import numpy as np
import scipy.signal as signal
import torch


class AudioAugmenter:
    """Applies realistic acoustic augmentations to audio signals and spectrogram tensors."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    # 1. Telephony Codec Emulation (G.711 & Bandpass 300Hz - 3400Hz)
    def apply_telecom_codec(self, audio: np.ndarray, codec: str = "g711_ulaw") -> np.ndarray:
        """
        Emulates PSTN / Cellular / VoIP telephony compression:
        - 300Hz - 3400Hz standard telephony bandpass filter
        - 8-bit non-linear logarithmic mu-law/A-law quantization
        """
        if len(audio) < 160:
            return audio

        # Bandpass filter for telephony frequency range (300Hz - 3400Hz)
        sos = signal.butter(4, [300.0, 3400.0], btype="bandpass", fs=self.sample_rate, output="sos")
        filtered = signal.sosfilt(sos, audio)

        if codec == "g711_ulaw":
            # Mu-law companding simulation (mu = 255)
            mu = 255.0
            x = np.clip(filtered, -1.0, 1.0)
            # Compression: sgn(x) * ln(1 + mu*|x|) / ln(1 + mu)
            compressed = np.sign(x) * np.log1p(mu * np.abs(x)) / np.log1p(mu)
            # Quantize to 8-bit integer (256 discrete levels)
            quantized = np.round((compressed + 1.0) * 127.5) / 127.5 - 1.0
            # Expansion: sgn(y) * ((1 + mu)^|y| - 1) / mu
            expanded = np.sign(quantized) * ((1.0 + mu) ** np.abs(quantized) - 1.0) / mu
            return expanded.astype(np.float32)
        else:
            return filtered.astype(np.float32)

    # 2. Additive Background Noise (Call Center, Babble, Street Noise)
    def add_background_noise(self, audio: np.ndarray, snr_db: float = 15.0, noise_type: str = "gaussian") -> np.ndarray:
        """
        Injects additive background noise at a designated Signal-to-Noise Ratio (SNR).
        """
        sig_power = np.mean(audio ** 2)
        if sig_power < 1e-8:
            return audio

        noise_power = sig_power / (10 ** (snr_db / 10.0))

        if noise_type == "gaussian":
            noise = np.random.normal(0, np.sqrt(noise_power), len(audio))
        elif noise_type == "babble":
            # Synthesize cocktail-party babble (multi-tone harmonic interference)
            t = np.linspace(0, len(audio) / self.sample_rate, len(audio), endpoint=False)
            noise = (
                np.sin(2 * np.pi * 220 * t) * np.random.randn(len(audio)) +
                np.sin(2 * np.pi * 440 * t) * np.random.randn(len(audio)) +
                np.sin(2 * np.pi * 880 * t) * np.random.randn(len(audio))
            )
            curr_pow = np.mean(noise ** 2) + 1e-9
            noise = noise * np.sqrt(noise_power / curr_pow)
        else:
            noise = np.random.uniform(-1, 1, len(audio)) * np.sqrt(3 * noise_power)

        augmented = audio + noise
        max_val = np.max(np.abs(augmented))
        if max_val > 1.0:
            augmented = augmented / max_val * 0.95
        return augmented.astype(np.float32)

    # 3. Room Impulse Response (Reverberation) Simulation
    def apply_reverberation(self, audio: np.ndarray, room_scale: float = 0.5) -> np.ndarray:
        """
        Simulates multi-path acoustic reflections in an office/room environment.
        """
        delays_ms = [18, 35, 52, 70]
        decay_factors = [0.25, 0.15, 0.08, 0.04]
        
        reverbed = np.copy(audio)
        for delay_ms, decay in zip(delays_ms, decay_factors):
            delay_samples = int(self.sample_rate * (delay_ms / 1000.0) * room_scale)
            if len(audio) > delay_samples:
                reverbed[delay_samples:] += decay * audio[:-delay_samples]

        max_val = np.max(np.abs(reverbed))
        if max_val > 1.0:
            reverbed = reverbed / max_val * 0.95
        return reverbed.astype(np.float32)

    # 4. SpecAugment (Time & Frequency Masking on PyTorch Tensors)
    def apply_spec_augment(
        self,
        spec_tensor: torch.Tensor,
        freq_mask_max: int = 12,
        time_mask_max: int = 25,
        num_freq_masks: int = 2,
        num_time_masks: int = 2
    ) -> torch.Tensor:
        """
        Applies SpecAugment masking directly to spectrogram feature tensors [Channels, Freq, Time].
        """
        augmented = spec_tensor.clone()
        if augmented.ndim == 2:
            augmented = augmented.unsqueeze(0)

        c, num_freqs, num_times = augmented.shape

        # Frequency Masking
        for _ in range(num_freq_masks):
            f_len = random.randint(1, min(freq_mask_max, num_freqs - 1))
            f0 = random.randint(0, num_freqs - f_len)
            augmented[:, f0:f0 + f_len, :] = 0.0

        # Time Masking
        if num_times > 10:
            for _ in range(num_time_masks):
                t_len = random.randint(1, min(time_mask_max, num_times // 4))
                t0 = random.randint(0, num_times - t_len)
                augmented[:, :, t0:t0 + t_len] = 0.0

        return augmented.squeeze(0) if spec_tensor.ndim == 2 else augmented

    def random_pipeline(self, audio: np.ndarray, augment_prob: float = 0.6) -> np.ndarray:
        """
        Applies a randomized combination of acoustic augmentations for robust training.
        """
        if random.random() > augment_prob:
            return audio

        aug = np.copy(audio)

        # 50% chance of telephony codec
        if random.random() < 0.5:
            aug = self.apply_telecom_codec(aug)

        # 60% chance of background noise (SNR 8-22 dB)
        if random.random() < 0.6:
            snr = random.uniform(8.0, 22.0)
            noise_type = random.choice(["gaussian", "babble"])
            aug = self.add_background_noise(aug, snr_db=snr, noise_type=noise_type)

        # 40% chance of room reverberation
        if random.random() < 0.4:
            scale = random.uniform(0.3, 0.8)
            aug = self.apply_reverberation(aug, room_scale=scale)

        return aug


augmenter = AudioAugmenter()
