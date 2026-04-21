from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


class ConfigBackupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    device_id: str
    checksum: str
    source: str
    label: Optional[str] = None
    created_by: str
    created_at: datetime


class ConfigBackupDetail(ConfigBackupRead):
    content: str


class BackupRequest(BaseModel):
    device_id: str
    label: Optional[str] = None
    source: str = "manual"


class DiffResult(BaseModel):
    unified_diff: str
    lines_added: int
    lines_removed: int


class ConfigPushRequest(BaseModel):
    device_ids: list[str]
    config_snippet: str


class ConfigTemplateBase(BaseModel):
    name: str
    platform: str = "all"
    body: str
    variables: Optional[dict] = {}


class ConfigTemplateCreate(ConfigTemplateBase):
    pass


class ConfigTemplateUpdate(BaseModel):
    name: Optional[str] = None
    platform: Optional[str] = None
    body: Optional[str] = None
    variables: Optional[dict] = None


class ConfigTemplateRead(ConfigTemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class TemplateRenderRequest(BaseModel):
    variables: dict


class TemplateDeployRequest(BaseModel):
    device_ids: list[str]
    variables: dict
