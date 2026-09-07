"""
test_experiments.py
===================
Unit and API integration tests for Phase 4 evaluation experiments,
baseline comparison, threshold trade-offs, proxy validation, and verification audit log.
"""

import os
import json
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from experiments.baseline import run_baseline_simulation
from experiments.evaluation import evaluate_threshold_tradeoffs
from experiments.validation import run_validation_study

client = TestClient(app)


def test_baseline_simulation_unit():
    result = run_baseline_simulation()
    assert "baseline_fifo" in result
    assert "priority_dashboard" in result
    assert "time_saved_percentage" in result
    assert result["baseline_fifo"]["avg_time_to_first_critical_mins"] > result["priority_dashboard"]["avg_time_to_first_critical_mins"]
    assert result["time_saved_percentage"] > 0


def test_baseline_experiment_endpoint():
    local_client = TestClient(app)
    res = local_client.get("/api/experiments/baseline")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert "status" in data, f"Key 'status' missing from response: {data}"
    assert data["status"] == "success"
    assert "results" in data
    assert "disclaimer" in data
    assert "simulated" in data["disclaimer"].lower()



def test_threshold_evaluation_unit():
    results = evaluate_threshold_tradeoffs()
    assert len(results) >= 3
    for row in results:
        assert "threshold" in row
        assert "precision" in row
        assert "recall" in row
        assert "reports_surfaced" in row or "surfaced_count" in row
        assert 0.0 <= row["precision"] <= 1.0
        assert 0.0 <= row["recall"] <= 1.0


def test_threshold_experiment_endpoint():
    res = client.get("/api/experiments/thresholds")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "results" in data
    assert "recommended_strategies" in data
    assert "0.30" in data["recommended_strategies"]
    assert "0.50" in data["recommended_strategies"]
    assert "0.65" in data["recommended_strategies"]


def test_validation_study_unit():
    study = run_validation_study()
    assert "summary" in study
    assert "results" in study
    assert len(study["results"]) == 3
    for item in study["results"]:
        assert item["time_saved_percent"] > 0
        assert item["evaluation_status"] == "COMPLETED_SIMULATION"



def test_validation_endpoint():
    res = client.get("/api/validation")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "summary" in data
    assert "results" in data
    assert "disclaimer" in data
    assert "proxy" in data["disclaimer"].lower() or "simulated" in data["disclaimer"].lower()


def test_verification_audit_log_append():
    # Perform a verification action
    res = client.post(
        "/api/reports/RPT-00003/verify",
        json={"status": "Rejected", "notes": "Phase 4 audit test note."},
    )
    assert res.status_code == 200

    # Verify that data/verification_audit.json exists and contains our entry
    audit_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "verification_audit.json")
    assert os.path.exists(audit_file)

    with open(audit_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    assert isinstance(records, list)
    matching = [r for r in records if r.get("report_id") == "RPT-00003" and r.get("new_status") == "Rejected"]
    assert len(matching) > 0
    latest = matching[-1]
    assert latest["notes"] == "Phase 4 audit test note."
    assert "timestamp" in latest
