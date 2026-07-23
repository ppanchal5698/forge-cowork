from functools import lru_cache

import jwt as pyjwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .aws import client
from .config import settings

# auto_error=False so a missing header is our 401, not FastAPI's 403
bearer = HTTPBearer(
    auto_error=False,
    description="Paste the **id_token** returned by POST /auth/login (not the access token — "
    "only the id token carries the tenant claim).",
)


@lru_cache
def cognito_ids() -> tuple[str, str]:
    """(pool_id, client_id) — from env if set, else discovered by pool name."""
    if settings.cognito_user_pool_id and settings.cognito_client_id:
        return settings.cognito_user_pool_id, settings.cognito_client_id
    idp = client("cognito-idp")
    pools = idp.list_user_pools(MaxResults=60)["UserPools"]
    pool_id = next(p["Id"] for p in pools if p["Name"] == settings.cognito_pool_name)
    clients = idp.list_user_pool_clients(UserPoolId=pool_id, MaxResults=60)["UserPoolClients"]
    return pool_id, clients[0]["ClientId"]


@lru_cache
def _jwk_client(pool_id: str) -> pyjwt.PyJWKClient:
    return pyjwt.PyJWKClient(
        f"{settings.cognito_issuer_base}/{pool_id}/.well-known/jwks.json"
    )


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    if creds is None:
        raise HTTPException(401, "missing bearer token")
    token = creds.credentials
    pool_id, client_id = cognito_ids()
    try:
        key = _jwk_client(pool_id).get_signing_key_from_jwt(token).key
        # ponytail: iss host differs local vs prod; pool-scoped JWKS already pins the
        # issuer via signature — add strict iss check when prod URLs are fixed (Sprint 4)
        claims = pyjwt.decode(
            token, key, algorithms=["RS256"], audience=client_id, options={"verify_iss": False}
        )
    except Exception:
        raise HTTPException(401, "invalid token")
    tenant_id = claims.get("custom:tenant_id")
    if not tenant_id:
        raise HTTPException(401, "token missing tenant_id claim")
    return {"sub": claims["sub"], "email": claims.get("email"), "tenant_id": tenant_id}
