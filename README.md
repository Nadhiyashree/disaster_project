# Disaster Response Crowd-Report Verification & Confidence Dashboard

> **Decision-Support System for Emergency Operations Command Centers**  
> *Human verification is required before all operational actions.*

---

## 🏛️ Project Overview

The **Disaster Response Command Center** is a professional, decision-support platform designed to ingest, process, correlate, evaluate, and prioritize multi-source disaster reports (citizen reports, emergency calls, field responders, sensors, and department logs) during municipal emergencies.

The system incorporates automated spatial-temporal conflict detection, near-duplicate correlation clustering, multi-factor evidence confidence scoring, freshness temporal decay, and operational priority ranking—all while maintaining strict ethical governance and human-in-the-loop auditability.

---

## 📊 Complete Project Progression & Status

| Phase | Description | Status | Completion |
|---|---|:---:|:---:|
| **Phase 1** | Runnable foundation, synthetic dataset (1,200 reports), basic REST backend, CSV data layer | ✅ | 35% |
| **Phase 2** | Spatial-temporal conflict engine, duplicate clustering, confidence/priority formulas, evaluation metrics, unit tests | ✅ | **70%** |
| **Phase 3** | Full operations dashboard UI, Leaflet map, analytics, methodology, human-verification workflow, API documentation | ⏳ *Planned* | 100% |

---

## 📁 Repository & Architectural Structure

```
disaster-response-dashboard/
│
├── backend/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application, REST endpoints, static file mounting
│   ├── models.py                # Core domain enums (IncidentType, Zone, PriorityCategory, etc.)
│   ├── schemas.py               # Pydantic request/response schemas & validation
│   ├── data_loader.py           # Synthetic dataset generation (seed=42) & CSV caching
│   └── services/
│       ├── __init__.py
│       ├── haversine_utils.py   # WGS-84 Haversine great-circle distance calculations
│       ├── confidence_engine.py # 6-factor evidence scoring & mandatory confidence capping rules
│       ├── priority_engine.py   # Severity, confidence, freshness, and urgency triage scoring
│       ├── freshness_engine.py  # Temporal decay evaluation (Fresh, Aging, Old, Stale, Unknown)
│       ├── conflict_detector.py # Spatial-temporal contradiction & status discrepancy detector
│       ├── duplicate_detector.py# Near-duplicate correlation clustering (SequenceMatcher + DFS)
│       └── metrics.py           # Ground-truth evaluation (Precision, Recall, FPR, Miss Rate)
│
├── frontend/
│   ├── index.html               # Landing portal
│   ├── dashboard.html           # Main operations command center
│   ├── reports.html             # Master report triage queue & multi-filter interface
│   ├── report-details.html      # Deep-dive report evidence breakdown & human verification modal
│   ├── analytics.html           # Interactive evaluation metrics & threshold experiment charts
│   ├── methodology.html         # Comprehensive system formulas & governance documentation
│   ├── css/
│   │   └── style.css            # Full design system (CSS variables, dark mode UI tokens)
│   └── js/
│       ├── api.js               # Centralized REST API client (fetch wrapper with error boundaries)
│       ├── app.js               # Global utilities, role switcher, toast notifications
│       ├── map.js               # Leaflet.js interactive GIS map module
│       ├── dashboard.js         # Command center controller & live activity feed
│       ├── reports.js           # Triage table controller, pagination & demo filter presets
│       ├── report-details.js    # Single-report inspector & human verification controller
│       └── analytics.js         # Chart.js visualization for metrics & experiments
│
├── data/
│   ├── disaster_reports.csv     # 1,200 row synthetic disaster report dataset
│   └── verification_audit.json  # Append-only human verification action audit trail
│
├── experiments/
│   ├── baseline.py              # Manual sequential review (FIFO) vs Dashboard triage simulation
│   ├── evaluation.py            # Threshold trade-off experiment (Responder, Balanced, Official)
│   └── validation.py            # 3-role, 5-task proxy validation study simulation
│
├── tests/
│   ├── test_api.py              # FastAPI endpoint integration tests (TestClient)
│   ├── test_confidence.py       # Confidence engine scoring & capping rule tests
│   ├── test_conflict.py         # Conflict detection unit tests
│   ├── test_duplicate.py        # Near-duplicate clustering & corroboration discount tests
│   ├── test_edge_cases.py       # Edge cases (missing timestamps, stale, future timestamps)
│   ├── test_experiments.py      # Baseline, evaluation, and validation experiment tests
│   ├── test_freshness.py        # Temporal decay unit tests
│   └── test_priority.py         # Priority triage scoring unit tests
│
├── requirements.txt             # Python dependencies (fastapi, uvicorn, pandas, pytest, etc.)
├── README.md                    # Comprehensive technical documentation & API specification
└── run instructions.txt         # Quickstart guide
```

---

## 🗄️ Database & Data Schema (`data/disaster_reports.csv`)

The data layer uses an in-memory cached CSV repository. Each report record conforms to the following schema:

