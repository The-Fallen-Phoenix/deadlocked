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
        # Security Policy: Synthetic voice clone combined with substantial financial exposure or coercion triggers immediate defense
        if synthetic_prob >= 0.70:
            if transaction_amount_inr >= 100000.0 or behavioral_threat_score >= 0.40:
                raw_score = max(raw_score, 84.5)  # Escalate to CRITICAL (Freeze / Hold)
            else:
                raw_score = max(raw_score, 68.0)  # Escalate to HIGH (Step-Up Challenge)

        raw_score = float(np.clip(raw_score, 0.0, 100.0))

        # Determine Risk Tier and Action Code
        if raw_score <= self.weights.threshold_low:
            tier = "LOW"
            action_code = "ALLOW"
            color = "#10B981"  # Emerald Green
            recommendation = "Interaction authenticated. Proceed normally."
        elif raw_score <= self.weights.threshold_moderate:
            tier = "MODERATE"
            action_code = "ALERT"
            color = "#F59E0B"  # Amber
            recommendation = "Step-up authentication recommended (OTP, secondary factor)."
        elif raw_score <= self.weights.threshold_high:
            tier = "HIGH"
            action_code = "DYNAMIC_CHALLENGE"
            color = "#EF5350"  # Red
            recommendation = "Transaction flagged for manual SOC review. Consider freezing."
        else:
            tier = "CRITICAL"
            action_code = "TRANSACTION_FREEZE"
            color = "#DC2626"  # Dark Red
            recommendation = "IMMEDIATE ACTION: Freeze transaction and alert Security Operations Center."

        total_contrib = c_synth + c_spk + c_exp + c_beh + c_ctx
        if total_contrib > 0:
            contributors_pct = {
                "synthetic_voice": round((c_synth / total_contrib) * 100.0, 1),
                "speaker_mismatch": round((c_spk / total_contrib) * 100.0, 1),
                "transaction_exposure": round((c_exp / total_contrib) * 100.0, 1),
                "behavioral_threat": round((c_beh / total_contrib) * 100.0, 1),
                "context_anomaly": round((c_ctx / total_contrib) * 100.0, 1)
            }
        else:
            contributors_pct = {
                "synthetic_voice": 35.0,
                "speaker_mismatch": 25.0,
                "transaction_exposure": 15.0,
                "behavioral_threat": 15.0,
                "context_anomaly": 10.0
            }

        return {
            "overall_risk_score": round(raw_score, 1),
            "risk_tier": tier,
            "action_code": action_code,
            "color_indicator": color,
            "recommendation": recommendation,
            "contributors_percentage": contributors_pct,
            "component_scores": contributors_pct,
            "thresholds": {
                "low_threshold": self.weights.threshold_low,
                "moderate_threshold": self.weights.threshold_moderate,
                "high_threshold": self.weights.threshold_high
            }
        }


risk_engine = SentryRiskEngine()
