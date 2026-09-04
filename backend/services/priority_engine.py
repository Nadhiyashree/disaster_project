"""
priority_engine.py
==================
Calculates the operational priority score (0–100) for a disaster report.

Determines response urgency independent of confidence.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


# Weights
WEIGHT_INCIDENT_SEVERITY = 0.35
WEIGHT_CONFIDENCE_SCORE = 0.30
WEIGHT_FRESHNESS_URGENCY = 0.20
WEIGHT_OPERATIONAL_URGENCY = 0.15

# Incident severity baseline mapping
INCIDENT_SEVERITY_MAP: Dict[str, float] = {
    "Medical Emergency": 1.00,
    "Evacuation Needed": 1.00,
    "Structural Damage": 0.85,
    "Road Flooding": 0.80,
    "Water Contamination": 0.80,
    "Power Outage": 0.60,
}

# Freshness urgency mapping
FRESHNESS_URGENCY_MAP: Dict[str, float] = {
    "Fresh": 1.00,
    "Aging": 0.75,
    "Old": 0.45,
    "Stale": 0.20,
    "Unknown": 0.00,
}


def get_priority_category(score: float) -> str:
    """Categorize priority score into Low, Medium, High, Critical."""
    if score >= 80.0:
        return "Critical"
    elif score >= 60.0:
        return "High"
    elif score >= 35.0:
        return "Medium"
    else:
        return "Low"


def calculate_operational_urgency(report: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Computes operational urgency based on infrastructure impact, permit impact, and hazard scale.
    Returns (score_in_0_to_1, factors_list).
    """
    incident = str(report.get("incident_type", ""))
    permit = str(report.get("permit_impact", "None"))
    desc = str(report.get("description", "")).lower()

    score = 0.50
    factors = []

    if incident in ("Medical Emergency", "Evacuation Needed"):
        score += 0.35
        factors.append("Immediate risk to human life or safety")

    if permit in ("Critical", "High"):
        score += 0.25
        factors.append(f"High infrastructure permit impact ({permit})")
    elif permit == "Medium":
        score += 0.10
        factors.append("Moderate infrastructure impact")

    if any(k in desc for k in ("collapse", "trapped", "hospital", "toxic", "explosion", "substation")):
        score += 0.15
        factors.append("Critical utility or structural hazard indicated in description")

    if any(k in desc for k in ("blocked", "impassable", "disrupted")):
        score += 0.10
        factors.append("Transportation/access route blocked")

    score = min(1.00, max(0.00, round(score, 2)))
    if not factors:
        factors.append("Standard operational monitoring")

    return score, factors


def calculate_priority(
    report: Dict[str, Any],
    confidence_score: float,
    freshness_state: str,
) -> Dict[str, Any]:
    """
    Calculates operational priority score (0–100) and structured explanation.
    """
    incident = str(report.get("incident_type", "Road Flooding"))
    permit = str(report.get("permit_impact", "None"))

    # Baseline incident severity
    base_sev = INCIDENT_SEVERITY_MAP.get(incident, 0.70)
    # Context adjustment: permit impact can boost severity by up to 0.05
    if permit == "Critical":
        base_sev = min(1.00, base_sev + 0.05)
    sev_val = round(base_sev, 2)

    # Confidence score normalized to 0–1.0
    conf_val = max(0.00, min(1.00, confidence_score / 100.0))

    # Freshness urgency
    fresh_urg_val = FRESHNESS_URGENCY_MAP.get(freshness_state, 0.00)

    # Operational urgency
    op_urg_val, op_factors = calculate_operational_urgency(report)

    # Formula calculation (scaled to 100)
    c_sev = sev_val * WEIGHT_INCIDENT_SEVERITY * 100.0
    c_conf = conf_val * WEIGHT_CONFIDENCE_SCORE * 100.0
    c_fresh = fresh_urg_val * WEIGHT_FRESHNESS_URGENCY * 100.0
    c_op = op_urg_val * WEIGHT_OPERATIONAL_URGENCY * 100.0

    raw_priority = c_sev + c_conf + c_fresh + c_op
    priority_score = round(raw_priority, 2)
    priority_category = get_priority_category(priority_score)

    # Human-readable labels
    sev_label = "Very High" if sev_val >= 0.9 else ("High" if sev_val >= 0.8 else "Medium")
    conf_label = "High" if conf_val >= 0.7 else ("Medium" if conf_val >= 0.4 else "Low")
    fresh_label = freshness_state
    op_label = "High" if op_urg_val >= 0.8 else ("Medium" if op_urg_val >= 0.5 else "Low")

    # Natural-language text
    explanation_text = (
        f"Why prioritized:\n"
        f"• Incident severity: {sev_label} ({sev_val*100:.0f}%)\n"
        f"• Confidence: {conf_label} ({confidence_score:.1f}/100)\n"
        f"• Freshness: {fresh_label}\n"
        f"• Operational urgency: {op_label}"
    )

    return {
        "priority_score": priority_score,
        "priority_category": priority_category,
        "priority_explanation": {
            "incident_severity": {
                "value": sev_val,
                "weight": WEIGHT_INCIDENT_SEVERITY,
                "contribution": round(c_sev, 2),
                "label": sev_label,
            },
            "confidence_contribution": {
                "value": conf_val,
                "weight": WEIGHT_CONFIDENCE_SCORE,
                "contribution": round(c_conf, 2),
                "label": conf_label,
            },
            "freshness_urgency": {
                "value": fresh_urg_val,
                "weight": WEIGHT_FRESHNESS_URGENCY,
                "contribution": round(c_fresh, 2),
                "label": fresh_label,
            },
            "operational_urgency": {
                "value": op_urg_val,
                "weight": WEIGHT_OPERATIONAL_URGENCY,
                "contribution": round(c_op, 2),
                "label": op_label,
                "factors": op_factors,
            },
            "text": explanation_text,
        },
    }
