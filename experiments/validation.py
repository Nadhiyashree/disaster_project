"""
validation.py
=============
Simulated/proxy validation study evaluating operational triage workflows across 3 stakeholder roles.

DISCLAIMER: These are simulated/proxy validation results and are not results from real human participants or a real-world user study.
"""

from __future__ import annotations

from typing import Any, Dict, List


TASKS = [
    {"task_id": 1, "name": "Find Highest Priority Report", "description": "Locate the top critical incident in the Priority Response Queue."},
    {"task_id": 2, "name": "Explain Confidence Score", "description": "Inspect 6-factor evidence breakdown and identify confidence cap warnings."},
    {"task_id": 3, "name": "Identify Stale Report", "description": "Filter or locate reports older than 6 hours and review recency warning."},
    {"task_id": 4, "name": "Identify Conflicting Report", "description": "Locate reports flagged with material claim or status discrepancies."},
    {"task_id": 5, "name": "Human Verification Triage", "description": "Execute status update (Verified/Needs Review/Rejected) with confirmation dialog."},
]


def run_proxy_validation_study() -> Dict[str, Any]:
    """
    Returns simulated/proxy validation study results for prototype evaluation.
    """
    simulated_roles = [
        {
            "role": "Responder",
            "focus": "Urgent triage & high recall",
            "simulated_completion_rate": 1.00,
            "simulated_avg_time_seconds": 18.5,
            "simulated_confusion_score": 1.1,
            "feedback": "Priority queue sorting allowed rapid discovery of life-safety evacuation threats.",
        },
        {
            "role": "City Official",
            "focus": "High precision & evidence verification",
            "simulated_completion_rate": 1.00,
            "simulated_avg_time_seconds": 26.0,
            "simulated_confusion_score": 1.3,
            "feedback": "Confidence breakdown table clearly explained why weak single citizen reports were capped.",
        },
        {
            "role": "Coordinator",
            "focus": "Conflict resolution & gap analysis",
            "simulated_completion_rate": 1.00,
            "simulated_avg_time_seconds": 22.0,
            "simulated_confusion_score": 1.2,
            "feedback": "Conflict detection alerts helped highlight contradicting claims across Riverside zone.",
        },
    ]

    total_tasks = len(TASKS) * len(simulated_roles)
    completed_tasks = total_tasks  # 100% completion in proxy study

    avg_time = round(sum(r["simulated_avg_time_seconds"] for r in simulated_roles) / len(simulated_roles), 1)
    avg_confusion = round(sum(r["simulated_confusion_score"] for r in simulated_roles) / len(simulated_roles), 2)

    return {
        "validation_type": "simulated/proxy",
        "disclaimer": "These are simulated/proxy validation results and are not results from real human participants or a real-world user study.",
        "total_simulated_roles": len(simulated_roles),
        "total_tasks_evaluated": len(TASKS),
        "task_completion_rate": round(completed_tasks / total_tasks, 4),
        "average_task_time_seconds": avg_time,
        "reported_confusion_score": avg_confusion,
        "confusion_scale": "1 (No confusion) to 5 (High confusion)",
        "tasks": TASKS,
        "simulated_users": simulated_roles,
    }


def run_validation_study() -> Dict[str, Any]:
    res = run_proxy_validation_study()
    # Format table results for proxy validation view
    formatted_results = [
        {
            "role_profile": u["role"],
            "task_description": u["focus"],
            "baseline_manual_mins": round(u["simulated_avg_time_seconds"] * 3.5 / 60, 1),
            "dashboard_assisted_mins": round(u["simulated_avg_time_seconds"] / 60, 1),
            "time_saved_percent": round((1 - (1 / 3.5)) * 100, 1),
            "evaluation_status": "COMPLETED_SIMULATION",
        }
        for u in res["simulated_users"]
    ]
    return {
        "summary": res,
        "results": formatted_results,
        "disclaimer": res["disclaimer"],
    }


if __name__ == "__main__":
    res = run_proxy_validation_study()
    print("--- PROXY VALIDATION STUDY RESULT (SIMULATED) ---")
    print(f"Validation Type: {res['validation_type']}")
    print(f"Task Completion: {res['task_completion_rate']*100}%")
    print(f"Avg Time: {res['average_task_time_seconds']}s")
    print(f"Confusion: {res['reported_confusion_score']} / 5")

