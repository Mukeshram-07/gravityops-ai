import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from db.session import Base

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    criticality = Column(String, nullable=False)  # tier-1 (critical), tier-2 (important), tier-3 (normal)
    sla_minutes = Column(Integer, nullable=False)   # SLA resolution time budget in minutes

    incidents = relationship("Incident", back_populates="service")

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    status = Column(String, default="open", nullable=False)  # open, investigating, mitigated, resolved
    severity = Column(String, default="medium", nullable=False)  # low, medium, high, critical
    sla_risk = Column(String, default="healthy", nullable=False)  # healthy, watch, at-risk, breach-likely
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    sla_deadline = Column(DateTime, nullable=False)

    predicted_severity = Column(String, nullable=True)
    predicted_root_cause = Column(String, nullable=True)

    # Relationships
    service = relationship("Service", back_populates="incidents")
    alerts = relationship("AlertEvent", back_populates="incident", cascade="all, delete-orphan")
    notes = relationship("IncidentNote", back_populates="incident", cascade="all, delete-orphan")
    timeline = relationship("IncidentTimelineEvent", back_populates="incident", cascade="all, delete-orphan")

class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    service_name = Column(String, nullable=False)
    message = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    host = Column(String, nullable=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True)
    raw_payload = Column(Text, nullable=True)

    # Relationships
    incident = relationship("Incident", back_populates="alerts")

class IncidentNote(Base):
    __tablename__ = "incident_notes"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    operator_name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    incident = relationship("Incident", back_populates="notes")

class IncidentTimelineEvent(Base):
    __tablename__ = "incident_timeline_events"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    event_type = Column(String, nullable=False)  # status_change, note_added, alert_grouped, severity_change, sla_escalation
    operator_name = Column(String, default="System", nullable=False)
    message = Column(Text, nullable=False)

    # Relationships
    incident = relationship("Incident", back_populates="timeline")

class UploadJob(Base):
    __tablename__ = "upload_jobs"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    status = Column(String, default="processing", nullable=False)  # processing, completed, failed
    alerts_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    error_message = Column(Text, nullable=True)
