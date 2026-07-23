from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.db import get_db
from ...core.security import get_current_user
from . import service
from .schemas import TaskCreate, TaskOut

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "",
    status_code=201,
    response_model=TaskOut,
    summary="Create a task for your tenant",
    responses={401: {"description": "Missing or invalid token"}},
)
def create_task(
    body: TaskCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Creates a task owned by the calling user, scoped to their tenant.

    `tenant_id` and owner come from your verified token — not from the request body.
    """
    return service.create(db, user["tenant_id"], user["sub"], body.title)


@router.get(
    "",
    response_model=list[TaskOut],
    summary="List your tenant's tasks",
    responses={401: {"description": "Missing or invalid token"}},
)
def list_tasks(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Returns every task belonging to your tenant, newest first."""
    return service.list_for_tenant(db, user["tenant_id"])


@router.get(
    "/{task_id}",
    response_model=TaskOut,
    summary="Get one task by id",
    responses={
        401: {"description": "Missing or invalid token"},
        404: {"description": "No such task in your tenant"},
    },
)
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Fetches a single task. Returns 404 if it belongs to a different tenant —
    ids from other tenants are indistinguishable from nonexistent ones.
    """
    return service.get(db, user["tenant_id"], task_id)
