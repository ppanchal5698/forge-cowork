# Product Requirements Document (PRD)
## Project: "Claude Cowork"-Style Multi-Tenant Agentic SaaS Platform

**Document Owner:** Parth
**Status:** Draft v1.0
**Last Updated:** July 23, 2026
**Audience:** Client, Developers, LLM Coding Agents (e.g., Claude Code)

---

## 1. Purpose & Vision

Build a mass-market, multi-tenant SaaS platform (a "Claude Cowork"-style product) that lets tenants run AI agents, skills, and plugins against their own data, with a graph-based knowledge layer (Neo4j) and self-hosted LLM inference (Ollama on GPUs) instead of pay-per-token APIs.

The platform must support **three coherent layers**:
1. **Local Dev Layer** — MiniStack + Docker emulating AWS services locally, with real Postgres/Redis and local Neo4j/Ollama.
2. **Production AWS Layer** — ECS Fargate, Step Functions, Cognito, S3, RDS, DynamoDB, SQS/SNS, following AWS's agentic AI multi-tenant prescriptive guidance.
3. **Migration Layer** — guarantees identical FastAPI/Next.js/agent code runs unchanged in both environments; only endpoints and credentials differ.

## 2. Problem Statement

Teams building agentic SaaS products typically hit a **"local vs cloud" rewrite trap**: local dev environments diverge from production AWS services, forcing throwaway adapters and duplicated logic. This project explicitly avoids that trap through **parity-first architecture**.

## 3. Goals & Non-Goals

### Goals
- Fast local iteration with production-fidelity AWS SDK calls (via MiniStack).
- Production-grade scalability, security, and multi-tenant isolation on AWS.
- Zero-rewrite migration path from local to production.
- Cost-efficient LLM inference via a self-hosted, GPU-backed Ollama fleet (no per-token API costs).
- Tiered (Free/Pro/Enterprise) service model with per-tenant quotas and observability.

### Non-Goals
- Not using third-party pay-per-token LLM APIs as the primary inference path.
- Not building a single-tenant or on-prem-only deployment model.
- Not covering mobile native apps (web-first via Next.js).

## 4. Architecture Principles

| Principle | Description |
|---|---|
| Parity first | Local dev uses MiniStack so engineers write real AWS SDK calls from day one; no throwaway local adapters. |
| Independent scaling | Next.js frontend and FastAPI+agents backend are separate ECS Fargate services, scaled independently. |
| Agent-centric design | Agent orchestration modeled as Step Functions state machines with SQS/SNS for async execution. |
| Multi-tenant by design | Shared infra with per-tenant isolation at data & control planes (Postgres RLS, DynamoDB partitioning, per-tenant rate limits). |
| GPU-aware model serving | Ollama models run on GPU-backed EC2/ECS as a dedicated, autoscaled inference fleet. |

## 5. System Architecture

### 5.1 Layer 1 — Local Dev (MiniStack + Docker)

**Purpose:** Full local sandbox that behaves like AWS, enabling development/debugging/integration testing without touching production accounts.

| Component | Local Implementation | Notes |
|---|---|---|
| Frontend | Next.js in Docker container, port 3000 | Talks to backend via NGINX/local ALB equivalent |
| Backend | FastAPI in Docker, same image as production | Uses boto3/AWS SDK pointed at MiniStack (`http://localhost:4566`) |
| Agent Orchestration | Step Functions emulator (MiniStack) | States = skill/plugin calls or sub-agent executions ("Graph Loop Engineering") |
| Skills/Plugins | Local Lambdas (short-lived) via MiniStack; ECS tasks (long-running/stateful) | e.g., text transforms vs. web scrapers/ETL |
| Graph DB | Neo4j in dedicated Docker container | Not AWS-native — identical in dev & prod, only host/creds differ |
| Object Storage | MiniStack S3 buckets | Same bucket names/key structure as production |
| Relational Data | Real Postgres containers (MiniStack RDS emulation) | Schemas/migrations behave exactly like production |
| Fast State/Session | MiniStack DynamoDB tables | Agent session state, conversation graphs, cache |
| Auth | MiniStack Cognito (user pools, JWT flows) | Triggers (PreSignUp/PostConfirmation) NOT executed locally — test against dedicated dev pool in real AWS |
| Async Tasks | MiniStack SQS/SNS | Orchestrator→worker handoffs, DLQs |
| Secrets/Config | MiniStack Secrets Manager + SSM Parameter Store | MCP keys, Ollama endpoints, 3rd-party API keys |
| Logs/Metrics | MiniStack CloudWatch Logs emulation | Validate log formats/queries before pushing to AWS |

