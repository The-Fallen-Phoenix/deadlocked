"""
Unit tests for SENTRY Data Engine, Augmentation Pipeline, and Benchmark Evaluator.
"""

import numpy as np
import torch
import pytest

from sentry.data_engine.augmentations import augmenter
from sentry.data_engine.dataset_loader import SentryAuthenticityDataset, dataset_builder
from sentry.data_engine.benchmark_evaluator import benchmark_evaluator
from sentry.audio.synth_generator import scenario_generator


def test_telephony_codec_and_noise_augmentation():
    audio = scenario_generator.generate_formant_speech(duration_sec=1.5)
    
    # Apply G.711 codec
    g711_audio = augmenter.apply_telecom_codec(audio, codec="g711_ulaw")
    assert len(g711_audio) == len(audio)
    assert np.max(np.abs(g711_audio)) <= 1.0

    # Apply background noise (10 dB SNR)
    noisy_audio = augmenter.add_background_noise(audio, snr_db=10.0, noise_type="gaussian")
    assert len(noisy_audio) == len(audio)

    # Apply room reverberation
    reverbed = augmenter.apply_reverberation(audio, room_scale=0.5)
    assert len(reverbed) == len(audio)


def test_spec_augment_tensor_masking():
    # Tensor of shape [1, 80, 100]
    spec = torch.ones(1, 80, 100)
    augmented_spec = augmenter.apply_spec_augment(spec, freq_mask_max=8, time_mask_max=15)

    assert augmented_spec.shape == spec.shape
    # Some values should be masked to 0.0
    assert (augmented_spec == 0.0).sum() > 0


def test_dataset_loader_batching():
    split = dataset_builder.build_synthetic_benchmark_split(num_genuine=4, num_synthetic=4)
    dataset = SentryAuthenticityDataset(split, apply_augmentation=True, apply_spec_augment=True)

    assert len(dataset) == 8
    mel_t, lfcc_t, label = dataset[0]

    assert mel_t.shape[0] == 1 and mel_t.shape[1] == 80
    assert lfcc_t.shape[0] == 1 and lfcc_t.shape[1] == 40
    assert label.item() in [0, 1]


def test_benchmark_evaluator_metrics():
    # Simulated ground truth and synthetic prediction scores
    y_true = [0, 0, 0, 0, 1, 1, 1, 1]
    y_scores = [0.1, 0.2, 0.15, 0.85, 0.75, 0.9, 0.95, 0.2]

    report = benchmark_evaluator.evaluate_model_predictions(y_true, y_scores)

    assert "equal_error_rate_pct" in report
    assert "roc_auc_score" in report
    assert "min_tdcf" in report
    assert "confusion_matrix" in report
    assert 0.0 <= report["roc_auc_score"] <= 1.0
