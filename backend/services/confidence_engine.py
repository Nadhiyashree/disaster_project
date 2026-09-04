"""
confidence_engine.py
====================
Calculates the evidence-based confidence score (0–100) for a disaster report.

Rule-based, transparent, and explainable. No citizen profiling or reputation scoring.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import pandas as pd


# Weight definitions
WEIGHT_SOURCE_RELIABILITY = 0.15
WEIGHT_CORROBORATION = 0.25
WEIGHT_FRESHNESS = 0.15
WEIGHT_LOCATION_PRECISION = 0.10
WEIGHT_MEDIA_EVIDENCE = 0.15
WEIGHT_RESPONDER_VERIFICATION = 0.20

# Source reliability mapping
SOURCE_RELIABILITY_MAP: Dict[str, float] = {
    "Field Responder": 1.00,
    "Department Report": 0.95,
    "Emergency Call": 0.90,
    "Sensor": 0.85,
    "Citizen Report": 0.40,
}

# Location precision mapping
LOCATION_PRECISION_MAP: Dict[str, float] = {
    "Exact": 1.00,
    "High": 0.80,
    "Medium": 0.60,
    "Low": 0.30,
    "Unknown": 0.00,
}

# Media evidence mapping
MEDIA_EVIDENCE_MAP: Dict[str, float] = {
    "Photo": 1.00,
    "Video": 1.00,
    "Audio": 0.70,
    "None": 0.00,
    "Unavailable": 0.00,
}

# Responder verification mapping
RESPONDER_VERIFICATION_MAP: Dict[str, float] = {
    "Verified": 1.00,
    "Needs Review": 0.50,
    "Pending": 0.25,
    "Rejected": 0.00,
    "Unknown": 0.00,
}


def get_corroboration_score(count: int) -> float:
    """Map independent corroboration report count to [0, 1.0] score."""
    if count <= 0:
        return 0.00
    elif count <= 2:
        return 0.50
    elif count <= 4:
        return 0.75
    else:
        return 1.00


def get_confidence_category(score: float) -> str:
    """Categorize confidence score into Low, Medium, High, Very High."""
    if score >= 85.0:
        return "Very High"
    elif score >= 70.0:
        return "High"
    elif score >= 40.0:
        return "Medium"
    else:
        return "Low"


def calculate_confidence(
    report: Dict[str, Any],
    freshness_score: float,
    independent_corroboration_count: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Calculates transparent confidence score and returns explanation breakdown.
    """
    source_type = str(report.get("source_type", "Citizen Report"))
    source_val = SOURCE_RELIABILITY_MAP.get(source_type, 0.40)

    # Use independent corroboration count if provided, else fallback to raw count
    if independent_corroboration_count is None:
        raw_corr = report.get("corroborating_report_count", 0)
        corr_count = int(raw_corr) if pd.notna(raw_corr) else 0
    else:
        corr_count = int(independent_corroboration_count)

    corr_val = get_corroboration_score(corr_count)

    loc_prec = str(report.get("location_precision", "Unknown"))
    loc_val = LOCATION_PRECISION_MAP.get(loc_prec, 0.00)

    media = str(report.get("media_type", "None"))
    media_val = MEDIA_EVIDENCE_MAP.get(media, 0.00)

    resp_stat = str(report.get("responder_status", "Pending"))
    resp_val = RESPONDER_VERIFICATION_MAP.get(resp_stat, 0.25)

    fresh_val = float(freshness_score)

    # Component contributions out of 100
    c_source = source_val * WEIGHT_SOURCE_RELIABILITY * 100.0
    c_corr = corr_val * WEIGHT_CORROBORATION * 100.0
    c_fresh = fresh_val * WEIGHT_FRESHNESS * 100.0
    c_loc = loc_val * WEIGHT_LOCATION_PRECISION * 100.0
    c_media = media_val * WEIGHT_MEDIA_EVIDENCE * 100.0
    c_resp = resp_val * WEIGHT_RESPONDER_VERIFICATION * 100.0

    raw_score = c_source + c_corr + c_fresh + c_loc + c_media + c_resp
    raw_score = round(raw_score, 2)

    # Confidence Cap Check
    capped = False
    cap_reason = None
    final_score = raw_score

    is_citizen = source_type == "Citizen Report"
    is_zero_corr = corr_count == 0
    is_no_media = media in ("None", "Unavailable")
    is_pending_review = resp_stat in ("Pending", "Needs Review")

    if is_citizen and is_zero_corr and is_no_media and is_pending_review:
        if raw_score > 69.0:
            final_score = 69.0
            capped = True
            cap_reason = (
                "Confidence capped due to insufficient independent evidence. "
                "Human verification recommended."
            )

    category = get_confidence_category(final_score)

    # Explanation object breakdown
    explanation_components = {
        "source_reliability": {
            "value": source_val,
            "weight": WEIGHT_SOURCE_RELIABILITY,
            "contribution": round(c_source, 2),
            "source_type": source_type,
        },
        "corroboration": {
            "value": corr_val,
            "weight": WEIGHT_CORROBORATION,
            "contribution": round(c_corr, 2),
            "independent_count": corr_count,
        },
        "freshness": {
            "value": fresh_val,
            "weight": WEIGHT_FRESHNESS,
            "contribution": round(c_fresh, 2),
        },
        "location_precision": {
            "value": loc_val,
            "weight": WEIGHT_LOCATION_PRECISION,
            "contribution": round(c_loc, 2),
            "precision": loc_prec,
        },
        "media_evidence": {
            "value": media_val,
            "weight": WEIGHT_MEDIA_EVIDENCE,
            "contribution": round(c_media, 2),
            "media_type": media,
        },
        "responder_verification": {
            "value": resp_val,
            "weight": WEIGHT_RESPONDER_VERIFICATION,
            "contribution": round(c_resp, 2),
            "status": resp_stat,
        },
    }

    # Generate concise summary text
    summary_parts = []
    if corr_val >= 0.75:
        summary_parts.append("strong corroboration")
    elif corr_val > 0:
        summary_parts.append("partial corroboration")
    else:
        summary_parts.append("uncorroborated single report")

    if loc_val >= 0.8:
        summary_parts.append("high location precision")
    if media_val >= 0.7:
        summary_parts.append("media evidence attached")
    if resp_val >= 1.0:
        summary_parts.append("verified by responder")
    elif resp_val == 0.0:
        summary_parts.append("rejected by responder")
    if fresh_val >= 0.75:
        summary_parts.append("recent report")

    summary_desc = ", ".join(summary_parts) if summary_parts else "standard report details"

    if capped:
        summary_text = (
            f"Confidence is capped at Medium ({final_score:.0f}) because this is a single "
            f"citizen report with no media or responder verification. Human verification recommended."
        )
    else:
        summary_text = (
            f"Confidence is {category} ({final_score:.1f}/100) based on {summary_desc}."
        )

    return {
        "confidence_score": final_score,
        "confidence_category": category,
        "confidence_capped": capped,
        "confidence_cap_reason": cap_reason,
        "confidence_explanation": {
            "components": explanation_components,
            "summary": summary_text,
            "raw_score": raw_score,
        },
    }
