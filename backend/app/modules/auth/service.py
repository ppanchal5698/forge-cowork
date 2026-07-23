from fastapi import HTTPException
from sqlalchemy.orm import Session

from ...core.aws import client
from ...core.security import cognito_ids
from ...models import Tenant, User


def signup(db: Session, email: str, password: str, tenant_name: str) -> str:
    idp = client("cognito-idp")
    pool_id, client_id = cognito_ids()
    tenant = Tenant(name=tenant_name)
    db.add(tenant)
    db.flush()
    try:
        resp = idp.sign_up(
            ClientId=client_id,
            Username=email,
            Password=password,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "custom:tenant_id", "Value": str(tenant.id)},
            ],
        )
        # No email verification flow yet — admin-confirm on signup. MiniStack can't run
        # Cognito triggers (CLAUDE.md §7), so the real verification flow needs an AWS dev pool.
        idp.admin_confirm_sign_up(UserPoolId=pool_id, Username=email)
    except idp.exceptions.UsernameExistsException:
        raise HTTPException(409, "email already registered")
    except idp.exceptions.InvalidPasswordException as e:
        raise HTTPException(400, e.response["Error"]["Message"])
    db.add(User(tenant_id=tenant.id, email=email, cognito_sub=resp["UserSub"]))
    db.commit()
    return str(tenant.id)


def login(email: str, password: str) -> dict:
    idp = client("cognito-idp")
    _, client_id = cognito_ids()
    try:
        result = idp.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": email, "PASSWORD": password},
        )["AuthenticationResult"]
    except (idp.exceptions.NotAuthorizedException, idp.exceptions.UserNotFoundException):
        raise HTTPException(401, "invalid credentials")
    return {
        "id_token": result["IdToken"],
        "access_token": result["AccessToken"],
        "refresh_token": result["RefreshToken"],
        "expires_in": result["ExpiresIn"],
    }


def refresh(refresh_token: str) -> dict:
    idp = client("cognito-idp")
    _, client_id = cognito_ids()
    try:
        result = idp.initiate_auth(
            ClientId=client_id,
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={"REFRESH_TOKEN": refresh_token},
        )["AuthenticationResult"]
    except idp.exceptions.NotAuthorizedException:
        raise HTTPException(401, "invalid refresh token")
    return {
        "id_token": result["IdToken"],
        "access_token": result["AccessToken"],
        "expires_in": result["ExpiresIn"],
    }
