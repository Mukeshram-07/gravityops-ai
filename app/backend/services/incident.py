import datetime
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from models.entities import Service, Incident, AlertEvent, IncidentNote, IncidentTimelineEvent
from schemas.models import AlertEventCreate
from ml.grouping import find_duplicate_incident
from ml.classifier import intel_service
from services.sla_scorer import calculate_sla_risk

def get_or_create_service(db: Session, name: str) -> Service:
    """
    Retrieves a service by name, or creates a default one if it doesn't exist.
    """
    service = db.query(Service).filter(Service.name == name).first()
    if not service:
        # Assign defaults based on typical service importance
        criticality = "tier-2"
        sla_minutes = 60
        if "auth" in name or "payment" in name or "order" in name:
            criticality = "tier-1"
            sla_minutes = 30
        elif "report" in name or "sync" in name or "support" in name:
            criticality = "tier-3"
            sla_minutes = 120
            
        service = Service(name=name, criticality=criticality, sla_minutes=sla_minutes)
        db.add(service)
        db.commit()
        db.refresh(service)
    return service

def ingest_alert(db: Session, alert_data: AlertEventCreate) -> AlertEvent:
    """
    Ingests an alert event, groups it under an existing active incident if it is a duplicate,
    otherwise creates a new incident and uses ML classification to predict severity/root cause.
    """
    service = get_or_create_service(db, alert_data.service_name)
    
    # Check if this alert matches any active incident (duplicate grouping)
    existing_incident = find_duplicate_incident(
        db=db,
        service_name=alert_data.service_name,
        alert_message=alert_data.message,
        alert_timestamp=alert_data.timestamp
    )
    
    if existing_incident:
        # Group alert under existing incident
        alert = AlertEvent(
            timestamp=alert_data.timestamp,
            service_name=alert_data.service_name,
            message=alert_data.message,
            severity=alert_data.severity,
            host=alert_data.host,
            raw_payload=alert_data.raw_payload,
            incident_id=existing_incident.id
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        # Add timeline audit event
        timeline_msg = f"Alert grouped under incident: [{alert.severity.upper()}] {alert.message} (Host: {alert.host or 'N/A'})"
        timeline_event = IncidentTimelineEvent(
            incident_id=existing_incident.id,
            timestamp=datetime.datetime.utcnow(),
            event_type="alert_grouped",
            operator_name="System Engine",
            message=timeline_msg
        )
        db.add(timeline_event)
        
        # Update incident severity if the incoming alert is higher
        severities_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        current_sev_rank = severities_order.get(existing_incident.severity.lower(), 2)
        alert_sev_rank = severities_order.get(alert.severity.lower(), 2)
        
        if alert_sev_rank > current_sev_rank:
            old_sev = existing_incident.severity
            existing_incident.severity = alert.severity
            severity_escalation_event = IncidentTimelineEvent(
                incident_id=existing_incident.id,
                timestamp=datetime.datetime.utcnow(),
                event_type="severity_change",
                operator_name="System Engine",
                message=f"Incident severity auto-escalated from {old_sev} to {alert.severity} due to incoming high-severity alert."
            )
            db.add(severity_escalation_event)
            
        # Recalculate SLA Risk
        score, risk = calculate_sla_risk(
            created_at=existing_incident.created_at,
            sla_minutes=service.sla_minutes,
            severity=existing_incident.severity,
            status=existing_incident.status
        )
        existing_incident.sla_risk = risk
        existing_incident.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(alert)
        return alert
        
    else:
        # Create a new incident
        # ML-assisted severity and root cause prediction
        pred_severity, pred_rc = intel_service.predict(alert_data.service_name, alert_data.message)
        
        # Base severity is the higher of ML prediction and the raw alert severity
        severities_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        raw_sev_rank = severities_order.get(alert_data.severity.lower(), 2)
        pred_sev_rank = severities_order.get(pred_severity.lower(), 2)
        final_severity = alert_data.severity if raw_sev_rank >= pred_sev_rank else pred_severity
        
        sla_deadline = alert_data.timestamp + datetime.timedelta(minutes=service.sla_minutes)
        
        # Initial SLA Risk
        score, risk = calculate_sla_risk(
            created_at=alert_data.timestamp,
            sla_minutes=service.sla_minutes,
            severity=final_severity,
            status="open",
            current_time=alert_data.timestamp
        )
        
        incident = Incident(
            title=f"{alert_data.service_name} operational failure: {alert_data.message[:60]}...",
            service_id=service.id,
            status="open",
            severity=final_severity,
            sla_risk=risk,
            created_at=alert_data.timestamp,
            updated_at=alert_data.timestamp,
            sla_deadline=sla_deadline,
            predicted_severity=pred_severity,
            predicted_root_cause=pred_rc
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        
        # Save alert linked to new incident
        alert = AlertEvent(
            timestamp=alert_data.timestamp,
            service_name=alert_data.service_name,
            message=alert_data.message,
            severity=alert_data.severity,
            host=alert_data.host,
            raw_payload=alert_data.raw_payload,
            incident_id=incident.id
        )
        db.add(alert)
        
        # Timeline audit events
        t1 = IncidentTimelineEvent(
            incident_id=incident.id,
            timestamp=alert_data.timestamp,
            event_type="status_change",
            operator_name="System Engine",
            message=f"Incident generated automatically from alert. Initial status set to OPEN."
        )
        t2 = IncidentTimelineEvent(
            incident_id=incident.id,
            timestamp=alert_data.timestamp,
            event_type="severity_change",
            operator_name="ML Engine",
            message=f"ML predicted severity: {pred_severity.upper()} (Root Cause: {pred_rc.upper()}). Assigned operational severity: {final_severity.upper()}."
        )
        db.add(t1)
        db.add(t2)
        
        db.commit()
        db.refresh(alert)
        return alert

def add_note_to_incident(db: Session, incident_id: int, operator_name: str, content: str) -> IncidentNote:
    """
    Appends an operator note to an incident and log a timeline event.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise ValueError("Incident not found")
        
    note = IncidentNote(
        incident_id=incident_id,
        operator_name=operator_name,
        content=content,
        created_at=datetime.datetime.utcnow()
    )
    db.add(note)
    
    # Audit log timeline event
    snippet = content[:60] + "..." if len(content) > 60 else content
    timeline_event = IncidentTimelineEvent(
        incident_id=incident_id,
        timestamp=datetime.datetime.utcnow(),
        event_type="note_added",
        operator_name=operator_name,
        message=f"Operator note appended: \"{snippet}\""
    )
    db.add(timeline_event)
    
    incident.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(note)
    return note

def update_incident_status(
    db: Session,
    incident_id: int,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    sla_risk: Optional[str] = None,
    operator_name: str = "Operator"
) -> Incident:
    """
    Updates incident status, severity, or manual SLA risk overrides, logging transitions on the timeline.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise ValueError("Incident not found")
        
    now = datetime.datetime.utcnow()
    
    if status and status != incident.status:
        old_status = incident.status
        incident.status = status
        
        # If status changes to resolved, set resolved_at
        if status == "resolved":
            incident.resolved_at = now
            incident.sla_risk = "healthy"
            
        # Log status transition
        t_event = IncidentTimelineEvent(
            incident_id=incident_id,
            timestamp=now,
            event_type="status_change",
            operator_name=operator_name,
            message=f"Status transitioned from {old_status.upper()} to {status.upper()}."
        )
        db.add(t_event)
        
    if severity and severity != incident.severity:
        old_severity = incident.severity
        incident.severity = severity
        
        # Log severity transition
        t_event = IncidentTimelineEvent(
            incident_id=incident_id,
            timestamp=now,
            event_type="severity_change",
            operator_name=operator_name,
            message=f"Incident severity modified from {old_severity.upper()} to {severity.upper()}."
        )
        db.add(t_event)

    if sla_risk and sla_risk != incident.sla_risk:
        old_risk = incident.sla_risk
        incident.sla_risk = sla_risk
        
        t_event = IncidentTimelineEvent(
            incident_id=incident_id,
            timestamp=now,
            event_type="sla_escalation",
            operator_name=operator_name,
            message=f"SLA risk status override from {old_risk.upper()} to {sla_risk.upper()}."
        )
        db.add(t_event)
        
    incident.updated_at = now
    db.commit()
    db.refresh(incident)
    return incident

def refresh_all_sla_risks(db: Session):
    """
    Iterates over active incidents and updates their SLA risk scores/categories based on elapsed time.
    """
    active_incidents = (
        db.query(Incident)
        .filter(Incident.status != "resolved")
        .all()
    )
    
    now = datetime.datetime.utcnow()
    for incident in active_incidents:
        score, new_risk = calculate_sla_risk(
            created_at=incident.created_at,
            sla_minutes=incident.service.sla_minutes,
            severity=incident.severity,
            status=incident.status,
            current_time=now
        )
        
        if new_risk != incident.sla_risk:
            old_risk = incident.sla_risk
            incident.sla_risk = new_risk
            
            # Log SLA status change on timeline
            t_event = IncidentTimelineEvent(
                incident_id=incident.id,
                timestamp=now,
                event_type="sla_escalation",
                operator_name="System SLA Watchdog",
                message=f"SLA breach risk level updated from {old_risk.upper()} to {new_risk.upper()} (score: {score}/100)."
            )
            db.add(t_event)
            
    db.commit()
