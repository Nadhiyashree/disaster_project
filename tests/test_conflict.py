"""
test_conflict.py
================
Tests for conflict_detector.py module.
"""

import pandas as pd
import pytest
from backend.services.conflict_detector import detect_conflicts


def test_detect_claim_conflict():
    df = pd.DataFrame([
        {
            "report_id": "RPT-001",
            "incident_type": "Road Flooding",
            "zone": "Riverside",
            "latitude": 28.6700,
            "longitude": 77.2700,
            "status": "Needs Review",
            "description": "Road completely blocked and submerged under water.",
            "timestamp": "2026-09-04T10:00:00Z",
        },
        {
            "report_id": "RPT-002",
            "incident_type": "Road Flooding",
            "zone": "Riverside",
            "latitude": 28.6701,
            "longitude": 77.2701,
            "status": "Verified",
            "description": "Road currently passable with no standing water.",
            "timestamp": "2026-09-04T10:15:00Z",
        },
    ])

    conflicts = detect_conflicts(df)
    assert conflicts["RPT-001"]["conflict_detected"] is True
    assert conflicts["RPT-002"]["conflict_detected"] is True
    assert "Conflicting observations" in conflicts["RPT-001"]["conflict_explanation"]


def test_no_conflict_different_zones():
    df = pd.DataFrame([
        {
            "report_id": "RPT-010",
            "incident_type": "Road Flooding",
            "zone": "North District",
            "latitude": 28.7500,
            "longitude": 77.1200,
            "status": "Verified",
            "description": "Road blocked.",
            "timestamp": "2026-09-04T10:00:00Z",
        },
        {
            "report_id": "RPT-011",
            "incident_type": "Road Flooding",
            "zone": "South District",
            "latitude": 28.5000,
            "longitude": 77.1800,
            "status": "Verified",
            "description": "Road clear.",
            "timestamp": "2026-09-04T10:00:00Z",
        },
    ])

    conflicts = detect_conflicts(df)
    assert conflicts["RPT-010"]["conflict_detected"] is False
    assert conflicts["RPT-011"]["conflict_detected"] is False
