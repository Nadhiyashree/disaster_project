"""
main.py
=======
FastAPI application entry point for the Disaster Response Dashboard (Phase 2).

Integrates the core intelligence layer:
  - Confidence Engine
  - Priority Engine
  - Freshness Engine
  - Conflict Detector
  - Duplicate / Correlation Detector
  - Human Verification API
  - Dashboard Statistics & Metrics APIs
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.data_loader import CSV_PATH, generate_dataset, get_reports_df, reload_reports_df
from backend.schemas import (
    DashboardStats,
    ErrorResponse,
    HealthResponse,
    MetricsResponse,
    ReportDetailResponse,
    ReportListResponse,
    ReportSchema,
    VerificationRequest,
)
from backend.services.confidence_engine import calculate_confidence
from backend.services.conflict_detector import detect_conflicts
from backend.services.duplicate_detector import detect_duplicates_and_correlations
from backend.services.freshness_engine import evaluate_freshness
from backend.services.metrics import compute_system_metrics
from backend.services.priority_engine import calculate_priority

from experiments.baseline import run_baseline_experiment
from experiments.evaluation import run_threshold_experiment
from experiments.validation import run_proxy_validation_study
import json
from backend.data_loader import DATA_DIR

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Disaster Response Crowd-Report Verification & Confidence Dashboard",
    description=(
        "Phase 2 Backend: Core intelligence layer with rule-based confidence, priority, "
        "freshness, conflict detection, duplicate detection, and explainable triage queues."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static files & Root route
# ---------------------------------------------------------------------------

_FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

if _FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_FRONTEND_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def root() -> FileResponse:
    index = _FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return JSONResponse({"message": "Disaster Response Dashboard API (Phase 2)", "docs": "/docs"})


@app.get("/dashboard.html", include_in_schema=False)
@app.get("/dashboard", include_in_schema=False)
async def dashboard_page() -> FileResponse:
    page = _FRONTEND_DIR / "dashboard.html"
    if page.exists():
        return FileResponse(str(page))
    raise HTTPException(status_code=404, detail="Dashboard page not found.")


@app.get("/reports.html", include_in_schema=False)
@app.get("/reports", include_in_schema=False)
async def reports_page() -> FileResponse:
    page = _FRONTEND_DIR / "reports.html"
    if page.exists():
        return FileResponse(str(page))
    raise HTTPException(status_code=404, detail="Reports page not found.")


@app.get("/report-details.html", include_in_schema=False)
@app.get("/report-details", include_in_schema=False)
async def report_details_page() -> FileResponse:
    page = _FRONTEND_DIR / "report-details.html"
    if page.exists():
        return FileResponse(str(page))
    raise HTTPException(status_code=404, detail="Report details page not found.")


@app.get("/analytics.html", include_in_schema=False)
@app.get("/analytics", include_in_schema=False)
async def analytics_page() -> FileResponse:
    page = _FRONTEND_DIR / "analytics.html"
    if page.exists():
        return FileResponse(str(page))
    raise HTTPException(status_code=404, detail="Analytics page not found.")


@app.get("/methodology.html", include_in_schema=False)
@app.get("/methodology", include_in_schema=False)
async def methodology_page() -> FileResponse:
    page = _FRONTEND_DIR / "methodology.html"
    if page.exists():
        return FileResponse(str(page))
    raise HTTPException(status_code=404, detail="Methodology page not found.")


# ---------------------------------------------------------------------------
# Enriched Intelligence Cache Management
# ---------------------------------------------------------------------------

_enriched_cache: Optional[List[Dict[str, Any]]] = None


def get_enriched_reports(force_reload: bool = False) -> List[Dict[str, Any]]:
    """
    Returns full list of reports enriched with Phase 2 derived intelligence.
    Caches results in memory for high API performance.
    """
    global _enriched_cache
    if _enriched_cache is not None and not force_reload:
        return _enriched_cache

    df = get_reports_df() if not force_reload else reload_reports_df()

    logger.info("Computing Phase 2 intelligence layer for %d reports...", len(df))
    dup_map = detect_duplicates_and_correlations(df)
    conf_map = detect_conflicts(df)

    enriched: List[Dict[str, Any]] = []
    now = datetime.now(tz=timezone.utc)

    for idx, row in df.iterrows():
        rid = str(row["report_id"])
        ts = row["timestamp"]
        lu = row["last_updated"]

        raw_dict = {
            "report_id": rid,
            "timestamp": ts.isoformat() if pd.notna(ts) else None,
            "zone": str(row["zone"]),
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "incident_type": str(row["incident_type"]),
            "description": str(row["description"]),
            "source_type": str(row["source_type"]),
            "corroborating_report_count": int(row["corroborating_report_count"]),
            "responder_status": str(row["responder_status"]),
            "location_precision": str(row["location_precision"]),
            "media_type": str(row["media_type"]),
            "ground_truth": str(row["ground_truth"]),
            "department": str(row["department"]),
            "permit_impact": str(row["permit_impact"]),
            "status": str(row["status"]),
            "last_updated": lu.isoformat() if pd.notna(lu) else None,
        }

        # 1. Freshness
        fresh = evaluate_freshness(ts, lu, now=now)

        # 2. Duplicate / Correlation info
        dup = dup_map.get(
            rid,
            {
                "duplicate_detected": False,
                "correlation_group_id": None,
                "related_report_ids": [],
                "similarity_reason": None,
                "raw_corroboration_count": raw_dict["corroborating_report_count"],
                "independent_corroboration_count": raw_dict["corroborating_report_count"],
                "corroboration_adjustment_note": None,
            },
        )

        # 3. Conflict info
        conflict = conf_map.get(
            rid,
            {
                "conflict_detected": False,
                "conflict_type": None,
                "related_report_ids": [],
                "conflict_explanation": "No known conflicting reports.",
            },
        )

        # 4. Confidence
        confres = calculate_confidence(
            raw_dict,
            freshness_score=fresh["freshness_score"],
            independent_corroboration_count=dup["independent_corroboration_count"],
        )

        # 5. Priority
        priores = calculate_priority(
            raw_dict,
            confidence_score=confres["confidence_score"],
            freshness_state=fresh["freshness_state"],
        )

        # Combine into enriched record
        record = {
            **raw_dict,
            "confidence_score": confres["confidence_score"],
            "confidence_category": confres["confidence_category"],
            "confidence_capped": confres["confidence_capped"],
            "confidence_cap_reason": confres["confidence_cap_reason"],
            "priority_score": priores["priority_score"],
            "priority_category": priores["priority_category"],
            "freshness_score": fresh["freshness_score"],
            "freshness_state": fresh["freshness_state"],
            "minutes_since_report": fresh["minutes_since_report"],
            "freshness_warning": fresh.get("freshness_warning"),
            "conflict_detected": conflict["conflict_detected"],
            "conflict_type": conflict["conflict_type"],
            "conflict_explanation": conflict["conflict_explanation"],
            "spatial_distance_km": conflict.get("spatial_distance_km"),
            "temporal_difference_minutes": conflict.get("temporal_difference_minutes"),
            "duplicate_detected": dup["duplicate_detected"],
            "correlation_group_id": dup["correlation_group_id"],
            "related_report_ids": dup["related_report_ids"],
            "similarity_reason": dup["similarity_reason"],
            "raw_corroboration_count": dup["raw_corroboration_count"],
            "independent_corroboration_count": dup["independent_corroboration_count"],
            "corroboration_adjustment_note": dup["corroboration_adjustment_note"],
            "confidence_explanation": confres["confidence_explanation"],
            "priority_explanation": priores["priority_explanation"],
        }
        enriched.append(record)

    _enriched_cache = enriched
    logger.info("Enriched %d disaster reports successfully.", len(_enriched_cache))
    return _enriched_cache


@app.on_event("startup")
async def startup_event() -> None:
    if not CSV_PATH.exists():
        logger.info("Dataset not found; generating dataset now...")
        generate_dataset()
    get_enriched_reports(force_reload=True)


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

# ── Health ──────────────────────────────────────────────────────────────────

@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check",
)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="disaster-response-dashboard",
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
    )


# ── Reports (List & Filters) ────────────────────────────────────────────────

@app.get(
    "/api/reports",
    response_model=ReportListResponse,
    tags=["Reports"],
    summary="List enriched reports with search, filtering, sorting, and pagination",
)
async def list_reports(
    search: Optional[str] = Query(None, description="Free-text search on description, zone, incident_type, ID"),
    incident_type: Optional[str] = Query(None, description="Filter by incident type"),
    zone: Optional[str] = Query(None, description="Filter by zone"),
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    status: Optional[str] = Query(None, description="Filter by report status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    priority: Optional[str] = Query(None, alias="priority_category", description="Filter by priority category (Critical, High, Medium, Low)"),
    confidence: Optional[str] = Query(None, alias="confidence_category", description="Filter by confidence category (Very High, High, Medium, Low)"),
    freshness: Optional[str] = Query(None, alias="freshness_state", description="Filter by freshness state (Fresh, Aging, Old, Stale, Unknown)"),
    conflict: Optional[bool] = Query(None, description="Filter reports with conflict detected"),
    correlation: Optional[bool] = Query(None, description="Filter reports with duplicate/correlation detected"),
    sort_by: str = Query("priority_score", description="Field to sort by (priority_score, confidence_score, freshness_score, last_updated)"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    limit: int = Query(25, ge=1, le=500, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
) -> ReportListResponse:
    reports = get_enriched_reports()

    filtered = []
    for r in reports:
        if incident_type and r["incident_type"].lower() != incident_type.lower():
            continue
        if zone and r["zone"].lower() != zone.lower():
            continue
        if source_type and r["source_type"].lower() != source_type.lower():
            continue
        if status and r["status"].lower() != status.lower():
            continue
        if department and r["department"].lower() != department.lower():
            continue
        if priority and r["priority_category"].lower() != priority.lower():
            continue
        if confidence and r["confidence_category"].lower() != confidence.lower():
            continue
        if freshness and r["freshness_state"].lower() != freshness.lower():
            continue
        if conflict is not None and r["conflict_detected"] != conflict:
            continue
        if correlation is not None and r["duplicate_detected"] != correlation:
            continue
        if search:
            q = search.lower()
            m = (
                q in r["description"].lower()
                or q in r["zone"].lower()
                or q in r["incident_type"].lower()
                or q in r["report_id"].lower()
                or q in r["department"].lower()
            )
            if not m:
                continue
        filtered.append(r)

    # Sorting
    reverse = sort_order.lower() == "desc"

    def get_sort_key(item: Dict[str, Any]) -> Any:
        val = item.get(sort_by)
        if val is None:
            return "" if isinstance(val, str) else -999999
        return val

    filtered.sort(key=get_sort_key, reverse=reverse)

    total = len(filtered)
    page_items = filtered[offset : offset + limit]

    items = [ReportSchema.model_validate(r) for r in page_items]
    return ReportListResponse(items=items, total=total, limit=limit, offset=offset)


# ── Priority Queue API ──────────────────────────────────────────────────────

@app.get(
    "/api/reports/priority",
    response_model=ReportListResponse,
    tags=["Reports"],
    summary="Priority Response Queue sorted by priority_score DESC",
)
async def priority_reports(
    priority: Optional[str] = Query(None, description="Filter by priority category: Critical, High, Medium, Low"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> ReportListResponse:
    reports = get_enriched_reports()
    if priority:
        reports = [r for r in reports if r["priority_category"].lower() == priority.lower()]

    sorted_reports = sorted(reports, key=lambda x: x["priority_score"], reverse=True)
    total = len(sorted_reports)
    page = sorted_reports[offset : offset + limit]

    return ReportListResponse(
        items=[ReportSchema.model_validate(r) for r in page],
        total=total,
        limit=limit,
        offset=offset,
    )


# ── Stale Reports API ───────────────────────────────────────────────────────

@app.get(
    "/api/reports/stale",
    response_model=ReportListResponse,
    tags=["Reports"],
    summary="List all reports with freshness state = Stale",
)
async def stale_reports(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> ReportListResponse:
    reports = get_enriched_reports()
    stale = [r for r in reports if r["freshness_state"] == "Stale"]
    total = len(stale)
    page = stale[offset : offset + limit]
    return ReportListResponse(
        items=[ReportSchema.model_validate(r) for r in page],
        total=total,
        limit=limit,
        offset=offset,
    )


# ── Conflicts API ───────────────────────────────────────────────────────────

@app.get(
    "/api/reports/conflicts",
    response_model=ReportListResponse,
    tags=["Reports"],
    summary="List reports with detected conflicts",
)
async def conflict_reports(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> ReportListResponse:
    reports = get_enriched_reports()
    conflicts = [r for r in reports if r["conflict_detected"]]
    total = len(conflicts)
    page = conflicts[offset : offset + limit]
    return ReportListResponse(
        items=[ReportSchema.model_validate(r) for r in page],
        total=total,
        limit=limit,
        offset=offset,
    )


# ── Single Report & Details ─────────────────────────────────────────────────

@app.get(
    "/api/reports/{report_id}",
    response_model=ReportDetailResponse,
    tags=["Reports"],
    summary="Get complete evidence, scoring breakdowns, conflicts, and correlated reports for a report",
    responses={404: {"description": "Report not found"}},
)
async def get_report_detail(report_id: str) -> ReportDetailResponse:
    reports = get_enriched_reports()
    match = next((r for r in reports if r["report_id"] == report_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")

    # Find full related conflict report objects
    conflict_objs = []
    if match["conflict_detected"]:
        for rel_id in match["related_report_ids"]:
            rel = next((r for r in reports if r["report_id"] == rel_id), None)
            if rel:
                conflict_objs.append({
                    "report_id": rel["report_id"],
                    "incident_type": rel["incident_type"],
                    "status": rel["status"],
                    "source_type": rel["source_type"],
                    "description": rel["description"],
                })

    # Find full correlated report objects
    corr_objs = []
    if match["duplicate_detected"]:
        for rel_id in match["related_report_ids"]:
            rel = next((r for r in reports if r["report_id"] == rel_id), None)
            if rel:
                corr_objs.append({
                    "report_id": rel["report_id"],
                    "incident_type": rel["incident_type"],
                    "zone": rel["zone"],
                    "timestamp": rel["timestamp"],
                    "description": rel["description"],
                })

    conf_dict = {
        "score": match["confidence_score"],
        "category": match["confidence_category"],
        "capped": match["confidence_capped"],
        "cap_reason": match["confidence_cap_reason"],
        "explanation": match["confidence_explanation"],
    }

    prio_dict = {
        "score": match["priority_score"],
        "category": match["priority_category"],
        "explanation": match["priority_explanation"],
    }

    fresh_dict = {
        "score": match["freshness_score"],
        "state": match["freshness_state"],
        "minutes_since_report": match["minutes_since_report"],
        "warning": match["freshness_warning"],
    }

    return ReportDetailResponse(
        report=ReportSchema.model_validate(match),
        confidence=conf_dict,
        priority=prio_dict,
        freshness=fresh_dict,
        conflicts=conflict_objs,
        correlated_reports=corr_objs,
    )


AUDIT_LOG_PATH = DATA_DIR / "verification_audit.json"


def _append_verification_audit_log(report_id: str, prev_status: str, new_status: str, notes: Optional[str]) -> None:
    """Appends verification event record to data/verification_audit.json for prototype accountability."""
    entry = {
        "report_id": report_id,
        "previous_status": prev_status,
        "new_status": new_status,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "notes": notes,
        "action": f"Operational verification status changed from '{prev_status}' to '{new_status}'",
    }
    audit_data = []
    if AUDIT_LOG_PATH.exists():
        try:
            with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
                audit_data = json.load(f)
        except Exception:
            audit_data = []
    audit_data.append(entry)
    try:
        with open(AUDIT_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(audit_data, f, indent=2)
    except Exception as e:
        logger.error("Failed to write verification audit log: %s", e)


# ── Human Verification Endpoint ─────────────────────────────────────────────

@app.post(
    "/api/reports/{report_id}/verify",
    response_model=ReportSchema,
    tags=["Human Verification"],
    summary="Update report verification status (Human-in-the-loop)",
)
async def verify_report(report_id: str, req: VerificationRequest) -> ReportSchema:
    valid_statuses = {"Pending", "Verified", "Rejected", "Needs Review"}
    if req.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{req.status}'. Must be one of {valid_statuses}",
        )

    df = get_reports_df()
    mask = df["report_id"] == report_id
    if df[mask].empty:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")

    prev_status = str(df.loc[mask, "status"].values[0])

    # Update in DataFrame
    now_iso = datetime.now(tz=timezone.utc).isoformat()
    df.loc[mask, "status"] = req.status
    df.loc[mask, "responder_status"] = (
        req.status if req.status in ("Verified", "Rejected", "Needs Review", "Pending") else "Pending"
    )
    df.loc[mask, "last_updated"] = now_iso

    # Persist updated CSV
    df.to_csv(CSV_PATH, index=False)
    logger.info("Report %s status updated to %s by human verifier.", report_id, req.status)

    # Append to verification audit log
    _append_verification_audit_log(report_id, prev_status, req.status, req.notes)

    # Refresh enriched cache
    enriched = get_enriched_reports(force_reload=True)
    match = next((r for r in enriched if r["report_id"] == report_id), None)
    return ReportSchema.model_validate(match)


# ── Experiments & Validation APIs ──────────────────────────────────────────

@app.get(
    "/api/experiments/baseline",
    tags=["Experiments"],
    summary="Simulated baseline comparison (Manual Sequential Review vs Dashboard-Assisted)",
)
async def experiment_baseline() -> Dict[str, Any]:
    from experiments.baseline import run_baseline_simulation
    reports = get_enriched_reports()
    sim_data = run_baseline_simulation(reports)
    return {
        "status": "success",
        "results": sim_data,
        "baseline_fifo": sim_data.get("baseline_fifo"),
        "priority_dashboard": sim_data.get("priority_dashboard"),
        "time_saved_percentage": sim_data.get("time_saved_percentage"),
        "disclaimer": "Simulated prototype baseline measurement for algorithm evaluation. Does not represent field performance.",
    }


@app.get(
    "/api/experiments/thresholds",
    tags=["Experiments"],
    summary="Threshold trade-off experiment (Responder 0.30, Balanced 0.50, City Official 0.65)",
)
async def experiment_thresholds() -> Dict[str, Any]:
    from experiments.evaluation import evaluate_threshold_tradeoffs
    reports = get_enriched_reports()
    results = evaluate_threshold_tradeoffs(reports)
    return {
        "status": "success",
        "results": results,
        "recommended_strategies": {
            "0.30": "Responder (High Recall)",
            "0.50": "Balanced Default",
            "0.65": "City Official (High Precision)",
        },
        "disclaimer": "Simulated evaluation against internal ground truth. Does not establish real-world emergency performance.",
    }


@app.get(
    "/api/validation",
    tags=["Experiments"],
    summary="Simulated/proxy validation study results",
)
async def proxy_validation() -> Dict[str, Any]:
    from experiments.validation import run_validation_study
    study_data = run_validation_study()
    return {
        "status": "success",
        "summary": study_data.get("summary"),
        "results": study_data.get("results"),
        "disclaimer": study_data.get("disclaimer"),
    }



# ── Dashboard Statistics ─────────────────────────────────────────────────────

@app.get(
    "/api/dashboard/stats",
    response_model=DashboardStats,
    tags=["Dashboard"],
    summary="Aggregated dashboard statistics including Phase 2 intelligence metrics",
)
async def dashboard_stats() -> DashboardStats:
    reports = get_enriched_reports()
    total = len(reports)

    status_counts: Dict[str, int] = {}
    incident_type_counts: Dict[str, int] = {}
    zone_counts: Dict[str, int] = {}
    source_counts: Dict[str, int] = {}
    department_counts: Dict[str, int] = {}
    permit_impact_counts: Dict[str, int] = {}

    critical_reports = 0
    high_prio_reports = 0
    stale_reports = 0
    low_conf_reports = 0
    total_conf = 0.0
    total_prio = 0.0
    conflict_count = 0
    correlated_report_count = 0

    for r in reports:
        st = r["status"]
        status_counts[st] = status_counts.get(st, 0) + 1

        inc = r["incident_type"]
        incident_type_counts[inc] = incident_type_counts.get(inc, 0) + 1

        zn = r["zone"]
        zone_counts[zn] = zone_counts.get(zn, 0) + 1

        src = r["source_type"]
        source_counts[src] = source_counts.get(src, 0) + 1

        dept = r["department"]
        department_counts[dept] = department_counts.get(dept, 0) + 1

        pm = r["permit_impact"]
        permit_impact_counts[pm] = permit_impact_counts.get(pm, 0) + 1

        if r["priority_category"] == "Critical":
            critical_reports += 1
        if r["priority_category"] in ("Critical", "High"):
            high_prio_reports += 1

        if r["freshness_state"] == "Stale":
            stale_reports += 1

        if r["confidence_category"] == "Low":
            low_conf_reports += 1

        total_conf += r["confidence_score"]
        total_prio += r["priority_score"]

        if r["conflict_detected"]:
            conflict_count += 1

        if r["duplicate_detected"]:
            correlated_report_count += 1

    avg_conf = round(total_conf / total, 1) if total > 0 else 0.0
    avg_prio = round(total_prio / total, 1) if total > 0 else 0.0

    # Recent activity
    recent_sorted = sorted(
        reports,
        key=lambda x: x.get("last_updated") or "",
        reverse=True,
    )[:10]

    recent_activity = [
        {
            "report_id": r["report_id"],
            "incident_type": r["incident_type"],
            "zone": r["zone"],
            "status": r["status"],
            "priority_category": r["priority_category"],
            "confidence_category": r["confidence_category"],
            "last_updated": r["last_updated"],
        }
        for r in recent_sorted
    ]

    return DashboardStats(
        total_reports=total,
        verified_reports=status_counts.get("Verified", 0),
        pending_reports=status_counts.get("Pending", 0),
        rejected_reports=status_counts.get("Rejected", 0),
        needs_review_reports=status_counts.get("Needs Review", 0),
        critical_reports=critical_reports,
        high_priority_reports=high_prio_reports,
        stale_reports=stale_reports,
        low_confidence_reports=low_conf_reports,
        average_confidence=avg_conf,
        average_priority=avg_prio,
        conflict_count=conflict_count,
        correlated_report_count=correlated_report_count,
        incident_type_counts=incident_type_counts,
        zone_counts=zone_counts,
        source_counts=source_counts,
        department_counts=department_counts,
        permit_impact_counts=permit_impact_counts,
        recent_activity=recent_activity,
    )


# ── Metrics API ─────────────────────────────────────────────────────────────

@app.get(
    "/api/metrics",
    response_model=MetricsResponse,
    tags=["Evaluation Metrics"],
    summary="System performance and precision/recall evaluation metrics",
)
async def system_metrics() -> MetricsResponse:
    reports = get_enriched_reports()
    metrics_data = compute_system_metrics(reports)
    return MetricsResponse.model_validate(metrics_data)


