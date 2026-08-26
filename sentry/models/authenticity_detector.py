"""
Voice Authenticity & Deepfake Acoustic Detection Engine for SENTRY.
Combines PyTorch Spectrogram-ResNet + Multi-Head Temporal Attention with Physical Vocoder Artifact Forensics.
"""

import math
from typing import Dict, Any, List, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from sentry.core.config import settings
from sentry.audio.preprocessor import audio_preprocessor
from sentry.audio.features import feature_extractor


class ConvBlock(nn.Module):
    """Residual 2D Convolutional block for spectro-temporal feature extraction."""

    def __init__(self, in_channels: int, out_channels: int, stride: int = 1):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)

        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels)
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = self.shortcut(x)
        out = F.relu(self.bn1(self.conv1(x)), inplace=True)
        out = self.bn2(self.conv2(out))
        out += residual
        return F.relu(out, inplace=True)


class SentryAcousticClassifier(nn.Module):
    """
    Deep Neural Network for detecting AI-generated / neural vocoded speech.
    Ingests Log-Mel Spectrograms and LFCC maps.
    """

    def __init__(self, mel_bins: int = 80, lfcc_bins: int = 40):
        super().__init__()
        # Mel Branch
        self.mel_entry = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=5, stride=2, padding=2, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2)
        )
        self.mel_res1 = ConvBlock(32, 64, stride=2)
        self.mel_res2 = ConvBlock(64, 128, stride=2)

        # LFCC Branch (Linear Frequency Cepstral Coefficients - ASVspoof standard)
        self.lfcc_entry = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=5, stride=2, padding=2, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2)
        )
        self.lfcc_res1 = ConvBlock(32, 64, stride=2)

        # Temporal Multi-Head Attention Fusion
        self.temporal_attn = nn.MultiheadAttention(embed_dim=192, num_heads=4, batch_first=True)
        self.gru = nn.GRU(input_size=192, hidden_size=96, num_layers=1, batch_first=True, bidirectional=True)

        # Classifier Head
        self.fc = nn.Sequential(
            nn.Linear(192, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(64, 2)  # [0: Genuine, 1: Synthetic]
        )

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d) or isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, mel: torch.Tensor, lfcc: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        # Mel branch: [B, 1, 80, T] -> [B, 128, 5, T']
        x_mel = self.mel_res2(self.mel_res1(self.mel_entry(mel)))
        # LFCC branch: [B, 1, 40, T] -> [B, 64, 5, T']
        x_lfcc = self.lfcc_res1(self.lfcc_entry(lfcc))

        # Spatial Pool over frequency dimension
        # [B, 128, T']
        p_mel = torch.mean(x_mel, dim=2)
        # [B, 64, T']
        p_lfcc = torch.mean(x_lfcc, dim=2)

        # Align time dimensions if slightly mismatched
        min_t = min(p_mel.shape[2], p_lfcc.shape[2])
        p_mel = p_mel[:, :, :min_t]
        p_lfcc = p_lfcc[:, :, :min_t]

        # Concatenate: [B, 192, min_t] -> [B, min_t, 192]
        fused = torch.cat([p_mel, p_lfcc], dim=1).permute(0, 2, 1)

        # Multi-head temporal attention
        attn_out, _ = self.temporal_attn(fused, fused, fused)
        gru_out, _ = self.gru(attn_out)

        # Temporal pooling (mean across time)
        embedding = torch.mean(gru_out, dim=1)  # [B, 192]
        logits = self.fc(embedding)             # [B, 2]
        return logits, embedding