**Developer Experience:** Single `docker-compose.yml` starts Next.js, FastAPI, Neo4j, Ollama, MiniStack, and supporting services. Same env vars (`AWS_REGION`, `AWS_ACCESS_KEY_ID`, etc.) as production — only endpoint URLs point to MiniStack.

### 5.2 Layer 2 — Production AWS Architecture

**Network & Security**
- VPC with public subnets (ALB, NAT gateways) and private subnets (ECS Fargate tasks, RDS, ElastiCache — no public IPs).
- Security Groups restrict inbound traffic to ALB only; no direct exposure of ECS tasks or databases.

**Compute Services**
- **Frontend (Next.js):** ECS Fargate service behind ALB (path/hostname routing); independent autoscaling (CPU-based, request count).
- **Backend (FastAPI + Agents):** ECS Fargate service, same ALB, different target group; identical Docker image as local dev — only env vars/endpoints change.
- **Skills/Plugins Runtime:** AWS Lambda (short/stateless) + ECS tasks (long-running/stateful: crawlers, ETL, integrations); orchestrated via Step Functions + EventBridge.
- **Agent Orchestration:** Step Functions state machines implement orchestrator-worker pattern (orchestrator agent, specialized workers, evaluation agents); SQS/SNS handle async comms, retries, DLQs.

**Data Layer**
| Store | Purpose | Isolation Pattern |
|---|---|---|
| RDS Postgres (Multi-AZ) | Users, tenants, tasks, billing, config | `tenant_id` column + row-level security |
| DynamoDB | Agent state graphs, session metadata, cached decisions | Partition key includes `tenant_id` |
| S3 | Task outputs, logs, knowledge snapshots | `tenant_id` prefixes + lifecycle policies per tier |
| Neo4j (Managed) | Task graphs, knowledge graphs, agent relationships | EC2/ECS + EBS, or AuraDB SaaS — identical usage to dev |

**Platform Services**
- **Cognito:** User Pool, Hosted UI, MFA, social login/SSO; Lambda triggers for validation, enrichment, tenant provisioning (assign `tenant_id` on signup).
- **Secrets Manager & SSM:** MCP/plugin API keys, Ollama endpoints, 3rd-party creds — accessed via IAM roles, never hardcoded.
- **CloudWatch + Container Insights:** Centralized logs/metrics/traces for ECS, Lambda, Step Functions, Ollama nodes; per-tenant dashboards & alarms.

### 5.3 Layer 3 — Migration & Parity Strategy

**"No Rewrite" Guarantee:** All app code (Next.js, FastAPI, agent orchestration, skills, plugins) is written against AWS SDKs and Neo4j/Ollama APIs that behave identically in dev and prod. Moving from local to AWS requires only:
1. Changing endpoint URLs from `http://localhost:4566` (MiniStack) to real AWS endpoints.
2. Rotating credentials from local test keys to IAM roles.
3. Pointing Neo4j/Ollama URLs to managed instances.

**Infrastructure as Code:** Terraform or AWS CDK defines VPC, ECS, ALB, RDS, DynamoDB, S3, Cognito, Step Functions, CloudWatch. Same IaC templates provision dev, staging, and production for reproducibility and easy rollback.

**Data/Schema Migration:** Because MiniStack uses real Postgres, migration tooling (Alembic, Flyway) is identical in both environments. Initial production deployment seeds baseline data (tenants, task templates, skills registry) via IaC or dedicated migrations.

## 6. Multi-Tenancy & Isolation

