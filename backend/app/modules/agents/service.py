import json
import uuid
from functools import lru_cache

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ...core import graph, storage
from ...core.aws import client
from ...models import AgentRun, Artifact, Task

STEPS = ["orchestrator", "worker", "evaluator"]


@lru_cache
def _state_machine_arn() -> str:
    machines = client("stepfunctions").list_state_machines()["stateMachines"]
    return next(m["stateMachineArn"] for m in machines if m["name"] == "graph-loop")


def _run_in_tenant(db: Session, tenant_id: str, run_id: str) -> AgentRun:
    try:
        rid = uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(404, "run not found")
    run = (
        db.query(AgentRun)
        .filter(AgentRun.id == rid, AgentRun.tenant_id == uuid.UUID(tenant_id))
        .first()
    )
    if run is None:
        raise HTTPException(404, "run not found")
    return run


def start(db: Session, tenant_id: str, task_id: str) -> AgentRun:
    try:
        tid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(404, "task not found")
    task = (
        db.query(Task).filter(Task.id == tid, Task.tenant_id == uuid.UUID(tenant_id)).first()
    )
    if task is None:
        raise HTTPException(404, "task not found")

    run = AgentRun(tenant_id=task.tenant_id, task_id=task.id, status="running", step=STEPS[0])
    db.add(run)
    db.commit()
    db.refresh(run)

    execution = client("stepfunctions").start_execution(
        stateMachineArn=_state_machine_arn(),
        name=f"run-{run.id}",
        input=json.dumps({"title": task.title, "tenant_id": tenant_id, "run_id": str(run.id)}),
    )
    run.execution_arn = execution["executionArn"]
    task.status = "running"
    db.commit()
    db.refresh(run)
    return run


def get(db: Session, tenant_id: str, run_id: str) -> AgentRun:
    run = _run_in_tenant(db, tenant_id, run_id)
    # ponytail: finalize-on-poll — no background worker yet. A completion callback
    # (EventBridge/SF) or a poller plugin replaces this in Sprint 3.
    if run.status == "running" and run.execution_arn:
        _sync(db, run)
    return run


def _sync(db: Session, run: AgentRun):
    d = client("stepfunctions").describe_execution(executionArn=run.execution_arn)
    status = d["status"]
    if status == "RUNNING":
        return
    if status != "SUCCEEDED":
        run.status = "failed"
        db.commit()
        return

    out = json.loads(d["output"])
    task = db.query(Task).filter(Task.id == run.task_id).first()
    key = storage.put_artifact(
        str(run.tenant_id),
        str(run.id),
        "output.json",
        json.dumps(out).encode(),
        content_type="application/json",
    )
    graph.write_run_graph(
        str(run.tenant_id),
        str(run.task_id),
        task.title if task else "",
        str(run.id),
        STEPS,
        key,
    )
    db.add(Artifact(tenant_id=run.tenant_id, run_id=run.id, s3_key=key))
    run.status = "done"
    run.step = STEPS[-1]
    run.output_key = key
    if task:
        task.status = "done"
    db.commit()
