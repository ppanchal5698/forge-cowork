# Forge Cowork

Multi-tenant "Claude Cowork"-style agentic SaaS platform: tenants run AI agents/skills/plugins against their own data, backed by a Neo4j knowledge graph and self-hosted GPU Ollama inference. See [CLAUDE.md](CLAUDE.md) and [docs/PRD.md](docs/PRD.md) for full architecture.

## Branching Model (git-flow)

| Branch | Purpose | Merges from | Merges to |
|---|---|---|---|
| `main` | Production. Every commit is deployable; releases are tagged (`vX.Y.Z`). Protected — PR only. | `release/*`, `hotfix/*` | — |
| `develop` | Integration branch and default PR target. Always builds. | `feature/*`, `release/*`, `hotfix/*` | `release/*` |
| `feature/<ticket>-<desc>` | One feature/task. Branch off `develop`, PR back to `develop`, delete after merge. | `develop` | `develop` |
| `release/vX.Y.Z` | Release stabilization: version bumps, final fixes only. | `develop` | `main` + back-merge to `develop` |
| `hotfix/vX.Y.Z` | Urgent production fix. Branch off `main`. | `main` | `main` + back-merge to `develop` |

Rules:

- No direct pushes to `main` or `develop` — all changes land via pull request.
- PRs target `develop` unless it's a release or hotfix.
- Sprint work (see `docs/Sprint1-5.md`) maps to `feature/sprint<N>-<task>` branches.
