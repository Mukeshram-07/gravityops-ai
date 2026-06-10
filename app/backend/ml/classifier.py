import re
from typing import Tuple, List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import numpy as np

# Fallback heuristic rules for cold starts
HEURISTIC_SEVERITY_KEYWORDS = {
    "critical": ["outage", "down", "critical", "db connection failed", "database connection failed", "payment failure", "500 burst", "signature validation failure"],
    "high": ["latency", "timeout", "high error rate", "backlog", "queue full", "auth token refresh failure", "mismatch"],
    "medium": ["memory spike", "retry", "threshold crossed", "drift", "jobs slow"],
    "low": ["retry queue", "warning", "info", "healthcheck", "slow latency"]
}

HEURISTIC_ROOT_CAUSE_KEYWORDS = {
    "deployment regression": ["deploy", "release", "version", "rollout", "upstream schema drift", "5xx burst after release"],
    "dependency timeout": ["timeout", "gateway", "provider", "external api", "latency spike", "api latency", "downstream"],
    "schema drift": ["schema", "drift", "mismatch", "column", "migration", "table mutation"],
    "infrastructure saturation": ["memory", "cpu", "disk", "saturation", "oom", "thread pool", "resource limit"],
    "message queue backlog": ["backlog", "queue", "kafka", "rabbitmq", "celery", "retry queue", "dead letter"],
    "credential rotation issue": ["credential", "auth", "token", "signature", "jwt", "unauthorized", "expired", "key"],
    "cache invalidation bug": ["cache", "redis", "memcached", "stale", "eviction", "miss rate"],
    "third-party provider degradation": ["provider", "stripe", "twilio", "aws", "third-party", "webhook failure"]
}

class IncidentIntelligenceService:
    def __init__(self):
        self.severity_vectorizer = TfidfVectorizer(token_pattern=r'(?u)\b\w+\b')
        self.severity_clf = MultinomialNB()
        self.severity_trained = False

        self.rc_vectorizer = TfidfVectorizer(token_pattern=r'(?u)\b\w+\b')
        self.rc_clf = MultinomialNB()
        self.rc_trained = False
        self.training_sample_count = 0

    def fallback_predict_severity(self, message: str) -> str:
        msg_lower = message.lower()
        for sev, keywords in HEURISTIC_SEVERITY_KEYWORDS.items():
            if any(kw in msg_lower for kw in keywords):
                return sev
        return "medium"  # default

    def fallback_predict_root_cause(self, message: str) -> str:
        msg_lower = message.lower()
        best_match = "dependency timeout"  # default
        max_matches = 0
        for rc, keywords in HEURISTIC_ROOT_CAUSE_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in msg_lower)
            if matches > max_matches:
                max_matches = matches
                best_match = rc
        return best_match

    def train(self, training_data: List[Dict[str, Any]]):
        """
        Trains the models.
        training_data format: [{'message': str, 'severity': str, 'root_cause': str}]
        """
        if not training_data or len(training_data) < 4:
            # Not enough data to train scikit-learn models properly, stick to fallback
            self.severity_trained = False
            self.rc_trained = False
            self.training_sample_count = 0
            return

        texts = [d['message'] for d in training_data]
        self.training_sample_count = len(texts)
        severities = [d['severity'] for d in training_data]
        root_causes = [d['root_cause'] for d in training_data]

        try:
            # Train severity model
            X_sev = self.severity_vectorizer.fit_transform(texts)
            self.severity_clf.fit(X_sev, severities)
            self.severity_trained = True

            # Train root-cause model
            X_rc = self.rc_vectorizer.fit_transform(texts)
            self.rc_clf.fit(X_rc, root_causes)
            self.rc_trained = True
        except Exception as e:
            # Fail silently to fallbacks if scikit-learn vectorization fails (e.g. empty inputs)
            self.severity_trained = False
            self.rc_trained = False

    def predict(self, service_name: str, message: str) -> Tuple[str, str]:
        """
        Predicts (severity, root_cause) for a given alert event.
        """
        # Combine service name and message for better contextual features
        combined_text = f"{service_name} {message}"

        # 1. Severity Prediction
        if self.severity_trained:
            try:
                X = self.severity_vectorizer.transform([combined_text])
                severity = self.severity_clf.predict(X)[0]
            except Exception:
                severity = self.fallback_predict_severity(message)
        else:
            severity = self.fallback_predict_severity(message)

        # 2. Root Cause Prediction
        if self.rc_trained:
            try:
                X = self.rc_vectorizer.transform([combined_text])
                root_cause = self.rc_clf.predict(X)[0]
            except Exception:
                root_cause = self.fallback_predict_root_cause(message)
        else:
            root_cause = self.fallback_predict_root_cause(message)

        return severity, root_cause

# Singleton instance for the application
intel_service = IncidentIntelligenceService()
