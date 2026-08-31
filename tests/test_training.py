"""
Unit tests for SENTRY PyTorch Training Loops & Multilingual Foundation Models.
"""

import pytest
from sentry.training.train_authenticity import train_authenticity_model
from sentry.training.train_speaker import train_speaker_model
from sentry.models.foundation_models import foundation_manager
from sentry.models.transcription_ai import multilingual_parser


def test_authenticity_training_dry_run(tmp_path):
    # Dry run 1 epoch on CPU
    checkpoint_path = train_authenticity_model(
        epochs=1,
        batch_size=8,
        lr=1e-4,
        device_str="cpu",
        dry_run=True,
        output_dir=str(tmp_path)
    )
    assert checkpoint_path.exists()


def test_speaker_training_dry_run(tmp_path):
    # Dry run 1 epoch on CPU
    checkpoint_path = train_speaker_model(
        epochs=1,
        batch_size=8,
        lr=2e-4,
        margin=0.2,
        device_str="cpu",
        dry_run=True,
        output_dir=str(tmp_path)
    )
    assert checkpoint_path.exists()


def test_foundation_manager_list():
    models = foundation_manager.list_available_foundation_models()
    assert len(models) >= 4
    keys = [m["model_key"] for m in models]
    assert "wav2vec2-xlsr" in keys
    assert "whisper-tiny" in keys
    assert "ecapa-tdnn" in keys


def test_multilingual_intent_parsing_hindi_hinglish():
    # Hindi phrase
    res_hindi = multilingual_parser.parse_transcript("CBI police thana se phone hai. Giraftari warrant nikla hai, line mat kaatna!")
    assert res_hindi["linguistic_score"] >= 0.70
    assert "DIGITAL_ARREST_POLICE" in res_hindi["matched_categories"]
    assert "Hindi" in res_hindi["detected_language"]

    # Hinglish UPI fraud phrase
    res_hinglish = multilingual_parser.parse_transcript("Turant paise bhejo, UPI PIN dalo warna account block ho jayega.")
    assert res_hinglish["linguistic_score"] >= 0.70
    assert "URGENT_UPI_TRANSFER" in res_hinglish["matched_categories"]

    # Clean Hindi phrase
    res_clean = multilingual_parser.parse_transcript("Namaste, kal meeting 4 baje hogi.")
    assert res_clean["linguistic_score"] <= 0.15
