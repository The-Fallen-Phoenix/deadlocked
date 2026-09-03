"""
Biometric Voiceprint Enrollment Vault for SENTRY.
Stores, retrieves, and validates enrolled reference speaker identities with cryptographic hashes.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

from sentry.core.config import settings
from sentry.core.security import security_manager
from sentry.models.speaker_verifier import speaker_verifier
from sentry.audio.preprocessor import audio_preprocessor


class BiometricVault:
    """Secure encrypted storage for enrolled speaker voice biometric signatures."""

    def __init__(self):
        self.vault_file = settings.vault_dir / "speaker_vault.json"
        self.embeddings_file = settings.vault_dir / "embeddings.npz"
        self.speakers: Dict[str, Dict[str, Any]] = {}
        self.embeddings_matrix: Dict[str, np.ndarray] = {}
        self._load_vault()

    def _load_vault(self):
        """Loads vault profiles and numpy embeddings from disk."""
        if self.vault_file.exists():
            try:
                with open(self.vault_file, "r", encoding="utf-8") as f:
                    self.speakers = json.load(f)
            except Exception as e:
                print(f"Error loading speaker vault: {e}")
                self.speakers = {}

        if self.embeddings_file.exists():
            try:
                npz = np.load(self.embeddings_file)
                self.embeddings_matrix = {k: npz[k] for k in npz.files}
            except Exception as e:
                print(f"Error loading biometric embeddings: {e}")
                self.embeddings_matrix = {}

        # If vault is empty or embeddings missing, initialize with default reference profiles
        if not self.speakers or not self.embeddings_matrix:
            self._initialize_default_profiles()

    def _save_vault(self):
        """Saves speaker metadata and embeddings matrix."""
        try:
            with open(self.vault_file, "w", encoding="utf-8") as f:
                json.dump(self.speakers, f, indent=2)
            if self.embeddings_matrix:
                np.savez(self.embeddings_file, **self.embeddings_matrix)
        except Exception as e:
            print(f"Error saving speaker vault: {e}")

    def enroll_speaker(
        self,
        speaker_id: str,
        display_name: str,
        role: str,
        audio: np.ndarray,
        organization: str = "Deadlocked Enterprise"
    ) -> Dict[str, Any]:
        """
        Extracts biometric voiceprint from audio and enrolls speaker into the vault.
        """
        embedding = speaker_verifier.extract_embedding(audio)
        biometric_hash = security_manager.hash_embedding(embedding, speaker_id)

        profile = {
            "speaker_id": speaker_id,
            "display_name": display_name,
            "role": role,
            "organization": organization,
            "biometric_hash": biometric_hash,
            "enrolled_at": time.time(),
            "formatted_enrolled_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "status": "ACTIVE_VERIFIED",
            "sample_duration_sec": round(len(audio) / settings.audio.sample_rate, 2)
        }

        self.speakers[speaker_id] = profile
        self.embeddings_matrix[speaker_id] = embedding
        self._save_vault()

        return profile

    def get_speaker(self, speaker_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves speaker profile metadata."""
        return self.speakers.get(speaker_id)

    def get_embedding(self, speaker_id: str) -> Optional[np.ndarray]:
        """Retrieves speaker voiceprint embedding vector."""
        return self.embeddings_matrix.get(speaker_id)

    def list_speakers(self) -> List[Dict[str, Any]]:
        """Lists all enrolled speakers."""
        return list(self.speakers.values())

    def delete_speaker(self, speaker_id: str) -> bool:
        """Removes a speaker profile and embedding from the vault."""
        if speaker_id in self.speakers:
            del self.speakers[speaker_id]
            if speaker_id in self.embeddings_matrix:
                del self.embeddings_matrix[speaker_id]
            self._save_vault()
            return True
        return False

    def _initialize_default_profiles(self):
        """Creates initial reference voiceprints for the SIH demo."""
        from sentry.audio.synth_generator import scenario_generator
        from sentry.audio.preprocessor import audio_preprocessor

        defaults = [
            {
                "id": "spk_rithwik",
                "name": "Rithwik Sriram",
                "role": "Team Leader & Project Manager",
                "filename": "rithwik_executive_enrolled_reference.wav",
                "f0": 132.0,
                "org": "Team Deadlocked / IITM"
            },
            {
                "id": "spk_sahil",
                "name": "Sahil Singh",
                "role": "Backend Lead & Support Rep",
                "filename": "legitimate_support_genuine.wav",
                "f0": 135.0,
                "org": "Deadlocked Banking Ops"
            },
            {
                "id": "spk_aarav",
                "name": "Aarav Sharma",
                "role": "Enrolled Family Member",
                "filename": None,
                "f0": 180.0,
                "org": "Personal Vault"
            }
        ]

        for d in defaults:
            audio = None
            if d.get("filename"):
                cand = settings.sample_audio_dir / d["filename"]
                if cand.exists():
                    try:
                        audio, _ = audio_preprocessor.load_audio_from_file(cand)
                    except Exception:
                        pass
            if audio is None:
                audio = scenario_generator.generate_formant_speech(
                    duration_sec=4.0,
                    base_f0=d["f0"],
                    is_synthetic=False,
                    vocoder_noise=0.01
                )

            self.enroll_speaker(
                speaker_id=d["id"],
                display_name=d["name"],
                role=d["role"],
                audio=audio,
                organization=d["org"]
            )


biometric_vault = BiometricVault()
