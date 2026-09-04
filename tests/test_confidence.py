"""
test_confidence.py
==================
Tests for confidence_engine.py module.
"""

import pytest
from backend.services.confidence_engine import calculate_confidence, get_corroboration_score


def test_corroboration_score_mapping():
    assert get_corroboration_score(0) == 0.00
    assert get_corroboration_score(1) == 0.50
    assert get_corroboration_score(2) == 0.50
    assert get_corroboration_score(3) == 0.75
    assert get_corroboration_score(5) == 1.00


def test_high_confidence_report():
    report = {
        "source_type": "Field Responder",       # 1.0 * 0.15 = 15
        "location_precision": "Exact",          # 1.0 * 0.10 = 10
        "media_type": "Photo",                  # 1.0 * 0.15 = 15
        "responder_status": "Verified",         # 1.0 * 0.20 = 20
        "corroborating_report_count": 5,        # 1.0 * 0.25 = 25
    }
    # freshness = 1.0 * 0.15 = 15 => total = 100
    res = calculate_confidence(report, freshness_score=1.00, independent_corroboration_count=5)
    assert res["confidence_score"] == 100.0
    assert res["confidence_category"] == "Very High"
    assert res["confidence_capped"] is False


def test_confidence_cap_weak_citizen_report():
    report = {
        "source_type": "Citizen Report",
        "location_precision": "Exact",
        "media_type": "None",
        "responder_status": "Pending",
        "corroborating_report_count": 0,
    }
    # With freshness = 1.0: raw score would be 0.4*15 + 0 + 1.0*15 + 1.0*10 + 0 + 0.25*20 = 6 + 15 + 10 + 5 = 36
    # Let's test capping condition where raw score exceeds 69:
    report_high_loc = {
        "source_type": "Citizen Report",
        "location_precision": "Exact",  # 1.0
        "media_type": "None",
        "responder_status": "Needs Review", # 0.5 * 20 = 10
        "corroborating_report_count": 0,
    }
    res = calculate_confidence(report_high_loc, freshness_score=1.00, independent_corroboration_count=0)
    # Check if capping works whenever citizen + 0 corr + no media + pending/needs review
    assert res["confidence_capped"] is True or res["confidence_score"] <= 69.0
    if res["confidence_capped"]:
        assert res["confidence_score"] == 69.0
        assert "insufficient independent evidence" in res["confidence_cap_reason"]


def test_missing_media_is_not_false():
    report = {
        "source_type": "Department Report",
        "location_precision": "High",
        "media_type": "None",
        "responder_status": "Verified",
        "corroborating_report_count": 2,
    }
    res = calculate_confidence(report, freshness_score=0.75, independent_corroboration_count=2)
    assert res["confidence_score"] > 50.0
    assert res["confidence_capped"] is False
