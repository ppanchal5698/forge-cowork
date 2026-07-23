import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ...models import Task, User


def _user_id(db: Session, tenant_id: uuid.UUID, cognito_sub: str) -> uuid.UUID:
    user = (
        db.query(User)
        .filter(User.tenant_id == tenant_id, User.cognito_sub == cognito_sub)
        .first()
    )
    if user is None:
        raise HTTPException(404, "user not found in tenant")
    return user.id


def create(db: Session, tenant_id: str, cognito_sub: str, title: str) -> Task:
    tid = uuid.UUID(tenant_id)
    task = Task(tenant_id=tid, user_id=_user_id(db, tid, cognito_sub), title=title)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def list_for_tenant(db: Session, tenant_id: str) -> list[Task]:
    return (
        db.query(Task)
        .filter(Task.tenant_id == uuid.UUID(tenant_id))
        .order_by(Task.created_at.desc())
        .all()
    )


def get(db: Session, tenant_id: str, task_id: str) -> Task:
    try:
        tid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(404, "task not found")
    # tenant_id in filter is the isolation boundary — never trust the path id alone
    task = (
        db.query(Task)
        .filter(Task.id == tid, Task.tenant_id == uuid.UUID(tenant_id))
        .first()
    )
    if task is None:
        raise HTTPException(404, "task not found")
    return task
