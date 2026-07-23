# Sprint 5 — CI/CD, Autoscaling & Operational Hardening

**Duration:** 2 weeks
**Goal:** Automate build/deploy pipelines, finalize autoscaling policies, and put operational guardrails (alarms, rollback, cost controls) in place for a production-ready launch.

## Objectives
1. Fully automated CI/CD pipeline from code commit to production deployment.
2. Finalized autoscaling policies for ECS services and the Ollama GPU fleet.
3. Operational guardrails: alarms, automated rollback, and Ollama-only cost controls.
4. Final documentation handoff (PRD, sprint docs, CLAUDE.md) validated against live system.

## Deliverables
- [ ] GitHub Actions/GitLab CI pipeline: build Docker images (frontend/backend/skills/plugins) → push to ECR → update ECS task definitions → deploy via rolling or blue/green strategy.
- [ ] Automated test gates in CI: unit tests, cross-tenant isolation tests (from Sprint 3), integration smoke tests against staging.
- [ ] ECS autoscaling policies finalized: target 60-70% CPU utilization + request-count scaling for frontend/backend; SQS queue depth + Step Functions backlog driving agent worker scaling.
- [ ] Ollama fleet autoscaling finalized: GPU utilization + request queue length thresholds; capacity plan confirming model sizes fit GPU memory with bounded concurrency.
- [ ] CloudWatch alarms: CPU, memory, SQS backlog, Step Functions failure rate, Ollama error counts — wired to notification channel (email/Slack/PagerDuty per client preference).
- [ ] Automated rollback: deployment pipeline reverts on failed health checks.
- [ ] Ollama-only cost model dashboard: tracks model count/size, average concurrency/utilization, and per-tenant quota consumption.
- [ ] Cost control enforcement: per-tenant quotas on concurrent/long-running requests; tier-based access to heavy models confirmed live.
- [ ] Runbook for "regular utilization review" cadence to adjust scaling rules and model set.
- [ ] Final review pass: PRD, Sprint 1-5 docs, and CLAUDE.md updated to reflect any deviations made during build.
- [ ] Go-live checklist signed off by client.

## Tasks Breakdown
| # | Task | Owner | Notes |
|---|---|---|---|
| 1 | Build CI pipeline: image build + ECR push | Dev | One pipeline per service (frontend/backend/skills/plugins) |
| 2 | Add automated test gates (unit, isolation, smoke) | Dev | Block deploy on failure |
| 3 | Configure blue/green or rolling deploy strategy | Dev | Client to confirm risk tolerance/preference |
| 4 | Tune ECS autoscaling policies | Dev | Validate under synthetic load test |
| 5 | Tune Ollama fleet autoscaling | Dev | Validate under synthetic inference load |
| 6 | Configure CloudWatch alarms + notification routing | Dev | Confirm on-call/notification channel with client |
| 7 | Implement automated rollback on failed health checks | Dev | Test by intentionally deploying a broken build |
| 8 | Build cost model dashboard (model size, concurrency, per-tenant quota usage) | Dev | Ties back to Section 8 of PRD |
| 9 | Load-test per-tenant quota enforcement | Dev | Confirm no tenant can saturate GPU fleet |
| 10 | Final documentation sync + go-live checklist | Dev + Client | Sign-off required before launch |

## Acceptance Criteria
- A merged PR automatically results in a deployed, health-checked production update with zero manual steps.
- Synthetic load tests confirm ECS and Ollama fleet autoscale within target thresholds without manual intervention.
- A deliberately broken deployment is automatically rolled back without downtime beyond the health-check window.
- Cost dashboard accurately reflects per-tenant GPU/model usage and enforces documented quotas.
- All project documentation (PRD, Sprints 1-5, CLAUDE.md) matches the actual deployed system.

## Dependencies / Blockers
- Sprint 4 production environment live and stable.
- Client confirmation on notification channels and deploy strategy (rolling vs. blue/green).

## Out of Scope (this sprint)
- New feature development beyond what's defined in this document set.
- Billing/invoicing system integration (flagged as future work unless specified by client).

## Post-Launch Recommendations
- Establish a recurring (e.g., monthly) review of GPU utilization metrics to right-size the Ollama fleet and model set (per PRD Section 8.2).
- Periodically re-run cross-tenant isolation tests as new features/tables are added.
- Revisit tiered plan limits as usage patterns emerge.
