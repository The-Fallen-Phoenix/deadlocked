"""
Unit tests for SENTRY Financial Exposure & ROI Simulator Engine.
"""

import pytest
from sentry.risk.financial_engine import financial_engine
from sentry.risk.roi_simulator import roi_simulator


def test_financial_exposure_calculation():
    amount = 75000.0
    synth_prob = 0.93
    risk_score = 92.0

    res = financial_engine.compute_transaction_exposure(
        transaction_amount_inr=amount,
        synthetic_prob=synth_prob,
        overall_risk_score=risk_score
    )

    assert res["transaction_amount_inr"] == amount
    assert res["expected_loss_baseline_inr"] > res["residual_loss_inr"]
    assert res["avoided_exposure_inr"] > 0.0
    assert "₹" in res["formatted_avoided_exposure"]


def test_enterprise_roi_simulation():
    # Model mid-size bank from brief (12M interactions, ₹25k ticket, 0.15% fraud, ₹24 Lakhs cost)
    sim = roi_simulator.simulate(
        annual_interactions=12000000,
        avg_transaction_value_inr=25000.0,
        estimated_fraud_rate_pct=0.15,
        detection_improvement_pct=65.0,
        annual_platform_cost_inr=2400000.0
    )

    m = sim["metrics"]
    assert m["annual_fraud_incidents"] == 18000
    assert m["total_exposure_before_inr"] == 450000000.0  # ₹4.5 Cr
    assert m["potential_exposure_avoided_inr"] == 292500000.0  # ₹2.925 Cr
    assert m["roi_multiplier"] > 10.0  # >10x ROI
    assert m["break_even_months"] < 3.0  # <3 months break-even
