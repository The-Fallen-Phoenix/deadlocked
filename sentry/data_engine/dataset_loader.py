"""
PyTorch Dataset Loaders and Batch Generators for Voice Authenticity and Biometrics in SENTRY.
Supports ASVspoof protocol, WaveFake vocoder directories, and procedural benchmark datasets.
"""

import os
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

from sentry.core.config import settings
from sentry.audio.preprocessor import audio_preprocessor
from sentry.audio.features import feature_extractor
from sentry.audio.synth_generator import scenario_generator
from sentry.data_engine.augmentations import augmenter


class SentryAuthenticityDataset(Dataset):
    """
    PyTorch Dataset for Voice Authenticity (Deepfake / Synthetic vs Genuine).
    Extracts Log-Mel Spectrograms and LFCC maps with optional SpecAugment.
    """

    def __init__(
        self,
        samples_list: List[Dict[str, Any]],
        sample_rate: int = 16000,
        apply_augmentation: bool = True,
        apply_spec_augment: bool = False,
        fixed_length_sec: float = 3.0
    ):
        self.samples = samples_list
        self.sample_rate = sample_rate
        self.apply_augmentation = apply_augmentation
        self.apply_spec_augment = apply_spec_augment
        self.fixed_length_samples = int(sample_rate * fixed_length_sec)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        item = self.samples[idx]
        
        # Load audio (either from file path or generated array)
        if "filepath" in item and Path(item["filepath"]).exists():
            with open(item["filepath"], "rb") as f:
                audio, _ = audio_preprocessor.load_audio_from_bytes(f.read())
        elif "audio" in item:
            audio = item["audio"]
        else:
            # Fallback procedural generation
            is_synth = bool(item.get("label", 0) == 1)
            audio = scenario_generator.generate_formant_speech(
                duration_sec=3.0,
                base_f0=float(item.get("f0", 140.0)),
                is_synthetic=is_synth
            )

        # Standardize duration (pad or crop)
        if len(audio) < self.fixed_length_samples:
            pad_len = self.fixed_length_samples - len(audio)
            audio = np.pad(audio, (0, pad_len), mode="constant")
        else:
            audio = audio[:self.fixed_length_samples]

        # Apply acoustic augmentations (telephony codec, noise, reverb)
        if self.apply_augmentation:
            audio = augmenter.random_pipeline(audio)

        audio_t = audio_preprocessor.to_torch_tensor(audio)

        # Extract features
        mel_np = feature_extractor.extract_mel_spectrogram(audio_t)
        lfcc_np = feature_extractor.extract_lfcc(audio_t)

        mel_t = torch.from_numpy(mel_np).unsqueeze(0).float()   # [1, 80, Time]
        lfcc_t = torch.from_numpy(lfcc_np).unsqueeze(0).float() # [1, 40, Time]

        # Apply SpecAugment if training
        if self.apply_spec_augment:
            mel_t = augmenter.apply_spec_augment(mel_t)
            lfcc_t = augmenter.apply_spec_augment(lfcc_t)

        label = torch.tensor(item.get("label", 0), dtype=torch.long)
        return mel_t, lfcc_t, label


class SentrySpeakerTripletDataset(Dataset):
    """
    PyTorch Triplet Dataset for Speaker Verification (Anchor, Positive, Negative).
    Used for Triplet Margin Loss & ArcFace metric learning.
    """

    def __init__(
        self,
        speakers_dict: Dict[str, List[np.ndarray]],
        samples_per_epoch: int = 500
    ):
        self.speakers_dict = speakers_dict
        self.speaker_ids = list(speakers_dict.keys())
        self.samples_per_epoch = samples_per_epoch

    def __len__(self) -> int:
        return self.samples_per_epoch

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        # Choose random anchor speaker
        anchor_spk = random.choice(self.speaker_ids)
        while len(self.speakers_dict[anchor_spk]) < 2:
            anchor_spk = random.choice(self.speaker_ids)

        # Choose anchor & positive
        a_idx, p_idx = random.sample(range(len(self.speakers_dict[anchor_spk])), 2)
        anchor_audio = self.speakers_dict[anchor_spk][a_idx]
        pos_audio = self.speakers_dict[anchor_spk][p_idx]

        # Choose negative speaker
        neg_spk = random.choice(self.speaker_ids)
        while neg_spk == anchor_spk:
            neg_spk = random.choice(self.speaker_ids)
        neg_audio = random.choice(self.speakers_dict[neg_spk])

        # Extract Mel spectrograms
        a_mel = torch.from_numpy(feature_extractor.extract_mel_spectrogram(audio_preprocessor.to_torch_tensor(anchor_audio))).float()
        p_mel = torch.from_numpy(feature_extractor.extract_mel_spectrogram(audio_preprocessor.to_torch_tensor(pos_audio))).float()
        n_mel = torch.from_numpy(feature_extractor.extract_mel_spectrogram(audio_preprocessor.to_torch_tensor(neg_audio))).float()

        return a_mel, p_mel, n_mel


class DatasetBuilder:
    """Utility to generate balanced training, validation, and test splits."""

    @staticmethod
    def build_synthetic_benchmark_split(
        num_genuine: int = 100,
        num_synthetic: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Creates a diverse balanced benchmark list across various speaker pitches and vocoder profiles.
        """
        samples = []

        # Genuine Human Vocal Tract Samples (F0: 90Hz to 240Hz)
        f0_range_genuine = np.linspace(90.0, 240.0, num_genuine)
        for i, f0 in enumerate(f0_range_genuine):
            samples.append({
                "id": f"gen_{i:04d}",
                "label": 0,  # Genuine
                "f0": float(f0),
                "is_synthetic": False
            })

        # Synthetic Vocoder Samples (Simulating HiFi-GAN, WaveGlow, Tacotron, Bark)
        f0_range_synth = np.linspace(95.0, 235.0, num_synthetic)
        for j, f0 in enumerate(f0_range_synth):
            samples.append({
                "id": f"synth_{j:04d}",
                "label": 1,  # Synthetic Deepfake
                "f0": float(f0),
                "is_synthetic": True
            })

        random.shuffle(samples)
        return samples


dataset_builder = DatasetBuilder()
