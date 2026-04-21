from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


class DeviceMetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    device_id: str
    cpu_percent: Optional[float] = None
    mem_used_percent: Optional[float] = None
    uptime_seconds: Optional[float] = None
    interface_stats: Optional[dict] = None
    collected_at: datetime


class MetricHistoryEntry(BaseModel):
    collected_at: datetime
    cpu_percent: Optional[float] = None
    mem_used_percent: Optional[float] = None
    uptime_seconds: Optional[float] = None