| Field Name | Type | Description / Valid Values |
|---|---|---|
| `report_id` | `string` | Unique identifier (e.g. `RPT-00001`) |
| `timestamp` | `datetime` | ISO-8601 UTC timestamp of original crowd observation |
| `zone` | `string` | Municipal zone (`North District`, `South District`, `East District`, `West District`, `Central District`, `Riverside`, `Industrial Zone`, `Old Town`) |
| `latitude` | `float` | Spatial coordinate in decimal degrees |
| `longitude` | `float` | Spatial coordinate in decimal degrees |
| `incident_type` | `string` | Hazard type (`Road Flooding`, `Structural Damage`, `Power Outage`, `Medical Emergency`, `Evacuation Needed`, `Water Contamination`) |
| `description` | `string` | Free-text narrative observation provided by source |
| `source_type` | `string` | Reporting source (`Citizen Report`, `Emergency Call`, `Field Responder`, `Sensor`, `Department Report`) |
| `corroborating_report_count` | `int` | Raw number of matching crowd submissions |
| `responder_status` | `string` | Initial operational status (`Pending`, `Verified`, `Needs Review`, `Rejected`) |
| `location_precision` | `string` | Spatial accuracy category (`Exact`, `High`, `Medium`, `Low`, `Unknown`) |
| `media_type` | `string` | Supporting attachment evidence (`Photo`, `Video`, `Audio`, `None`) |
| `ground_truth` | `string` | Evaluation-only internal truth indicator (`TRUE`, `FALSE`, `UNKNOWN`) |
| `department` | `string` | Assigned department (`Emergency Services`, `Public Works`, `Medical Services`, `Water Department`, `Electricity Department`, `Disaster Management`) |
| `permit_impact` | `string` | Hazard impact rating (`Critical`, `High`, `Medium`, `Low`) |
| `status` | `string` | Current operational state (`Pending`, `Verified`, `Needs Review`, `Rejected`) |
| `last_updated` | `datetime` | ISO-8601 UTC timestamp of last human action or system enrichment |

---

## 🌐 Complete API Endpoints Specification

All REST APIs are served by FastAPI under `/api/`. Interactive Swagger UI is available at `http://127.0.0.1:8000/docs`.

### 1. System & Health
* **`GET /api/health`**
  * **Summary**: System operational status check.
  * **Response**: `{"status": "ok", "service": "disaster-response-dashboard", "timestamp": "..."}`

### 2. Report Management & Triage
* **`GET /api/reports`**
  * **Summary**: Paginated and filterable master report listing.
  * **Query Parameters**:
    * `search` (str): Free-text search on ID, zone, incident, description, or department.
    * `incident_type` (str): Filter by hazard type.
    * `zone` (str): Filter by zone.
    * `source_type` (str): Filter by reporting source.
    * `priority_category` (str): Filter by priority (`Critical`, `High`, `Medium`, `Low`).
    * `confidence_category` (str): Filter by confidence (`Very High`, `High`, `Medium`, `Low`).
    * `freshness_state` (str): Filter by freshness (`Fresh`, `Aging`, `Old`, `Stale`, `Unknown`).
    * `status` (str): Filter by operational verification status (`Pending`, `Verified`, `Needs Review`, `Rejected`).
    * `department` (str): Filter by assigned department.
    * `sort_by` (str): Field to sort by (`priority_score`, `confidence_score`, `freshness_score`, `last_updated`).
    * `sort_order` (str): Sort order (`asc`, `desc`). Default: `desc`.
    * `limit` (int): Page size (default: 25, max: 500).
    * `offset` (int): Page offset (default: 0).
  * **Response**: `ReportListResponse` containing `items` list and `total` count.

* **`GET /api/reports/{report_id}`**
  * **Summary**: Retrieve a single report with full evidence score breakdowns.
  * **Response**: `ReportDetailResponse` containing `report`, `confidence`, `priority`, `freshness`, `conflicts`, and `correlated_reports`.

* **`GET /api/reports/priority`**
  * **Summary**: Urgent Priority Response Queue sorted strictly by `priority_score` descending.

* **`GET /api/reports/stale`**
  * **Summary**: Retrieve reports with `freshness_state == "Stale"` (> 6 hours old).

* **`GET /api/reports/conflicts`**
  * **Summary**: Retrieve all reports flagged with spatial-temporal or textual contradictions.

### 3. Human Verification & Audit
* **`POST /api/reports/{report_id}/verify`**
  * **Summary**: Submit a human dispatcher verification action.
  * **Request Body**: `{"status": "Verified" | "Rejected" | "Needs Review" | "Pending", "notes": "Optional dispatcher notes"}`
  * **Action**: Updates report status in-memory and appends an immutable audit entry to `data/verification_audit.json`.

### 4. Dashboard Statistics & Analytics
* **`GET /api/dashboard/stats`**
  * **Summary**: Aggregated real-time command center metrics (total counts, priority counts, stale counts, average scores, incident/zone distributions).

* **`GET /api/metrics`**
  * **Summary**: System evaluation metrics computed against ground truth (`precision`, `recall`, `false_positive_rate`, `high_priority_missed`, etc.).

