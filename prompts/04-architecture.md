# 04-architecture.md

## Preferred stack
### Frontend
- Next.js or React
- TypeScript
- Component-based architecture
- Chart library for analytics
- Clean design system

### Backend
- FastAPI
- Python
- Pydantic schemas
- SQLAlchemy or equivalent ORM

### Data + workers
- PostgreSQL
- Redis
- Celery for async/background jobs

### ML / intelligence layer
- Severity prediction module
- Duplicate incident grouping module
- Root-cause category suggestion module
- MLflow for experiment tracking hooks

### Observability
- Prometheus metrics endpoints
- Grafana-ready metrics naming
- Structured logging

### Testing
- Unit tests for API/services
- Basic integration tests
- Optional browser smoke tests

## Suggested domain entities
- User
- Service
- AlertEvent
- Incident
- IncidentGroup
- IncidentNote
- IncidentTimelineEvent
- SeverityPrediction
- RootCauseSuggestion
- SlaPolicy
- SlaRiskScore
- UploadJob
- AuditLog

## Suggested backend modules
- api/
- core/
- db/
- models/
- schemas/
- services/
- workers/
- ml/
- tests/

## Suggested frontend modules
- app/ or src/
- components/
- features/incidents/
- features/analytics/
- features/uploads/
- features/settings/
- lib/
- hooks/
- types/

## API expectations
- GET /incidents
- GET /incidents/{id}
- POST /incidents/upload
- PATCH /incidents/{id}
- POST /incidents/{id}/notes
- GET /analytics/overview
- GET /analytics/services
- GET /health
- GET /metrics

## Data flow
1. Upload alert file
2. Validate and normalize
3. Store raw alert events
4. Group duplicates
5. Create/update incidents
6. Predict severity
7. Suggest root-cause category
8. Score SLA risk
9. Return updated dashboard and analytics

## Engineering expectations
- Clear README
- Env example file
- Docker support
- Modular code structure
- Seed script for demo
- Consistent naming
