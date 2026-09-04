"""
data_loader.py
==============
Responsible for:
  - Locating and loading the disaster_reports.csv
  - Validating required columns
  - Generating the dataset if it does not already exist
  - Exposing clean, typed DataFrames to the rest of the backend
  - Caching the DataFrame in memory so it is not re-read on every request

Public API
----------
get_reports_df()          -> pd.DataFrame  (full, cached dataset)
generate_dataset()        -> None          (writes CSV to disk if missing)
validate_csv_columns()    -> bool
"""

from __future__ import annotations

import logging
import math
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from backend.models import (
    Department,
    GroundTruth,
    IncidentType,
    LocationPrecision,
    MediaType,
    PermitImpact,
    ReportStatus,
    ResponderStatus,
    SourceType,
    Zone,
    ZONE_COORDINATES,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_BACKEND_DIR = Path(__file__).parent
_PROJECT_ROOT = _BACKEND_DIR.parent
DATA_DIR = _PROJECT_ROOT / "data"
CSV_PATH = DATA_DIR / "disaster_reports.csv"

# ---------------------------------------------------------------------------
# Required columns (subset used for validation)
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = [
    "report_id", "timestamp", "zone", "latitude", "longitude",
    "incident_type", "description", "source_type", "corroborating_report_count",
    "responder_status", "location_precision", "media_type", "ground_truth",
    "department", "permit_impact", "status", "last_updated",
]

# ---------------------------------------------------------------------------
# In-memory cache
# ---------------------------------------------------------------------------

_df_cache: Optional[pd.DataFrame] = None


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def get_reports_df() -> pd.DataFrame:
    """Return the full dataset as a DataFrame (cached after first load)."""
    global _df_cache
    if _df_cache is None:
        _df_cache = _load_csv()
    return _df_cache


def reload_reports_df() -> pd.DataFrame:
    """Force a reload from disk, refreshing the cache."""
    global _df_cache
    _df_cache = _load_csv()
    return _df_cache


def validate_csv_columns(df: pd.DataFrame) -> bool:
    """Return True if all required columns are present."""
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        logger.error("CSV is missing required columns: %s", missing)
        return False
    return True


def generate_dataset(n: int = 1200, seed: int = 42) -> None:
    """Generate n synthetic disaster reports and write to CSV_PATH."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = _build_dataframe(n, seed)
    df.to_csv(CSV_PATH, index=False)
    logger.info("Generated %d rows -> %s", len(df), CSV_PATH)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_csv() -> pd.DataFrame:
    if not CSV_PATH.exists():
        logger.warning("CSV not found; generating dataset…")
        generate_dataset()

    df = pd.read_csv(CSV_PATH, dtype=str)

    if not validate_csv_columns(df):
        raise RuntimeError(f"CSV at {CSV_PATH} is missing required columns.")

    # Parse timestamps, coerce errors to NaT
    for col in ("timestamp", "last_updated"):
        df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

    # Numeric coercion
    df["corroborating_report_count"] = pd.to_numeric(
        df["corroborating_report_count"], errors="coerce"
    ).fillna(0).astype(int)
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    logger.info("Loaded %d reports from %s", len(df), CSV_PATH)
    return df


# ---------------------------------------------------------------------------
# Dataset generation
# ---------------------------------------------------------------------------

# Realistic description templates keyed by incident type
_DESCRIPTIONS: dict[str, list[str]] = {
    IncidentType.ROAD_FLOODING: [
        "Heavy water accumulation reported near the main road, vehicles unable to pass.",
        "Floodwater covering the intersection, depth estimated at 30 cm.",
        "Road submerged after heavy rainfall; residents warned to avoid the area.",
        "Waterlogging observed along the central corridor; traffic diverted.",
        "Standing water blocking access road; multiple vehicles stranded.",
        "Flooding on underpass reported by commuters; immediate attention needed.",
        "Low-lying road completely inundated following storm surge.",
        "Residents report rapidly rising water levels along the service road.",
        "Drainage overflow causing road flooding; pedestrian safety at risk.",
        "Emergency vehicles unable to reach destination due to flooded road.",
    ],
    IncidentType.STRUCTURAL_DAMAGE: [
        "Possible structural damage observed near a residential building following tremors.",
        "Cracks reported on the exterior walls of the apartment block.",
        "Partial collapse of boundary wall after last night's storm.",
        "Building foundation appears compromised; residents evacuated as precaution.",
        "Roof section collapsed on commercial premises; no injuries reported yet.",
        "Field responder confirms structural cracks on load-bearing column.",
        "Overhead bridge shows signs of structural instability; area cordoned off.",
        "House wall leaning dangerously; occupants requested to vacate premises.",
        "Old structure shows severe erosion damage; engineer inspection required.",
        "Multiple reports of ceiling damage in adjacent buildings after tremor.",
    ],
    IncidentType.POWER_OUTAGE: [
        "Multiple residents report loss of electrical power in the neighbourhood.",
        "Complete power failure affecting an estimated 500 households.",
        "Substation tripped due to flooding; restoration time unknown.",
        "Power lines down across the main avenue; risk of electrocution.",
        "Electricity supply disrupted; hospitals on backup generators.",
        "Transformer explosion reported; area in complete darkness.",
        "Widespread outage affecting critical facilities including water treatment plant.",
        "Sensor network confirms power failure across the grid sector.",
        "Repeated fluctuations followed by complete outage; residents concerned.",
        "Street lighting out; increased security risk in affected area.",
    ],
    IncidentType.MEDICAL_EMERGENCY: [
        "Medical assistance reportedly required near the intersection.",
        "Elderly resident collapsed; ambulance requested immediately.",
        "Multiple casualties reported at scene; medical teams needed urgently.",
        "Injured person found in flooded basement; rescue and medical support needed.",
        "Emergency call received about a person trapped and showing signs of distress.",
        "Child with respiratory symptoms reported; possible exposure to contaminant.",
        "Mass casualty event suspected following building partial collapse.",
        "Caller reports two unconscious individuals at the site.",
        "Severe trauma case reported by field responder; air evacuation may be needed.",
        "Person found unresponsive; bystanders performing CPR; ambulance en route.",
    ],
    IncidentType.EVACUATION_NEEDED: [
        "Mandatory evacuation ordered for low-lying residential blocks.",
        "Rising floodwater threatening neighbourhood; evacuation in progress.",
        "Residents refusing to evacuate despite imminent structural risk.",
        "Evacuation shelters at capacity; additional sites urgently required.",
        "Mass evacuation of high-rise building due to fire and smoke.",
        "Families stranded; evacuation routes blocked by debris.",
        "Chemical leak nearby necessitates immediate area evacuation.",
        "Multiple elderly residents require assisted evacuation support.",
        "Evacuation order issued for industrial zone due to hazardous spill.",
        "Neighbourhood cordoned off; evacuation underway with police assistance.",
    ],
    IncidentType.WATER_CONTAMINATION: [
        "Residents report discoloured tap water with unusual odour.",
        "Water samples show elevated turbidity following pipeline damage.",
        "Possible sewage intrusion into potable water supply reported.",
        "Multiple residents hospitalised with gastrointestinal symptoms after water consumption.",
        "Chemical smell detected in municipal water supply in the district.",
        "Water department confirms contamination in sector; do-not-drink advisory issued.",
        "Sensor alert: pH level outside safe range in distribution main.",
        "Illegal industrial discharge suspected to have contaminated water source.",
        "Blue-green algae bloom observed in reservoir; water supply may be affected.",
        "Pipe burst near waste facility; contamination risk flagged by engineers.",
    ],
}


def _pick(choices: list, rng: random.Random) -> str:
    return rng.choice(choices)


def _gauss_clamp(centre: float, spread: float, rng: random.Random) -> float:
    val = rng.gauss(centre, spread / 2.5)
    return round(val, 6)


def _build_dataframe(n: int, seed: int) -> pd.DataFrame:
    rng = random.Random(seed)
    now = datetime.now(tz=timezone.utc)

    # Freshness window boundaries (minutes before now)
    FRESH_MAX = 15
    AGING_MAX = 120
    OLD_MAX = 360
    STALE_MAX = 4320   # ~3 days

    zones = [z for z in Zone]
    incident_types = [i for i in IncidentType]
    source_types = [s for s in SourceType]

    # ---------------------------------------------------------------------------
    # Define realistic incident profiles
    # ---------------------------------------------------------------------------

    incident_profiles: dict[str, dict] = {
        IncidentType.ROAD_FLOODING: {
            "sources": [SourceType.CITIZEN_REPORT, SourceType.CITIZEN_REPORT,
                        SourceType.EMERGENCY_CALL, SourceType.SENSOR,
                        SourceType.FIELD_RESPONDER],
            "media": [MediaType.PHOTO, MediaType.PHOTO, MediaType.VIDEO,
                      MediaType.NONE, MediaType.AUDIO],
            "precision": [LocationPrecision.LOW, LocationPrecision.MEDIUM,
                          LocationPrecision.HIGH, LocationPrecision.EXACT,
                          LocationPrecision.UNKNOWN],
            "corroboration_range": (0, 12),
            "departments": [Department.PUBLIC_WORKS, Department.EMERGENCY_SERVICES,
                            Department.DISASTER_MANAGEMENT],
            "permit_impact": [PermitImpact.LOW, PermitImpact.MEDIUM, PermitImpact.HIGH],
            "status_weights": {"Pending": 0.35, "Verified": 0.30,
                               "Needs Review": 0.25, "Rejected": 0.10},
            "ground_truth_weights": {"TRUE": 0.60, "FALSE": 0.15, "UNKNOWN": 0.25},
        },
        IncidentType.STRUCTURAL_DAMAGE: {
            "sources": [SourceType.FIELD_RESPONDER, SourceType.FIELD_RESPONDER,
                        SourceType.CITIZEN_REPORT, SourceType.EMERGENCY_CALL,
                        SourceType.DEPARTMENT_REPORT],
            "media": [MediaType.PHOTO, MediaType.PHOTO, MediaType.VIDEO,
                      MediaType.UNAVAILABLE, MediaType.NONE],
            "precision": [LocationPrecision.EXACT, LocationPrecision.HIGH,
                          LocationPrecision.MEDIUM, LocationPrecision.HIGH],
            "corroboration_range": (0, 8),
            "departments": [Department.PUBLIC_WORKS, Department.EMERGENCY_SERVICES,
                            Department.DISASTER_MANAGEMENT],
            "permit_impact": [PermitImpact.MEDIUM, PermitImpact.HIGH, PermitImpact.CRITICAL],
            "status_weights": {"Pending": 0.20, "Verified": 0.45,
                               "Needs Review": 0.25, "Rejected": 0.10},
            "ground_truth_weights": {"TRUE": 0.65, "FALSE": 0.10, "UNKNOWN": 0.25},
        },
        IncidentType.POWER_OUTAGE: {
            "sources": [SourceType.SENSOR, SourceType.SENSOR,
                        SourceType.DEPARTMENT_REPORT, SourceType.CITIZEN_REPORT,
                        SourceType.EMERGENCY_CALL],
            "media": [MediaType.NONE, MediaType.NONE, MediaType.PHOTO,
                      MediaType.VIDEO, MediaType.UNAVAILABLE],
            "precision": [LocationPrecision.HIGH, LocationPrecision.EXACT,
                          LocationPrecision.MEDIUM, LocationPrecision.LOW],
            "corroboration_range": (2, 20),
            "departments": [Department.ELECTRICITY_DEPARTMENT, Department.PUBLIC_WORKS,
                            Department.EMERGENCY_SERVICES],
            "permit_impact": [PermitImpact.NONE, PermitImpact.LOW, PermitImpact.MEDIUM],
            "status_weights": {"Pending": 0.25, "Verified": 0.50,
                               "Needs Review": 0.15, "Rejected": 0.10},
            "ground_truth_weights": {"TRUE": 0.70, "FALSE": 0.10, "UNKNOWN": 0.20},
        },
        IncidentType.MEDICAL_EMERGENCY: {
            "sources": [SourceType.EMERGENCY_CALL, SourceType.EMERGENCY_CALL,
                        SourceType.FIELD_RESPONDER, SourceType.CITIZEN_REPORT,
                        SourceType.DEPARTMENT_REPORT],
            "media": [MediaType.NONE, MediaType.AUDIO, MediaType.VIDEO,
                      MediaType.PHOTO, MediaType.UNAVAILABLE],
            "precision": [LocationPrecision.EXACT, LocationPrecision.HIGH,
                          LocationPrecision.HIGH, LocationPrecision.MEDIUM],
            "corroboration_range": (0, 5),
            "departments": [Department.MEDICAL_SERVICES, Department.EMERGENCY_SERVICES],
            "permit_impact": [PermitImpact.NONE, PermitImpact.LOW],
            "status_weights": {"Pending": 0.15, "Verified": 0.60,
                               "Needs Review": 0.20, "Rejected": 0.05},
            "ground_truth_weights": {"TRUE": 0.75, "FALSE": 0.05, "UNKNOWN": 0.20},
        },
        IncidentType.EVACUATION_NEEDED: {
            "sources": [SourceType.FIELD_RESPONDER, SourceType.DEPARTMENT_REPORT,
                        SourceType.EMERGENCY_CALL, SourceType.CITIZEN_REPORT,
                        SourceType.SENSOR],
            "media": [MediaType.VIDEO, MediaType.PHOTO, MediaType.NONE,
                      MediaType.AUDIO, MediaType.UNAVAILABLE],
            "precision": [LocationPrecision.HIGH, LocationPrecision.EXACT,
                          LocationPrecision.MEDIUM, LocationPrecision.LOW],
            "corroboration_range": (3, 25),
            "departments": [Department.EMERGENCY_SERVICES, Department.DISASTER_MANAGEMENT,
                            Department.PUBLIC_WORKS],
            "permit_impact": [PermitImpact.HIGH, PermitImpact.CRITICAL],
            "status_weights": {"Pending": 0.20, "Verified": 0.50,
                               "Needs Review": 0.20, "Rejected": 0.10},
            "ground_truth_weights": {"TRUE": 0.65, "FALSE": 0.10, "UNKNOWN": 0.25},
        },
        IncidentType.WATER_CONTAMINATION: {
            "sources": [SourceType.SENSOR, SourceType.DEPARTMENT_REPORT,
                        SourceType.CITIZEN_REPORT, SourceType.FIELD_RESPONDER,
                        SourceType.EMERGENCY_CALL],
            "media": [MediaType.NONE, MediaType.PHOTO, MediaType.VIDEO,
                      MediaType.UNAVAILABLE, MediaType.AUDIO],
            "precision": [LocationPrecision.HIGH, LocationPrecision.EXACT,
                          LocationPrecision.MEDIUM, LocationPrecision.LOW,
                          LocationPrecision.UNKNOWN],
            "corroboration_range": (1, 15),
            "departments": [Department.WATER_DEPARTMENT, Department.PUBLIC_WORKS,
                            Department.MEDICAL_SERVICES, Department.EMERGENCY_SERVICES],
            "permit_impact": [PermitImpact.MEDIUM, PermitImpact.HIGH, PermitImpact.CRITICAL],
            "status_weights": {"Pending": 0.30, "Verified": 0.40,
                               "Needs Review": 0.20, "Rejected": 0.10},
            "ground_truth_weights": {"TRUE": 0.60, "FALSE": 0.15, "UNKNOWN": 0.25},
        },
    }

    # Timestamp freshness distribution weights
    freshness_bins = ["fresh", "aging", "old", "stale", "missing"]
    freshness_weights = [0.12, 0.25, 0.28, 0.30, 0.05]

    rows = []
    for i in range(n):
        incident = _pick(incident_types, rng)
        profile = incident_profiles[incident]
        zone_name = _pick(zones, rng)
        zone_coords = ZONE_COORDINATES[zone_name]

        lat = _gauss_clamp(zone_coords["lat_centre"], zone_coords["lat_spread"], rng)
        lon = _gauss_clamp(zone_coords["lon_centre"], zone_coords["lon_spread"], rng)

        source = _pick(profile["sources"], rng)
        media = _pick(profile["media"], rng)
        precision = _pick(profile["precision"], rng)
        department = _pick(profile["departments"], rng)
        permit_impact = _pick(profile["permit_impact"], rng)

        corr_min, corr_max = profile["corroboration_range"]
        corroboration = rng.randint(corr_min, corr_max)

        # Status
        sw = profile["status_weights"]
        status_keys = list(sw.keys())
        status_vals = [sw[k] for k in status_keys]
        status = rng.choices(status_keys, weights=status_vals, k=1)[0]

        # Responder status aligned with report status
        if status == "Verified":
            responder_status = ResponderStatus.VERIFIED
        elif status == "Rejected":
            responder_status = ResponderStatus.REJECTED
        elif status == "Needs Review":
            responder_status = rng.choice([ResponderStatus.NEEDS_REVIEW, ResponderStatus.PENDING])
        else:
            responder_status = rng.choice([ResponderStatus.PENDING, ResponderStatus.NEEDS_REVIEW])

        # Ground truth
        gtw = profile["ground_truth_weights"]
        gt_keys = list(gtw.keys())
        gt_vals = [gtw[k] for k in gt_keys]
        ground_truth = rng.choices(gt_keys, weights=gt_vals, k=1)[0]

        # Timestamp
        freshness = rng.choices(freshness_bins, weights=freshness_weights, k=1)[0]
        if freshness == "missing":
            timestamp = None
            last_updated = None
        else:
            if freshness == "fresh":
                minutes_ago = rng.uniform(0, FRESH_MAX)
            elif freshness == "aging":
                minutes_ago = rng.uniform(FRESH_MAX, AGING_MAX)
            elif freshness == "old":
                minutes_ago = rng.uniform(AGING_MAX, OLD_MAX)
            else:  # stale
                minutes_ago = rng.uniform(OLD_MAX, STALE_MAX)

            timestamp = now - timedelta(minutes=minutes_ago)
            # last_updated is slightly after timestamp
            delta_update = rng.uniform(0, max(1, minutes_ago * 0.3))
            last_updated = timestamp + timedelta(minutes=delta_update)

        description = _pick(_DESCRIPTIONS[incident], rng)

        # Inject deliberate difficult cases (~8% of reports)
        if rng.random() < 0.08:
            difficulty = rng.choice([
                "high_corr_no_media",     # high corroboration but unavailable media
                "stale_critical",         # old/stale but high permit impact
                "low_conf_serious",       # citizen-only, no corroboration
                "conflicting_status",     # needs review despite sensor data
                "near_duplicate",         # duplicate-like coordinates
                "missing_responder",      # no responder status finalized
            ])
            if difficulty == "high_corr_no_media":
                corroboration = rng.randint(10, 25)
                media = MediaType.UNAVAILABLE
            elif difficulty == "stale_critical":
                if freshness != "missing":
                    minutes_ago = rng.uniform(OLD_MAX, STALE_MAX)
                    timestamp = now - timedelta(minutes=minutes_ago)
                    last_updated = timestamp + timedelta(minutes=rng.uniform(0, 30))
                permit_impact = PermitImpact.CRITICAL
            elif difficulty == "low_conf_serious":
                source = SourceType.CITIZEN_REPORT
                corroboration = 0
                status = "Needs Review"
                responder_status = ResponderStatus.NEEDS_REVIEW
            elif difficulty == "conflicting_status":
                source = SourceType.SENSOR
                status = "Needs Review"
                responder_status = ResponderStatus.NEEDS_REVIEW
            elif difficulty == "near_duplicate":
                if rows:
                    ref = rng.choice(rows[-min(50, len(rows)):])
                    lat = round(float(ref["latitude"]) + rng.uniform(-0.001, 0.001), 6)
                    lon = round(float(ref["longitude"]) + rng.uniform(-0.001, 0.001), 6)
                    incident = ref["incident_type"]
                    zone_name = ref["zone"]
            elif difficulty == "missing_responder":
                responder_status = ResponderStatus.PENDING
                status = "Pending"

        report_id = f"RPT-{i+1:05d}"

        rows.append({
            "report_id": report_id,
            "timestamp": timestamp.isoformat() if timestamp else None,
            "zone": zone_name,
            "latitude": lat,
            "longitude": lon,
            "incident_type": incident,
            "description": description,
            "source_type": source,
            "corroborating_report_count": corroboration,
            "responder_status": responder_status,
            "location_precision": precision,
            "media_type": media,
            "ground_truth": ground_truth,
            "department": department,
            "permit_impact": permit_impact,
            "status": status,
            "last_updated": last_updated.isoformat() if last_updated else None,
        })

    df = pd.DataFrame(rows)
    return df
