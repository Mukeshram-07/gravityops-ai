# 02-requirements.md

## Product name
GravityOps AI

## Product type
A full-stack SaaS-style web application for engineering operations teams.

## Core problem
Engineering teams receive too many alerts from logs, jobs, and services. Many alerts are duplicates, severity is inconsistent, and incident response becomes slow. Teams need one workspace to triage incidents, estimate risk, track action history, and identify recurring failures.

## Primary users
1. SRE / DevOps Engineer
2. Engineering Manager
3. On-call Engineer
4. Platform Operations Analyst

## Main value proposition
GravityOps AI reduces alert fatigue and speeds up response by grouping duplicate incidents, predicting severity, highlighting probable root-cause categories, tracking SLA risk, and giving teams a single operational timeline.

## Primary modules
1. Authentication-ready app shell (mock auth is acceptable for v1)
2. Incident dashboard
3. Incident detail view
4. Alert ingestion and normalization
5. Duplicate grouping engine
6. Severity prediction service
7. Root-cause recommendation panel
8. SLA risk scoring
9. Analytics and trends
10. Audit trail and operator notes

## User stories
- As an on-call engineer, I want to see all active incidents sorted by urgency so I can respond faster.
- As an SRE, I want duplicate alerts grouped into one cluster so I do not waste time on noise.
- As an engineering manager, I want to see recurring service failures and MTTR trends.
- As an operator, I want to inspect the timeline of status changes, assignments, notes, and acknowledgements.
- As a reviewer, I want demo-ready data to simulate realistic incidents.

## Key workflows
### Workflow 1: Incident triage
- User lands on dashboard
- Sees incident list with filters: status, severity, service, SLA risk
- Opens one incident
- Reviews grouped alerts, predicted severity, probable root cause, timeline, and recommended actions
- Updates status and adds a note

### Workflow 2: Alert ingestion
- User uploads CSV or JSON alert data
- System validates and normalizes fields
- System groups duplicates and creates/updates incidents
- Dashboard refreshes with newly ingested incidents

### Workflow 3: Analytics
- Manager opens analytics page
- Views top noisy services, repeated incidents, MTTR, status mix, and SLA breach risk
- Filters by date range and service

## Functional requirements
- Dashboard with incident table/cards
- Search and filtering
- Incident detail page
- Grouped alerts section
- Root-cause recommendation section
- Severity prediction field
- SLA risk score and badge
- Timeline with notes and status updates
- Analytics page with charts/cards
- Upload flow for CSV/JSON
- Demo data seeding
- Responsive UI
- Light and dark mode

## Non-functional requirements
- Clean architecture
- Strong typing where possible
- Reusable components
- Error handling and empty states
- Loading skeletons
- Test coverage for critical paths
- Demo-ready seeded environment
- Accessible and keyboard-friendly UI
- Mobile-friendly layout

## V1 constraints
- No real third-party auth required
- No live cloud deployment required in first pass
- Use local/demo data where helpful
- ML can begin with practical heuristic + trainable pipeline design
- Focus on product quality and architecture clarity

## Success criteria
A reviewer should be able to run the app, ingest sample data, inspect incidents, see severity and SLA insights, navigate analytics, and believe this is a credible operations product.
