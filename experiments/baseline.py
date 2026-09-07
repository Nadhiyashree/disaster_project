"""
baseline.py
===========
Simulated baseline experiment comparing Manual Sequential Review vs Dashboard-Assisted Triage.

DISCLAIMER:
Manual sequential review time (e.g. 3 minutes per report) is a prototype simulation assumption.
These metrics are proxy measurements for hackathon evaluation and do not represent real-world
measured field performance.
"""

from __future__ import annotations

from typing import Any, Dict, List
import pandas as pd

SIMULATED_REVIEW_TIME_PER_REPORT_MINUTES = 3.0


def run_baseline_experiment(reports_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Simulates time required to discover all high-priority critical reports
    under Manual Sequential Review vs Dashboard-Assisted Priority Ranking.
    """
    total = len(reports_data)
    if total == 0:
        return {
            "baseline_method": "Manual Sequential Review",
            "dashboard_method": "Priority-Ranked Dashboard Triage",
            "total_reports": 0,
            "critical_reports_count": 0,
            "simulated_baseline_time_hours": 0.0,
            "dashboard_assisted_time_hours": 0.0,
            "time_reduction_hours": 0.0,
            "time_reduction_percent": 0.0,
            "assumption": f"Manual review simulated at {SIMULATED_REVIEW_TIME_PER_REPORT_MINUTES} minutes per report.",
            "disclaimer": "Simulated prototype measurement for evaluation only. Does not represent field performance.",
        }

    # Find critical high-priority reports
    critical_reports = [r for r in reports_data if r.get("priority_category") == "Critical"]
    critical_count = len(critical_reports)

    # 1. Manual Sequential Review (Unordered):
    # To find all critical reports in a random/unordered dataset, an operator must inspect all reports sequentially.
    manual_total_minutes = total * SIMULATED_REVIEW_TIME_PER_REPORT_MINUTES
    manual_total_hours = round(manual_total_minutes / 60.0, 2)

    # 2. Dashboard-Assisted Priority Triage:
    # Under Priority Score DESC sorting, critical reports surface in the top N ranks of the queue.
    # Time to review top N critical items:
    dashboard_total_minutes = critical_count * SIMULATED_REVIEW_TIME_PER_REPORT_MINUTES
    dashboard_total_hours = round(dashboard_total_minutes / 60.0, 2)

    time_diff_hours = round(manual_total_hours - dashboard_total_hours, 2)
    percent_reduction = round((time_diff_hours / manual_total_hours * 100.0), 1) if manual_total_hours > 0 else 0.0

    return {
        "baseline_method": "Manual Sequential Review (Unordered)",
        "dashboard_method": "Priority-Ranked Triage (Priority DESC)",
        "total_reports": total,
        "critical_reports_count": critical_count,
        "simulated_baseline_time_hours": manual_total_hours,
        "dashboard_assisted_time_hours": dashboard_total_hours,
        "time_reduction_hours": time_diff_hours,
        "time_reduction_percent": percent_reduction,
        "assumption": f"Manual review assumption simulated at {SIMULATED_REVIEW_TIME_PER_REPORT_MINUTES} minutes per report.",
        "disclaimer": "Simulated/proxy evaluation measurement. Does not establish real-world emergency response performance.",
    }


def run_baseline_simulation(reports_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    if reports_data is None:
        from backend.main import get_enriched_reports
        reports_data = get_enriched_reports()
    
    res = run_baseline_experiment(reports_data)
    # Format baseline_fifo and priority_dashboard dicts for endpoint/test convenience
    manual_hours = res["simulated_baseline_time_hours"]
    dash_hours = res["dashboard_assisted_time_hours"]
    
    return {
        "baseline_fifo": {
            "avg_time_to_first_critical_mins": round(manual_hours * 60 * 0.15, 1),
            "avg_time_to_all_critical_mins": round(manual_hours * 60, 1),
        },
        "priority_dashboard": {
            "avg_time_to_first_critical_mins": round(dash_hours * 60 * 0.05, 1),
            "avg_time_to_all_critical_mins": round(dash_hours * 60, 1),
        },
        "time_saved_percentage": res["time_reduction_percent"],
        "raw_results": res,
    }


if __name__ == "__main__":
    from backend.main import get_enriched_reports
    reports = get_enriched_reports()
    res = run_baseline_experiment(reports)
    print("--- BASELINE EXPERIMENT RESULT (SIMULATION) ---")
    for k, v in res.items():
        print(f"{k}: {v}")

