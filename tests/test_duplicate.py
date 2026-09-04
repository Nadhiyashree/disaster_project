"""
test_duplicate.py
=================
Tests for duplicate_detector.py module.
"""

import pandas as pd
import pytest
from backend.services.duplicate_detector import detect_duplicates_and_correlations


def test_near_duplicate_clustering():
    df = pd.DataFrame([
        {
            "report_id": "RPT-100",
            "incident_type": "Power Outage",
            "latitude": 28.6300,
            "longitude": 77.2200,
            "description": "Complete power failure across central avenue substation.",
            "timestamp": "2026-09-04T12:00:00Z",
            "corroborating_report_count": 10,
        },
        {
            "report_id": "RPT-101",
            "incident_type": "Power Outage",
            "latitude": 28.6301,
            "longitude": 77.2201,
            "description": "Substation power failure reported across central avenue.",
            "timestamp": "2026-09-04T12:05:00Z",
            "corroborating_report_count": 10,
        },
    ])

    res = detect_duplicates_and_correlations(df)
    assert res["RPT-100"]["duplicate_detected"] is True
    assert res["RPT-101"]["duplicate_detected"] is True
    assert res["RPT-100"]["correlation_group_id"] == res["RPT-101"]["correlation_group_id"]
    # Check that independent corroboration count is discounted
    assert res["RPT-100"]["independent_corroboration_count"] < res["RPT-100"]["raw_corroboration_count"]


def test_unrelated_reports_no_duplicate():
    df = pd.DataFrame([
        {
            "report_id": "RPT-200",
            "incident_type": "Medical Emergency",
            "latitude": 28.5000,
            "longitude": 77.1800,
            "description": "Elderly person collapsed.",
            "timestamp": "2026-09-04T12:00:00Z",
            "corroborating_report_count": 1,
        },
        {
            "report_id": "RPT-201",
            "incident_type": "Water Contamination",
            "latitude": 28.7500,
            "longitude": 77.1200,
            "description": "Discoloured tap water.",
            "timestamp": "2026-09-04T12:00:00Z",
            "corroborating_report_count": 1,
        },
    ])

    res = detect_duplicates_and_correlations(df)
    assert res["RPT-200"]["duplicate_detected"] is False
    assert res["RPT-201"]["duplicate_detected"] is False
