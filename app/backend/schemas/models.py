from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- SERVICE SCHEMAS ---
class ServiceBase(BaseModel):
    name: str
    criticality: str
    sla_minutes: int

class ServiceCreate(ServiceBase):
    pass

class ServiceResponse(ServiceBase):
    id: int

    class Config:
        from_attributes = True

# --- ALERT SCHEMAS ---
class AlertEventBase(BaseModel):
    timestamp: datetime
    service_name: str
    message: str
    severity: str
    host: Optional[str] = None
    raw_payload: Optional[str] = None

class AlertEventCreate(AlertEventBase):
    pass

class AlertEventResponse(AlertEventBase):
    id: int
    incident_id: Optional[int] = None

    class Config:
        from_attributes = True

# --- NOTE SCHEMAS ---
class IncidentNoteBase(BaseModel):
    operator_name: str
    content: str

class IncidentNoteCreate(IncidentNoteBase):
    pass

class IncidentNoteResponse(IncidentNoteBase):
    id: int
    incident_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- TIMELINE SCHEMAS ---
class IncidentTimelineEventResponse(BaseModel):
    id: int
    incident_id: int
    timestamp: datetime
    event_type: str
    operator_name: str
    message: str

    class Config:
        from_attributes = True

# --- INCIDENT SCHEMAS ---
class IncidentBase(BaseModel):
    title: str
    status: str
    severity: str
    sla_risk: str
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    sla_deadline: datetime
    predicted_severity: Optional[str] = None
    predicted_root_cause: Optional[str] = None

class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None
    sla_risk: Optional[str] = None

class IncidentResponse(IncidentBase):
    id: int
    service: ServiceResponse

    class Config:
        from_attributes = True

class IncidentDetailResponse(IncidentResponse):
    alerts: List[AlertEventResponse] = []
    notes: List[IncidentNoteResponse] = []
    timeline: List[IncidentTimelineEventResponse] = []

    class Config:
        from_attributes = True

# --- UPLOAD JOB SCHEMAS ---
class UploadJobResponse(BaseModel):
    id: str
    filename: str
    status: str
    alerts_count: int
    created_at: datetime
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

# --- ANALYTICS SCHEMAS ---
class SeverityMix(BaseModel):
    low: int = 0
    medium: int = 0
    high: int = 0
    critical: int = 0

class StatusMix(BaseModel):
    open: int = 0
    investigating: int = 0
    mitigated: int = 0
    resolved: int = 0

class SlaRiskMix(BaseModel):
    healthy: int = 0
    watch: int = 0
    at_risk: int = 0
    breach_likely: int = 0

class ServiceNoisyMetric(BaseModel):
    service_name: str
    alert_count: int
    incident_count: int
    mttr_minutes: float

class DailyOutageTrend(BaseModel):
    date: str
    count: int

class AnalyticsOverviewResponse(BaseModel):
    total_incidents: int
    active_incidents: int
    resolved_incidents: int
    mttr_minutes: float
    sla_breach_rate: float  # Percentage (e.g. 15.5)
    severity_mix: SeverityMix
    status_mix: StatusMix
    sla_risk_mix: SlaRiskMix
    noisy_services: List[ServiceNoisyMetric]
    daily_trends: List[DailyOutageTrend]
