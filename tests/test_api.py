"""
test_api.py
===========
FastAPI endpoint integration tests using TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "disaster-response-dashboard"


def test_list_reports():
    res = client.get("/api/reports?limit=25&offset=0")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1000
    assert len(data["items"]) == 25

    # Check Phase 2 intelligence fields present
    first = data["items"][0]
    assert "confidence_score" in first
    assert "priority_score" in first
    assert "freshness_state" in first
    assert "conflict_detected" in first
    assert "duplicate_detected" in first


def test_single_report_details():
    res = client.get("/api/reports/RPT-00001")
    assert res.status_code == 200
    data = res.json()
    assert "report" in data
    assert data["report"]["report_id"] == "RPT-00001"
    assert "confidence" in data
    assert "priority" in data
    assert "freshness" in data


def test_single_report_not_found():
    res = client.get("/api/reports/RPT-999999-INVALID")
    assert res.status_code == 404


def test_priority_endpoint():
    res = client.get("/api/reports/priority?limit=10")
    assert res.status_code == 200
    data = res.json()
    items = data["items"]
    assert len(items) <= 10
    if len(items) > 1:
        # Check sorted by priority DESC
        assert items[0]["priority_score"] >= items[1]["priority_score"]


def test_stale_reports_endpoint():
    res = client.get("/api/reports/stale?limit=10")
    assert res.status_code == 200
    data = res.json()
    for item in data["items"]:
        assert item["freshness_state"] == "Stale"


def test_conflict_reports_endpoint():
    res = client.get("/api/reports/conflicts?limit=10")
    assert res.status_code == 200
    data = res.json()
    for item in data["items"]:
        assert item["conflict_detected"] is True


def test_human_verification_endpoint():
    # Update RPT-00002 to Verified
    res = client.post(
        "/api/reports/RPT-00002/verify",
        json={"status": "Verified", "notes": "Verified by responder unit 5."},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "Verified"
    assert data["responder_status"] == "Verified"


def test_dashboard_stats():
    res = client.get("/api/dashboard/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_reports"] >= 1000
    assert "critical_reports" in data
    assert "stale_reports" in data
    assert "average_confidence" in data
    assert "average_priority" in data


def test_metrics_endpoint():
    res = client.get("/api/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "precision" in data
    assert "recall" in data
    assert "false_positive_rate" in data
    assert "high_priority_missed" in data
    assert data["total_evaluated"] >= 1000
