from pydantic import BaseModel, Field


class SignupIn(BaseModel):
    email: str = Field(
        description="Email address — becomes the Cognito username.",
        examples=["ada@acme.com"],
    )
    password: str = Field(
        description="Must satisfy the Cognito password policy: 8+ characters with upper, lower, digit, and symbol.",
        examples=["Passw0rd!123"],
    )
    tenant_name: str = Field(
        description="Name of the new tenant (organization) created for this account.",
        examples=["acme"],
    )


class SignupOut(BaseModel):
    tenant_id: str = Field(
        description="UUID of the newly created tenant. Also embedded in every JWT as `custom:tenant_id`.",
        examples=["9440bf75-d7b8-481f-b471-36a638ee78a5"],
    )


class LoginIn(BaseModel):
    email: str = Field(examples=["ada@acme.com"])
    password: str = Field(examples=["Passw0rd!123"])


class TokenPair(BaseModel):
    id_token: str = Field(
        description="JWT carrying the `custom:tenant_id` claim — **use this as the Bearer token** on protected endpoints."
    )
    access_token: str = Field(description="Cognito access token (no custom claims).")
    refresh_token: str = Field(description="Long-lived token for POST /auth/refresh.")
    expires_in: int = Field(
        description="Seconds until id/access tokens expire.", examples=[3600]
    )


class RefreshIn(BaseModel):
    refresh_token: str = Field(description="The `refresh_token` returned by /auth/login.")


class RefreshOut(BaseModel):
    id_token: str = Field(description="Fresh id token — replace your Bearer token with this.")
    access_token: str
    expires_in: int = Field(examples=[3600])


class MeOut(BaseModel):
    sub: str = Field(description="Cognito user id.", examples=["c3e0..."])
    email: str | None = Field(examples=["ada@acme.com"])
    tenant_id: str = Field(
        description="Tenant this request is scoped to, taken from the verified JWT — never from request input.",
        examples=["9440bf75-d7b8-481f-b471-36a638ee78a5"],
    )