### 5. Experiments & Validation
* **`GET /api/experiments/baseline`**
  * **Summary**: Time-to-Surface simulation comparing manual FIFO review vs priority dashboard triage.
* **`GET /api/experiments/thresholds`**
  * **Summary**: Strategy threshold trade-off evaluation (`Responder` 0.30, `Balanced` 0.50, `City Official` 0.65).
* **`GET /api/validation`**
  * **Summary**: Simulated 3-role, 5-task proxy validation study results.

---

## 🧪 Unit Testing, Test Coverage & Error Boundaries

The project includes an extensive automated test suite built with `pytest` and `fastapi.testclient.TestClient`.

### 1. Running the Automated Test Suite

```bash
python -m pytest tests/ -v
```

### 2. Test Suite Breakdown (42 Passing Tests)

| Test Module | Coverage & Objective | Status |
|---|---|:---:|
| **`tests/test_api.py`** | REST API integration tests (health, reports, single report details, 404 handling, priority queue, stale reports, conflicts, verification endpoint, stats, metrics) | ✅ PASSED (10/10) |
| **`tests/test_confidence.py`** | 6-factor evidence confidence formula, corroboration mappings, and mandatory confidence capping rules for weak single citizen reports | ✅ PASSED (4/4) |
| **`tests/test_conflict.py`** | Spatial-temporal conflict candidate selection (Haversine $\le 1.0\text{ km}$, $|\Delta t| \le 30\text{ min}$) and material claim contradiction detection | ✅ PASSED (2/2) |
| **`tests/test_duplicate.py`** | Near-duplicate spatial-temporal score calculations, `SequenceMatcher` text similarity, connected components DFS clustering, and corroboration discounting | ✅ PASSED (2/2) |
| **`tests/test_freshness.py`** | Temporal decay evaluation across time windows (Fresh $0\text{--}15\text{m}$, Aging $15\text{--}120\text{m}$, Old $2\text{--}6\text{h}$, Stale $>6\text{h}$) | ✅ PASSED (6/6) |
| **`tests/test_priority.py`** | Priority triage scoring, incident severity weighting, and verifying **Confidence $\neq$ Priority** | ✅ PASSED (3/3) |
| **`tests/test_experiments.py`** | Baseline simulation, threshold trade-off experiments, validation study data, and audit logging persistence | ✅ PASSED (7/7) |
| **`tests/test_edge_cases.py`** | 8 specific edge-case validations (missing timestamps, future timestamps, missing media, high severity + low confidence, etc.) | ✅ PASSED (8/8) |

### 3. Error Boundaries & Resilience Mechanisms

* **Missing / NaN Coordinates**: `safe_haversine_distance()` gracefully returns `None` without raising exceptions when latitude or longitude is missing.
* **Missing or Future Timestamps**: `evaluate_freshness()` assigns `freshness_state = "Unknown"` ($0.00$ score) and attaches a descriptive warning rather than throwing parser errors.
* **Missing Media Evidence**: Reports missing photos or videos receive a media evidence score of $0.00$, but are **never** automatically marked false or hidden.
* **Confidence Capping Boundary**: Prevents single unverified citizen reports without media or corroboration from exceeding $69.0$ (Medium category) to stop ungrounded rumor surfacing.
* **API Error Response Boundary**: All invalid requests, missing report IDs (`404 Not Found`), or malformed filter inputs return structured `ErrorResponse` objects with `detail` messages.
* **Frontend Resilience**: `frontend/js/api.js` wraps all HTTP fetch requests in `try/catch` blocks, providing fallback UI empty states, spinner indicators, and toast error notifications.

---

## ⚡ Installation & Quickstart

### Step 1 — Clone Repository & Install Dependencies
```bash
git clone https://github.com/Nadhiyashree/disaster_project.git
cd disaster_project
pip install -r requirements.txt
```

### Step 2 — Start Backend Server
```bash
uvicorn backend.main:app --reload
```
* The backend auto-generates `data/disaster_reports.csv` on first startup if it does not exist.
* Server URL: **http://127.0.0.1:8000**
* API Swagger Docs: **http://127.0.0.1:8000/docs**

### Step 3 — Open Web Application
Open your web browser at:
* Landing Page: `http://127.0.0.1:8000`
* Operations Dashboard: `http://127.0.0.1:8000/dashboard.html`
* Master Reports Triage: `http://127.0.0.1:8000/reports.html`
* Analytics & Experiments: `http://127.0.0.1:8000/analytics.html`
* System Methodology: `http://127.0.0.1:8000/methodology.html`

---

## 🔒 Responsible AI & Privacy Guarantees

- ❌ **No Citizen Reputation Scoring**: All citizen reports receive the exact same baseline source reliability weight ($0.40$).
- ❌ **No User Profiling or Behavioral Tracking**: No user identity tracking, device fingerprinting, or IP logging.
- ❌ **No Automatic Enforcement**: Operational dispatch, permit rejection, or emergency deployment actions are **100% human-authorized**.
- 🔒 **Ground Truth Isolation**: Internal `ground_truth` values are strictly used for evaluation metrics and are never displayed in operational views.
