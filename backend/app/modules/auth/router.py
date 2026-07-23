from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.db import get_db
from ...core.security import get_current_user
from . import service
from .schemas import LoginIn, MeOut, RefreshIn, RefreshOut, SignupIn, SignupOut, TokenPair

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    status_code=201,
    response_model=SignupOut,
    summary="Create a tenant and its first user",
    responses={
        400: {"description": "Password rejected by the Cognito password policy"},
        409: {"description": "Email already registered"},
    },
)
def signup(body: SignupIn, db: Session = Depends(get_db)):
    """Creates a new **tenant** (organization) and registers the user in Cognito
    with the tenant id embedded as a custom JWT claim.

    The account is immediately usable — call `/auth/login` next.
    """
    return {"tenant_id": service.signup(db, body.email, body.password, body.tenant_name)}


@router.post(
    "/login",
    response_model=TokenPair,
    summary="Exchange credentials for tokens",
    responses={401: {"description": "Invalid credentials"}},
)
def login(body: LoginIn):
    """Authenticates against Cognito and returns three tokens.

    Copy the **id_token** into the *Authorize* dialog (padlock, top right)
    to call protected endpoints from this page.
    """
    return service.login(body.email, body.password)


@router.post(
    "/refresh",
    response_model=RefreshOut,
    summary="Refresh expired tokens",
    responses={401: {"description": "Invalid or expired refresh token"}},
)
def refresh(body: RefreshIn):
    """Exchanges a `refresh_token` for fresh id/access tokens.

    The refresh token itself stays valid and is not rotated.
    """
    return service.refresh(body.refresh_token)


@router.get(
    "/me",
    response_model=MeOut,
    summary="Who am I? (verifies your token)",
    responses={401: {"description": "Missing, invalid, or expired token"}},
)
def me(user: dict = Depends(get_current_user)):
    """Returns the identity and tenant encoded in your Bearer token.

    Use this to confirm your token works and to see which tenant
    your requests are scoped to.
    """
    return user
