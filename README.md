# GravityOps AI - SRE Incident Command & Triage Workspace

[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Vite v5](https://img.shields.io/badge/Vite-v5-646CFF.svg)](https://vitejs.dev/)
[![React v18](https://img.shields.io/badge/React-v18-61DAFB.svg)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**GravityOps AI** is an enterprise-grade, DevOps-focused full-stack incident command-center and triage platform designed to reduce alert fatigue for SRE, Platform Engineering, and on-call teams. By combining similarity grouping for alert deduplication and standard machine learning (TF-IDF + Naive Bayes) for severity/root-cause recommendations, the platform accelerates resolution times and enhances SLA watchdogs.

---

## 🚀 Key Features

*   **Operator Authentication Portal**: Pre-defined SRE profiles (Team Lead, On-call Engineer, Director) and guest logins that bind operational roles to comments, status updates, and timeline event streams.
*   **Intelligence & Deduplication Layer**:
    *   *Deduplication Grouping*: Computes token-based **Jaccard similarity** (window: 30 minutes, threshold: 0.4) across active alerts, clustering duplicate issues automatically.
    *   *ML Classification*: TF-IDF + Multinomial Naive Bayes model to predict incident severity and categorize root causes, falling back to heuristic cold-starts.
    *   *SLA Watchdog*: Auto-escalates incident threat levels (`healthy`, `watch`, `at-risk`, `breach-likely`) using criticality weights and resolution time windows.
*   **Operational Analytics & MTTR**: Live graphs (noisy services, status mix, 10-day outage trends) powered by Recharts.
*   **Demo-Ready Ingestion Pipeline**: Asynchronous CSV/JSON upload card with instant sample downloads and dynamic telemetry status reporting.
*   **ML Model Diagnostics Card**: Full visibility into the ML engine status, showing current mode (Rule-Based Fallback or Trained Model) and training sample count.

---

## 🛠️ Directory Structure

```text
gravityops-ai/
├── prompts/              # Requirement guidelines & design systems
├── app/
    ├── backend/          # FastAPI server, ML logic, tests, DB session setup
    │   ├── db/           # Session management & dotenv config loaders
    │   ├── ml/           # Grouping algorithms & Naive Bayes classifiers
    │   ├── models/       # SQLAlchemy entities
    │   ├── schemas/      # Pydantic validation schemas
    │   ├── services/     # SLA watchdogs, incident managers, analytics
    │   ├── tests/        # Pytest test suite
    │   ├── main.py       # FastAPI REST endpoints
    │   ├── seed.py       # Database seeding utility (seeds 26 incidents)
    │   └── .env          # Environment-driven configuration variables
    └── frontend/         # Vite React TS monorepo
        ├── src/
        │   ├── lib/      # Client API wrappers
        │   ├── App.tsx   # Core dashboard views & slide-out panel
        │   └── index.css # Premium dark-mode-first styling sheet
```

---

## ⚙️ Quick Start Guide

Ensure you have **Python 3.13** and **Node.js v24+** installed.

### 1. Setup & Start Backend Server

1. Navigate to the backend directory:
   ```bash
   cd app/backend
   ```
2. Install Python requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize the SQLite database and seed 26 initial incidents:
   ```bash
   python seed.py
   ```
4. Start the FastAPI Uvicorn server:
   ```bash
   python -m uvicorn main:app --reload --port 8000
   ```
   *The backend will run on `http://127.0.0.1:8000`. Exposes Swagger docs at `/docs` and metrics at `/api/metrics`.*

### 2. Setup & Start Frontend client

1. Navigate to the frontend directory:
   ```bash
   cd app/frontend
   ```
2. Install Node packages:
   ```bash
   npm install
   ```
3. Launch the Vite development server:
   ```bash
   npm run dev
   ```
   *Open `http://localhost:3000` in your web browser.*

### 3. Execution of Backend Tests

Verify database entities, similarity grouping filters, SLA escalations, and FastAPI endpoints:
```bash
cd app/backend
python -m pytest tests/test_services.py
```

---

## 🔒 Production Readiness Note

To deploy GravityOps AI to a cloud environment:
1. **Database**: Swap `DATABASE_URL` in `app/backend/.env` to point to a PostgreSQL cluster.
2. **Auth**: Replace the Operator local session manager with a secure OAuth2 JWT provider.
3. **Queue**: Configure a Celery + Redis worker pool for heavy asynchronous file uploads.
