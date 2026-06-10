import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from models.entities import Incident, AlertEvent, Service
from schemas.models import (
    AnalyticsOverviewResponse, SeverityMix, StatusMix, SlaRiskMix,
    ServiceNoisyMetric, DailyOutageTrend
)
from collections import defaultdict

def get_analytics_overview(db: Session) -> AnalyticsOverviewResponse:
    """
    Computes aggregated analytics, MTTR, SLA compliance, service rankings, and timeline charts.
    """
    now = datetime.datetime.utcnow()
    
    # Basic metrics
    total_incidents = db.query(Incident).count()
    active_incidents = db.query(Incident).filter(Incident.status != "resolved").count()
    resolved_incidents = db.query(Incident).filter(Incident.status == "resolved").count()
    
    # Calculate MTTR (Mean Time to Resolution)
    resolved_incidents_list = db.query(Incident).filter(Incident.status == "resolved").all()
    total_resolution_time_minutes = 0.0
    for inc in resolved_incidents_list:
        if inc.resolved_at:
            delta = (inc.resolved_at - inc.created_at).total_seconds() / 60.0
            total_resolution_time_minutes += max(0.0, delta)
            
    mttr = 0.0
    if len(resolved_incidents_list) > 0:
        mttr = total_resolution_time_minutes / len(resolved_incidents_list)
        
    # Calculate SLA Breach Rate
    # A breach is when an incident resolved after deadline, or is active and current time is past deadline
    breached_count = 0
    all_incidents = db.query(Incident).all()
    for inc in all_incidents:
        if inc.status == "resolved":
            if inc.resolved_at and inc.resolved_at > inc.sla_deadline:
                breached_count += 1
        else:
            if now > inc.sla_deadline:
                breached_count += 1
                
    sla_breach_rate = 0.0
    if total_incidents > 0:
        sla_breach_rate = (breached_count / total_incidents) * 100.0
        
    # Severity Mix
    severity_mix = SeverityMix(
        low=db.query(Incident).filter(Incident.severity == "low").count(),
        medium=db.query(Incident).filter(Incident.severity == "medium").count(),
        high=db.query(Incident).filter(Incident.severity == "high").count(),
        critical=db.query(Incident).filter(Incident.severity == "critical").count()
    )
    
    # Status Mix
    status_mix = StatusMix(
        open=db.query(Incident).filter(Incident.status == "open").count(),
        investigating=db.query(Incident).filter(Incident.status == "investigating").count(),
        mitigated=db.query(Incident).filter(Incident.status == "mitigated").count(),
        resolved=db.query(Incident).filter(Incident.status == "resolved").count()
    )
    
    # SLA Risk Mix
    sla_risk_mix = SlaRiskMix(
        healthy=db.query(Incident).filter(Incident.sla_risk == "healthy").count(),
        watch=db.query(Incident).filter(Incident.sla_risk == "watch").count(),
        at_risk=db.query(Incident).filter(Incident.sla_risk == "at-risk").count(),
        breach_likely=db.query(Incident).filter(Incident.sla_risk == "breach-likely").count()
    )
    
    # Noisy Services
    # Query services, list total alerts, total incidents, and service MTTR
    services = db.query(Service).all()
    noisy_services = []
    
    for srv in services:
        # Alerts count
        alert_count = db.query(AlertEvent).filter(AlertEvent.service_name == srv.name).count()
        # Incident count
        incident_count = db.query(Incident).filter(Incident.service_id == srv.id).count()
        
        # Service MTTR
        srv_resolved = db.query(Incident).filter(Incident.service_id == srv.id, Incident.status == "resolved").all()
        srv_res_time = 0.0
        for inc in srv_resolved:
            if inc.resolved_at:
                srv_res_time += max(0.0, (inc.resolved_at - inc.created_at).total_seconds() / 60.0)
                
        srv_mttr = 0.0
        if len(srv_resolved) > 0:
            srv_mttr = srv_res_time / len(srv_resolved)
            
        noisy_services.append(
            ServiceNoisyMetric(
                service_name=srv.name,
                alert_count=alert_count,
                incident_count=incident_count,
                mttr_minutes=round(srv_mttr, 1)
            )
        )
        
    # Sort noisy services by alert count descending
    noisy_services.sort(key=lambda x: x.alert_count, reverse=True)
    
    # Daily Outage Trends (Last 10 days)
    daily_trend_map = defaultdict(int)
    for i in range(10):
        date_str = (now - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        daily_trend_map[date_str] = 0
        
    # Fill actual values
    all_incidents_chronological = db.query(Incident).filter(Incident.created_at >= now - datetime.timedelta(days=10)).all()
    for inc in all_incidents_chronological:
        date_str = inc.created_at.strftime("%Y-%m-%d")
        if date_str in daily_trend_map:
            daily_trend_map[date_str] += 1
            
    # Convert map to sorted list
    daily_trends = [
        DailyOutageTrend(date=dt, count=cnt)
        for dt, cnt in sorted(daily_trend_map.items())
    ]
    
    return AnalyticsOverviewResponse(
        total_incidents=total_incidents,
        active_incidents=active_incidents,
        resolved_incidents=resolved_incidents,
        mttr_minutes=round(mttr, 1),
        sla_breach_rate=round(sla_breach_rate, 1),
        severity_mix=severity_mix,
        status_mix=status_mix,
        sla_risk_mix=sla_risk_mix,
        noisy_services=noisy_services[:5],  # top 5 noisy services
        daily_trends=daily_trends
    )
