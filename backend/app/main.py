from fastapi import FastAPI

from .modules.agents.router import router as agents_router
from .modules.auth.router import router as auth_router
from .modules.tasks.router import router as tasks_router

DESCRIPTION = """
Multi-tenant AI agent platform: tenants run agents/skills/plugins against their own
data, backed by a Neo4j knowledge graph and self-hosted Ollama inference.

## How to use this API

Every protected endpoint expects a Cognito **ID token** as a Bearer token:

1. **POST /auth/signup** — create your tenant + account.
2. **POST /auth/login** — copy the `id_token` from the response.
3. Click **Authorize** (padlock, top right) and paste the `id_token`.
4. Call protected endpoints — try **GET /auth/me** first.
5. Token expired (~1 h)? **POST /auth/refresh** with your `refresh_token`, re-authorize.

## Multi-tenancy

Your `tenant_id` lives inside the verified JWT (`custom:tenant_id` claim) and scopes
every request server-side. Tenant ids sent in request bodies are never trusted.

## Local development

Base URL `http://localhost:8000` · auth backed by the MiniStack Cognito pool
`forge-local` · reset all local state with `POST http://localhost:4566/_ministack/reset?init=1`.
"""

app = FastAPI(
    title="Forge Cowork API",
    version="0.2.0",
    description=DESCRIPTION,
    openapi_tags=[
        {
            "name": "auth",
            "description": "Tenant signup, login, token refresh, and the token probe (`/auth/me`).",
        },
        {"name": "ops", "description": "Health and diagnostics — no auth required."},
    ],
)
app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(agents_router)


@app.get("/health", tags=["ops"], summary="Liveness probe")
def health():
    """Returns `{"status": "ok"}` if the API process is up. No dependencies checked."""
    return {"status": "ok"}
