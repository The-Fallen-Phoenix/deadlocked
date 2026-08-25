"""
Voice Activity Detection (VAD) and Speech Segmentation for SENTRY.
"""

from typing import List, Tuple, Dict, Any
import numpy as np


class VoiceActivityDetector:
    """Detects active speech frames and filters out non-speech silence/background noise."""

    def __init__(
        self,
        sample_rate: int = 16000,
        frame_duration_ms: int = 30,
        energy_threshold: float = 0.005,
        entropy_threshold: float = 4.5
    ):
        self.sample_rate = sample_rate
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        self.energy_threshold = energy_threshold
        self.entropy_threshold = entropy_threshold

    def process(self, audio: np.ndarray) -> Dict[str, Any]:
        """
        Analyzes audio signal for speech presence, silence ratio, and active segments.
        """
        if len(audio) < self.frame_size:
            return {
                "speech_ratio": 1.0,
                "is_active_speech": True,
                "voiced_samples": len(audio),
                "silence_ratio": 0.0,
                "num_speech_segments": 1
            }

        num_frames = len(audio) // self.frame_size
        voiced_frames = 0
        speech_mask = np.zeros(len(audio), dtype=bool)

        for i in range(num_frames):
            start = i * self.frame_size
            end = start + self.frame_size
            frame = audio[start:end]

            # 1. Short-Time Energy
            energy = np.mean(frame**2)

            # 2. Zero-Crossing Rate
            zcr = np.mean(np.abs(np.diff(np.sign(frame)))) / 2.0

            # 3. Spectral Entropy
            fft_mag = np.abs(np.fft.rfft(frame))
            fft_norm = fft_mag / (np.sum(fft_mag) + 1e-9)
            entropy = -np.sum(fft_norm * np.log2(fft_norm + 1e-9))

            # Multi-parameter decision
            if energy > self.energy_threshold and (zcr < 0.35 or entropy < self.entropy_threshold):
                voiced_frames += 1
                speech_mask[start:end] = True

        speech_ratio = voiced_frames / max(num_frames, 1)
        silence_ratio = 1.0 - speech_ratio

        return {
            "speech_ratio": round(float(speech_ratio), 3),
            "silence_ratio": round(float(silence_ratio), 3),
            "is_active_speech": bool(speech_ratio > 0.15),
            "total_duration_sec": round(len(audio) / self.sample_rate, 2),
            "voiced_duration_sec": round(float(speech_ratio * len(audio) / self.sample_rate), 2)
        }

    def trim_silence(self, audio: np.ndarray, top_db: float = 30.0) -> np.ndarray:
        """Trims leading and trailing silence based on energy threshold."""
        if len(audio) == 0:
            return audio
        threshold = np.max(np.abs(audio)) * (10 ** (-top_db / 20.0))
        indices = np.where(np.abs(audio) > threshold)[0]
        if len(indices) == 0:
            return audio
        return audio[indices[0]:indices[-1] + 1]


vad_detector = VoiceActivityDetector()
