# Sprint 2 — Core Application: FastAPI Backend, Next.js Frontend, Agent Orchestration Skeleton

**Duration:** 2 weeks
**Goal:** Build the core backend/frontend application logic and the first working agent orchestration loop (Step Functions state machine emulated via MiniStack).

## Objectives
1. FastAPI backend exposes core REST/GraphQL endpoints for auth, tasks, and artifacts.
2. Next.js frontend implements auth flow (against MiniStack Cognito) and a basic task dashboard.
3. First agent orchestration state machine ("Graph Loop") runs end-to-end locally via Step Functions emulator.
4. Skills/plugins execution model established: short-lived Lambda-based skills vs. long-running ECS-task-based plugins.

## Deliverables
- [ ] Auth endpoints (signup/login/refresh) using MiniStack Cognito; JWT contains `tenant_id` custom claim.
- [ ] Core data models in Postgres: `tenants`, `users`, `tasks`, `agent_runs`, `artifacts` (all with `tenant_id`).
- [ ] Next.js pages: login, signup, dashboard (list tasks), task detail (agent run status/output).
- [ ] Step Functions state machine definition modeling: orchestrator agent → worker agent(s) → evaluation agent.
- [ ] At least 2 example skills implemented as MiniStack Lambdas (e.g., text summarization, small research call).
- [ ] At least 1 example long-running plugin implemented as an ECS-task-style container (e.g., web scraper).
- [ ] SQS/SNS wiring for orchestrator→worker handoff, including DLQ handling and retry logic.
- [ ] Neo4j integration: agent runs write task-graph nodes/edges (task → skill → sub-agent → output).
- [ ] Ollama integration: FastAPI calls local Ollama endpoint for at least one agent step (e.g., planning or summarization).
- [ ] S3 integration: agent run outputs stored under `artifacts/<tenant_id>/<run_id>/...`.

## Tasks Breakdown
| # | Task | Owner | Notes |
|---|---|---|---|
| 1 | Design Postgres schema (tenants, users, tasks, agent_runs, artifacts) | Dev | RLS policies scaffolded now, enforced in Sprint 3 |
| 2 | Implement auth flow (FastAPI + MiniStack Cognito + Next.js) | Dev | JWT includes `tenant_id` |
| 3 | Build Next.js dashboard + task detail UI | Dev | Talks to FastAPI via local ALB-equivalent (NGINX) |
| 4 | Define Step Functions "Graph Loop" state machine (orchestrator/worker/evaluator) | Dev | Each state = skill/plugin/sub-agent call |
| 5 | Implement 2 sample skills as Lambda functions | Dev | Stateless, short-lived |
| 6 | Implement 1 sample plugin as ECS-task container | Dev | Stateful/long-running (e.g., scraper) |
| 7 | Wire SQS/SNS handoff + DLQ | Dev | Test failure/retry path explicitly |
| 8 | Integrate Neo4j writes from agent run lifecycle | Dev | Task graph populated per run |
| 9 | Integrate Ollama call into at least one orchestration step | Dev | Confirm latency is acceptable |
| 10 | Wire S3 artifact storage with tenant-prefixed keys | Dev | Same key structure as future prod |

## Acceptance Criteria
- A user can sign up, log in, submit a task, and see an agent run progress through orchestrator → worker → evaluator states, ending with an artifact stored in S3 and a task graph in Neo4j.
- Skills and plugins are cleanly separated in code (different execution model, different directories) so their production mapping (Lambda vs. ECS) is unambiguous.
- Failure in a worker step correctly triggers SQS retry, then DLQ after max retries.

## Dependencies / Blockers
- Sprint 1 environment fully functional.
- Step Functions/Lambda emulation confirmed working in MiniStack.

## Out of Scope (this sprint)
- Row-level security enforcement and per-tenant rate limiting (Sprint 3).
- Production AWS deployment (Sprint 4).
- Autoscaling and CI/CD (Sprint 5).
