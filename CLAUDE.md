# CLAUDE.md — Project Context for LLM Coding Agents

This file gives Claude (or any LLM coding assistant) the full context needed to work productively on this codebase without re-deriving architecture decisions. Read this before generating or modifying code.

## 1. What This Project Is

A mass-market, multi-tenant "Claude Cowork"-style SaaS platform where tenants run AI agents/skills/plugins against their own data, backed by a Neo4j knowledge graph and a self-hosted, GPU-backed Ollama inference fleet (not pay-per-token APIs).

Three layers, one codebase:
1. **Local Dev** — MiniStack + Docker (emulates AWS locally).
2. **Production AWS** — ECS Fargate, Step Functions, Cognito, S3, RDS, DynamoDB, SQS/SNS.
3. **Migration** — same code runs in both; only endpoints/credentials differ.

**Golden rule: never write code that only works locally or only works in AWS.** If a change requires an `if os.environ["ENV"] == "local"` branch anywhere outside a config/bootstrap file, stop and reconsider — it likely violates the parity principle.

## 2. Architecture Principles (apply to every change)

- **Parity first:** Always use real AWS SDK calls (boto3) pointed at an endpoint from config/env — never write MiniStack-specific code paths.
- **Independent scaling:** Frontend (Next.js) and backend (FastAPI+agents) are separate services/containers — never merge their concerns into one deployable unit.
- **Agent-centric design:** Agent orchestration = Step Functions state machines + SQS/SNS. Each state = one skill/plugin/sub-agent call. Do not build ad-hoc orchestration loops outside this model.
- **Multi-tenant by design:** Every table, partition key, S3 path, and JWT claim must carry `tenant_id`. There is no "single-tenant mode."
- **GPU-aware model serving:** All LLM calls go through the Ollama endpoint (local container or production GPU fleet) — never introduce a third-party per-token API call as a default path.

## 3. Environment & Config Conventions

| Variable | Local (MiniStack) | Production (AWS) |
|---|---|---|
| `AWS_ENDPOINT_URL` | `http://localhost:4566` | (unset — real AWS) |
| `AWS_REGION` | e.g. `us-east-1` | same region as prod |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | MiniStack test keys | IAM role (no static keys) |
| `NEO4J_URI` | `bolt://neo4j:7687` | Managed Neo4j (EC2/ECS or AuraDB) URI |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | GPU fleet load balancer URL |
| `DATABASE_URL` | Local Postgres container | RDS Postgres (Multi-AZ) endpoint |

**Rule for code generation:** Never hardcode any of the above. Always read from environment/config, defaulting to a `.env`/settings object pattern (e.g., pydantic Settings in FastAPI).

## 4. Repository Structure (expected)

> **Current state:** Sprint 1 scaffold. All services run via `docker compose up -d --build`. Key commands (see README Quickstart): `docker compose exec backend python scripts/smoke_test.py` (parity smoke test), `docker compose exec backend alembic upgrade head` (migrations — also run automatically on backend start), `docker compose exec neo4j cypher-shell -u neo4j -p forgelocal -f /seed/seed.cypher` (graph schema). `/infra` Terraform and real skills/plugins land in later sprints.

```
/frontend        Next.js app (independent ECS Fargate service)
/backend          FastAPI app + agent orchestration + tenant middleware
/skills           Short-lived, stateless functions -> AWS Lambda in prod, MiniStack Lambda locally
/plugins          Long-running/stateful tasks -> ECS tasks in both dev and prod
/infra            Terraform/CDK: VPC, ECS, ALB, RDS, DynamoDB, S3, Cognito, Step Functions, CloudWatch
/graph            Neo4j schema/seed scripts (identical in dev and prod)
docker-compose.yml   Local dev orchestration (frontend, backend, neo4j, ollama, ministack, postgres, redis)
```

## 5. Multi-Tenancy Rules (non-negotiable)

