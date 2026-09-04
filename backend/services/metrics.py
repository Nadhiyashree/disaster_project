"""
metrics.py
==========
Computes internal evaluation metrics by comparing system confidence/priority/status
outputs against internal ground truth.

NOTE: Ground truth data is simulated and used for offline evaluation only.
It is never exposed to operators as live operational knowledge.
"""

from __future__ import annotations

from typing import Any, Dict, List
import pandas as pd


def compute_system_metrics(reports_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes precision, recall, false positive rate, missed high priorities,
    and average confidence/priority scores across all enriched reports.
    """
    total = len(reports_data)
    if total == 0:
        return {
            "total_evaluated": 0,
            "precision": 0.0,
            "recall": 0.0,
            "false_positive_rate": 0.0,
            "high_priority_missed": 0,
            "high_priority_missed_rate": 0.0,
            "average_confidence": 0.0,
            "average_priority": 0.0,
            "note": "No reports available for evaluation.",
        }

    tp = 0
    fp = 0
    fn = 0
    tn = 0
    high_priority_missed = 0
    gt_true_count = 0

    total_conf = 0.0
    total_prio = 0.0

    for r in reports_data:
        gt = str(r.get("ground_truth", "UNKNOWN")).upper()
        conf = float(r.get("confidence_score", 0.0))
        prio = float(r.get("priority_score", 0.0))
        status = str(r.get("status", "Pending"))

        total_conf += conf
        total_prio += prio

        # System decision: Report is treated as actionable/verified if Verified or High/Very High confidence
        pred_positive = (status == "Verified") or (conf >= 70.0)

        if gt == "TRUE":
            gt_true_count += 1
            if pred_positive:
                tp += 1
            else:
                fn += 1
            
            # Missed high priority check: Ground truth TRUE but priority assigned was Low (< 35)
            if prio < 35.0:
                high_priority_missed += 1

        elif gt == "FALSE":
            if pred_positive:
                fp += 1
            else:
                tn += 1

    precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
    recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
    fpr = round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0
    missed_rate = round(high_priority_missed / gt_true_count, 4) if gt_true_count > 0 else 0.0

    avg_conf = round(total_conf / total, 2)
    avg_prio = round(total_prio / total, 2)

    return {
        "total_evaluated": total,
        "ground_truth_true_count": gt_true_count,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "precision": precision,
        "recall": recall,
        "false_positive_rate": fpr,
        "high_priority_missed": high_priority_missed,
        "high_priority_missed_rate": missed_rate,
        "average_confidence": avg_conf,
        "average_priority": avg_prio,
        "evaluation_notice": (
            "Ground truth data is simulated for algorithm evaluation purposes only. "
            "Operator triage decisions rely on transparent confidence and priority metrics."
        ),
    }
