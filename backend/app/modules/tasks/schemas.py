import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    title: str = Field(
        description="What the agent should work on.",
        examples=["Summarize the Q3 board deck"],
        min_length=1,
    )


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    title: str
    status: str = Field(description="pending → running → done/failed.", examples=["pending"])
    created_at: datetime
