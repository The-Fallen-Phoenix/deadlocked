"""
Integration tests for SENTRY FastAPI Endpoints using TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from sentry.api.main import app

client = TestClient(app)


def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert data["app"] == "SENTRY"


def test_api_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_threats_analyzed" in data
    assert "total_avoided_inr" in data


def test_api_scenarios_list_and_execution():
    # List scenarios
    res_list = client.get("/api/scenarios")
    assert res_list.status_code == 200
    scenarios = res_list.json()
    assert len(scenarios) >= 4

    # Run first scenario
    sc_id = scenarios[0]["id"]
    res_run = client.post(f"/api/scenarios/run/{sc_id}")
    assert res_run.status_code == 200
    res_data = res_run.json()
    assert "authenticity" in res_data
    assert "risk_evaluation" in res_data
    assert "prevention_action" in res_data


def test_api_speakers():
    response = client.get("/api/speakers")
    assert response.status_code == 200
    speakers = response.json()
    assert isinstance(speakers, list)
    assert len(speakers) >= 1


def test_api_roi_simulation():
    payload = {
        "annual_interactions": 10000000,
        "avg_transaction_value_inr": 20000.0,
        "estimated_fraud_rate_pct": 0.20,
        "detection_improvement_pct": 70.0,
        "annual_platform_cost_inr": 2000000.0
    }
    response = client.post("/api/simulation/roi", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert data["metrics"]["roi_multiplier"] > 5.0