### 6.1 Data Isolation Patterns
- **RDS:** `tenant_id` column on all multi-tenant tables; row-level security policies restrict app roles to their own tenant's rows.
- **DynamoDB:** Composite keys `PK = TENANT#<tenant_id>` isolate per-tenant state and enable per-tenant throttling.
- **S3:** Bucket prefixes `s3://artifacts/<tenant_id>/...` with bucket policies limiting path access.
- **Cognito:** Tenants modeled as groups/custom claims; backend derives `tenant_id` from JWT for all data operations.

### 6.2 Agentic-Specific Controls
- **Rate Limiting per Tenant:** Caps on concurrent agent tasks and Ollama inference calls, tiered by plan (Free/Pro/Enterprise), to prevent noisy neighbors.
- **Tenant-Aware Observability:** CloudWatch dashboards keyed by `tenant_id` (error rates, latency, CPU/GPU usage); alarms for per-tenant anomalies, not just global.
- **Tiered Service Model:**

| Tier | Agent Concurrency | Plugins | Retention | SLA |
|---|---|---|---|---|
| Free | Limited | Basic skills only | Small artifact retention | Best-effort |
| Pro | Higher limits | More plugins | Longer retention | Standard |
| Enterprise | Dedicated quotas | Custom plugins | Extended/custom | Stricter SLAs |

## 7. CI/CD & Scaling

**CI/CD Pipeline:** GitHub Actions/GitLab CI builds Docker images for frontend/backend/skills/plugins → pushes to ECR → updates ECS task definitions → deploys via rolling or blue/green strategy.

**Autoscaling Policies**
- ECS Services: target 60-70% CPU utilization + request-based scaling for frontend/backend; SQS queue depth and Step Functions backlog drive agent worker scaling.
- Ollama Fleet: GPU-backed EC2/ECS nodes (G4/G5/G6 instances) autoscaled on GPU utilization and request queue length; capacity planning ensures model sizes fit GPU memory with bounded concurrency.

**Operational Guardrails:** CloudWatch alarms on CPU, memory, SQS backlog, Step Functions failure rate, Ollama error counts; automated rollback on failed health checks.

## 8. Ollama-Only Cost Model

**Compute Strategy:** Inference runs on owned GPU fleet (not per-token APIs). Cost drivers: number/size of models (parameter count, VRAM needs), average concurrency/utilization, autoscaling thresholds (min idle capacity vs. burst tolerance).

**Cost Controls:** Per-tenant quotas on concurrent/long-running requests prevent GPU saturation by a single tenant; tier-based access to heavy models (larger context/expensive architectures reserved for higher plans); regular utilization review to adjust scaling rules and model set.

## 9. Success Metrics

- 100% functional parity between local (MiniStack) and production AWS environments — zero code changes required beyond config/endpoints.
- P95 agent task latency and Ollama inference latency within tiered SLA targets per plan.
- Zero cross-tenant data leakage incidents (validated via RLS/partition/bucket-policy audits).
- GPU fleet utilization maintained within target range (avoiding over/under-provisioning).
- CI/CD deployment lead time and rollback time meet defined targets (see Sprint 5).

## 10. Key Risks & Mitigations

| Risk | Mitigation |
|---|---|
| MiniStack gaps vs. real AWS (e.g., Cognito triggers) | Explicitly test triggers against a dedicated AWS dev pool; document all known MiniStack limitations in CLAUDE.md |
| GPU fleet cost overruns | Per-tenant quotas, tiered model access, utilization-based autoscaling |
| Cross-tenant data leakage | RLS policies, partition key enforcement, S3 bucket policy audits, automated tenant-isolation tests |
| Agent orchestration failures | Step Functions retries, DLQs, CloudWatch alarms on failure rate |
| Local/prod drift | Same Docker images, same IaC templates, same env var naming convention across environments |

## 11. Glossary

- **MiniStack:** Local AWS-service emulator (S3, RDS, DynamoDB, Cognito, SQS/SNS, Step Functions, Lambda, Secrets Manager, CloudWatch) accessed via a single-port endpoint.
- **Graph Loop Engineering:** The project's term for modeling agent orchestration as state-machine loops (Step Functions states = skill/sub-agent calls).
- **Tenant:** A customer organization/account with isolated data and resource quotas.