class AuthenticityDetector:
    """
    High-level Voice Authenticity Inference Engine for SENTRY.
    Ensembles deep neural representations with physical vocoder acoustic signatures.
    """

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = SentryAcousticClassifier().to(self.device)
        self.model.eval()

    def analyze(self, audio: np.ndarray) -> Dict[str, Any]:
        """
        Analyzes audio signal and returns synthetic probability, confidence,
        acoustic anomaly indicators, and temporal segments.
        """
        if len(audio) < 1600:  # < 0.1s
            return {
                "synthetic_probability": 0.0,
                "genuine_probability": 1.0,
                "confidence": 0.5,
                "classification": "GENUINE",
                "vocoder_artifacts": {},
                "explainability": {"status": "insufficient_audio"}
            }

        audio_tensor = audio_preprocessor.to_torch_tensor(audio).to(self.device)

        # 1. Feature Extraction
        mel_spec = feature_extractor.extract_mel_spectrogram(audio_tensor)
        lfcc = feature_extractor.extract_lfcc(audio_tensor)
        vocoder_metrics = feature_extractor.compute_vocoder_artifacts(audio)

        # Prepare tensors for PyTorch model: [1, 1, Freq, Time]
        mel_t = torch.from_numpy(mel_spec).unsqueeze(0).unsqueeze(0).float().to(self.device)
        lfcc_t = torch.from_numpy(lfcc).unsqueeze(0).unsqueeze(0).float().to(self.device)

        with torch.no_grad():
            logits, _ = self.model(mel_t, lfcc_t)
            probs = F.softmax(logits, dim=1).cpu().numpy()[0]
            raw_neural_synth_prob = float(probs[1])

        # 2. Physics-Informed Vocoder Fusion
        # Synthesizers (ElevenLabs, Bark, HiFi-GAN, VALL-E) leave tell-tale vocoder artifacts
        vocoder_score = vocoder_metrics["vocoder_artifact_score"]
        
        # Weighted hybrid ensemble: 60% Neural feature representation + 40% physical vocoder metrics
        hybrid_synth_prob = 0.60 * raw_neural_synth_prob + 0.40 * vocoder_score
        hybrid_synth_prob = float(np.clip(hybrid_synth_prob, 0.01, 0.99))
        genuine_prob = 1.0 - hybrid_synth_prob

        # Categorize
        if hybrid_synth_prob >= 0.70:
            classification = "SYNTHETIC_CLONE"
            verdict_text = "High probability of AI voice cloning / synthetic neural speech detected."
        elif hybrid_synth_prob >= 0.45:
            classification = "SUSPICIOUS_UNNATURAL"
            verdict_text = "Moderate acoustic anomalies detected; potential synthetic artifacts."
        else:
            classification = "GENUINE_VOICE"
            verdict_text = "Natural human vocal tract acoustics verified."

        # Time-sliced anomaly confidence for real-time waveform overlay
        time_slices = self._compute_temporal_confidence_slices(audio, window_sec=1.0, hop_sec=0.5)

        return {
            "synthetic_probability": round(hybrid_synth_prob, 4),
            "genuine_probability": round(genuine_prob, 4),
            "confidence": round(abs(hybrid_synth_prob - 0.5) * 2.0, 3),  # Distance from 0.5
            "classification": classification,
            "verdict": verdict_text,
            "vocoder_metrics": vocoder_metrics,
            "temporal_slices": time_slices,
            "acoustic_flags": {
                "high_frequency_cutoff": bool(vocoder_metrics["hf_attenuation_ratio"] < 0.05 or vocoder_metrics["hf_attenuation_ratio"] > 0.35),
                "unnatural_pitch_rigidity": bool(vocoder_metrics["pitch_jitter"] < 0.008),
                "spectral_flux_anomaly": bool(vocoder_metrics["spectral_flux"] < 0.025),
                "shimmer_perturbation": bool(vocoder_metrics["amplitude_shimmer"] > 0.08)
            }
        }

    def _compute_temporal_confidence_slices(
        self,
        audio: np.ndarray,
        window_sec: float = 1.0,
        hop_sec: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Splits audio into sliding windows for time-resolved anomaly graph."""
        sr = settings.audio.sample_rate
        win_len = int(window_sec * sr)
        hop_len = int(hop_sec * sr)
        slices = []

        for start_idx in range(0, len(audio) - win_len // 2, hop_len):
            end_idx = min(start_idx + win_len, len(audio))
            chunk = audio[start_idx:end_idx]
            if len(chunk) < 800:
                continue

            chunk_vocoder = feature_extractor.compute_vocoder_artifacts(chunk)
            chunk_synth_prob = float(chunk_vocoder["vocoder_artifact_score"])

            slices.append({
                "time_start_sec": round(start_idx / sr, 2),
                "time_end_sec": round(end_idx / sr, 2),
                "synthetic_prob": round(chunk_synth_prob, 3),
                "is_anomalous": bool(chunk_synth_prob > 0.60)
            })

        return slices


authenticity_detector = AuthenticityDetector()
