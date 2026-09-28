"""
conflict_detector.py
====================
Detects conflicting crowd-reports using a documented spatial-temporal
first-pass filter followed by evidence contradiction analysis.

Algorithm (Phase 2)
-------------------
Step 1 — Spatial-temporal candidate selection:
    Two reports become conflict *candidates* when:
        Haversine distance ≤ SPATIAL_THRESHOLD_KM  (1.0 km)
        AND |Δt| ≤ TEMPORAL_WINDOW_MINUTES         (30 min)
    If either timestamp is missing the temporal condition is *skipped*
    (reports with missing timestamps are not falsely excluded).

Step 2 — Evidence contradiction analysis:
    Among candidates, a conflict is raised when at least one of:

    a) Verification Status Discrepancy
       One report has status "Verified" while the other has "Rejected" for
       the SAME incident type in the SAME vicinity and timeframe.

    b) Material Claim Conflict
       One description contains BLOCKED_WORDS (severe/blocked/submerged …)
       while the other contains CLEAR_WORDS (clear/passable/resolved …)
       for reports about the same incident type.

Thresholds (single source of truth — no inline magic numbers)
-------------------------------------------------------------
SPATIAL_THRESHOLD_KM    = 1.0  km
TEMPORAL_WINDOW_MINUTES = 30   min

Output fields per report
------------------------
    conflict_detected           : bool
    conflict_type               : str | None
    related_report_ids          : List[str]
    conflict_explanation        : str
    spatial_distance_km         : float | None   (distance to first conflicting peer)
    temporal_difference_minutes : float | None   (|Δt| to first conflicting peer)

Privacy / operational note
--------------------------
The conflict explanation never exposes the internal ``ground_truth`` field.
All wording refers only to submitted report content and verification status.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from backend.services.haversine_utils import SPATIAL_THRESHOLD_KM, safe_haversine_distance

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Documented thresholds
# ---------------------------------------------------------------------------

#: Temporal window (minutes) for conflict candidate selection.
#: Two same-type reports within this window AND within SPATIAL_THRESHOLD_KM
#: become conflict candidates.  Inherited from haversine_utils for spatial.
TEMPORAL_WINDOW_MINUTES: float = 30.0

# ---------------------------------------------------------------------------
# Evidence keyword lists
# ---------------------------------------------------------------------------

#: Words that indicate a severe / blocked / dangerous situation.
BLOCKED_WORDS: frozenset = frozenset({
    "blocked", "impassable", "submerged", "inundated", "collapsed",
    "trapped", "severe", "flooding", "destroyed", "inaccessible",
})

#: Words that indicate the situation is clear / safe / resolved.
CLEAR_WORDS: frozenset = frozenset({
    "clear", "passable", "open", "minor", "intact", "no damage",
    "resolved", "safe", "passable", "driveable", "accessible",
})


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _has_blocked_signal(description: str) -> bool:
    return any(w in description for w in BLOCKED_WORDS)


def _has_clear_signal(description: str) -> bool:
    return any(w in description for w in CLEAR_WORDS)


def _build_conflict_explanation(
    conflict_type: str,
    dist_km: float,
    time_diff_min: Optional[float],
) -> str:
    """Return a human-readable, non-sensitive conflict explanation string."""
    base = (
        f"Conflicting observations detected within "
        f"{dist_km * 1000:.0f} m"
    )
    if time_diff_min is not None:
        base += f" and {time_diff_min:.0f} min"
    base += f". Type: {conflict_type}. Human verification recommended."
    return base


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_conflicts(
    df: pd.DataFrame,
    dist_threshold_km: float = SPATIAL_THRESHOLD_KM,
    time_window_minutes: float = TEMPORAL_WINDOW_MINUTES,
) -> Dict[str, Dict[str, Any]]:
    """Detect conflicting disaster reports using spatial-temporal evidence.

    Parameters
    ----------
    df : pd.DataFrame
        Reports dataframe with columns: report_id, latitude, longitude,
        incident_type, status, description, timestamp.
    dist_threshold_km : float
        Spatial candidate threshold in km (Haversine). Default = 1.0 km.
    time_window_minutes : float
        Temporal candidate window in minutes. Default = 30 min.

    Returns
    -------
    dict mapping report_id (str) to:
        conflict_detected           : bool
        conflict_type               : str | None
        related_report_ids          : List[str]
        conflict_explanation        : str
        spatial_distance_km         : float | None
        temporal_difference_minutes : float | None
    """
    records = df.to_dict("records")
    n = len(records)

    # Initialise output for every report
    conflicts: Dict[str, Dict[str, Any]] = {
        str(r["report_id"]): {
            "conflict_detected": False,
            "conflict_type": None,
            "related_report_ids": [],
            "conflict_explanation": "No known conflicting reports.",
            "spatial_distance_km": None,
            "temporal_difference_minutes": None,
        }
        for r in records
    }

    for i in range(n):
        r1 = records[i]
        id1 = str(r1["report_id"])
        lat1: Optional[float] = float(r1["latitude"]) if pd.notna(r1["latitude"]) else None
        lon1: Optional[float] = float(r1["longitude"]) if pd.notna(r1["longitude"]) else None
        inc1: str = str(r1["incident_type"])
        status1: str = str(r1["status"])
        desc1: str = str(r1.get("description", "")).lower()
        ts1 = pd.to_datetime(r1["timestamp"], utc=True) if pd.notna(r1["timestamp"]) else None

        if lat1 is None or lon1 is None:
            continue

        for j in range(i + 1, n):
            r2 = records[j]
            id2 = str(r2["report_id"])
            inc2: str = str(r2["incident_type"])

            # Only compare reports of the same incident type
            if inc1 != inc2:
                continue

            lat2: Optional[float] = float(r2["latitude"]) if pd.notna(r2["latitude"]) else None
            lon2: Optional[float] = float(r2["longitude"]) if pd.notna(r2["longitude"]) else None

            if lat2 is None or lon2 is None:
                continue

            # Step 1a — Spatial filter (Haversine)
            dist_km = safe_haversine_distance(lat1, lon1, lat2, lon2)
            if dist_km is None or dist_km > dist_threshold_km:
                continue

            # Step 1b — Temporal filter (skip if either timestamp missing)
            ts2 = pd.to_datetime(r2["timestamp"], utc=True) if pd.notna(r2["timestamp"]) else None
            time_diff_min: Optional[float] = None
            if ts1 is not None and ts2 is not None:
                time_diff_min = abs((ts1 - ts2).total_seconds()) / 60.0
                if time_diff_min > time_window_minutes:
                    continue
            # If timestamps are missing, do NOT skip — the reports are still
            # spatially proximate candidates; lack of timestamp ≠ no conflict.

            # Step 2 — Evidence contradiction analysis
            status2: str = str(r2["status"])
            desc2: str = str(r2.get("description", "")).lower()

            # Condition A: Verification status discrepancy
            is_status_conflict: bool = (
                (status1 == "Verified" and status2 == "Rejected")
                or (status1 == "Rejected" and status2 == "Verified")
            )

            # Condition B: Opposing description claims
            is_claim_conflict: bool = (
                (_has_blocked_signal(desc1) and _has_clear_signal(desc2))
                or (_has_clear_signal(desc1) and _has_blocked_signal(desc2))
            )

            if not (is_status_conflict or is_claim_conflict):
                continue

            # Determine conflict type label
            conflict_type: str
            if is_status_conflict and is_claim_conflict:
                conflict_type = "Verification Status & Material Claim Conflict"
            elif is_status_conflict:
                conflict_type = "Verification Status Discrepancy"
            else:
                conflict_type = "Material Claim Conflict"

            explanation = _build_conflict_explanation(conflict_type, dist_km, time_diff_min)

            # Record for report id1
            _update_conflict_record(
                conflicts, id1, id2, conflict_type, explanation, dist_km, time_diff_min
            )
            # Record for report id2 (symmetrical)
            _update_conflict_record(
                conflicts, id2, id1, conflict_type, explanation, dist_km, time_diff_min
            )

    return conflicts


def _update_conflict_record(
    conflicts: Dict[str, Dict[str, Any]],
    primary_id: str,
    related_id: str,
    conflict_type: str,
    explanation: str,
    dist_km: float,
    time_diff_min: Optional[float],
) -> None:
    """Update the conflict record for a single report in-place."""
    rec = conflicts[primary_id]
    rec["conflict_detected"] = True
    rec["conflict_type"] = conflict_type
    rec["conflict_explanation"] = explanation
    if related_id not in rec["related_report_ids"]:
        rec["related_report_ids"].append(related_id)
    # Store spatial/temporal metadata from the first detected conflict pair
    if rec["spatial_distance_km"] is None:
        rec["spatial_distance_km"] = round(dist_km, 4)
    if rec["temporal_difference_minutes"] is None and time_diff_min is not None:
        rec["temporal_difference_minutes"] = round(time_diff_min, 2)
