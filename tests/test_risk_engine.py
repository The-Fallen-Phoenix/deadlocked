"""
Unit tests for SENTRY Multi-Factor Dynamic Risk Scoring Engine.
"""

import pytest
from sentry.risk.risk_engine import risk_engine


def test_transaction_exposure_scaling():
    # Low amount
    f_low = risk_engine.calculate_transaction_exposure_factor(5000.0)
    # High amount
    f_high = risk_engine.calculate_transaction_exposure_factor(1000000.0)

    assert 0.05 <= f_low < f_high <= 1.0


def test_risk_evaluation_tiers():
    # 1. Critical Attack Scenario (High synth, mismatch, high amount, high threat)
    res_crit = risk_engine.evaluate_risk(
        synthetic_prob=0.95,
        speaker_match_risk=0.90,
        behavioral_threat_score=0.90,
        transaction_amount_inr=500000.0
    )
    assert res_crit["overall_risk_score"] >= 80.0
    assert res_crit["risk_tier"] == "CRITICAL"
    assert res_crit["action_code"] == "TRANSACTION_FREEZE"

    # 2. Low Risk Legitimate Scenario (Low synth, low mismatch, low threat, zero amount)
    res_low = risk_engine.evaluate_risk(
        synthetic_prob=0.05,
        speaker_match_risk=0.05,
        behavioral_threat_score=0.05,
        transaction_amount_inr=0.0
    )
    assert res_low["overall_risk_score"] <= 30.0
    assert res_low["risk_tier"] == "LOW"
    assert res_low["action_code"] == "ALLOW"


def test_risk_contributors_breakdown():
    res = risk_engine.evaluate_risk(
        synthetic_prob=0.8,
        speaker_match_risk=0.7,
        behavioral_threat_score=0.6,
        transaction_amount_inr=100000.0
    )
    contribs = res["contributors_percentage"]
    assert "synthetic_voice" in contribs
    assert "speaker_mismatch" in contribs
    assert "transaction_exposure" in contribs
    # Sum of percentages should be close to 100%
    total_pct = sum(contribs.values())
    assert 99.0 <= total_pct <= 101.0
