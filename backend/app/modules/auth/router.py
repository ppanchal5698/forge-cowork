from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.db import get_db
from ...core.security import get_current_user
from . import service
from .schemas import LoginIn, RefreshIn, SignupIn

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", status_code=201)
def signup(body: SignupIn, db: Session = Depends(get_db)):
    return {"tenant_id": service.signup(db, body.email, body.password, body.tenant_name)}


@router.post("/login")
def login(body: LoginIn):
    return service.login(body.email, body.password)


@router.post("/refresh")
def refresh(body: RefreshIn):
    return service.refresh(body.refresh_token)


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user
