# Sprint 1 — Foundations: Local Dev Environment (MiniStack + Docker)

**Duration:** 2 weeks
**Goal:** Stand up the full local sandbox so all future development happens against MiniStack-emulated AWS services with real Postgres and local Neo4j/Ollama — establishing parity from day one.

## Objectives
1. Single `docker-compose.yml` brings up: Next.js frontend, FastAPI backend, Neo4j, Ollama, MiniStack, Postgres, Redis.
2. Backend uses boto3/AWS SDK pointed at MiniStack's single-port endpoint (`http://localhost:4566`).
3. Baseline repo structure supports the same Docker image used later in ECS (no dev-only code paths).

## Deliverables
- [ ] `docker-compose.yml` with services: `frontend`, `backend`, `neo4j`, `ollama`, `ministack`, `postgres`, `redis`.
- [ ] `.env.example` with shared variable names (`AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_ENDPOINT_URL`, `NEO4J_URI`, `OLLAMA_BASE_URL`) used identically in dev and prod.
- [ ] MiniStack S3 bucket(s) created with production-matching names and key structure (e.g., `artifacts/<tenant_id>/...`).
- [ ] MiniStack RDS emulation (real Postgres container) with initial schema via Alembic migration `0001_init`.
- [ ] MiniStack DynamoDB table(s) created for agent session state / conversation graphs (composite key `PK = TENANT#<tenant_id>`).
- [ ] MiniStack Cognito user pool configured (Hosted UI stub, JWT issuance) for local login testing.
- [ ] MiniStack SQS queues + SNS topics for orchestrator→worker handoff, including a DLQ.
- [ ] MiniStack Secrets Manager + SSM Parameter Store populated with dummy MCP/Ollama/API keys.
- [ ] MiniStack CloudWatch Logs emulation verified (log format matches what will be pushed to AWS).
- [ ] Neo4j container running with a seed script for task-graph / knowledge-graph schema.
- [ ] Ollama container running with at least one pulled model, reachable from FastAPI backend.

## Tasks Breakdown
| # | Task | Owner | Notes |
|---|---|---|---|
| 1 | Scaffold monorepo (`/frontend`, `/backend`, `/infra`, `/skills`) | Dev | Shared Docker base images |
| 2 | Write `docker-compose.yml` + Dockerfiles for frontend/backend | Dev | Same images reused in ECS later |
| 3 | Configure MiniStack container with S3, RDS, DynamoDB, Cognito, SQS/SNS, Secrets Manager, SSM, CloudWatch Logs, Step Functions, Lambda | Dev | Single endpoint `localhost:4566` |
| 4 | Wire FastAPI boto3 clients to MiniStack endpoint via env var | Dev | No hardcoded endpoints in code |
| 5 | Create Postgres schema + Alembic migration baseline | Dev | Include `tenant_id` columns from the start |
| 6 | Stand up Neo4j container + seed graph schema | Dev | Task graphs, agent relationships |
| 7 | Stand up Ollama container + pull baseline model | Dev | Confirm GPU passthrough works if local GPU available |
| 8 | Smoke-test Next.js → FastAPI → MiniStack S3/DynamoDB round trip | Dev | End-to-end "hello world" artifact write/read |
| 9 | Document known MiniStack limitations (e.g., Cognito triggers not executed) | Dev | Feed into CLAUDE.md |

## Acceptance Criteria
- `docker-compose up` starts all services with zero manual steps beyond `.env` setup.
- A test script can create an S3 object, write/read a DynamoDB item, and query Postgres — all via MiniStack — using the same SDK calls that will run in production.
- Neo4j and Ollama are reachable from the FastAPI backend container by hostname.
- Documented list of MiniStack gaps vs. real AWS (starting with Cognito Lambda triggers).

## Dependencies / Blockers
- Docker Desktop / Docker Engine with sufficient resources (GPU passthrough optional but recommended for Ollama).
- MiniStack license/setup (community or licensed tier as required).

## Out of Scope (this sprint)
- Production AWS provisioning (Sprint 4).
- Multi-tenant rate limiting logic (Sprint 3).
- CI/CD pipeline (Sprint 5).
