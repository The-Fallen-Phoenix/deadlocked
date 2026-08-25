"""
Configuration module for SENTRY Voice Trust & Cyber-Defense Platform.
"""

import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_AUDIO_DIR = DATA_DIR / "sample_audio"
REFERENCE_SPEAKERS_DIR = DATA_DIR / "reference_speakers"
VAULT_DIR = DATA_DIR / "vault"
INCIDENTS_DIR = DATA_DIR / "incidents"

for d in [DATA_DIR, SAMPLE_AUDIO_DIR, REFERENCE_SPEAKERS_DIR, VAULT_DIR, INCIDENTS_DIR]:
    os.makedirs(d, exist_ok=True)


class AudioConfig(BaseModel):
    sample_rate: int = 16000
    n_fft: int = 512
    hop_length: int = 160
    win_length: int = 400
    n_mels: int = 80
    n_lfcc: int = 40
    n_mfcc: int = 40
    stream_window_sec: float = 2.0
    stream_hop_sec: float = 0.5
    min_audio_len_sec: float = 0.5


class RiskWeightConfig(BaseModel):
    # Weights sum to 1.0 (or normalized dynamically)
    weight_synthetic: float = 0.35
    weight_speaker_mismatch: float = 0.25
    weight_transaction_exposure: float = 0.15
    weight_behavioral_threat: float = 0.15
    weight_context_anomaly: float = 0.10

    # Risk Tier Thresholds
    threshold_low: float = 30.0
    threshold_moderate: float = 60.0
    threshold_high: float = 80.0
    # 81-100 is Critical


class BiometricConfig(BaseModel):
    embedding_dim: int = 256
    match_threshold: float = 0.72  # Cosine similarity >= 0.72 is considered a valid match
    ambiguous_margin: float = 0.08  # 0.64 to 0.72 considered ambiguous


class PreventionPolicyConfig(BaseModel):
    auto_freeze_risk_threshold: float = 80.0
    step_up_auth_risk_threshold: float = 60.0
    alert_overlay_risk_threshold: float = 35.0
    require_secondary_challenge_amount: float = 50000.0  # INR >= 50k requires step-up on moderate risk


class AppSettings(BaseModel):
    app_name: str = "SENTRY"
    tagline: str = "Hear the Truth."
    problem_statement: str = "SIH26104 — AI-Powered Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Paths
    data_dir: Path = DATA_DIR
    sample_audio_dir: Path = SAMPLE_AUDIO_DIR
    reference_speakers_dir: Path = REFERENCE_SPEAKERS_DIR
    vault_dir: Path = VAULT_DIR
    incidents_dir: Path = INCIDENTS_DIR

    audio: AudioConfig = AudioConfig()
    risk_weights: RiskWeightConfig = RiskWeightConfig()
    biometrics: BiometricConfig = BiometricConfig()
    prevention: PreventionPolicyConfig = PreventionPolicyConfig()


settings = AppSettings()