- **Postgres/RDS:** every multi-tenant table has a `tenant_id` column; row-level security (RLS) policies must be applied — never rely on application-layer filtering alone.
- **DynamoDB:** partition key pattern is always `PK = TENANT#<tenant_id>`. Never write an item without this prefix.
- **S3:** object keys always follow `artifacts/<tenant_id>/...`. Never write to a bucket root or a non-tenant-prefixed path.
- **Cognito/JWT:** `tenant_id` is derived from the JWT custom claim in backend middleware on every request — never trust a `tenant_id` passed directly in a request body/query param without cross-checking the JWT.
- **Rate limiting:** agent concurrency and Ollama call limits are enforced per tenant, tiered by plan (Free/Pro/Enterprise). Any new agent/skill/plugin must go through the existing rate limiter, not bypass it.

## 6. Agent Orchestration Model ("Graph Loop Engineering")

- Orchestration = Step Functions state machine with pattern: **orchestrator agent → specialized worker agent(s) → evaluation agent**.
- Async handoffs between states use SQS/SNS; every queue has a corresponding DLQ.
- Skills (short/stateless) → Lambda. Plugins (long-running/stateful, e.g., scrapers/ETL) → ECS tasks. Do not implement a stateful plugin as a Lambda, or a simple stateless skill as an ECS task — this breaks the cost/scaling model.
- Every agent run writes nodes/edges into Neo4j representing the task graph (task → skill/plugin → sub-agent → output).
- Every agent run's output artifact is stored in S3 under the tenant-prefixed path.

## 7. Known MiniStack Limitations (must-read before touching auth)

- **Cognito Lambda triggers (PreSignUp, PostConfirmation) do NOT execute in MiniStack.** These must be tested against a dedicated AWS dev Cognito pool, never assumed working from local tests alone.
- Any other MiniStack gaps discovered during development must be appended here immediately, with the workaround/test strategy used.
- **Cognito user pools are not available in the community MiniStack edition** (the `ministack` service is backed by the `localstack/localstack` image, where Cognito is a licensed feature). `infra/ministack-init/ready.sh` attempts pool creation and warns on failure. Workaround: local auth testing requires a licensed image or a dedicated AWS dev Cognito pool (which is also required for trigger testing per the point above).

## 8. Ollama / Cost Model Rules

- Never call a third-party pay-per-token LLM API as a default/fallback — the platform's cost model assumes self-hosted GPU inference only.
- Model access is tier-gated: larger/more expensive models are reserved for higher plans (Pro/Enterprise). Any new model integration must declare which tiers can access it.
- All Ollama calls must respect the per-tenant concurrency rate limiter — never call Ollama directly from a skill/plugin without going through the shared client wrapper that enforces this.

## 9. CI/CD & Deployment Rules

- Docker images for frontend/backend/skills/plugins are built once and pushed to ECR; the same image is deployed to ECS regardless of environment — never build environment-specific images.
- Deployments use rolling or blue/green strategy with automated rollback on failed health checks.
- Any infra change must go through Terraform/CDK (`/infra`) — never make manual changes in the AWS console for anything that should be reproducible.

## 10. When Generating Code, Always

1. Check whether the change needs a `tenant_id` — if it touches data, it almost certainly does.
2. Check whether the change needs to go through the rate limiter (if it invokes an agent/skill/plugin/Ollama call).
3. Check whether the change belongs in `/skills` (Lambda-style) or `/plugins` (ECS-task-style) based on its runtime characteristics.
4. Use environment variables/config objects for any endpoint, never hardcode `localhost:4566` or real AWS URLs.
5. If touching auth, remember MiniStack cannot test Cognito triggers — flag for AWS dev-pool testing.
6. Update the relevant Sprint doc's checklist and this file if the change introduces a new pattern, limitation, or convention.

## 11. Reference Documents

- `docs/PRD.md` — full product requirements, architecture rationale, success metrics, risks.
- `docs/Sprint1.md` – Local dev environment setup (MiniStack + Docker).
- `docs/Sprint2.md` – Core application, agent orchestration skeleton.
- `docs/Sprint3.md` – Multi-tenancy, isolation, agentic controls.
- `docs/Sprint4.md` – Production AWS provisioning & migration.
- `docs/Sprint5.md` – CI/CD, autoscaling, operational hardening.
