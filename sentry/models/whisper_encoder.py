"""
Whisper-Inspired Phonetic & Acoustic Latent Extractor for SENTRY.
Extracts 384-dimensional acoustic & phonemic embeddings for voice deepfake detection.
Inspired by Piotr Kawa et al. ("Improved DeepFake Detection Using Whisper Features").
"""

from typing import Dict, Any, Optional
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from sentry.core.config import settings
from sentry.audio.preprocessor import audio_preprocessor
from sentry.audio.features import feature_extractor


class WhisperAcousticEncoder(nn.Module):
    """
    Lightweight 1D Convolutional & Multi-Head Self-Attention Encoder
    mimicking the Whisper Audio Encoder architecture.
    """

    def __init__(self, in_features: int = 80, hidden_dim: int = 384, num_heads: int = 6):
        super().__init__()
        # 1D Convolution stem
        self.conv1 = nn.Conv1d(in_features, hidden_dim, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(hidden_dim, hidden_dim, kernel_size=3, stride=2, padding=1)
        
        # Transformer Multi-Head Self-Attention Block
        self.layer_norm1 = nn.LayerNorm(hidden_dim)
        self.self_attn = nn.MultiheadAttention(embed_dim=hidden_dim, num_heads=num_heads, batch_first=True)
        self.layer_norm2 = nn.LayerNorm(hidden_dim)
        self.mlp = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 2),
            nn.GELU(),
            nn.Linear(hidden_dim * 2, hidden_dim)
        )

        # Classification Head
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 2)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, 80, Time]
        h = F.gelu(self.conv1(x))
        h = F.gelu(self.conv2(h))  # [B, 384, Time/2]

        # [B, Time/2, 384]
        h_seq = h.permute(0, 2, 1)

        # Transformer attention block
        norm_h = self.layer_norm1(h_seq)
        attn_out, _ = self.self_attn(norm_h, norm_h, norm_h)
        h_seq = h_seq + attn_out

        norm_h2 = self.layer_norm2(h_seq)
        mlp_out = self.mlp(norm_h2)
        h_seq = h_seq + mlp_out

        # Global average pool over time
        pooled = torch.mean(h_seq, dim=1)  # [B, 384]
        logits = self.classifier(pooled)
        return logits


class WhisperDeepfakeDetector:
    """Inference wrapper for Whisper-Encoder Deepfake Detection."""

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = WhisperAcousticEncoder().to(self.device)
        self.model.eval()

    def predict(self, audio: np.ndarray) -> Dict[str, Any]:
        """Infers deepfake probability using Whisper encoder acoustic features."""
        if len(audio) < 1600:
            return {"synthetic_probability": 0.0, "classification": "GENUINE_VOICE", "model": "WhisperEncoder"}

        audio_tensor = audio_preprocessor.to_torch_tensor(audio).to(self.device)
        mel_spec = feature_extractor.extract_mel_spectrogram(audio_tensor)
        mel_t = torch.from_numpy(mel_spec).unsqueeze(0).float().to(self.device)

        with torch.no_grad():
            logits = self.model(mel_t)
            probs = F.softmax(logits, dim=1).cpu().numpy()[0]
            synth_prob = float(probs[1])

        return {
            "synthetic_probability": round(synth_prob, 4),
            "genuine_probability": round(1.0 - synth_prob, 4),
            "classification": "SYNTHETIC_CLONE" if synth_prob >= 0.65 else "GENUINE_VOICE",
            "model_architecture": "Whisper Feature Transformer Encoder"
        }


whisper_detector = WhisperDeepfakeDetector()
