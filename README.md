# GravityOps AI - Incident Command Workspace

**GravityOps AI** is a production-style, DevOps-focused full-stack incident triage and root-cause analysis platform built to reduce alert fatigue for SRE, DevOps, and on-call engineering teams. Leveraging Jaccard similarity metrics for duplicate alert deduplication and standard machine learning (TF-IDF + Naive Bayes) for severity and probable root cause category predictions, the platform provides a unified operations dashboard with SLA risk tracking, audit timeline events, operator notes, and historical MTTR analytics.

---

## Technical Stack & Architecture

- **Frontend**: Vite + React + TypeScript, chart visualizations with Recharts, interface icons by Lucide-React, and styled with a custom Vanilla CSS design system supporting theme-toggles (dark-mode first).
- **Backend**: FastAPI (Python 3.13), data validation with Pydantic, persistence using SQLAlchemy + SQLite.
- **ML & Automation**:
  - *Deduplication Grouping*: Computes message token similarity (Jaccard index) across active incident alerts within a rolling 30-minute time-window.
  - *Classification Engine*: TF-IDF vectorizer + Multinomial Naive Bayes model to dynamically predict incident severity and classify root causes, with an rule-based heuristic cold-start fallback.
  - *SLA Risk Watchdog*: Escalates incident SLA threat levels (`healthy`, `watch`, `at-risk`, `breach-likely`) using severity weights and elapsed time relative to Service criticality tiers.

---

## Directory Structure

```text
gravityops-ai/
├── prompts/              # System prompt and requirements files
├── app/
│   ├── backend/          # FastAPI REST API, database models, tests
│   │   ├── db/           # Session management
│   │   ├── ml/           # Grouping algorithms & ML classifiers
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # SLA scorers, Incident managers, Analytics engines
│   │   ├── tests/        # Pytest test suite
│   │   ├── main.py       # REST endpoints entrypoint
│   │   └── seed.py       # Out-of-the-box DB populating script
│   └── frontend/         # Vite React TS monorepo
│       ├── src/
│       │   ├── lib/      # API wrappers
│       │   ├── App.tsx   # Core dashboard views & sidebar
│       │   └── index.css # Premium design system stylesheet
```

---

## Quick Start Guide

Ensure you have **Python 3.13** and **Node.js v24+** installed.

### 1. Run Backend Server

1. Navigate to the backend directory:
   ```bash
   cd app/backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize tables and seed 25+ realistic incident logs:
   ```bash
   python seed.py
   ```
4. Start the FastAPI Uvicorn server:
   ```bash
   python -m uvicorn main:app --reload --port 8000
   ```
   The backend API will run on `http://127.0.0.1:8000`. Exposes Grafana-ready metrics on `http://127.0.0.1:8000/api/metrics`.

### 2. Run Frontend Dashboard

1. Navigate to the frontend directory:
   ```bash
   cd app/frontend
   ```
2. Install Node packages:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The application will launch on `http://localhost:3000`. API requests to `/api` are automatically proxied to the backend.

### 3. Execution of Backend Tests

Verify database entities, similarity grouping filters, SLA escalations, and FastAPI endpoints:
```bash
cd app/backend
python -m pytest tests/
```
