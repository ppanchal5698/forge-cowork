from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.db import get_db
from ...core.security import get_current_user
from . import service
from .schemas import AgentRunOut

router = APIRouter(tags=["agents"])


@router.post(
    "/tasks/{task_id}/runs",
    status_code=201,
    response_model=AgentRunOut,
    summary="Start an agent run (Graph Loop) for a task",
    responses={
        401: {"description": "Missing or invalid token"},
        404: {"description": "No such task in your tenant"},
    },
)
def start_run(
    task_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Kicks off the orchestrator→worker→evaluator Step Functions execution for the
    task and returns the run (status `running`). Poll `GET /runs/{run_id}` for progress.
    """
    return service.start(db, user["tenant_id"], task_id)


@router.get(
    "/runs/{run_id}",
    response_model=AgentRunOut,
    summary="Get agent run status/output",
    responses={
        401: {"description": "Missing or invalid token"},
        404: {"description": "No such run in your tenant"},
    },
)
def get_run(
    run_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Returns current run status. On the first poll after the execution finishes, the
    output is stored to S3 (`artifacts/<tenant>/<run>/`), the task graph is written to
    Neo4j, and status flips to `done`; `output_key` then points at the S3 artifact.
    """
    return service.get(db, user["tenant_id"], run_id)
