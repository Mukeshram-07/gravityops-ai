# 07-seed-data-and-demo.md

## Demo services
- payment-service
- auth-service
- order-service
- scheduler-worker
- notification-gateway
- reporting-engine
- inventory-sync
- customer-support-api

## Incident examples
- Payment API latency spike in APAC region
- Repeated auth token refresh failures
- Scheduler job timeout during nightly settlement
- Notification retry queue backlog
- Inventory sync mismatch after upstream schema drift
- Reporting engine memory spike
- Order-service 5xx burst after release
- Customer-support webhook signature validation failures

## Root-cause categories
- deployment regression
- dependency timeout
- schema drift
- infrastructure saturation
- message queue backlog
- credential rotation issue
- cache invalidation bug
- third-party provider degradation

## Severity classes
- low
- medium
- high
- critical

## SLA risk classes
- healthy
- watch
- at-risk
- breach-likely

## Seed expectations
- 20–30 incidents minimum
- 5–8 services
- mix of open, investigating, mitigated, resolved
- realistic timestamps over several days
- realistic operator names and notes
- grouped duplicate alerts for some incidents

## Demo notes examples
- “Escalated after repeated retries crossed threshold.”
- “Correlated with deploy 2026.06.08.3 on payment-service.”
- “Temporary mitigation applied by queue throttling.”
- “Likely tied to provider latency spike.”
