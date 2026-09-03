"""
Attack Scenario Manager for SENTRY Demonstrations and Security Evaluation.
"""

from typing import Dict, Any, List, Optional
from sentry.core.config import settings


class ScenarioManager:
    """Pre-configures real-world fraud and impersonation attack scenarios for live testing."""

    SCENARIOS = [
        {
            "id": "scenario_ceo_wire_transfer",
            "title": "CEO Urgent Wire Transfer Scam",
            "category": "Corporate Executive Impersonation",
            "description": "Deepfake voice clone of the Team Leader/CEO demanding an emergency ₹5 Lakh wire transfer to an unknown vendor account.",
            "claimed_speaker_id": "spk_rithwik",
            "claimed_speaker_name": "Rithwik Sriram (Executive Profile)",
            "audio_filename": "ceo_urgent_wire_cloned.wav",
            "transcript": "Sahil, this is Rithwik. I am in an urgent closed-door board meeting right now. We need an immediate wire transfer of ₹5,00,000 to this vendor account to secure the contract before 2 PM. Do not delay, process it right away!",
            "transaction_amount_inr": 500000.0,
            "target_beneficiary": "Acme Ventures Holdings (Unregistered Payee)",
            "attack_type": "AI Voice Cloning + Executive Authority Impersonation",
            "target_victim": "Corporate Finance Officer",
            "is_synthetic_ground_truth": True
        },
        {
            "id": "scenario_digital_arrest_police",
            "title": "Digital Arrest & Police Coercion Scam",
            "category": "Authority Extortion & Social Engineering",
            "description": "Fraudulent caller using synthetic speech claiming to be a CBI officer threatening digital arrest unless ₹2.5 Lakh is sent to a fake judicial escrow.",
            "claimed_speaker_id": None,
            "claimed_speaker_name": "Inspector Verma (Claimed Official)",
            "audio_filename": "digital_arrest_coercion_cloned.wav",
            "transcript": "This is Inspector Verma from CBI Cyber Cell Headquarters. An arrest warrant has been issued in your name for money laundering. You are under digital arrest. Transfer ₹2,50,000 immediately to the judicial escrow account or police will raid your premises within 30 minutes. Do not disconnect!",
            "transaction_amount_inr": 250000.0,
            "target_beneficiary": "Judicial Escrow Cyber Cell (Fraudulent Account)",
            "attack_type": "Digital Arrest + Legal Coercion Extortion",
            "target_victim": "Citizen / Banking Customer",
            "is_synthetic_ground_truth": True
        },
        {
            "id": "scenario_grandchild_emergency",
            "title": "Grandchild Emergency ICU Scam",
            "category": "Family Impersonation Extortion",
            "description": "AI-generated voice clone of a grandchild claiming to be in a hospital accident demanding an immediate ₹75,000 emergency deposit.",
            "claimed_speaker_id": "spk_aarav",
            "claimed_speaker_name": "Aarav Sharma (Enrolled Grandchild)",
            "audio_filename": "grandchild_hospital_cloned.wav",
            "transcript": "Grandpa, please help me! I was in a terrible road accident and the hospital doctor needs an immediate emergency ICU deposit of ₹75,000 right now. Please approve the UPI transfer immediately, my phone is dying!",
            "transaction_amount_inr": 75000.0,
            "target_beneficiary": "City Care Emergency Clinic (Unverified UPI VPA)",
            "attack_type": "Family Voice Clone + Urgent Medical Distress",
            "target_victim": "Senior Citizen",
            "is_synthetic_ground_truth": True
        },
        {
            "id": "scenario_legitimate_bank_support",
            "title": "Legitimate Bank Support Verification",
            "category": "Normal Banking Interaction",
            "description": "Legitimate support representative with natural acoustic human vocal tract and verified enrolled voice biometric profile.",
            "claimed_speaker_id": "spk_sahil",
            "claimed_speaker_name": "Sahil Singh (Enrolled Support Officer)",
            "audio_filename": "legitimate_support_genuine.wav",
            "transcript": "Good morning, this is Sahil from support. I am calling to follow up on your ticket regarding the recent statement query. There are no fees or transactions required, just confirming your request has been resolved.",
            "transaction_amount_inr": 0.0,
            "target_beneficiary": None,
            "attack_type": "None (Legitimate Customer Support)",
            "target_victim": "Account Holder",
            "is_synthetic_ground_truth": False
        },
        {
            "id": "scenario_dataset_test",
            "title": "Voice Dataset Benchmark Sample",
            "category": "Dataset Analysis Benchmarking",
            "description": "Synthetic voice clone sample extracted directly from the test split (UK Male) of the training dataset.",
            "claimed_speaker_id": None,
            "claimed_speaker_name": "Unknown Dataset Speaker (UK Male Test Split)",
            "audio_filename": "dataset_test_synthetic.mp3",
            "transcript": "(Dataset audio sample playing for forensic analysis)",
            "transaction_amount_inr": 0.0,
            "target_beneficiary": "N/A",
            "attack_type": "Synthetic Voice Generation",
            "target_victim": "System Evaluator",
            "is_synthetic_ground_truth": True
        }
    ]

    def list_scenarios(self) -> List[Dict[str, Any]]:
        """Returns all configured test scenarios."""
        return self.SCENARIOS

    def get_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific scenario configuration."""
        for s in self.SCENARIOS:
            if s["id"] == scenario_id:
                return s
        return None


scenario_manager = ScenarioManager()
