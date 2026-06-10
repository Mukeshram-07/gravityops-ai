import csv
import json
import uuid
import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from db.session import engine, Base, get_db
from models.entities import Incident, AlertEvent, Service, IncidentNote, IncidentTimelineEvent, UploadJob
import schemas.models as schemas
import services.incident as incident_service
import services.analytics as analytics_service
from ml.classifier import intel_service
from services.sla_scorer import calculate_sla_risk

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="GravityOps AI Backend",
    description="Incident Triage & Root-Cause Analysis API",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STARTUP EVENT ---
@app.on_event("startup")
def startup_event():
    """
    On startup, train the ML classifier using all historical incident data in the DB.
    """
    db = next(get_db())
    try:
        incidents = db.query(Incident).all()
        training_data = []
        for inc in incidents:
            # Gather alert messages associated with the incident
            for alert in inc.alerts:
                if inc.severity and inc.predicted_root_cause:
                    training_data.append({
                        "message": alert.message,
                        "severity": inc.severity,
                        "root_cause": inc.predicted_root_cause
                    })
        if training_data:
            intel_service.train(training_data)
            print(f"ML Classifier trained successfully on startup with {len(training_data)} records.")
    except Exception as e:
        print(f"Failed to pre-train ML classifier: {e}")
    finally:
        db.close()


