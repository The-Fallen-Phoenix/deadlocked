"""
Unit tests for SENTRY Audio Processing & Feature Extraction Pipeline.
"""

import numpy as np
import torch
import pytest

from sentry.audio.preprocessor import audio_preprocessor
from sentry.audio.vad import vad_detector
from sentry.audio.features import feature_extractor
from sentry.audio.synth_generator import scenario_generator


def test_audio_resampling_and_normalization():
    # Generate 1 second 44.1kHz sine wave
    sr_orig = 44100
    t = np.linspace(0, 1.0, sr_orig, endpoint=False)
    sig = 0.8 * np.sin(2 * np.pi * 440.0 * t).astype(np.float32)

    resampled, sr_target = audio_preprocessor.resample_if_needed(sig, sr_orig)
    assert sr_target == 16000
    assert len(resampled) == 16000

    normalized = audio_preprocessor.normalize_volume(resampled, target_rms=0.1)
    assert np.max(np.abs(normalized)) <= 1.0


def test_voice_activity_detection():
    # Active audio vs pure silence
    active_audio = scenario_generator.generate_formant_speech(duration_sec=1.5, base_f0=140.0)
    vad_res = vad_detector.process(active_audio)

    assert "speech_ratio" in vad_res
    assert vad_res["speech_ratio"] > 0.3
    assert vad_res["is_active_speech"] is True

    silence = np.zeros(16000, dtype=np.float32)
    vad_silence = vad_detector.process(silence)
    assert vad_silence["is_active_speech"] is False


def test_spectrogram_and_lfcc_extraction():
    audio = scenario_generator.generate_formant_speech(duration_sec=1.0)
    audio_t = audio_preprocessor.to_torch_tensor(audio)

    mel = feature_extractor.extract_mel_spectrogram(audio_t)
    assert mel.shape[0] == 80  # 80 mel bins
    assert mel.ndim == 2
    assert np.min(mel) >= 0.0 and np.max(mel) <= 1.0

    lfcc = feature_extractor.extract_lfcc(audio_t)
    assert lfcc.shape[0] == 40  # 40 lfcc coefficients


def test_vocoder_artifact_metrics():
    # Generate synthetic vs genuine
    synthetic_audio = scenario_generator.generate_formant_speech(duration_sec=2.0, is_synthetic=True)
    genuine_audio = scenario_generator.generate_formant_speech(duration_sec=2.0, is_synthetic=False)

    synth_metrics = feature_extractor.compute_vocoder_artifacts(synthetic_audio)
    gen_metrics = feature_extractor.compute_vocoder_artifacts(genuine_audio)

    assert "vocoder_artifact_score" in synth_metrics
    assert "pitch_jitter" in synth_metrics
    assert 0.0 <= synth_metrics["vocoder_artifact_score"] <= 1.0
