# Sprint 3 — Multi-Tenancy, Isolation & Agentic Controls

**Duration:** 2 weeks
**Goal:** Implement full multi-tenant isolation (data + control plane) and agentic-specific controls (rate limiting, tenant-aware observability, tiered service model).

## Objectives
1. Enforce tenant isolation across RDS, DynamoDB, S3, and Cognito.
2. Implement per-tenant rate limiting for agent concurrency and Ollama inference calls.
3. Implement tiered service model (Free/Pro/Enterprise) with plan-based limits.
4. Build tenant-aware observability (dashboards, alarms) on top of CloudWatch Logs emulation.

## Deliverables
- [ ] RDS: Row-level security (RLS) policies on all multi-tenant tables; app DB role restricted to its `tenant_id`.
- [ ] DynamoDB: All tables use composite key pattern `PK = TENANT#<tenant_id>`; verified per-tenant query isolation.
- [ ] S3: Bucket policies (or MiniStack-equivalent checks) enforce access only to `artifacts/<tenant_id>/...` prefixes.
- [ ] Cognito: Tenants modeled as groups/custom claims; backend middleware derives `tenant_id` from JWT on every request.
- [ ] Rate limiting middleware: caps concurrent agent tasks and Ollama calls per tenant, differentiated by plan tier.
- [ ] Tiered plan config (Free/Pro/Enterprise) stored in Postgres/config, driving: agent concurrency limits, available skills/plugins, artifact retention period, model access (light vs. heavy models).
- [ ] Tenant-aware CloudWatch-style dashboards (via MiniStack Logs locally): error rate, latency, CPU/GPU usage per `tenant_id`.
- [ ] Alarm definitions (to be wired to real CloudWatch in Sprint 4) for per-tenant anomaly detection.
- [ ] Automated isolation test suite: attempts cross-tenant reads/writes across RDS, DynamoDB, S3 and asserts failure.

## Tasks Breakdown
| # | Task | Owner | Notes |
|---|---|---|---|
| 1 | Write and apply RLS policies for all multi-tenant Postgres tables | Dev | Test with two seeded tenants |
| 2 | Refactor DynamoDB access layer to enforce `TENANT#<id>` partition keys | Dev | Update all existing skill/plugin writes |
| 3 | Implement S3 key-prefix enforcement + policy checks | Dev | Validate via automated test |
| 4 | Build `tenant_id` extraction middleware from JWT | Dev | Reject requests without valid tenant claim |
| 5 | Implement per-tenant rate limiter (Redis-backed token bucket or similar) | Dev | Separate limits for agent concurrency vs. Ollama calls |
| 6 | Define plan tiers config (Free/Pro/Enterprise) | Dev + Client | Client to confirm exact limits/pricing |
| 7 | Build tenant-aware log/metrics dashboard (local) | Dev | Foundation for CloudWatch dashboards in prod |
| 8 | Write automated cross-tenant isolation test suite | Dev | Must run in CI (Sprint 5) |
| 9 | Document tenant onboarding flow (signup → tenant_id assignment → plan default) | Dev | Feed into CLAUDE.md |

## Acceptance Criteria
- Two seeded test tenants cannot read/write each other's data in RDS, DynamoDB, or S3 under any code path (verified by automated tests).
- Free-tier tenant is blocked from exceeding concurrency/model-access limits; Pro/Enterprise tenants have correspondingly higher limits.
- Dashboards show per-tenant metrics, not just global aggregates.

## Dependencies / Blockers
- Sprint 2 core application and agent orchestration functional.
- Plan tier definitions confirmed with client (pricing/limits).

## Out of Scope (this sprint)
- Production AWS CloudWatch alarms (real, not emulated) — Sprint 4.
- Billing integration (flagged as future work unless client specifies otherwise).
