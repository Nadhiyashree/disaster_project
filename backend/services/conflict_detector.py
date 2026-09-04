"""
conflict_detector.py
====================
Detects conflicting crowd-reports for the same geographic zone / location and incident.

Uses neutral language and transparent criteria without judging individual reporters.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def detect_conflicts(
    df: pd.DataFrame,
    dist_threshold_km: float = 1.0,
    time_window_minutes: float = 360.0,
) -> Dict[str, Dict[str, Any]]:
    """
    Scans the dataset to identify conflicting reports.

    Returns mapping of report_id to:
      - conflict_detected: bool
      - conflict_type: Optional[str]
      - related_report_ids: List[str]
      - conflict_explanation: str
    """
    records = df.to_dict("records")
    n = len(records)

    # Keywords indicative of opposing operational assessments
    BLOCKED_WORDS = {"blocked", "impassable", "submerged", "inundated", "collapsed", "trapped", "severe"}
    CLEAR_WORDS = {"clear", "passable", "open", "minor", "intact", "no damage", "resolved", "safe"}

    conflicts: Dict[str, Dict[str, Any]] = {
        str(r["report_id"]): {
            "conflict_detected": False,
            "conflict_type": None,
            "related_report_ids": [],
            "conflict_explanation": "No known conflicting reports.",
        }
        for r in records
    }

    for i in range(n):
        r1 = records[i]
        id1 = str(r1["report_id"])
        lat1 = float(r1["latitude"]) if pd.notna(r1["latitude"]) else None
        lon1 = float(r1["longitude"]) if pd.notna(r1["longitude"]) else None
        inc1 = str(r1["incident_type"])
        status1 = str(r1["status"])
        desc1 = str(r1.get("description", "")).lower()
        ts1 = pd.to_datetime(r1["timestamp"], utc=True) if pd.notna(r1["timestamp"]) else None

        if lat1 is None or lon1 is None:
            continue

        for j in range(i + 1, n):
            r2 = records[j]
            id2 = str(r2["report_id"])
            inc2 = str(r2["incident_type"])

            if inc1 != inc2:
                continue

            lat2 = float(r2["latitude"]) if pd.notna(r2["latitude"]) else None
            lon2 = float(r2["longitude"]) if pd.notna(r2["longitude"]) else None

            if lat2 is None or lon2 is None:
                continue

            dist = _haversine_km(lat1, lon1, lat2, lon2)
            if dist > dist_threshold_km:
                continue

            ts2 = pd.to_datetime(r2["timestamp"], utc=True) if pd.notna(r2["timestamp"]) else None
            if ts1 is not None and ts2 is not None:
                time_diff = abs((ts1 - ts2).total_seconds()) / 60.0
                if time_diff > time_window_minutes:
                    continue

            status2 = str(r2["status"])
            desc2 = str(r2.get("description", "")).lower()

            # Conflict condition 1: Opposite status in same vicinity (Verified vs Rejected)
            is_status_conflict = (
                (status1 == "Verified" and status2 == "Rejected")
                or (status1 == "Rejected" and status2 == "Verified")
            )

            # Conflict condition 2: Description opposing claim
            has_blocked_1 = any(w in desc1 for w in BLOCKED_WORDS)
            has_clear_1 = any(w in desc1 for w in CLEAR_WORDS)
            has_blocked_2 = any(w in desc2 for w in BLOCKED_WORDS)
            has_clear_2 = any(w in desc2 for w in CLEAR_WORDS)

            is_claim_conflict = (has_blocked_1 and has_clear_2) or (has_clear_1 and has_blocked_2)

            if is_status_conflict or is_claim_conflict:
                c_type = (
                    "Verification Status Discrepancy"
                    if is_status_conflict
                    else "Material Claim Conflict"
                )
                exp = "Conflicting observations detected. Human verification recommended."

                # Update id1
                conflicts[id1]["conflict_detected"] = True
                conflicts[id1]["conflict_type"] = c_type
                if id2 not in conflicts[id1]["related_report_ids"]:
                    conflicts[id1]["related_report_ids"].append(id2)
                conflicts[id1]["conflict_explanation"] = exp

                # Update id2
                conflicts[id2]["conflict_detected"] = True
                conflicts[id2]["conflict_type"] = c_type
                if id1 not in conflicts[id2]["related_report_ids"]:
                    conflicts[id2]["related_report_ids"].append(id1)
                conflicts[id2]["conflict_explanation"] = exp

    return conflicts
