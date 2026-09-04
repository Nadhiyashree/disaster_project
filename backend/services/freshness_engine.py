"""
freshness_engine.py
===================
Calculates report freshness based on timestamp recency.

Rules:
  0–15 minutes   → 1.00 ("Fresh")
  15–120 minutes → 0.75 ("Aging")
  2–6 hours      → 0.45 ("Old")
  >6 hours       → 0.20 ("Stale")
  Missing/Future → 0.00 ("Unknown")
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import pandas as pd


def evaluate_freshness(
    timestamp: Any,
    last_updated: Any = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Evaluates the freshness score and human-readable state of a report.
    Handles None, NaT, invalid formats, and future timestamps safely.
    """
    if now is None:
        now = datetime.now(tz=timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    # Parse timestamp safely
    ts_dt = _parse_datetime(timestamp)
    lu_dt = _parse_datetime(last_updated) or ts_dt

    if ts_dt is None:
        return {
            "freshness_score": 0.00,
            "freshness_state": "Unknown",
            "minutes_since_report": None,
            "last_updated": lu_dt.isoformat() if lu_dt else None,
            "freshness_warning": "Missing or unparseable timestamp.",
        }

    # Ensure UTC timezone
    if ts_dt.tzinfo is None:
        ts_dt = ts_dt.replace(tzinfo=timezone.utc)

    delta_seconds = (now - ts_dt).total_seconds()

    # Future timestamp check
    if delta_seconds < 0:
        return {
            "freshness_score": 0.00,
            "freshness_state": "Unknown",
            "minutes_since_report": round(delta_seconds / 60.0, 2),
            "last_updated": lu_dt.isoformat() if lu_dt else ts_dt.isoformat(),
            "freshness_warning": "Timestamp appears to be in the future.",
        }

    minutes_since = delta_seconds / 60.0

    if minutes_since <= 15:
        score = 1.00
        state = "Fresh"
    elif minutes_since <= 120:
        score = 0.75
        state = "Aging"
    elif minutes_since <= 360:  # 6 hours
        score = 0.45
        state = "Old"
    else:
        score = 0.20
        state = "Stale"

    return {
        "freshness_score": score,
        "freshness_state": state,
        "minutes_since_report": round(minutes_since, 1),
        "last_updated": lu_dt.isoformat() if lu_dt else ts_dt.isoformat(),
        "freshness_warning": None,
    }


def _parse_datetime(val: Any) -> Optional[datetime]:
    if val is None or pd.isna(val):
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception:
            try:
                dt = pd.to_datetime(val, utc=True)
                return dt.to_pydatetime() if pd.notna(dt) else None
            except Exception:
                return None
    return None
