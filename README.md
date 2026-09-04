# Disaster Response Crowd-Report Verification & Confidence Dashboard

> **Decision-support system for emergency operations.**  
> Human verification is required before all actions.

---

## Project

A professional disaster-response dashboard that ingests simulated citizen and responder reports and supports verification, prioritisation, and situational awareness for emergency coordinators.

---

## Phase 1

Phase 1 implements the complete runnable foundation:

| Feature | Status |
|---|---|
| FastAPI REST backend | ✅ |
| 1200 synthetic disaster reports | ✅ |
| CSV data layer (no database) | ✅ |
| REST APIs (health, reports, stats) | ✅ |
| Paginated & filterable report listing | ✅ |
| Dashboard statistics (live from CSV) | ✅ |
| Leaflet map with incident markers | ✅ |
| Report detail modal | ✅ |
| Responsive UI (desktop → mobile) | ✅ |
| Accessible controls | ✅ |
| Frontend served by FastAPI | ✅ |

---

## Project Structure

```
disaster-response-dashboard/
│
├── backend/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, routes
│   ├── models.py        # Domain enums and dataclasses
│   ├── schemas.py       # Pydantic API schemas
│   └── data_loader.py   # CSV loading, caching, dataset generation
│
├── frontend/
│   ├── index.html       # Landing page
│   ├── dashboard.html   # Main operations dashboard
│   │
│   ├── css/
│   │   └── style.css    # Full design system
│   │
│   └── js/
│       ├── api.js       # Centralised API client
│       ├── app.js       # Global utilities, role selector, toasts
│       ├── map.js       # Leaflet map module
│       └── dashboard.js # Dashboard controller
│
├── data/
│   └── disaster_reports.csv   # Generated on first run (1200 rows)
│
├── experiments/         # Reserved for Phase 2+
├── tests/               # Reserved for Phase 2+
│
├── requirements.txt
├── README.md
└── run instructions.txt
```

---

## Installation

```bash
cd disaster-response-dashboard
pip install -r requirements.txt
```

---

## Running the Backend

```bash
uvicorn backend.main:app --reload
```

The dataset is generated automatically on first startup if `data/disaster_reports.csv` does not exist.

Backend URL: **http://127.0.0.1:8000**

---

## Accessing the Frontend

The frontend is served by FastAPI as static files.

Open your browser at:

```
http://127.0.0.1:8000
```

This loads the landing page. Click **Enter Operations Dashboard** to open the full dashboard at:

```
http://127.0.0.1:8000/dashboard
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/reports` | List reports (paginated, filterable) |
| GET | `/api/reports/{report_id}` | Get a single report |
| GET | `/api/dashboard/stats` | Aggregated dashboard statistics |
| GET | `/docs` | Interactive API documentation (Swagger UI) |

### Query Parameters — `/api/reports`

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Free-text search (ID, zone, incident, description) |
| `incident_type` | string | Filter by incident type |
| `zone` | string | Filter by zone |
| `source_type` | string | Filter by source type |
| `status` | string | Filter by report status |
| `department` | string | Filter by department |
| `limit` | int | Page size (default 25, max 500) |
| `offset` | int | Page offset (default 0) |

---

## Dataset

- **File**: `data/disaster_reports.csv`
- **Rows**: 1200 (generated with seed=42 for determinism)
- **Incident types**: Road Flooding, Structural Damage, Power Outage, Medical Emergency, Evacuation Needed, Water Contamination
- **Zones**: North District, South District, East District, West District, Central District, Riverside, Industrial Zone, Old Town
- **Source types**: Citizen Report, Emergency Call, Field Responder, Sensor, Department Report
- **Realistic relationships**: incident type ↔ source type ↔ media ↔ precision ↔ corroboration
- **Difficult cases**: stale-critical reports, low-confidence serious incidents, near-duplicates, missing media, conflicting evidence

---

## Future Phases

Phase 1 is structured to cleanly accommodate:

```
confidence_engine.py
priority_engine.py
freshness_engine.py
conflict_detector.py
duplicate_detector.py
metrics.py
```

---

## Design Principles

- **Decision-support only** — does not profile citizens, create reputation scores, or deploy resources automatically.
- **Human verification required** — all reports require a human decision before any operational action.
- **Ground truth is evaluation-only** — not shown in the operational UI.
