from functools import lru_cache

import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .aws import client
from .db import get_db
from .models import Tenant, User
from .settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])


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


def get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(401, "missing bearer token")
    token = auth_header.removeprefix("Bearer ")
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


class SignupIn(BaseModel):
    email: str
    password: str
    tenant_name: str


@router.post("/signup", status_code=201)
def signup(body: SignupIn, db: Session = Depends(get_db)):
    idp = client("cognito-idp")
    pool_id, client_id = cognito_ids()
    tenant = Tenant(name=body.tenant_name)
    db.add(tenant)
    db.flush()
    try:
        resp = idp.sign_up(
            ClientId=client_id,
            Username=body.email,
            Password=body.password,
            UserAttributes=[
                {"Name": "email", "Value": body.email},
                {"Name": "custom:tenant_id", "Value": str(tenant.id)},
            ],
        )
        # No email verification flow yet — admin-confirm on signup. MiniStack can't run
        # Cognito triggers (CLAUDE.md §7), so the real verification flow needs an AWS dev pool.
        idp.admin_confirm_sign_up(UserPoolId=pool_id, Username=body.email)
    except idp.exceptions.UsernameExistsException:
        raise HTTPException(409, "email already registered")
    except idp.exceptions.InvalidPasswordException as e:
        raise HTTPException(400, e.response["Error"]["Message"])
    db.add(User(tenant_id=tenant.id, email=body.email, cognito_sub=resp["UserSub"]))
    db.commit()
    return {"tenant_id": str(tenant.id)}


class LoginIn(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(body: LoginIn):
    idp = client("cognito-idp")
    _, client_id = cognito_ids()
    try:
        result = idp.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": body.email, "PASSWORD": body.password},
        )["AuthenticationResult"]
    except (idp.exceptions.NotAuthorizedException, idp.exceptions.UserNotFoundException):
        raise HTTPException(401, "invalid credentials")
    return {
        "id_token": result["IdToken"],
        "access_token": result["AccessToken"],
        "refresh_token": result["RefreshToken"],
        "expires_in": result["ExpiresIn"],
    }


class RefreshIn(BaseModel):
    refresh_token: str


@router.post("/refresh")
def refresh(body: RefreshIn):
    idp = client("cognito-idp")
    _, client_id = cognito_ids()
    try:
        result = idp.initiate_auth(
            ClientId=client_id,
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={"REFRESH_TOKEN": body.refresh_token},
        )["AuthenticationResult"]
    except idp.exceptions.NotAuthorizedException:
        raise HTTPException(401, "invalid refresh token")
    return {
        "id_token": result["IdToken"],
        "access_token": result["AccessToken"],
        "expires_in": result["ExpiresIn"],
    }


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user
