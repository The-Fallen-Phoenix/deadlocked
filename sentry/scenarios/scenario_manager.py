"""
Attack Scenario Manager for SENTRY Demonstrations and Security Evaluation.
Populates test scenarios directly from the held-out 20% test split of data/voice_dataset.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from sentry.core.config import settings
from sentry.data_engine.dataset_loader import dataset_builder


class ScenarioManager:
    """Pre-configures real-world fraud and impersonation attack scenarios for live testing."""

    def __init__(self):
        self._cache = None

    def list_scenarios(self) -> List[Dict[str, Any]]:
        """Returns test scenarios generated from the held-out 20% test split of voice_dataset."""
        if self._cache is not None:
            return self._cache

        scenarios = []
        try:
            # Build 80-20 speaker-aware split
            _, test_samples = dataset_builder.build_real_vs_fake_split(
                dataset_dir="data/voice_dataset",
                train_ratio=0.8,
                seed=42
            )

            for idx, sample in enumerate(test_samples):
                spk = sample.get("speaker_id", "Unknown_Speaker")
                sample_id = sample.get("id", f"sample_{idx}")
                is_fake = (sample.get("label", 0) == 1)

                parts = spk.split("_")
                country = parts[0] if len(parts) > 0 else "Global"
                gender = parts[1].capitalize() if len(parts) > 1 else "Unknown"
                spk_num = parts[2] if len(parts) > 2 else "1"

                scenario_id = f"scenario_ds_{spk}_{sample_id}"

                if is_fake:
                    title = f"{country} {gender} Speaker #{spk_num} — AI Voice Clone ({sample_id})"
                    category = f"Test Split | {country} {gender} Cloned Vector"
                    desc = f"Synthetic voice clone from held-out 20% test split. Ground-Truth: FAKE (Label 1)."
                    tx_amount = 150000.0 + (idx % 5) * 50000.0
                    target_ben = "Fraudulent Escrow VPA (Unverified Payee)"
                    attack_type = "AI Voice Cloning + Coercion Extortion"
                    transcript = f"Emergency request: Please process ₹{tx_amount:,.0f} immediately to our escrow account before 2 PM."
                else:
                    title = f"{country} {gender} Speaker #{spk_num} — Authentic Human Voice"
                    category = f"Test Split | {country} {gender} Genuine Baseline"
                    desc = f"Genuine human vocal tract recording from held-out 20% test split. Ground-Truth: REAL (Label 0)."
                    tx_amount = 0.0
                    target_ben = None
                    attack_type = "Legitimate Customer Verification"
                    transcript = f"Good morning, this is authentic human speech from test speaker #{spk_num}. No transaction required."

                scenarios.append({
                    "id": scenario_id,
                    "title": title,
                    "category": category,
                    "description": desc,
                    "claimed_speaker_id": f"spk_{spk.lower()}",
                    "claimed_speaker_name": f"Speaker {country} {gender} #{spk_num}",
                    "audio_filename": Path(sample["filepath"]).name,
                    "audio_filepath": sample["filepath"],
                    "transcript": transcript,
                    "transaction_amount_inr": tx_amount,
                    "target_beneficiary": target_ben,
                    "attack_type": attack_type,
                    "target_victim": "Financial Customer / Verification System",
                    "is_synthetic_ground_truth": is_fake,
                    "dataset_sample_id": sample_id,
                    "speaker_id": spk
                })
        except Exception as e:
            print(f"[!] ScenarioManager exception loading dataset: {e}")

        if not scenarios:
            scenarios = self._get_fallback_scenarios()

        self._cache = scenarios
        return self._cache

    def get_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific scenario configuration."""
        for s in self.list_scenarios():
            if s["id"] == scenario_id:
                return s
        return None

    def _get_fallback_scenarios(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "scenario_ceo_wire_transfer",
                "title": "CEO Urgent Wire Transfer Scam",
                "category": "Corporate Executive Impersonation",
                "description": "Deepfake voice clone demanding an emergency ₹5 Lakh wire transfer.",
                "claimed_speaker_id": "spk_rithwik",
                "claimed_speaker_name": "Rithwik Sriram (Executive Profile)",
                "audio_filename": "ceo_urgent_wire_cloned.wav",
                "transcript": "Urgent wire transfer required.",
                "transaction_amount_inr": 500000.0,
                "target_beneficiary": "Acme Ventures Holdings",
                "attack_type": "AI Voice Cloning",
                "target_victim": "Corporate Officer",
                "is_synthetic_ground_truth": True
            }
        ]


scenario_manager = ScenarioManager()
