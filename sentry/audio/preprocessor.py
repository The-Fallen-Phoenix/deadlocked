"""
Audio preprocessing and standardization pipeline for SENTRY.
"""

import io
import base64
from pathlib import Path
from typing import Tuple, Optional, Union
import numpy as np
import scipy.io.wavfile as wavfile
import scipy.signal as signal
import torch

from sentry.core.config import settings


class AudioPreprocessor:
    """Standardizes, normalizes, and filters audio for acoustic neural networks."""

    def __init__(self, target_sample_rate: int = 16000):
        self.target_sr = target_sample_rate

    def load_audio_from_file(self, filepath: Union[str, Path]) -> Tuple[np.ndarray, int]:
        """
        Loads and decodes audio from a file path (supporting .wav, .mp3, .m4a, .flac, etc.)
        Resamples audio to target sample rate (default 16kHz float32 mono).
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Audio file does not exist: {filepath}")

        # 1. Try PyAV (av) for broad format support including M4A and MP3
        try:
            import av
            container = av.open(str(filepath))
            resampler = av.audio.resampler.AudioResampler(format='flt', layout='mono', rate=self.target_sr)
            audio_frames = []
            for frame in container.decode(audio=0):
                resampled_frames = resampler.resample(frame)
                for rframe in resampled_frames:
                    audio_frames.append(rframe.to_ndarray())
            if audio_frames:
                audio = np.concatenate(audio_frames, axis=1).squeeze()
                return audio.astype(np.float32), self.target_sr
        except Exception:
            pass

        # 2. Fallback to soundfile
        try:
            import soundfile as sf
            data, orig_sr = sf.read(str(filepath), dtype="float32")
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)
            return self.resample_if_needed(data, orig_sr)
        except Exception:
            pass

        # 3. Fallback to reading file bytes via load_audio_from_bytes
        with open(filepath, "rb") as f:
            return self.load_audio_from_bytes(f.read())

    def load_audio_from_bytes(self, audio_bytes: bytes) -> Tuple[np.ndarray, int]:
        """
        Decodes raw audio bytes (WAV, PCM) into a float32 numpy array [-1.0, 1.0].
        """
        # Try standard WAV header decoding first
        try:
            sr, data = wavfile.read(io.BytesIO(audio_bytes))
            # Convert multi-channel to mono
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)
            # Normalize according to dtype
            if data.dtype == np.int16:
                data = data.astype(np.float32) / 32768.0
            elif data.dtype == np.int32:
                data = data.astype(np.float32) / 2147483648.0
            elif data.dtype == np.uint8:
                data = (data.astype(np.float32) - 128.0) / 128.0
            else:
                data = data.astype(np.float32)
                max_val = np.max(np.abs(data)) if np.max(np.abs(data)) > 0 else 1.0
                data = data / max_val
            return self.resample_if_needed(data, sr)
        except Exception:
            # Fallback: treat as raw 16-bit PCM mono 16kHz
            try:
                data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                return data, self.target_sr
            except Exception as e:
                raise ValueError(f"Unable to decode audio buffer: {e}")

    def load_audio_from_base64(self, b64_string: str) -> Tuple[np.ndarray, int]:
        """Decodes base64 string from frontend Web Audio API."""
        if "," in b64_string:
            b64_string = b64_string.split(",")[1]
        raw_bytes = base64.b64decode(b64_string)
        return self.load_audio_from_bytes(raw_bytes)

    def resample_if_needed(self, audio: np.ndarray, orig_sr: int) -> Tuple[np.ndarray, int]:
        """Resamples audio to target sample rate using scipy polyphase resample."""
        if orig_sr == self.target_sr:
            return audio, self.target_sr
        num_target_samples = int(len(audio) * float(self.target_sr) / orig_sr)
        resampled = signal.resample(audio, num_target_samples)
        return resampled.astype(np.float32), self.target_sr

    def apply_pre_emphasis(self, audio: np.ndarray, coef: float = 0.97) -> np.ndarray:
        """Applies pre-emphasis filter to enhance high-frequency speech features."""
        if len(audio) < 2:
            return audio
        return np.append(audio[0], audio[1:] - coef * audio[:-1])

    def normalize_volume(self, audio: np.ndarray, target_rms: float = 0.1) -> np.ndarray:
        """Normalizes audio volume to standard RMS."""
        rms = np.sqrt(np.mean(audio**2))
        if rms > 1e-6:
            audio = audio * (target_rms / rms)
        # Clip to prevent clipping distortion
        return np.clip(audio, -1.0, 1.0)

    def to_torch_tensor(self, audio: np.ndarray) -> torch.Tensor:
        """Converts numpy array into 1D PyTorch float32 tensor."""
        return torch.from_numpy(audio).float()


audio_preprocessor = AudioPreprocessor()

