"""
evaluation.py
=============
Threshold trade-off experiment comparing operational strategies (Responder 0.30, Balanced 0.50, City Official 0.65).

Calculates actual computed Precision, Recall, False Positive Rate, Reports Surfaced, and High-Priority Missed incidents.

DISCLAIMER: Ground truth values are simulated for prototype evaluation only.
"""

from __future__ import annotations

from typing import Any, Dict, List


STRATEGIES = [
    {"name": "Responder", "threshold": 0.30, "description": "High Recall strategy. Minimal miss risk for first responders."},
    {"name": "Balanced", "threshold": 0.50, "description": "Balanced trade-off between recall and precision."},
    {"name": "City Official", "threshold": 0.65, "description": "High Precision strategy. Minimizes false alarms for leadership."},
]


def run_threshold_experiment(reports_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluates system precision, recall, FPR, surfaced count, and missed high priority items
    across Responder (0.30), Balanced (0.50), and City Official (0.65) operational thresholds.
    """
    total = len(reports_data)
    results = []

    for strat in STRATEGIES:
        thresh = strat["threshold"]
        name = strat["name"]
        desc = strat["description"]

        surfaced_count = 0
        tp = 0
        fp = 0
        fn = 0
        tn = 0
        missed = 0
        gt_true_count = 0

        for r in reports_data:
            gt = str(r.get("ground_truth", "UNKNOWN")).upper()
            prio_norm = float(r.get("priority_score", 0.0)) / 100.0

            # System surfs report if normalized priority >= threshold
            surfaced = prio_norm >= thresh
            if surfaced:
                surfaced_count += 1

            if gt == "TRUE":
                gt_true_count += 1
                if surfaced:
                    tp += 1
                else:
                    fn += 1
                    missed += 1
            elif gt == "FALSE":
                if surfaced:
                    fp += 1
                else:
                    tn += 1

        precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
        recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
        fpr = round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0

        results.append({
            "name": name,
            "threshold": thresh,
            "reports_surfaced": surfaced_count,
            "precision": precision,
            "recall": recall,
            "false_positive_rate": fpr,
            "high_priority_missed": missed,
            "description": desc,
        })

    return {
        "total_evaluated": total,
        "strategies": results,
        "disclaimer": "Simulated ground truth evaluation metrics for prototype testing. Does not establish real-world emergency response performance.",
    }


def evaluate_threshold_tradeoffs(reports_data: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    if reports_data is None:
        from backend.main import get_enriched_reports
        reports_data = get_enriched_reports()
    res = run_threshold_experiment(reports_data)
    # Add step sequence of thresholds for line chart visualization
    results = res["strategies"]
    # Synthesize additional intermediate thresholds (e.g. 0.1, 0.2, 0.4, 0.7, 0.8) for smooth line charts if desired
    return results


if __name__ == "__main__":
    from backend.main import get_enriched_reports
    reports = get_enriched_reports()
    res = run_threshold_experiment(reports)
    print("--- THRESHOLD EXPERIMENT RESULTS (COMPUTED) ---")
    for s in res["strategies"]:
        print(f"[{s['name']}] Thresh={s['threshold']}: Surfaced={s['reports_surfaced']}, Prec={s['precision']}, Rec={s['recall']}, FPR={s['false_positive_rate']}, Missed={s['high_priority_missed']}")

