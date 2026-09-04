"""
test_edge_cases.py
==================
Tests for the 8 key edge cases specified in Section 47.
"""

from datetime import datetime, timedelta, timezone
import pandas as pd
import pytest

from backend.services.confidence_engine import calculate_confidence
from backend.services.conflict_detector import detect_conflicts
from backend.services.duplicate_detector import detect_duplicates_and_correlations
from backend.services.freshness_engine import evaluate_freshness
from backend.services.priority_engine import calculate_priority


def test_edge_case_1_single_citizen_report_confidence_capped():
    """Case 1: Single Citizen Report, No corroboration, No media, Pending verification -> Capped."""
    report = {
        "source_type": "Citizen Report",
        "corroborating_report_count": 0,
        "media_type": "None",
        "responder_status": "Pending",
        "location_precision": "Exact",
    }
    # Raw formula with freshness=1.0 & exact location might yield score > 69 if uncapped
    res = calculate_confidence(report, freshness_score=1.00, independent_corroboration_count=0)
    assert res["confidence_score"] <= 69.0


def test_edge_case_2_missing_timestamp():
    """Case 2: Missing timestamp -> Freshness = Unknown, No crash."""
    res = evaluate_freshness(None)
    assert res["freshness_state"] == "Unknown"
    assert res["freshness_score"] == 0.00


def test_edge_case_3_stale_report():
    """Case 3: Stale report -> Freshness = Stale, report remains visible."""
    now = datetime.now(tz=timezone.utc)
    stale_ts = now - timedelta(hours=12)
    res = evaluate_freshness(stale_ts, now=now)
    assert res["freshness_state"] == "Stale"
    assert res["freshness_score"] == 0.20


def test_edge_case_4_conflicting_reports():
    """Case 4: Conflicting reports -> Conflict detected, human review recommended."""
    df = pd.DataFrame([
        {
            "report_id": "RPT-C1",
            "incident_type": "Road Flooding",
            "latitude": 28.6000,
            "longitude": 77.2000,
            "status": "Verified",
            "description": "Road completely blocked.",
            "timestamp": "2026-09-04T10:00:00Z",
        },
        {
            "report_id": "RPT-C2",
            "incident_type": "Road Flooding",
            "latitude": 28.6001,
            "longitude": 77.2001,
            "status": "Rejected",
            "description": "Road clear.",
            "timestamp": "2026-09-04T10:05:00Z",
        },
    ])
    conflicts = detect_conflicts(df)
    assert conflicts["RPT-C1"]["conflict_detected"] is True
    assert "Human verification" in conflicts["RPT-C1"]["conflict_explanation"]


def test_edge_case_5_near_duplicate_reports():
    """Case 5: Near-duplicate reports -> Grouped/correlated, independent corroboration discounted."""
    df = pd.DataFrame([
        {
            "report_id": "RPT-D1",
            "incident_type": "Structural Damage",
            "latitude": 28.6500,
            "longitude": 77.2300,
            "description": "Building wall leaning dangerously near old town.",
            "timestamp": "2026-09-04T10:00:00Z",
            "corroborating_report_count": 8,
        },
        {
            "report_id": "RPT-D2",
            "incident_type": "Structural Damage",
            "latitude": 28.6501,
            "longitude": 77.2301,
            "description": "Building wall leaning dangerously near old town.",
            "timestamp": "2026-09-04T10:02:00Z",
            "corroborating_report_count": 8,
        },
    ])
    dups = detect_duplicates_and_correlations(df)
    assert dups["RPT-D1"]["duplicate_detected"] is True
    assert dups["RPT-D1"]["independent_corroboration_count"] < 8


def test_edge_case_6_future_timestamp():
    """Case 6: Future timestamp -> Freshness = Unknown, Warning shown."""
    now = datetime.now(tz=timezone.utc)
    future_ts = now + timedelta(hours=2)
    res = evaluate_freshness(future_ts, now=now)
    assert res["freshness_state"] == "Unknown"
    assert "future" in res["freshness_warning"]


def test_edge_case_7_missing_media():
    """Case 7: Missing media -> Media evidence = 0, report NOT automatically false."""
    report = {
        "source_type": "Emergency Call",
        "location_precision": "High",
        "media_type": "None",
        "responder_status": "Verified",
        "corroborating_report_count": 3,
    }
    res = calculate_confidence(report, freshness_score=0.80)
    assert res["confidence_score"] > 60.0


def test_edge_case_8_high_priority_low_confidence():
    """Case 8: Evacuation Needed + Fresh + Low confidence -> High Priority surfaced."""
    report = {
        "incident_type": "Evacuation Needed",
        "permit_impact": "Critical",
        "description": "Chemical spill nearby necessitates evacuation.",
    }
    res = calculate_priority(report, confidence_score=35.0, freshness_state="Fresh")
    assert res["priority_score"] >= 60.0
    assert res["priority_category"] in ("High", "Critical")
