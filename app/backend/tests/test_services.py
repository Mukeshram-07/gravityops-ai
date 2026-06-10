import datetime
import pytest
from fastapi.testclient import TestClient

from main import app
from db.session import Base, engine, SessionLocal
from services.sla_scorer import calculate_sla_risk
from ml.grouping import calculate_jaccard_similarity, get_tokens
from ml.classifier import IncidentIntelligenceService

# --- CLIENT FIXTURE ---
@pytest.fixture
def client():
    # Make sure database is initialized for the test suite
    Base.metadata.create_all(bind=engine)
    return TestClient(app)

# --- 1. SLA RISK SCORING TESTS ---
def test_sla_risk_scorer_resolved():
    score, risk = calculate_sla_risk(
        created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=2),
        sla_minutes=30,
        severity="critical",
        status="resolved"
    )
    assert score == 0.0
    assert risk == "healthy"

def test_sla_risk_scorer_critical_breach():
    created_at = datetime.datetime.utcnow() - datetime.timedelta(minutes=45)
    score, risk = calculate_sla_risk(
        created_at=created_at,
        sla_minutes=30,
        severity="critical",
        status="open"
    )
    assert score == 100.0
    assert risk == "breach-likely"

def test_sla_risk_scorer_critical_watch():
    created_at = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
    score, risk = calculate_sla_risk(
        created_at=created_at,
        sla_minutes=30,
        severity="critical",
        status="open"
    )
    # 5/30 = 16.6% elapsed -> watch state (since >= 15% and < 40%)
    assert risk == "watch"
    assert 30.0 < score < 60.0

# --- 2. JACCARD SIMILARITY & TOKENS TESTS ---
def test_get_tokens():
    tokens = get_tokens("Auth: token refresh failure!")
    assert "auth" in tokens
    assert "token" in tokens
    assert "refresh" in tokens
    assert "failure" in tokens
    assert len(tokens) == 4

def test_jaccard_similarity_exact():
    sim = calculate_jaccard_similarity("payment gateway latency spike", "payment gateway latency spike")
    assert sim == 1.0

def test_jaccard_similarity_partial():
    sim = calculate_jaccard_similarity("payment gateway latency spike", "database gateway pool latency spike")
    # Tokens 1: {payment, gateway, latency, spike} - 4 tokens
    # Tokens 2: {database, gateway, pool, latency, spike} - 5 tokens
    # Intersection: {gateway, latency, spike} - 3 tokens
    # Union: {payment, gateway, latency, spike, database, pool} - 6 tokens
    # Jaccard = 3/6 = 0.5
    assert sim == 0.5

def test_jaccard_similarity_none():
    sim = calculate_jaccard_similarity("auth token expired", "database lock deadlock")
    assert sim == 0.0

# --- 3. ML CLASSIFIER COLD START / TRAINING TESTS ---
def test_ml_classifier_cold_start():
    service = IncidentIntelligenceService()
    assert not service.severity_trained
    assert not service.rc_trained
    
    # Check that fallback works
    sev, rc = service.predict("payment-service", "database connection failed during transaction checkout")
    assert sev == "critical"
    assert rc == "dependency timeout"

def test_ml_classifier_training():
    service = IncidentIntelligenceService()
    
    # Feed minimum training items (>= 4 records)
    training_data = [
        {"message": "OutOfMemoryError heap limit crossed", "severity": "critical", "root_cause": "infrastructure saturation"},
        {"message": "auth signature encryption key expired", "severity": "high", "root_cause": "credential rotation issue"},
        {"message": "upstream gateway stripe timeout response", "severity": "high", "root_cause": "dependency timeout"},
        {"message": "minor retry warning scheduler log", "severity": "low", "root_cause": "message queue backlog"},
        {"message": "critical database server down outage", "severity": "critical", "root_cause": "infrastructure saturation"},
    ]
    
    service.train(training_data)
    assert service.severity_trained
    assert service.rc_trained
    
    # Perform prediction
    sev, rc = service.predict("reporting-api", "OutOfMemoryError in reporting service")
    assert sev == "critical"
    assert rc == "infrastructure saturation"

# --- 4. API ENPOINTS INTEGRATION TESTS ---
def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_incidents_list(client):
    response = client.get("/api/incidents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_metrics_endpoint(client):
    response = client.get("/api/metrics")
    assert response.status_code == 200
    assert "gravityops_incidents_total" in response.text
    assert "gravityops_alerts_total" in response.text
