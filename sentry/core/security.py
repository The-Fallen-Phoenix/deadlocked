"""
Security, Cryptographic Hashing, and Zero-Trust Voice Gateway helpers for SENTRY.
"""

import hashlib
import hmac
import secrets
import time
from typing import List, Dict, Any
import numpy as np


import os

class SecurityManager:
    """Handles biometric voice hashing, challenge tokens, and privacy controls."""

    def __init__(self, secret_key: str = None):
        if secret_key is None:
            secret_key = os.getenv("SENTRY_SECRET_KEY", "SENTRY_CYBER_DEFENSE_SECRET_KEY_2026")
        self.secret_key = secret_key.encode("utf-8")

    def hash_embedding(self, embedding: np.ndarray, speaker_id: str) -> str:
        """
        Creates a tamper-evident HMAC-SHA256 signature of a speaker's voiceprint vector.
        Ensures biometric vectors are pseudonymized and immutable.
        """
        raw_bytes = embedding.astype(np.float32).tobytes()
        mac = hmac.new(self.secret_key, raw_bytes + speaker_id.encode("utf-8"), hashlib.sha256)
        return mac.hexdigest()

    def generate_step_up_challenge(self) -> Dict[str, Any]:
        """
        Generates a dynamic, time-limited out-of-band verification challenge.
        Attackers using real-time voice cloning models typically suffer 200-800ms synthesis latency
        and cannot easily anticipate dynamic numeric/phonetic challenge tokens.
        """
        words = ["DELTA", "KAPPA", "ORION", "PHOENIX", "SHIELD", "VECTOR", "COBALT", "NEXUS"]
        chosen_word = secrets.choice(words)
        token_num = secrets.randbelow(9000) + 1000  # 4-digit code
        challenge_id = secrets.token_hex(8)
        phrase = f"SENTRY-{chosen_word}-{token_num}"
        
        return {
            "challenge_id": challenge_id,
            "phrase": phrase,
            "expected_word": chosen_word,
            "expected_code": str(token_num),
            "issued_at": time.time(),
            "expires_in_sec": 45,
            "instruction": f"Please repeat immediately: '{phrase}' for secondary acoustic authentication."
        }

    def sign_incident_dossier(self, incident_data: Dict[str, Any]) -> str:
        """
        Creates a cryptographic hash of the incident forensics report for audit trails.
        """
        serialized = str(sorted(incident_data.items())).encode("utf-8")
        return hashlib.sha256(self.secret_key + serialized).hexdigest()


security_manager = SecurityManager()
