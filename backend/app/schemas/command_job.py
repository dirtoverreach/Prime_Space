from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


class CommandJobCreate(BaseModel):
    command: str
    target_devices: list[str]
    requested_by: str = "user"


class CommandJobResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    device_id: str
    output: Optional[str] = None
    exit_status: str
    duration_ms: Optional[int] = None
    completed_at: datetime


class CommandJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    command: str
    target_devices: list
    requested_by: str
    celery_task_id: Optional[str] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    results: list[CommandJobResultRead] = []


class CommandJobSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    command: str
    target_devices: list
    requested_by: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
