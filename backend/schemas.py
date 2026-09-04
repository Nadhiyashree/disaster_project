"""
Pydantic schemas for API request/response serialization.

All schemas used in FastAPI route definitions live here.
Business logic models are in models.py and backend/services/.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str = Field(..., example="ok")
    service: str = Field(..., example="disaster-response-dashboard")
    timestamp: Optional[str] = None


# ---------------------------------------------------------------------------
# Individual Enriched Report
# ---------------------------------------------------------------------------

class ReportSchema(BaseModel):
    # Raw report fields
    report_id: str
    timestamp: Optional[str] = None          # ISO-8601 string; None if missing
    zone: str
    latitude: float
    longitude: float
    incident_type: str
    description: str
    source_type: str
    corroborating_report_count: int
    responder_status: str
    location_precision: str
    media_type: str
    ground_truth: str                         # Evaluation field; internal
    department: str
    permit_impact: str
    status: str
    last_updated: Optional[str] = None       # ISO-8601 string; None if missing

    # Derived Phase 2 Intelligence Fields
    confidence_score: float = 0.0
    confidence_category: str = "Low"
    confidence_capped: bool = False
    confidence_cap_reason: Optional[str] = None

    priority_score: float = 0.0
    priority_category: str = "Low"

    freshness_score: float = 0.0
    freshness_state: str = "Unknown"
    minutes_since_report: Optional[float] = None
    freshness_warning: Optional[str] = None

    conflict_detected: bool = False
    conflict_type: Optional[str] = None
    conflict_explanation: Optional[str] = None

    duplicate_detected: bool = False
    correlation_group_id: Optional[str] = None
    related_report_ids: List[str] = Field(default_factory=list)
    similarity_reason: Optional[str] = None
    raw_corroboration_count: int = 0
    independent_corroboration_count: int = 0
    corroboration_adjustment_note: Optional[str] = None

    confidence_explanation: Dict[str, Any] = Field(default_factory=dict)
    priority_explanation: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Single Report Details Response Structure
# ---------------------------------------------------------------------------

class ReportDetailResponse(BaseModel):
    report: ReportSchema
    confidence: Dict[str, Any]
    priority: Dict[str, Any]
    freshness: Dict[str, Any]
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    correlated_reports: List[Dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Verification Request
# ---------------------------------------------------------------------------

class VerificationRequest(BaseModel):
    status: str = Field(..., description="Target status: Verified, Rejected, Needs Review, or Pending")
    notes: Optional[str] = Field(None, description="Optional verification notes")


# ---------------------------------------------------------------------------
# Paginated Reports Response
# ---------------------------------------------------------------------------

class ReportListResponse(BaseModel):
    items: List[ReportSchema]
    total: int = Field(..., description="Total number of reports matching the query")
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Dashboard Statistics
# ---------------------------------------------------------------------------

class DashboardStats(BaseModel):
    total_reports: int
    verified_reports: int
    pending_reports: int
    rejected_reports: int
    needs_review_reports: int

    # Intelligence metrics
    critical_reports: int = 0
    high_priority_reports: int = 0
    stale_reports: int = 0
    low_confidence_reports: int = 0
    average_confidence: float = 0.0
    average_priority: float = 0.0
    conflict_count: int = 0
    correlated_report_count: int = 0

    incident_type_counts: Dict[str, int]
    zone_counts: Dict[str, int]
    source_counts: Dict[str, int]
    department_counts: Dict[str, int]
    permit_impact_counts: Dict[str, int]
    recent_activity: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Last 10 most recently updated reports for activity feed",
    )


# ---------------------------------------------------------------------------
# Metrics Response
# ---------------------------------------------------------------------------

class MetricsResponse(BaseModel):
    total_evaluated: int
    ground_truth_true_count: int
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int
    precision: float
    recall: float
    false_positive_rate: float
    high_priority_missed: int
    high_priority_missed_rate: float
    average_confidence: float
    average_priority: float
    evaluation_notice: str


# ---------------------------------------------------------------------------
# Error Response
# ---------------------------------------------------------------------------

class ErrorResponse(BaseModel):
    detail: str
    report_id: Optional[str] = None
