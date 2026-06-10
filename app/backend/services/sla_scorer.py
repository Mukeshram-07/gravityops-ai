import datetime
from typing import Tuple

def calculate_sla_risk(
    created_at: datetime.datetime,
    sla_minutes: int,
    severity: str,
    status: str,
    current_time: datetime.datetime = None
) -> Tuple[float, str]:
    """
    Calculates the SLA risk score (0 to 100) and category (healthy, watch, at-risk, breach-likely).
    """
    if status == "resolved":
        return 0.0, "healthy"
        
    if current_time is None:
        current_time = datetime.datetime.utcnow()
        
    time_elapsed_seconds = (current_time - created_at).total_seconds()
    time_elapsed_minutes = max(0.0, time_elapsed_seconds / 60.0)
    
    if sla_minutes <= 0:
        sla_minutes = 60 # fallback safety
        
    pct_elapsed = (time_elapsed_minutes / sla_minutes) * 100.0
    
    # Capitalize severity for uniform matching
    sev = severity.lower()
    
    # Base calculation
    if pct_elapsed >= 100.0:
        return 100.0, "breach-likely"
        
    # Scale based on severity
    if sev == "critical":
        if pct_elapsed >= 75.0:
            score = 90.0 + (pct_elapsed - 75.0) * 0.4
            risk = "breach-likely"
        elif pct_elapsed >= 40.0:
            score = 60.0 + (pct_elapsed - 40.0) * 0.85
            risk = "at-risk"
        elif pct_elapsed >= 15.0:
            score = 30.0 + (pct_elapsed - 15.0) * 1.2
            risk = "watch"
        else:
            score = pct_elapsed * 2.0
            risk = "healthy"
            
    elif sev == "high":
        if pct_elapsed >= 85.0:
            score = 90.0 + (pct_elapsed - 85.0) * 0.67
            risk = "breach-likely"
        elif pct_elapsed >= 55.0:
            score = 60.0 + (pct_elapsed - 55.0) * 1.0
            risk = "at-risk"
        elif pct_elapsed >= 25.0:
            score = 30.0 + (pct_elapsed - 25.0) * 0.5
            risk = "watch"
        else:
            score = pct_elapsed * 1.2
            risk = "healthy"
            
    elif sev == "medium":
        if pct_elapsed >= 90.0:
            score = 90.0
            risk = "breach-likely"
        elif pct_elapsed >= 70.0:
            score = 60.0 + (pct_elapsed - 70.0) * 1.5
            risk = "at-risk"
        elif pct_elapsed >= 35.0:
            score = 30.0 + (pct_elapsed - 35.0) * 0.85
            risk = "watch"
        else:
            score = pct_elapsed
            risk = "healthy"
            
    else:  # low
        if pct_elapsed >= 95.0:
            score = 90.0
            risk = "breach-likely"
        elif pct_elapsed >= 80.0:
            score = 60.0
            risk = "at-risk"
        elif pct_elapsed >= 50.0:
            score = 30.0
            risk = "watch"
        else:
            score = pct_elapsed * 0.6
            risk = "healthy"
            
    # Cap score
    score = min(100.0, max(0.0, score))
    return round(score, 1), risk
