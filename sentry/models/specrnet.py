"""
SpecRNet: Spectrogram Residual Network with Squeeze-and-Excitation Attention
for Fast and Accessible Speech Deepfake Detection in SENTRY.
Inspired by Piotr Kawa et al. (IEEE / Interspeech) & ASVspoof SOTA baselines.
"""

import math
from typing import Tuple, Dict, Any
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from sentry.core.config import settings
from sentry.audio.preprocessor import audio_preprocessor
from sentry.audio.features import feature_extractor


class SqueezeExcitationBlock(nn.Module):
    """Squeeze-and-Excitation (SE) Channel Attention Block."""

    def __init__(self, channels: int, reduction: int = 8):
        super().__init__()
        self.fc = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(channels, max(channels // reduction, 8), bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(max(channels // reduction, 8), channels, bias=False),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, c, _, _ = x.shape
        w = self.fc(x).view(b, c, 1, 1)
        return x * w


class SpecRNetResidualBlock(nn.Module):
    """Residual 2D Convolution block with BatchNorm and Squeeze-and-Excitation."""

    def __init__(self, in_channels: int, out_channels: int, stride: int = 1):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.se = SqueezeExcitationBlock(out_channels)

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
        out = self.se(out)
        out += residual
        return F.relu(out, inplace=True)


class SpecRNet(nn.Module):
    """
    SpecRNet Architecture:
    Lightweight Spectrogram Residual Network optimized for real-time audio anti-spoofing.
    """

    def __init__(self, in_channels: int = 1, num_classes: int = 2):
        super().__init__()
        # Initial convolution
        self.entry = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        )

        # 4 Residual Stages with Squeeze-and-Excitation
        self.stage1 = SpecRNetResidualBlock(32, 64, stride=2)
        self.stage2 = SpecRNetResidualBlock(64, 128, stride=2)
        self.stage3 = SpecRNetResidualBlock(128, 256, stride=2)

        # Attentive Statistics Pooling over time
        self.attn_weights = nn.Sequential(
            nn.Linear(256, 128),
            nn.Tanh(),
            nn.Linear(128, 1)
        )

        # Classifier
        self.fc = nn.Sequential(
            nn.Linear(512, 128),  # 256 mean + 256 std
            nn.ReLU(inplace=True),
            nn.Dropout(0.35),
            nn.Linear(128, num_classes)
        )

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, (nn.Conv2d, nn.Linear)):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        # x: [B, 1, Freq, Time]
        h = self.entry(x)
        h = self.stage1(h)
        h = self.stage2(h)
        h = self.stage3(h)  # [B, 256, F', T']

        # Pool over frequency dimension
        # [B, 256, T']
        h_t = torch.mean(h, dim=2)
        # Permute for temporal attention: [B, T', 256]
        h_perm = h_t.permute(0, 2, 1)

        # Attentive Statistical Pooling (Mean + Std)
        w = F.softmax(self.attn_weights(h_perm), dim=1)  # [B, T', 1]
        mean = torch.sum(h_perm * w, dim=1)             # [B, 256]
        diff = h_perm - mean.unsqueeze(1)
        std = torch.sqrt(torch.sum((diff ** 2) * w, dim=1) + 1e-6)  # [B, 256]
        
        pooled = torch.cat([mean, std], dim=1)  # [B, 512]
        logits = self.fc(pooled)                # [B, 2]
        return logits, pooled


class SpecRNetInferenceEngine:
    """Inference wrapper for SpecRNet model."""

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = SpecRNet().to(self.device)
        self.model.eval()

    def predict(self, audio: np.ndarray) -> Dict[str, Any]:
        """Runs SpecRNet inference on input audio."""
        if len(audio) < 1600:
            return {"synthetic_probability": 0.0, "classification": "GENUINE_VOICE", "model": "SpecRNet"}

        audio_tensor = audio_preprocessor.to_torch_tensor(audio).to(self.device)
        mel_spec = feature_extractor.extract_mel_spectrogram(audio_tensor)
        mel_t = torch.from_numpy(mel_spec).unsqueeze(0).unsqueeze(0).float().to(self.device)

        with torch.no_grad():
            logits, _ = self.model(mel_t)
            probs = F.softmax(logits, dim=1).cpu().numpy()[0]
            synth_prob = float(probs[1])

        return {
            "synthetic_probability": round(synth_prob, 4),
            "genuine_probability": round(1.0 - synth_prob, 4),
            "classification": "SYNTHETIC_CLONE" if synth_prob >= 0.65 else "GENUINE_VOICE",
            "model_architecture": "SpecRNet (Squeeze-and-Excitation ResNet)"
        }


specrnet_engine = SpecRNetInferenceEngine()
