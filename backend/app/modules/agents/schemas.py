import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AgentRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    task_id: uuid.UUID
    status: str = Field(description="queued → running → done/failed.", examples=["running"])
    step: str | None = Field(description="Last state entered.", examples=["worker"])
    output_key: str | None = Field(
        description="S3 key of the run output once done.",
        examples=["artifacts/<tenant>/<run>/output.json"],
    )
    created_at: datetime
