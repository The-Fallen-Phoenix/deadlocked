"""
Enterprise ROI and What-If Economic Simulator for SENTRY.
Models enterprise deployments for Banks, Telecoms, and Fintech platforms.
"""

from typing import Dict, Any, Optional
from sentry.risk.financial_engine import financial_engine


class EnterpriseROISimulator:
    """Simulates economic impact, fraud loss reduction, and return on investment."""

    def simulate(
        self,
        annual_interactions: int = 12000000,      # e.g., 12 Million transactions/calls
        avg_transaction_value_inr: float = 25000.0, # e.g., ₹25,000 avg ticket size
        estimated_fraud_rate_pct: float = 0.15,   # e.g., 0.15% fraud incidence
        detection_improvement_pct: float = 65.0,  # e.g., 65% improvement
        annual_platform_cost_inr: float = 2400000.0 # e.g., ₹24 Lakhs platform cost
    ) -> Dict[str, Any]:
        """
        Executes enterprise economic ROI scenario modeling.
        """
        # Baseline calculations
        annual_fraud_incidents = int(annual_interactions * (estimated_fraud_rate_pct / 100.0))
        total_fraud_exposure_before = annual_fraud_incidents * avg_transaction_value_inr

        # SENTRY Impact
        prevention_rate = detection_improvement_pct / 100.0
        potential_exposure_avoided = total_fraud_exposure_before * prevention_rate
        residual_fraud_exposure_after = total_fraud_exposure_before - potential_exposure_avoided

        # Net Financial Savings & ROI
        net_annual_savings = potential_exposure_avoided - annual_platform_cost_inr
        roi_multiplier = (potential_exposure_avoided / max(annual_platform_cost_inr, 1.0))
        
        # Break-Even period in months
        monthly_avoided = potential_exposure_avoided / 12.0
        break_even_months = annual_platform_cost_inr / max(monthly_avoided, 1.0) if monthly_avoided > 0 else 12.0

        # Per interaction cost
        cost_per_interaction_inr = annual_platform_cost_inr / max(annual_interactions, 1)

        return {
            "inputs": {
                "annual_interactions": annual_interactions,
                "avg_transaction_value_inr": avg_transaction_value_inr,
                "estimated_fraud_rate_pct": estimated_fraud_rate_pct,
                "detection_improvement_pct": detection_improvement_pct,
                "annual_platform_cost_inr": annual_platform_cost_inr,
                "formatted_platform_cost": financial_engine.format_inr(annual_platform_cost_inr)
            },
            "metrics": {
                "annual_fraud_incidents": annual_fraud_incidents,
                "total_exposure_before_inr": round(total_fraud_exposure_before, 2),
                "formatted_exposure_before": financial_engine.format_inr(total_fraud_exposure_before),
                "residual_exposure_after_inr": round(residual_fraud_exposure_after, 2),
                "formatted_residual_exposure": financial_engine.format_inr(residual_fraud_exposure_after),
                "potential_exposure_avoided_inr": round(potential_exposure_avoided, 2),
                "formatted_exposure_avoided": financial_engine.format_inr(potential_exposure_avoided),
                "net_annual_savings_inr": round(net_annual_savings, 2),
                "formatted_net_savings": financial_engine.format_inr(net_annual_savings),
                "roi_multiplier": round(roi_multiplier, 1),
                "roi_label": f"{roi_multiplier:.1f}x",
                "break_even_months": round(break_even_months, 1),
                "cost_per_interaction_inr": round(cost_per_interaction_inr, 4)
            }
        }


roi_simulator = EnterpriseROISimulator()