# --- HEALTH & METRICS ENDPOINTS ---
@app.get("/api/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    try:
        # Simple query to verify DB connection
        db.execute(Base.metadata.tables['services'].select().limit(1))
        return {"status": "healthy", "database": "connected", "timestamp": datetime.datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection degraded: {str(e)}")

@app.get("/api/metrics", response_class=PlainTextResponse, tags=["System"])
def prometheus_metrics(db: Session = Depends(get_db)):
    """
    Exposes Grafana-ready, Prometheus-formatted metrics endpoints.
    """
    now = datetime.datetime.utcnow()
    total_inc = db.query(Incident).count()
    active_inc = db.query(Incident).filter(Incident.status != "resolved").count()
    resolved_inc = db.query(Incident).filter(Incident.status == "resolved").count()
    
    # Calculate total alerts
    total_alerts = db.query(AlertEvent).count()
    
    # Calculate SLA breaches
    breached_count = 0
    all_inc = db.query(Incident).all()
    for inc in all_inc:
        if inc.status == "resolved":
            if inc.resolved_at and inc.resolved_at > inc.sla_deadline:
                breached_count += 1
        else:
            if now > inc.sla_deadline:
                breached_count += 1
                
    # Calculate MTTR
    resolved_list = db.query(Incident).filter(Incident.status == "resolved").all()
    total_res_time = sum(
        max(0.0, (inc.resolved_at - inc.created_at).total_seconds())
        for inc in resolved_list if inc.resolved_at
    )
    mttr_seconds = (total_res_time / len(resolved_list)) if resolved_list else 0.0

    lines = [
        "# HELP gravityops_incidents_total Total number of incidents created.",
        "# TYPE gravityops_incidents_total counter",
        f"gravityops_incidents_total {total_inc}",
        
        "# HELP gravityops_incidents_active_total Current active incidents.",
        "# TYPE gravityops_incidents_active_total gauge",
        f"gravityops_incidents_active_total {active_inc}",
        
        "# HELP gravityops_incidents_resolved_total Total resolved incidents.",
        "# TYPE gravityops_incidents_resolved_total counter",
        f"gravityops_incidents_resolved_total {resolved_inc}",
        
        "# HELP gravityops_alerts_total Total alert events ingested.",
        "# TYPE gravityops_alerts_total counter",
        f"gravityops_alerts_total {total_alerts}",
        
        "# HELP gravityops_incidents_sla_breached_total Total incidents that breached SLA thresholds.",
        "# TYPE gravityops_incidents_sla_breached_total counter",
        f"gravityops_incidents_sla_breached_total {breached_count}",
        
        "# HELP gravityops_incidents_mttr_seconds Mean Time To Resolution in seconds.",
        "# TYPE gravityops_incidents_mttr_seconds gauge",
        f"gravityops_incidents_mttr_seconds {round(mttr_seconds, 2)}"
    ]
    return "\n".join(lines) + "\n"


# --- INCIDENT ENDPOINTS ---
@app.get("/api/incidents", response_model=List[schemas.IncidentResponse], tags=["Incidents"])
def get_incidents(
    status: Optional[str] = Query(None, description="Filter by status (comma-separated, e.g. open,investigating)"),
    severity: Optional[str] = Query(None, description="Filter by severity (comma-separated)"),
    service: Optional[str] = Query(None, description="Filter by service name"),
    sla_risk: Optional[str] = Query(None, description="Filter by SLA risk class"),
    search: Optional[str] = Query(None, description="Fuzzy search across title, message, or service name"),
    db: Session = Depends(get_db)
):
    # Proactively check and update SLA risk scoring before serving query
    incident_service.refresh_all_sla_risks(db)
    
    query = db.query(Incident).join(Incident.service)
    
    if status:
        statuses = [s.strip().lower() for s in status.split(",")]
        query = query.filter(Incident.status.in_(statuses))
        
    if severity:
        severities = [sev.strip().lower() for sev in severity.split(",")]
        query = query.filter(Incident.severity.in_(severities))
        
    if service:
        query = query.filter(Service.name.ilike(f"%{service}%"))
        
    if sla_risk:
        risks = [r.strip().lower() for r in sla_risk.split(",")]
        query = query.filter(Incident.sla_risk.in_(risks))
        
    if search:
        query = query.filter(
            (Incident.title.ilike(f"%{search}%")) |
            (Service.name.ilike(f"%{search}%")) |
            (Incident.predicted_root_cause.ilike(f"%{search}%"))
        )
        
    # Order active incidents first, and sort by urgency (severity rank)
    incidents = query.all()
    
    severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    status_order = {"open": 4, "investigating": 3, "mitigated": 2, "resolved": 1}
    
    incidents.sort(
        key=lambda inc: (
            status_order.get(inc.status.lower(), 1),
            severity_order.get(inc.severity.lower(), 1)
        ),
        reverse=True
    )
    
    return incidents

@app.get("/api/incidents/{incident_id}", response_model=schemas.IncidentDetailResponse, tags=["Incidents"])
def get_incident_detail(incident_id: int, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident record not found")
    return incident

@app.patch("/api/incidents/{incident_id}", response_model=schemas.IncidentResponse, tags=["Incidents"])
def patch_incident(
    incident_id: int, 
    update_data: schemas.IncidentUpdate, 
    operator_name: str = Query("Operator", alias="operator"),
    db: Session = Depends(get_db)
):
    try:
        updated = incident_service.update_incident_status(
            db=db,
            incident_id=incident_id,
            status=update_data.status,
            severity=update_data.severity,
            sla_risk=update_data.sla_risk,
            operator_name=operator_name
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/incidents/{incident_id}/notes", response_model=schemas.IncidentNoteResponse, tags=["Incidents"])
def add_incident_note(
    incident_id: int, 
    note_data: schemas.IncidentNoteCreate, 
    db: Session = Depends(get_db)
):
    try:
        note = incident_service.add_note_to_incident(
            db=db,
            incident_id=incident_id,
            operator_name=note_data.operator_name,
            content=note_data.content
        )
        return note
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- ANALYTICS ENDPOINTS ---
@app.get("/api/analytics/overview", response_model=schemas.AnalyticsOverviewResponse, tags=["Analytics"])
def get_analytics(db: Session = Depends(get_db)):
    return analytics_service.get_analytics_overview(db)


# --- INGESTION / UPLOAD PIPELINE ---
def process_alerts_background(job_id: str, file_content: bytes, file_name: str):
    """
    Background worker function to ingest alerts asynchronously from uploaded CSV/JSON.
    """
    db = next(get_db())
    job = db.query(UploadJob).filter(UploadJob.id == job_id).first()
    
    try:
        alerts_to_ingest = []
        
        # 1. Parse content based on file type
        if file_name.endswith('.json'):
            raw_data = json.loads(file_content.decode('utf-8'))
            if not isinstance(raw_data, list):
                raw_data = [raw_data]
            
            for index, item in enumerate(raw_data):
                alerts_to_ingest.append(
                    schemas.AlertEventCreate(
                        timestamp=datetime.datetime.fromisoformat(item.get("timestamp", datetime.datetime.utcnow().isoformat()).replace("Z", "+00:00")),
                        service_name=item.get("service_name", "unknown-service"),
                        message=item.get("message", "No description provided"),
                        severity=item.get("severity", "medium").lower(),
                        host=item.get("host", "unknown-host"),
                        raw_payload=json.dumps(item)
                    )
                )
        elif file_name.endswith('.csv'):
            decoded = file_content.decode('utf-8').splitlines()
            reader = csv.DictReader(decoded)
            for row in reader:
                ts_str = row.get("timestamp")
                if ts_str:
                    try:
                        timestamp = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    except Exception:
                        timestamp = datetime.datetime.utcnow()
                else:
                    timestamp = datetime.datetime.utcnow()
                
                alerts_to_ingest.append(
                    schemas.AlertEventCreate(
                        timestamp=timestamp,
                        service_name=row.get("service_name", "unknown-service"),
                        message=row.get("message", "No description provided"),
                        severity=row.get("severity", "medium").lower(),
                        host=row.get("host", "unknown-host"),
                        raw_payload=json.dumps(row)
                    )
                )
        else:
            raise ValueError("Unsupported file format. Please upload CSV or JSON.")

        # 2. Ingest alerts one by one through the service pipeline
        alerts_count = 0
        training_records = []
        for alert_data in alerts_to_ingest:
            alert = incident_service.ingest_alert(db, alert_data)
            alerts_count += 1
            
            # Save historical values for ML training feedback loop
            if alert.incident_id:
                inc = db.query(Incident).filter(Incident.id == alert.incident_id).first()
                if inc and inc.predicted_root_cause:
                    training_records.append({
                        "message": alert.message,
                        "severity": inc.severity,
                        "root_cause": inc.predicted_root_cause
                    })

        # 3. Trigger classifier re-train dynamically to update ML with newly ingested alert patterns
        if training_records:
            intel_service.train(training_records)

        # 4. Mark job as complete
        job.status = "completed"
        job.alerts_count = alerts_count
        db.commit()
        
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
    finally:
        db.close()

@app.post("/api/incidents/upload", response_model=schemas.UploadJobResponse, tags=["Ingestion"])
def upload_alerts(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Receives alerts CSV/JSON file, registers a background task to process it, and returns immediately.
    """
    job_id = str(uuid.uuid4())
    filename = file.filename or "uploaded_alerts"
    
    # Save a record of the upload job
    job = UploadJob(
        id=job_id,
        filename=filename,
        status="processing",
        created_at=datetime.datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    try:
        content = file.file.read()
        background_tasks.add_task(process_alerts_background, job_id, content, filename)
    except Exception as e:
        job.status = "failed"
        job.error_message = f"In-memory read error: {str(e)}"
        db.commit()
        db.refresh(job)
        raise HTTPException(status_code=500, detail="Failed to initialize file reader")
        
    return job

@app.get("/api/uploads/{job_id}", response_model=schemas.UploadJobResponse, tags=["Ingestion"])
def get_upload_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(UploadJob).filter(UploadJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Upload job not found")
    return job

from fastapi import Response

@app.get("/api/ml/diagnostics", tags=["System"])
def get_ml_diagnostics():
    mode = "trained" if (intel_service.severity_trained and intel_service.rc_trained) else "heuristic"
    return {
        "mode": mode,
        "training_sample_count": intel_service.training_sample_count
    }

@app.get("/api/demo/template", tags=["Ingestion"])
def get_demo_template():
    csv_content = "timestamp,service_name,message,severity,host\n"
    csv_content += "2026-06-10T12:00:00Z,payment-service,Database lock wait timeout exceeded,high,srv-pod-01\n"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=gravityops_alerts_template.csv"}
    )

@app.get("/api/demo/sample-outage", tags=["Ingestion"])
def get_demo_sample_outage():
    now_str = datetime.datetime.utcnow().isoformat() + "Z"
    csv_content = "timestamp,service_name,message,severity,host\n"
    csv_content += f"{now_str},auth-service,Repeated auth token refresh failures: invalid secret,high,srv-pod-99\n"
    csv_content += f"{now_str},auth-service,Auth credential decryption failure on keystore-prod-1,high,srv-pod-99\n"
    csv_content += f"{now_str},payment-service,HTTP 504 Gateway Timeout on POST /v1/charges,critical,srv-pod-12\n"
    csv_content += f"{now_str},payment-service,Database connection pool exhausted for payment-db,critical,srv-pod-12\n"
    csv_content += f"{now_str},payment-service,Transaction dispatch delayed for customer orders,critical,srv-pod-12\n"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=gravityops_sample_outage.csv"}
    )
