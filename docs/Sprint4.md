# Sprint 4 — Production AWS Provisioning & Migration

**Duration:** 2-3 weeks
**Goal:** Provision the production AWS environment via IaC and migrate the application from MiniStack to real AWS with zero code rewrites — only endpoints and credentials change.

## Objectives
1. Define full AWS infrastructure via Terraform or AWS CDK (VPC, ECS, ALB, RDS, DynamoDB, S3, Cognito, Step Functions, CloudWatch).
2. Deploy backend/frontend Docker images (same images as local dev) to ECS Fargate.
3. Cut over agent orchestration from MiniStack Step Functions emulator to real Step Functions/SQS/SNS/EventBridge.
4. Stand up GPU-backed Ollama fleet on EC2/ECS.
5. Validate full parity: same code, different endpoints/credentials.

## Deliverables
- [ ] Terraform/CDK modules: VPC (public subnets: ALB, NAT; private subnets: ECS, RDS, ElastiCache), Security Groups (ALB-only inbound, internal service-to-service).
- [ ] ECS Fargate service: Next.js frontend behind ALB (path/hostname routing), independent autoscaling policy.
- [ ] ECS Fargate service: FastAPI + agents backend behind same ALB (separate target group), same Docker image as dev.
- [ ] Lambda functions deployed for short-lived skills; ECS task definitions for long-running plugins.
- [ ] Step Functions state machines (orchestrator-worker-evaluator) deployed; EventBridge rules for triggering.
- [ ] SQS queues + SNS topics + DLQs provisioned matching local dev topology.
- [ ] RDS Postgres (Multi-AZ) provisioned; Alembic/Flyway migrations run against production DB; RLS policies applied.
- [ ] DynamoDB tables provisioned with same partition key scheme (`TENANT#<tenant_id>`).
- [ ] S3 buckets provisioned with tenant-prefix structure and lifecycle policies per tier (Free/Pro/Enterprise retention).
- [ ] Neo4j deployed on EC2/ECS with EBS volumes, or migrated to AuraDB SaaS.
- [ ] Cognito User Pool with Hosted UI, MFA, social login/SSO; Lambda triggers for tenant provisioning (assign `tenant_id` on signup) — tested here since MiniStack couldn't run real triggers.
- [ ] Secrets Manager + SSM populated with real MCP/Ollama/third-party keys; IAM roles grant ECS/Lambda access (nothing hardcoded in images).
- [ ] CloudWatch + Container Insights configured: logs/metrics/traces for ECS, Lambda, Step Functions, Ollama; per-tenant dashboards and alarms (carried over from Sprint 3 design).
- [ ] GPU-backed EC2/ECS Ollama fleet (G4/G5/G6 instances) with models sized to fit GPU memory.
- [ ] Migration runbook documenting exact steps: endpoint swap, credential rotation, Neo4j/Ollama URL repointing.

## Tasks Breakdown
| # | Task | Owner | Notes |
|---|---|---|---|
| 1 | Write Terraform/CDK for VPC + networking | Dev | Reusable for dev/staging/prod |
| 2 | Provision ECS clusters + Fargate services (frontend, backend) | Dev | Confirm ALB routing works for both |
| 3 | Provision RDS Multi-AZ + run migrations + apply RLS | Dev | Validate against Sprint 3 isolation tests |
| 4 | Provision DynamoDB tables | Dev | Match local partition key scheme exactly |
| 5 | Provision S3 buckets + lifecycle policies | Dev | Match tenant-prefix structure |
| 6 | Deploy Neo4j (EC2/ECS+EBS or AuraDB) | Dev | Decision point: client to confirm self-managed vs. AuraDB |
| 7 | Provision Cognito User Pool + Lambda triggers | Dev | Test PreSignUp/PostConfirmation triggers here (not testable in MiniStack) |
| 8 | Deploy Step Functions, SQS/SNS, EventBridge, Lambda skills, ECS plugin tasks | Dev | Mirror Sprint 2 orchestration design |
| 9 | Provision GPU Ollama fleet + autoscaling | Dev | Validate model VRAM fit and concurrency bounds |
| 10 | Configure Secrets Manager/SSM + IAM roles | Dev | Security review before go-live |
| 11 | Configure CloudWatch dashboards/alarms per tenant | Dev | Carry over Sprint 3 dashboard design |
| 12 | Run full migration rehearsal (staging environment) | Dev + Client | Validate zero-code-change claim end-to-end |
| 13 | Write migration runbook | Dev | Feed into CLAUDE.md |

## Acceptance Criteria
- The exact same Docker images from local dev run successfully in ECS Fargate with only environment variables/endpoints changed.
- End-to-end agent run (signup → task submission → orchestration → artifact storage → task graph in Neo4j) succeeds in production AWS, mirroring local dev behavior.
- Cognito triggers (PreSignUp, PostConfirmation) verified working in real AWS (previously untestable in MiniStack).
- Cross-tenant isolation tests from Sprint 3 pass against real AWS resources.
- GPU fleet successfully serves Ollama inference requests with autoscaling responding to load.

## Dependencies / Blockers
- AWS account(s) and billing set up; IAM permissions for infra provisioning.
- Client decision on Neo4j deployment mode (self-managed vs. AuraDB).
- Client decision on initial Ollama model set and GPU instance sizing/budget.

## Out of Scope (this sprint)
- CI/CD automation (Sprint 5).
- Fine-grained autoscaling tuning beyond initial thresholds (Sprint 5).
