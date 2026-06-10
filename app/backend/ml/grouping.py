import re
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from models.entities import Incident, AlertEvent
from datetime import datetime, timedelta

def get_tokens(text: str) -> set:
    """
    Cleans text, lowercases, and splits it into a set of alphanumeric tokens.
    """
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
    return set(cleaned.split())

def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """
    Computes Jaccard Similarity between two text messages.
    """
    tokens1 = get_tokens(text1)
    tokens2 = get_tokens(text2)
    
    if not tokens1 or not tokens2:
        return 0.0
        
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    
    return len(intersection) / len(union)

def find_duplicate_incident(
    db: Session,
    service_name: str,
    alert_message: str,
    alert_timestamp: datetime,
    time_window_minutes: int = 30,
    similarity_threshold: float = 0.4
) -> Optional[Incident]:
    """
    Queries database for active incidents belonging to the same service.
    Compares the incoming alert_message with the title or existing alerts of active incidents.
    Returns the incident if it falls within the time window and matches the similarity threshold.
    """
    # Define active statuses
    active_statuses = ["open", "investigating", "mitigated"]
    
    # Calculate time boundary (window minutes before the alert timestamp)
    boundary_time = alert_timestamp - timedelta(minutes=time_window_minutes)
    
    # Query incidents matching the service, status, and timeline window
    incidents = (
        db.query(Incident)
        .join(Incident.service)
        .filter(
            Incident.status.in_(active_statuses),
            Incident.created_at >= boundary_time
        )
        .all()
    )
    
    # Filter by service name
    service_incidents = [inc for inc in incidents if inc.service.name == service_name]
    
    best_incident = None
    best_score = 0.0
    
    for incident in service_incidents:
        # Check similarity against the incident's title
        title_score = calculate_jaccard_similarity(alert_message, incident.title)
        
        # Check similarity against individual alert messages in this incident
        alert_scores = [
            calculate_jaccard_similarity(alert_message, past_alert.message)
            for past_alert in incident.alerts
        ]
        
        max_alert_score = max(alert_scores) if alert_scores else 0.0
        max_score = max(title_score, max_alert_score)
        
        if max_score >= similarity_threshold and max_score > best_score:
            best_score = max_score
            best_incident = incident
            
    return best_incident
