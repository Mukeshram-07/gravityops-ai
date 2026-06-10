# 01-master-prompt.md

You are building a production-style full-stack application called **GravityOps AI**.

Read all files inside `/prompts` first and follow them in this order:
1. `02-requirements.md`
2. `03-design-system.md`
3. `04-architecture.md`
4. `05-task-plan.md`
5. `06-acceptance-criteria.md`
6. `07-seed-data-and-demo.md`

## Operating instructions
- Start by summarizing the product requirements in your own words.
- Then propose the final stack and folder structure before generating code.
- Then produce a task plan grouped by phases, with clear files to create or modify.
- Wait until the plan is internally consistent, then execute phase by phase.
- After each phase, run relevant checks and fix issues before moving forward.
- Prefer clean, modular, production-style code.
- Do not generate placeholder marketing copy or generic template UI.
- Use realistic naming for services, incidents, alerts, root-cause tags, and SLA states.
- Build with testability, maintainability, and demo quality in mind.
- Add comments only where they improve maintainability.
- Prioritize a polished, enterprise-grade user experience.

## Build goals
Create an industry-grade SaaS-style incident triage and root-cause analysis workspace for DevOps/SRE teams with:
- modern dashboard UI
- ML-assisted incident severity prediction
- duplicate alert grouping
- SLA risk scoring
- operator workflow timeline
- analytics for recurring incidents and MTTR
- clean demo-ready sample data

## Mandatory execution sequence
1. Read prompt files.
2. Produce requirements summary.
3. Produce implementation plan.
4. Create project structure.
5. Build backend and schema.
6. Build frontend and dashboard flows.
7. Add seed/demo data.
8. Add tests.
9. Run app and perform browser validation.
10. Fix issues found during testing.

## Quality bar
This project must feel like a real internal product a mid-sized engineering company would use, not a student CRUD app.
