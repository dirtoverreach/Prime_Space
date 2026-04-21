from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


class AlertRuleBase(BaseModel):
    name: str
    metric: str
    operator: str
    threshold: float
    severity: str = "warning"
    device_id: Optional[str] = None
    enabled: bool = True


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    metric: Optional[str] = None
    operator: Optional[str] = None
    threshold: Optional[float] = None
    severity: Optional[str] = None
    device_id: Optional[str] = None
    enabled: Optional[bool] = None


class AlertRuleRead(AlertRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    rule_id: str
    device_id: str
    metric: str
    value: float
    message: Optional[str] = None
    severity: str
    state: str
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
