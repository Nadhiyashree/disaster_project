"""
test_freshness.py
=================
Tests for freshness_engine.py module.
"""

from datetime import datetime, timedelta, timezone
import pytest
from backend.services.freshness_engine import evaluate_freshness


def test_fresh_report():
    now = datetime.now(tz=timezone.utc)
    ts = now - timedelta(minutes=5)
    res = evaluate_freshness(ts, now=now)
    assert res["freshness_score"] == 1.00
    assert res["freshness_state"] == "Fresh"
    assert res["minutes_since_report"] == 5.0
    assert res["freshness_warning"] is None


def test_aging_report():
    now = datetime.now(tz=timezone.utc)
    ts = now - timedelta(minutes=45)
    res = evaluate_freshness(ts, now=now)
    assert res["freshness_score"] == 0.75
    assert res["freshness_state"] == "Aging"


def test_old_report():
    now = datetime.now(tz=timezone.utc)
    ts = now - timedelta(minutes=200)
    res = evaluate_freshness(ts, now=now)
    assert res["freshness_score"] == 0.45
    assert res["freshness_state"] == "Old"


def test_stale_report():
    now = datetime.now(tz=timezone.utc)
    ts = now - timedelta(minutes=500)
    res = evaluate_freshness(ts, now=now)
    assert res["freshness_score"] == 0.20
    assert res["freshness_state"] == "Stale"


def test_missing_timestamp():
    res = evaluate_freshness(None)
    assert res["freshness_score"] == 0.00
    assert res["freshness_state"] == "Unknown"
    assert res["minutes_since_report"] is None
    assert "Missing" in res["freshness_warning"]


def test_future_timestamp():
    now = datetime.now(tz=timezone.utc)
    future_ts = now + timedelta(minutes=30)
    res = evaluate_freshness(future_ts, now=now)
    assert res["freshness_score"] == 0.00
    assert res["freshness_state"] == "Unknown"
    assert res["freshness_warning"] == "Timestamp appears to be in the future."
