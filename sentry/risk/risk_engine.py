"""
Multi-Factor Dynamic Risk Scoring & Explainability Engine for SENTRY.
Combines Voice Authenticity, Speaker Verification, Transaction Exposure,
and Behavioral Coercion into an actionable 0-100 Fraud Risk Score.
"""

from typing import Dict, Any, Optional
import numpy as np

from sentry.core.config import settings


class SentryRiskEngine:
    """Calculates multi-dimensional impersonation and financial fraud risk scores."""

    def __init__(self):
        self.weights = settings.risk_weights

    def calculate_transaction_exposure_factor(self, amount_inr: float) -> float:
        """
        Maps transaction amount in INR to a non-linear sensitivity factor [0.0, 1.0].
        ₹0 -> 0.05
        ₹10,000 -> 0.30
        ₹50,000 -> 0.65
        ₹2,00,000 -> 0.85
        ₹10,00,000+ -> 1.00
        """
        if amount_inr <= 0:
            return 0.05
        # Logarithmic saturation curve
        log_val = np.log10(max(amount_inr, 100.0))
        # Log10: 2 (100) -> 0.05, 4 (10k) -> 0.35, 5 (100k) -> 0.70, 6 (1M) -> 0.95
        factor = (log_val - 2.0) / 4.0
        return float(np.clip(factor, 0.05, 1.0))

    def evaluate_risk(
        self,
        synthetic_prob: float,
        speaker_match_risk: float,
        behavioral_threat_score: float,
        transaction_amount_inr: float = 0.0,
        context_risk: float = 0.10,
        is_enrolled_speaker: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluates the combined multi-layer risk score:
        Risk = w1*P_synth + w2*Speaker_Mismatch + w3*Exposure + w4*Behavioral + w5*Context
        """
        exposure_factor = self.calculate_transaction_exposure_factor(transaction_amount_inr)

        # Dynamic weight adjustment if speaker is not enrolled
        w_synth = self.weights.weight_synthetic
        w_spk = self.weights.weight_speaker_mismatch if is_enrolled_speaker else 0.05
        w_exp = self.weights.weight_transaction_exposure
        w_beh = self.weights.weight_behavioral_threat
        w_ctx = self.weights.weight_context_anomaly

        total_weight = w_synth + w_spk + w_exp + w_beh + w_ctx

        # Normalized contributions
        c_synth = (w_synth / total_weight) * synthetic_prob
        c_spk = (w_spk / total_weight) * speaker_match_risk
        c_exp = (w_exp / total_weight) * exposure_factor
        c_beh = (w_beh / total_weight) * behavioral_threat_score
        c_ctx = (w_ctx / total_weight) * context_risk

        raw_score = (c_synth + c_spk + c_exp + c_beh + c_ctx) * 100.0
        raw_score = float(np.clip(raw_score, 0.0, 100.0))

        # Determine Risk Tier
        if raw_score <= self.weights.threshold_low:
            tier = "LOW"
            color = "#10B981"  # Emerald Green
            recommendation = "Interaction authenticated. Proceed normally."
            action_code = "ALLOW"
        elif raw_score <= self.weights.threshold_moderate:
            tier = "MODERATE"
            color = "#F59E0B"  # Amber Warning
            recommendation = "Elevated risk signals detected. Recommend passive monitoring & step-up verification."
            action_code = "STEP_UP_RECOMMENDED"
        elif raw_score <= self.weights.threshold_high:
            tier = "HIGH"
            color = "#F97316"  # Orange Alert
            recommendation = "High impersonation threat! Trigger dynamic out-of-band challenge verification."
            action_code = "CHALLENGE_REQUIRED"
        else:
            tier = "CRITICAL"
            color = "#EF4444"  # Crimson Critical
            recommendation = "ACTIVE VOICE CLONING ATTACK DETECTED! Automated transaction hold & lock triggered."
            action_code = "TRANSACTION_FREEZE"

        # Percentage breakdown of risk factors (for explainable UI radar/bar chart)
        sum_c = c_synth + c_spk + c_exp + c_beh + c_ctx + 1e-9
        contributors = {
            "synthetic_voice": round(float(c_synth / sum_c * 100.0), 1),
            "speaker_mismatch": round(float(c_spk / sum_c * 100.0), 1),
            "transaction_exposure": round(float(c_exp / sum_c * 100.0), 1),
            "behavioral_coercion": round(float(c_beh / sum_c * 100.0), 1),
            "context_anomaly": round(float(c_ctx / sum_c * 100.0), 1)
        }

        return {
            "overall_risk_score": round(raw_score, 1),
            "risk_tier": tier,
            "tier_color": color,
            "action_code": action_code,
            "recommendation": recommendation,
            "factors": {
                "synthetic_probability": round(synthetic_prob, 4),
                "speaker_mismatch_risk": round(speaker_match_risk, 4),
                "transaction_exposure_factor": round(exposure_factor, 4),
                "behavioral_threat_score": round(behavioral_threat_score, 4),
                "context_risk": round(context_risk, 4)
            },
            "contributors_percentage": contributors
        }


risk_engine = SentryRiskEngine()
