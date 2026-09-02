"""
PyTorch Dataset Loaders and Batch Generators for Voice Authenticity and Biometrics in SENTRY.
Supports ASVspoof protocol, WaveFake vocoder directories, and procedural benchmark datasets.
"""

import os
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Union
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
            try:
                audio, _ = audio_preprocessor.load_audio_from_file(item["filepath"])
            except Exception:
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
    def build_real_vs_fake_split(
        dataset_dir: Union[str, Path] = "data/voice_dataset",
        train_ratio: float = 0.8,
        seed: int = 42
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Scans imported Real vs Fake Voice dataset directory structure:
        dataset_dir/{UK,USA}/{male,female}/{speaker_folder}/
           ├── original.wav / original.m4a (REAL -> label 0)
           ├── synthetic_1.mp3 (FAKE -> label 1)
           ├── synthetic_2.mp3 (FAKE -> label 1)
           └── synthetic_3.mp3 (FAKE -> label 1)

        Performs a SMART SPEAKER-AWARE 80-20 SPLIT (GroupKFold):
        80% of speaker IDs to Train, 20% to Test.
        Returns (train_samples, test_samples).
        """
        root_path = Path(dataset_dir)
        if not root_path.exists():
            print(f"[!] Dataset path {root_path} not found. Falling back to synthetic benchmark split.")
            train = DatasetBuilder.build_synthetic_benchmark_split(100, 100)
            val = DatasetBuilder.build_synthetic_benchmark_split(30, 30)
            return train, val

        # Group audio samples by speaker_id to prevent data leakage
        speakers: Dict[str, List[Dict[str, Any]]] = {}

        for filepath in root_path.rglob("*"):
            if not filepath.is_file():
                continue

            fname_lower = filepath.name.lower()
            if not (fname_lower.endswith(".m4a") or fname_lower.endswith(".mp3") or fname_lower.endswith(".wav")):
                continue

            # Derive speaker_id from path components
            # e.g., dataset_voice/USA/male/1/original.m4a -> speaker_id = "USA_male_1"
            rel_parts = filepath.relative_to(root_path).parts
            if len(rel_parts) >= 3:
                speaker_id = "_".join(rel_parts[:-1])
            else:
                speaker_id = filepath.parent.name

            # Determine real vs fake label
            if "original" in fname_lower:
                label = 0  # REAL / HUMAN
                voice_type = "real"
            elif "synthetic" in fname_lower or "fake" in fname_lower:
                label = 1  # FAKE / AI SYNTHETIC
                voice_type = "fake"
            else:
                continue

            sample_record = {
                "id": filepath.stem,
                "filepath": str(filepath),
                "label": label,
                "type": voice_type,
                "speaker_id": speaker_id
            }

            if speaker_id not in speakers:
                speakers[speaker_id] = []
            speakers[speaker_id].append(sample_record)

        # Smart Speaker-Aware 80-20 Split
        speaker_ids = sorted(list(speakers.keys()))
        rng = random.Random(seed)
        rng.shuffle(speaker_ids)

        num_train_speakers = int(len(speaker_ids) * train_ratio)
        train_speakers = set(speaker_ids[:num_train_speakers])
        test_speakers = set(speaker_ids[num_train_speakers:])

        train_samples_raw = []
        test_samples = []

        for spk_id, samples in speakers.items():
            if spk_id in train_speakers:
                train_samples_raw.extend(samples)
            else:
                test_samples.extend(samples)

        # Balance training set (Oversample Class 0 - Real voices to match Class 1 - Fake voices)
        real_train = [s for s in train_samples_raw if s["label"] == 0]
        fake_train = [s for s in train_samples_raw if s["label"] == 1]

        train_samples = []
        if real_train and fake_train:
            target_count = max(len(real_train), len(fake_train))
            multiplier = (target_count // len(real_train)) + 1
            balanced_real = (real_train * multiplier)[:target_count]
            train_samples = balanced_real + fake_train
        else:
            train_samples = train_samples_raw

        rng.shuffle(train_samples)
        rng.shuffle(test_samples)

        print(f"[*] Loaded Real vs. Fake Voice Dataset from {root_path}:")
        print(f"    - Total Speakers: {len(speaker_ids)} (Train: {len(train_speakers)}, Test: {len(test_speakers)})")
        print(f"    - Train Samples (Balanced): {len(train_samples)} (Real: {sum(1 for s in train_samples if s['label']==0)}, Fake: {sum(1 for s in train_samples if s['label']==1)})")
        print(f"    - Test Samples (20%):       {len(test_samples)} (Real: {sum(1 for s in test_samples if s['label']==0)}, Fake: {sum(1 for s in test_samples if s['label']==1)})")

        return train_samples, test_samples

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

