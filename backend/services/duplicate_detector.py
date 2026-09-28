"""
duplicate_detector.py
=====================
Identifies duplicate and correlated disaster reports using a documented
spatial-temporal composite score algorithm.

Algorithm (Phase 2)
-------------------
Two reports are *candidate* duplicates when they share the same incident type
AND at least one of the following is true:

  spatial_score  = 1 if haversine_distance <= SPATIAL_THRESHOLD_KM else 0
  temporal_score = 1 if |ts_i - ts_j| <= TEMPORAL_WINDOW_MINUTES  else 0   (0 when timestamps missing)
  incident_score = 1 if incident_type_i == incident_type_j           else 0

  duplicate_score =   0.40 * spatial_score
                    + 0.40 * temporal_score
                    + 0.20 * incident_score

  Classified as duplicate / correlated when: duplicate_score >= DUPLICATE_SCORE_THRESHOLD

Additional signal: text description similarity (SequenceMatcher) is integrated
as a *relaxation* condition that lets very close spatial matches (≤ 0.2 km)
qualify even when text similarity is moderate.

Thresholds (documented constants — do NOT scatter inline)
---------------------------------------------------------
SPATIAL_THRESHOLD_KM        = 1.0   km  (Haversine, not Euclidean)
TEMPORAL_WINDOW_MINUTES     = 30    min
DUPLICATE_SCORE_THRESHOLD   = 0.80

Privacy
-------
Does NOT use IP addresses, device IDs, or personal identity information.
Reports are matched solely on location, time, incident type, and description.
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

from backend.services.haversine_utils import safe_haversine_distance

# ---------------------------------------------------------------------------
# Documented thresholds — single source of truth
# ---------------------------------------------------------------------------

#: Spatial proximity threshold for duplicate/correlation candidate selection.
#: Two reports must be within this distance (kilometres, Haversine) to qualify.
SPATIAL_THRESHOLD_KM: float = 1.0

#: Temporal window (minutes) within which two reports are considered
#: temporally related.  Missing timestamps are handled gracefully (score = 0).
TEMPORAL_WINDOW_MINUTES: float = 30.0

#: Composite duplicate score threshold [0, 1].
#: Reports whose composite score meets or exceeds this value are classified
#: as duplicate/correlated.
DUPLICATE_SCORE_THRESHOLD: float = 0.80

# Weight components of the composite duplicate score.
WEIGHT_SPATIAL: float = 0.40
WEIGHT_TEMPORAL: float = 0.40
WEIGHT_INCIDENT: float = 0.20

#: Secondary spatial threshold (metres converted to km) for very-close
#: geographic matches that qualify with moderate text similarity.
NEAR_IDENTICAL_DISTANCE_KM: float = 0.20

#: Minimum text similarity ratio for the near-identical relaxation path.
NEAR_IDENTICAL_TEXT_SIM: float = 0.50


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _text_similarity(s1: str, s2: str) -> float:
    """Return SequenceMatcher similarity ratio in [0.0, 1.0].

    Returns 0.0 if either string is empty to avoid division by zero.
    """
    if not s1 or not s2:
        return 0.0
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def _compute_duplicate_score(
    dist_km: Optional[float],
    time_diff_min: Optional[float],
    same_incident_type: bool,
) -> float:
    """Compute the composite duplicate/correlation score.

    Parameters
    ----------
    dist_km : float or None
        Haversine distance between the two reports in kilometres.
        None if either report is missing coordinates.
    time_diff_min : float or None
        Absolute temporal difference in minutes.
        None if either report is missing a timestamp.
    same_incident_type : bool
        Whether the two reports share the same incident type.

    Returns
    -------
    float
        Composite score in [0.0, 1.0].
        Score = 0.40 * spatial_score + 0.40 * temporal_score + 0.20 * incident_score
    """
    spatial_score: float = (
        1.0 if (dist_km is not None and dist_km <= SPATIAL_THRESHOLD_KM) else 0.0
    )
    temporal_score: float = (
        1.0
        if (time_diff_min is not None and time_diff_min <= TEMPORAL_WINDOW_MINUTES)
        else 0.0
    )
    incident_score: float = 1.0 if same_incident_type else 0.0

    return (
        WEIGHT_SPATIAL * spatial_score
        + WEIGHT_TEMPORAL * temporal_score
        + WEIGHT_INCIDENT * incident_score
    )


def _build_similarity_reason(
    dist_km: float,
    time_diff_min: Optional[float],
    incident_type: str,
    text_sim: float,
) -> str:
    """Generate a human-readable explanation of why two reports were correlated."""
    parts: List[str] = [
        f"Geographic proximity ({dist_km * 1000:.0f} m, Haversine) for '{incident_type}'"
    ]
    if time_diff_min is not None:
        parts.append(f"temporal overlap ({time_diff_min:.0f} min apart)")
    if text_sim >= NEAR_IDENTICAL_TEXT_SIM:
        parts.append(f"description similarity ({text_sim * 100:.0f}%)")
    return "; ".join(parts) + "."


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_duplicates_and_correlations(
    df: pd.DataFrame,
    dist_threshold_km: float = SPATIAL_THRESHOLD_KM,
    time_window_minutes: float = TEMPORAL_WINDOW_MINUTES,
    score_threshold: float = DUPLICATE_SCORE_THRESHOLD,
) -> Dict[str, Dict[str, Any]]:
    """Detect duplicate and correlated disaster reports.

    Uses a composite spatial-temporal score:

        duplicate_score = 0.40 * spatial_score
                        + 0.40 * temporal_score
                        + 0.20 * incident_score

    where each component is 1.0 (match) or 0.0 (no match), and:
      - spatial_score  = 1 iff Haversine distance ≤ dist_threshold_km
      - temporal_score = 1 iff |Δt| ≤ time_window_minutes (0 when timestamps missing)
      - incident_score = 1 iff incident types match

    A pair is classified as duplicate/correlated when
    duplicate_score >= score_threshold (default 0.80).

    Additionally, very-close geographic pairs (≤ 0.20 km) with moderate text
    similarity (≥ 0.50) are also correlated regardless of temporal data.

    Parameters
    ----------
    df : pd.DataFrame
        Enriched reports dataframe.
    dist_threshold_km : float
        Spatial threshold in kilometres (Haversine). Default = 1.0 km.
    time_window_minutes : float
        Temporal window in minutes. Default = 30 min.
    score_threshold : float
        Minimum composite score to classify a pair as duplicate. Default = 0.80.

    Returns
    -------
    dict mapping report_id to:
        duplicate_detected           : bool
        correlation_group_id         : str | None
        related_report_ids           : List[str]
        similarity_reason            : str
        raw_corroboration_count      : int
        independent_corroboration_count : int
        corroboration_adjustment_note: str | None
        duplicate_score              : float  (score of highest-scoring pair, or 0.0)
    """
    records = df.to_dict("records")
    n = len(records)

    # Adjacency list for connected-component analysis
    adj: Dict[str, Set[str]] = {str(r["report_id"]): set() for r in records}
    reasons: Dict[Tuple[str, str], str] = {}
    scores: Dict[Tuple[str, str], float] = {}

    for i in range(n):
        r1 = records[i]
        id1 = str(r1["report_id"])
        lat1: Optional[float] = float(r1["latitude"]) if pd.notna(r1["latitude"]) else None
        lon1: Optional[float] = float(r1["longitude"]) if pd.notna(r1["longitude"]) else None
        inc1: str = str(r1["incident_type"])
        ts1 = pd.to_datetime(r1["timestamp"], utc=True) if pd.notna(r1["timestamp"]) else None
        desc1: str = str(r1.get("description", ""))

        if lat1 is None or lon1 is None:
            continue

        for j in range(i + 1, n):
            r2 = records[j]
            id2 = str(r2["report_id"])
            inc2: str = str(r2["incident_type"])

            lat2: Optional[float] = float(r2["latitude"]) if pd.notna(r2["latitude"]) else None
            lon2: Optional[float] = float(r2["longitude"]) if pd.notna(r2["longitude"]) else None

            if lat2 is None or lon2 is None:
                continue

            dist_km: float = safe_haversine_distance(lat1, lon1, lat2, lon2) or 0.0

            # Skip pairs too far apart to ever qualify (optimisation)
            if dist_km > dist_threshold_km:
                continue

            ts2 = pd.to_datetime(r2["timestamp"], utc=True) if pd.notna(r2["timestamp"]) else None
            time_diff_min: Optional[float] = None
            if ts1 is not None and ts2 is not None:
                time_diff_min = abs((ts1 - ts2).total_seconds()) / 60.0

            same_incident = inc1 == inc2
            score = _compute_duplicate_score(dist_km, time_diff_min, same_incident)

            # Near-identical spatial relaxation path
            text_sim = _text_similarity(desc1, str(r2.get("description", "")))
            near_identical = (
                dist_km <= NEAR_IDENTICAL_DISTANCE_KM and text_sim >= NEAR_IDENTICAL_TEXT_SIM
            )

            if score >= score_threshold or near_identical:
                adj[id1].add(id2)
                adj[id2].add(id1)
                reason = _build_similarity_reason(dist_km, time_diff_min, inc1, text_sim)
                reasons[(id1, id2)] = reason
                reasons[(id2, id1)] = reason
                scores[(id1, id2)] = score
                scores[(id2, id1)] = score

    # Connected-component grouping via DFS
    visited: Set[str] = set()
    results: Dict[str, Dict[str, Any]] = {}
    group_counter = 1

    for r in records:
        rid = str(r["report_id"])
        raw_corr: int = (
            int(r["corroborating_report_count"])
            if pd.notna(r.get("corroborating_report_count"))
            else 0
        )

        if rid in visited:
            continue

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
                first_nbr = related[0]
                reason = reasons.get(
                    (cid, first_nbr),
                    "Geographically and temporally correlated with neighbouring reports.",
                )
                best_score = max(
                    (scores.get((cid, nbr), 0.0) for nbr in related), default=0.0
                )

                # Independent corroboration discount:
                # A correlated group of size G represents 1 primary event cluster.
                # Independent count is proportionally discounted.
                discounted_corr = max(0, min(raw_corr, max(1, len(related) // 2)))
                note: Optional[str] = (
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
                    "duplicate_score": round(best_score, 4),
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
                "duplicate_score": 0.0,
            }

    return results
