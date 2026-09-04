"""
test_priority.py
================
Tests for priority_engine.py module.
"""

import pytest
from backend.services.priority_engine import calculate_priority


def test_critical_medical_incident():
    report = {
        "incident_type": "Medical Emergency",
        "permit_impact": "Critical",
        "description": "Severe trauma case requiring immediate medical intervention.",
    }
    res = calculate_priority(report, confidence_score=85.0, freshness_state="Fresh")
    assert res["priority_score"] >= 80.0
    assert res["priority_category"] == "Critical"


def test_low_confidence_but_high_priority():
    """
    Demonstrates Confidence != Priority.
    An Evacuation Needed report with Low confidence must still surface as High/Critical Priority.
    """
    report = {
        "incident_type": "Evacuation Needed",
        "permit_impact": "High",
        "description": "Rising floodwater threatening residential blocks.",
    }
    # Low confidence score (e.g. 30.0)
    res = calculate_priority(report, confidence_score=30.0, freshness_state="Fresh")
    # Severity (100*0.35 = 35), Confidence (0.3*30 = 9), Freshness (1.0*20 = 20), Op urgency (~1.0*15 = 15) => Total ~79
    assert res["priority_score"] >= 60.0
    assert res["priority_category"] in ("High", "Critical")


def test_low_severity_incident():
    report = {
        "incident_type": "Power Outage",
        "permit_impact": "None",
        "description": "Minor streetlight flicker.",
    }
    res = calculate_priority(report, confidence_score=40.0, freshness_state="Stale")
    assert res["priority_score"] < 50.0
    assert res["priority_category"] in ("Low", "Medium")
