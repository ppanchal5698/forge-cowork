from pydantic import BaseModel


class SignupIn(BaseModel):
    email: str
    password: str
    tenant_name: str


class LoginIn(BaseModel):
    email: str
    password: str


class RefreshIn(BaseModel):
    refresh_token: str
