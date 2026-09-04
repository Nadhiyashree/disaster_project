"""
duplicate_detector.py
=====================
Identifies duplicate and correlated disaster reports based on geographic proximity,
temporal proximity, incident type, and textual similarity.

Calculates independent corroboration count by discounting near-duplicate/correlated reports.
Does NOT use IP, device IDs, or personal identity tracking.
"""

from __future__ import annotations

from difflib import SequenceMatcher
import math
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in kilometers using Haversine formula."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def text_similarity(s1: str, s2: str) -> float:
    """Returns string similarity ratio between 0.0 and 1.0."""
    if not s1 or not s2:
        return 0.0
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def detect_duplicates_and_correlations(
    df: pd.DataFrame,
    dist_threshold_km: float = 0.5,
    text_sim_threshold: float = 0.6,
    time_window_minutes: float = 180.0,
) -> Dict[str, Dict[str, Any]]:
    """
    Scans the dataset to group correlated/duplicate reports.

    Returns a dictionary mapping report_id to:
      - duplicate_detected: bool
      - correlation_group_id: Optional[str]
      - related_report_ids: List[str]
      - similarity_reason: str
      - raw_corroboration_count: int
      - independent_corroboration_count: int
      - corroboration_adjustment_note: Optional[str]
    """
    records = df.to_dict("records")
    n = len(records)

    # Graph of connected components (adjacency list)
    adj: Dict[str, Set[str]] = {r["report_id"]: set() for r in records}
    reasons: Dict[Tuple[str, str], str] = {}

    for i in range(n):
        r1 = records[i]
        id1 = str(r1["report_id"])
        lat1 = float(r1["latitude"]) if pd.notna(r1["latitude"]) else None
        lon1 = float(r1["longitude"]) if pd.notna(r1["longitude"]) else None
        inc1 = str(r1["incident_type"])
        ts1 = pd.to_datetime(r1["timestamp"], utc=True) if pd.notna(r1["timestamp"]) else None
        desc1 = str(r1.get("description", ""))

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
            time_diff_min = None
            if ts1 is not None and ts2 is not None:
                time_diff_min = abs((ts1 - ts2).total_seconds()) / 60.0

            # Time proximity check (if timestamps exist)
            if time_diff_min is not None and time_diff_min > time_window_minutes:
                continue

            tsim = text_similarity(desc1, str(r2.get("description", "")))

            # If very close spatially & temporally + similar incident type
            is_match = False
            reason_str = ""

            if dist <= 0.2 and tsim >= 0.5:
                is_match = True
                reason_str = f"Near-identical location ({dist*1000:.0f}m away) and description similarity ({tsim*100:.0f}%)."
            elif dist <= dist_threshold_km and tsim >= text_sim_threshold:
                is_match = True
                reason_str = f"Geographic proximity ({dist*1000:.0f}m) and temporal overlap for {inc1}."

            if is_match:
                adj[id1].add(id2)
                adj[id2].add(id1)
                reasons[(id1, id2)] = reason_str
                reasons[(id2, id1)] = reason_str

    # Connected components for correlation groups
    visited: Set[str] = set()
    results: Dict[str, Dict[str, Any]] = {}
    group_counter = 1

    for r in records:
        rid = str(r["report_id"])
        raw_corr = int(r["corroborating_report_count"]) if pd.notna(r.get("corroborating_report_count")) else 0

        if rid in visited:
            continue

        # DFS to find cluster
        cluster: List[str] = []
        stack = [rid]
        visited.add(rid)
        while stack:
            curr = stack.pop()
            cluster.append(curr)
            for nbr in adj[curr]:
                if nbr not in visited:
                    visited.add(nbr)
                    stack.append(nbr)

        if len(cluster) > 1:
            group_id = f"CORR-GRP-{group_counter:04d}"
            group_counter += 1
            for cid in cluster:
                related = [x for x in cluster if x != cid]
                # Find specific reason with first neighbor
                first_nbr = related[0]
                reason = reasons.get(
                    (cid, first_nbr),
                    "Geographically and temporally correlated with neighboring reports.",
                )
                
                # Independent corroboration discount:
                # If there are correlated reports in the group, reduce the raw count to represent independent observations.
                # Correlated group of size G represents 1 primary event cluster.
                # Independent count is capped/discounted proportionally.
                discounted_corr = max(0, min(raw_corr, max(1, len(related) // 2)))
                note = (
                    "Several reports appear correlated and were not counted as fully independent corroboration."
                    if raw_corr > discounted_corr
                    else None
                )

                results[cid] = {
                    "duplicate_detected": True,
                    "correlation_group_id": group_id,
                    "related_report_ids": related,
                    "similarity_reason": reason,
                    "raw_corroboration_count": raw_corr,
                    "independent_corroboration_count": discounted_corr,
                    "corroboration_adjustment_note": note,
                }
        else:
            results[rid] = {
                "duplicate_detected": False,
                "correlation_group_id": None,
                "related_report_ids": [],
                "similarity_reason": "No duplicate or correlated reports detected.",
                "raw_corroboration_count": raw_corr,
                "independent_corroboration_count": raw_corr,
                "corroboration_adjustment_note": None,
            }

    return results
