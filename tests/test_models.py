"""
Unit tests for SENTRY AI Models (Authenticity, Speaker Verification, Threat Analyzer).
"""

import numpy as np
import pytest

from sentry.models.authenticity_detector import authenticity_detector
from sentry.models.speaker_verifier import speaker_verifier
from sentry.models.threat_analyzer import threat_analyzer
from sentry.audio.synth_generator import scenario_generator


def test_authenticity_detector_inference():
    audio = scenario_generator.generate_formant_speech(duration_sec=2.0, is_synthetic=True)
    res = authenticity_detector.analyze(audio)

    assert "synthetic_probability" in res
    assert 0.0 <= res["synthetic_probability"] <= 1.0
    assert 0.0 <= res["genuine_probability"] <= 1.0
    assert res["classification"] in ["GENUINE_VOICE", "SUSPICIOUS_UNNATURAL", "SYNTHETIC_CLONE"]
    assert "vocoder_metrics" in res
    assert "temporal_slices" in res


def test_speaker_verification_cosine_similarity():
    # Generate reference audio for speaker A
    audio_spk_a1 = scenario_generator.generate_formant_speech(duration_sec=2.5, base_f0=130.0)
    audio_spk_a2 = scenario_generator.generate_formant_speech(duration_sec=2.5, base_f0=132.0)
    # Generate different speaker B
    audio_spk_b = scenario_generator.generate_formant_speech(duration_sec=2.5, base_f0=210.0)

    emb_a1 = speaker_verifier.extract_embedding(audio_spk_a1)
    emb_a2 = speaker_verifier.extract_embedding(audio_spk_a2)
    emb_b = speaker_verifier.extract_embedding(audio_spk_b)

    assert emb_a1.shape == (256,)
    # Embedding is L2-normalized
    assert np.isclose(np.linalg.norm(emb_a1), 1.0, atol=1e-3)

    sim_same = speaker_verifier.compute_similarity(emb_a1, emb_a2)
    sim_diff = speaker_verifier.compute_similarity(emb_a1, emb_b)

    assert sim_same > sim_diff


def test_threat_analyzer_intent_and_cadence():
    # Coercive transcript
    transcript = "Emergency: CBI police arrest warrant issued! Transfer 50000 immediately to prevent arrest."
    intent_res = threat_analyzer.analyze_text_intent(transcript)

    assert intent_res["linguistic_threat_score"] >= 0.70
    assert intent_res["threat_level"] in ["HIGH_COERCION", "CRITICAL_SOCIAL_ENGINEERING", "CRITICAL_ATTACK"]
    assert "DIGITAL_ARREST_POLICE" in intent_res["matched_categories"]

    # Acoustic cadence
    audio = scenario_generator.generate_formant_speech(duration_sec=2.0)
    cadence_res = threat_analyzer.analyze_acoustic_cadence(audio, sample_rate=16000)

    assert "cadence_stress_score" in cadence_res
    assert "syllable_rate_hz" in cadence_res


def test_specrnet_inference():
    from sentry.models.specrnet import specrnet_engine
    audio = scenario_generator.generate_formant_speech(duration_sec=2.0)
    res = specrnet_engine.predict(audio)

    assert "synthetic_probability" in res
    assert "classification" in res
    assert res["model_architecture"] == "SpecRNet (Squeeze-and-Excitation ResNet)"


def test_whisper_detector_inference():
    from sentry.models.whisper_encoder import whisper_detector
    audio = scenario_generator.generate_formant_speech(duration_sec=2.0)
    res = whisper_detector.predict(audio)

    assert "synthetic_probability" in res
    assert "classification" in res
    assert res["model_architecture"] == "Whisper Feature Transformer Encoder"
