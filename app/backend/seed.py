import datetime
import random
from sqlalchemy.orm import Session
from db.session import SessionLocal, engine, Base
from models.entities import Service, Incident, AlertEvent, IncidentNote, IncidentTimelineEvent
from ml.classifier import intel_service
from services.sla_scorer import calculate_sla_risk

def seed_database():
    # Ensure tables are created before seeding
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # 1. Clean existing records to allow clean re-runs
    print("Clearing existing database tables...")
    db.query(IncidentTimelineEvent).delete()
    db.query(IncidentNote).delete()
    db.query(AlertEvent).delete()
    db.query(Incident).delete()
    db.query(Service).delete()
    db.commit()

    print("Seeding services...")
    services_data = [
        {"name": "payment-service", "criticality": "tier-1", "sla_minutes": 30},
        {"name": "auth-service", "criticality": "tier-1", "sla_minutes": 30},
        {"name": "order-service", "criticality": "tier-1", "sla_minutes": 30},
        {"name": "scheduler-worker", "criticality": "tier-2", "sla_minutes": 60},
        {"name": "notification-gateway", "criticality": "tier-2", "sla_minutes": 60},
        {"name": "reporting-engine", "criticality": "tier-3", "sla_minutes": 120},
        {"name": "inventory-sync", "criticality": "tier-3", "sla_minutes": 120},
        {"name": "customer-support-api", "criticality": "tier-3", "sla_minutes": 120}
    ]
    
    services_map = {}
    for s_data in services_data:
        srv = Service(
            name=s_data["name"],
            criticality=s_data["criticality"],
            sla_minutes=s_data["sla_minutes"]
        )
        db.add(srv)
        db.commit()
        db.refresh(srv)
        services_map[srv.name] = srv

    now = datetime.datetime.utcnow()
    
    # Define a library of pre-populated historical incidents
    # Format: (service, title_msg, severity, status, hours_ago, duration_hours, notes_list, alerts_list)
    incidents_seed_template = [
        # 1. Payment service latency spike (Resolved, SLA breached)
        (
            "payment-service",
            "Payment API latency spike in APAC region",
            "critical", "resolved", 72, 3.5,
            [
                ("SRE On-call", "Escalated after repeated retries crossed threshold."),
                ("Dev Lead", "Correlated with deploy 2026.06.08.3 on payment-service."),
                ("SRE On-call", "Temporary mitigation applied by database pool enlargement.")
            ],
            [
                "HTTP 504 Gateway Timeout on POST /v1/charges",
                "Database connection pool exhausted for payment-db",
                "Transaction dispatch delayed for customer orders"
            ]
        ),
        # 2. Auth service token refresh failures (Investigating, SLA breached)
        (
            "auth-service",
            "Repeated auth token refresh failures",
            "high", "investigating", 6, None,
            [
                ("Security Analyst", "Investigating expired certificate inside Kubernetes vault secrets."),
                ("SRE On-call", "Failed to renew trust token automatically. Attempting manual key generation.")
            ],
            [
                "Token refresh request rejected: Signature validation failed",
                "Auth credential decryption failure on keystore-prod-1"
            ]
        ),
        # 3. Order service 5xx burst after release (Open, Watch)
        (
            "order-service",
            "Order-service 5xx burst after release",
            "critical", "open", 0.2, None,
            [],
            [
                "Internal Server Error on POST /orders (NullPointerException in OrderValidationController:120)",
                "Error response spike on checkout endpoint - 502 Bad Gateway"
            ]
        ),
        # 4. Scheduler job timeout (Resolved, Healthy SLA)
        (
            "scheduler-worker",
            "Scheduler job timeout during nightly settlement",
            "medium", "resolved", 30, 0.75,
            [
                ("Platform Op", "Nightly settlement job failed to complete in under 20 mins. Force-killed."),
                ("Platform Op", "Settlement job re-run manually after partition optimization. Job completed successfully.")
            ],
            [
                "Job Execution Timeout: settlement-job-2026-06-09",
                "Task execution thread interrupted after 1200 seconds"
            ]
        ),
        # 5. Reporting engine memory spike (Mitigated, Watch)
        (
            "reporting-engine",
            "Reporting engine memory spike",
            "medium", "mitigated", 8, None,
            [
                ("Kubernetes watchdog", "Heap memory utilization reached 94% on replica reporting-api-78c"),
                ("Platform Op", "Temporary mitigation applied by scaling instances from 2 to 4 to relieve load.")
            ],
            [
                "JVM Garbage Collection duration exceeded limits",
                "OutOfMemoryError risk: Heap occupancy high"
            ]
        ),
        # 6. Inventory sync mismatch (Resolved, SLA breached)
        (
            "inventory-sync",
            "Inventory sync mismatch after upstream schema drift",
            "low", "resolved", 96, 6.0,
            [
                ("Catalog Engineer", "Upstream DB migration modified catalog fields without informing consumer."),
                ("Catalog Engineer", "Reparsed missing messages and patched consumer catalog parser mapping.")
            ],
            [
                "Payload parsing failed: key 'sku_id' is missing in event payload",
                "Skipping message payload sync due to validation errors"
            ]
        ),
        # 7. Customer Support Webhook failure (Investigating, Watch)
        (
            "customer-support-api",
            "Customer-support webhook signature validation failures",
            "low", "investigating", 1.5, None,
            [
                ("Tech Support Lead", "Zendesk webhook integrations started throwing security exceptions.")
            ],
            [
                "Invalid SHA256 signature on support webhook request",
                "Webhook request validation rejected for support-ticket-events"
            ]
        ),
        # 8. Notification Gateway queue backlog (Mitigated, Healthy SLA)
        (
            "notification-gateway",
            "Notification retry queue backlog",
            "high", "mitigated", 1.2, None,
            [
                ("SRE On-call", "AWS SES throttling notification emails due to daily sender limit."),
                ("Platform Manager", "Sourced alternative sendgrid route and switched gateway configs.")
            ],
            [
                "Notification queue latency exceeds 45s: 12,402 messages pending",
                "SMTP rate limiting error returned by remote host"
            ]
        ),
        # 9. Payment service gateway degradation (Resolved, Healthy)
        (
            "payment-service",
            "Payment Gateway response latency from Stripe",
            "high", "resolved", 48, 0.4,
            [
                ("SRE On-call", "Stripe API dashboard reported service outage in US-East."),
                ("SRE On-call", "Gateway auto-fallback redirected billing requests to PayPal secondary route.")
            ],
            [
                "Gateway timeout on call to stripe.com API endpoint",
                "Payment transaction latency spike: average 8400ms"
            ]
        ),
        # 10. Auth Database Lock Contention (Critical, Resolved)
        (
            "auth-service",
            "Authentication database transaction lock contention",
            "critical", "resolved", 120, 1.1,
            [
                ("DBA Team", "Deadlock identified on user-sessions tables due to lock escalation."),
                ("DBA Team", "Terminated blocking session ID 9445. Index re-build scheduled.")
            ],
            [
                "Lock wait timeout exceeded; try restarting transaction in auth-db",
                "Connection pool pool-auth exhausted under session lockups"
            ]
        )
    ]
    
    # Generate an extra 15 mock incidents to meet the 25 minimum requirement
    services_list = list(services_map.keys())
    severity_options = ["low", "medium", "high", "critical"]
    status_options = ["open", "investigating", "mitigated", "resolved"]
    root_cause_categories = [
        "deployment regression", "dependency timeout", "schema drift",
        "infrastructure saturation", "message queue backlog", "credential rotation issue",
        "cache invalidation bug", "third-party provider degradation"
    ]
    
    extra_templates = [
        ("Database query timeouts on {}", "high", "dependency timeout"),
        ("OutOfMemory exception on {} node", "critical", "infrastructure saturation"),
        ("CPU saturation on {} host", "medium", "infrastructure saturation"),
        ("API latency degradation in {}", "medium", "dependency timeout"),
        ("Retry count exceeded for {} events", "low", "message queue backlog"),
        ("Expired authorization certificate for {}", "high", "credential rotation issue"),
        ("Invalid response format from {}", "low", "schema drift"),
        ("Redis cache lookup failure in {}", "medium", "cache invalidation bug"),
        ("Failed to upload assets on {}", "low", "third-party provider degradation"),
        ("Upstream payload structure mismatch on {}", "medium", "schema drift"),
    ]
    
    # Populate predefined templates first
    all_seeded_records = []
    
    for t in incidents_seed_template:
        srv_name, title, sev, status, hrs_ago, dur_hrs, notes, alerts = t
        service = services_map[srv_name]
        
        created_at = now - datetime.timedelta(hours=hrs_ago)
        resolved_at = None
        if status == "resolved" and dur_hrs:
            resolved_at = created_at + datetime.timedelta(hours=dur_hrs)
            
        sla_deadline = created_at + datetime.timedelta(minutes=service.sla_minutes)
        
        # ML Predictions (we will simulate ML outputs here)
        pred_sev, pred_rc = intel_service.predict(srv_name, title)
        
        # Calculate real SLA risk state
        score, risk = calculate_sla_risk(
            created_at=created_at,
            sla_minutes=service.sla_minutes,
            severity=sev,
            status=status,
            current_time=resolved_at or now
        )
        
        inc = Incident(
            title=title,
            service_id=service.id,
            status=status,
            severity=sev,
            sla_risk=risk,
            created_at=created_at,
            updated_at=resolved_at or now,
            resolved_at=resolved_at,
            sla_deadline=sla_deadline,
            predicted_severity=pred_sev,
            predicted_root_cause=pred_rc
        )
        db.add(inc)
        db.commit()
        db.refresh(inc)
        
        # Store for ML training list later
        all_seeded_records.append(inc)
        
        # Seed Alerts
        for msg in alerts:
            alert = AlertEvent(
                timestamp=created_at + datetime.timedelta(minutes=random.randint(0, 5)),
                service_name=srv_name,
                message=msg,
                severity=sev,
                host=f"srv-pod-{random.randint(10, 99)}",
                incident_id=inc.id,
                raw_payload=f'{{"service": "{srv_name}", "error": "{msg}", "severity": "{sev}"}}'
            )
            db.add(alert)
            
        # Seed Notes
        for operator, note_txt in notes:
            note = IncidentNote(
                incident_id=inc.id,
                operator_name=operator,
                content=note_txt,
                created_at=created_at + datetime.timedelta(minutes=random.randint(10, 30))
            )
            db.add(note)
            
        # Seed Timeline events
        t1 = IncidentTimelineEvent(
            incident_id=inc.id,
            timestamp=created_at,
            event_type="status_change",
            operator_name="System",
            message=f"Incident generated automatically from alert. Initial status set to {status.upper()}."
        )
        db.add(t1)
        
        t2 = IncidentTimelineEvent(
            incident_id=inc.id,
            timestamp=created_at + datetime.timedelta(seconds=15),
            event_type="severity_change",
            operator_name="ML Engine",
            message=f"ML predicted severity: {pred_sev.upper()} (Root Cause: {pred_rc.upper()}). Assigned severity: {sev.upper()}."
        )
        db.add(t2)
        
        for index, (operator, note_txt) in enumerate(notes):
            n_time = created_at + datetime.timedelta(minutes=15 + index * 5)
            t_note = IncidentTimelineEvent(
                incident_id=inc.id,
                timestamp=n_time,
                event_type="note_added",
                operator_name=operator,
                message=f"Operator note added: \"{note_txt[:40]}...\""
            )
            db.add(t_note)
            
        if status == "resolved" and resolved_at:
            t_res = IncidentTimelineEvent(
                incident_id=inc.id,
                timestamp=resolved_at,
                event_type="status_change",
                operator_name="SRE On-call",
                message="Incident status updated to RESOLVED. Outage mitigated."
            )
            db.add(t_res)

        db.commit()

    # Generate additional 15 random historical incidents
    for idx in range(16):
        srv_name = random.choice(services_list)
        service = services_map[srv_name]
        
        template_text, sev, rc = random.choice(extra_templates)
        title = template_text.format(srv_name)
        status = random.choice(status_options)
        
        hrs_ago = random.randint(5, 120)
        created_at = now - datetime.timedelta(hours=hrs_ago)
        resolved_at = None
        if status == "resolved":
            resolved_at = created_at + datetime.timedelta(minutes=random.randint(15, 180))
            
        sla_deadline = created_at + datetime.timedelta(minutes=service.sla_minutes)
        
        # Predictions
        pred_sev, pred_rc = intel_service.predict(srv_name, title)
        
        score, risk = calculate_sla_risk(
            created_at=created_at,
            sla_minutes=service.sla_minutes,
            severity=sev,
            status=status,
            current_time=resolved_at or now
        )
        
        inc = Incident(
            title=title,
            service_id=service.id,
            status=status,
            severity=sev,
            sla_risk=risk,
            created_at=created_at,
            updated_at=resolved_at or now,
            resolved_at=resolved_at,
            sla_deadline=sla_deadline,
            predicted_severity=pred_sev,
            predicted_root_cause=rc
        )
        db.add(inc)
        db.commit()
        db.refresh(inc)
        
        # Add a couple of alerts
        alert_msg1 = f"Error threshold exceeded: {title}"
        alert1 = AlertEvent(
            timestamp=created_at,
            service_name=srv_name,
            message=alert_msg1,
            severity=sev,
            host=f"srv-pod-{random.randint(10, 99)}",
            incident_id=inc.id,
            raw_payload=f'{{"service": "{srv_name}", "error": "{alert_msg1}"}}'
        )
        db.add(alert1)
        
        if random.random() > 0.4:
            alert_msg2 = f"Duplicate event spike detected on {srv_name}"
            alert2 = AlertEvent(
                timestamp=created_at + datetime.timedelta(minutes=random.randint(2, 8)),
                service_name=srv_name,
                message=alert_msg2,
                severity=sev,
                host=f"srv-pod-{random.randint(10, 99)}",
                incident_id=inc.id,
                raw_payload=f'{{"service": "{srv_name}", "error": "{alert_msg2}"}}'
            )
            db.add(alert2)

        # Timeline
        t1 = IncidentTimelineEvent(
            incident_id=inc.id,
            timestamp=created_at,
            event_type="status_change",
            operator_name="System",
            message=f"Incident auto-generated from monitoring alert logs. Severity: {sev.upper()}."
        )
        db.add(t1)
        
        if status == "resolved":
            t2 = IncidentTimelineEvent(
                incident_id=inc.id,
                timestamp=resolved_at,
                event_type="status_change",
                operator_name="Auto-Healer",
                message=f"System checks returned to normal. Status set to RESOLVED."
            )
            db.add(t2)
            
        db.commit()

    print("Pre-training ML Classifier on all seeded incidents...")
    training_data = []
    for inc in db.query(Incident).all():
        for alert in inc.alerts:
            training_data.append({
                "message": alert.message,
                "severity": inc.severity,
                "root_cause": inc.predicted_root_cause or "dependency timeout"
            })
    
    if training_data:
        intel_service.train(training_data)
        print("ML Classifier successfully trained during seeding.")

    print(f"Successfully seeded database with {db.query(Service).count()} services, {db.query(Incident).count()} incidents, and {db.query(AlertEvent).count()} alerts.")
    db.close()

if __name__ == "__main__":
    seed_database()
