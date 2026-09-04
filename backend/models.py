"""
Internal data models for the Disaster Response Dashboard.

These are Python dataclasses and enums representing the core domain objects.
Pydantic schemas for API serialization are in schemas.py.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class IncidentType(str, Enum):
    ROAD_FLOODING = "Road Flooding"
    STRUCTURAL_DAMAGE = "Structural Damage"
    POWER_OUTAGE = "Power Outage"
    MEDICAL_EMERGENCY = "Medical Emergency"
    EVACUATION_NEEDED = "Evacuation Needed"
    WATER_CONTAMINATION = "Water Contamination"


class Zone(str, Enum):
    NORTH_DISTRICT = "North District"
    SOUTH_DISTRICT = "South District"
    EAST_DISTRICT = "East District"
    WEST_DISTRICT = "West District"
    CENTRAL_DISTRICT = "Central District"
    RIVERSIDE = "Riverside"
    INDUSTRIAL_ZONE = "Industrial Zone"
    OLD_TOWN = "Old Town"


class SourceType(str, Enum):
    CITIZEN_REPORT = "Citizen Report"
    EMERGENCY_CALL = "Emergency Call"
    FIELD_RESPONDER = "Field Responder"
    SENSOR = "Sensor"
    DEPARTMENT_REPORT = "Department Report"


# Conceptual reliability weights (for future confidence engine)
SOURCE_RELIABILITY: dict[str, float] = {
    SourceType.FIELD_RESPONDER: 1.00,
    SourceType.DEPARTMENT_REPORT: 0.95,
    SourceType.EMERGENCY_CALL: 0.90,
    SourceType.SENSOR: 0.85,
    SourceType.CITIZEN_REPORT: 0.40,
}


class ResponderStatus(str, Enum):
    VERIFIED = "Verified"
    PENDING = "Pending"
    REJECTED = "Rejected"
    NEEDS_REVIEW = "Needs Review"


class LocationPrecision(str, Enum):
    EXACT = "Exact"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNKNOWN = "Unknown"


class MediaType(str, Enum):
    PHOTO = "Photo"
    VIDEO = "Video"
    AUDIO = "Audio"
    NONE = "None"
    UNAVAILABLE = "Unavailable"


class GroundTruth(str, Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"


class Department(str, Enum):
    EMERGENCY_SERVICES = "Emergency Services"
    PUBLIC_WORKS = "Public Works"
    ELECTRICITY_DEPARTMENT = "Electricity Department"
    WATER_DEPARTMENT = "Water Department"
    MEDICAL_SERVICES = "Medical Services"
    DISASTER_MANAGEMENT = "Disaster Management"


class PermitImpact(str, Enum):
    NONE = "None"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ReportStatus(str, Enum):
    PENDING = "Pending"
    VERIFIED = "Verified"
    REJECTED = "Rejected"
    NEEDS_REVIEW = "Needs Review"


# ---------------------------------------------------------------------------
# Zone geographic centres (approximate bounding boxes for realistic scatter)
# ---------------------------------------------------------------------------

ZONE_COORDINATES: dict[str, dict] = {
    Zone.NORTH_DISTRICT: {
        "lat_centre": 28.7500,
        "lon_centre": 77.1200,
        "lat_spread": 0.025,
        "lon_spread": 0.030,
    },
    Zone.SOUTH_DISTRICT: {
        "lat_centre": 28.5000,
        "lon_centre": 77.1800,
        "lat_spread": 0.025,
        "lon_spread": 0.030,
    },
    Zone.EAST_DISTRICT: {
        "lat_centre": 28.6200,
        "lon_centre": 77.3500,
        "lat_spread": 0.020,
        "lon_spread": 0.025,
    },
    Zone.WEST_DISTRICT: {
        "lat_centre": 28.6400,
        "lon_centre": 76.9500,
        "lat_spread": 0.020,
        "lon_spread": 0.025,
    },
    Zone.CENTRAL_DISTRICT: {
        "lat_centre": 28.6300,
        "lon_centre": 77.2200,
        "lat_spread": 0.015,
        "lon_spread": 0.020,
    },
    Zone.RIVERSIDE: {
        "lat_centre": 28.6700,
        "lon_centre": 77.2700,
        "lat_spread": 0.010,
        "lon_spread": 0.015,
    },
    Zone.INDUSTRIAL_ZONE: {
        "lat_centre": 28.5800,
        "lon_centre": 77.0800,
        "lat_spread": 0.018,
        "lon_spread": 0.022,
    },
    Zone.OLD_TOWN: {
        "lat_centre": 28.6550,
        "lon_centre": 77.2300,
        "lat_spread": 0.012,
        "lon_spread": 0.015,
    },
}


# ---------------------------------------------------------------------------
# Dataclass for a single report (internal representation)
# ---------------------------------------------------------------------------

@dataclass
class DisasterReport:
    report_id: str
    timestamp: Optional[datetime]
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
    ground_truth: str
    department: str
    permit_impact: str
    status: str
    last_updated: Optional[datetime]
