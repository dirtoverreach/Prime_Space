from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


class InterfaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    device_id: str
    name: str
    description: Optional[str] = None
    admin_status: str
    oper_status: str
    speed_mbps: Optional[int] = None
    mtu: Optional[int] = None
    mac_address: Optional[str] = None
    neighbor_device_id: Optional[str] = None
    neighbor_interface: Optional[str] = None


class DeviceBase(BaseModel):
    hostname: str
    ip_address: str
    platform: str
    username: str
    site: Optional[str] = None
    tags: Optional[list[str]] = []
    snmp_version: str = "v2c"


class DeviceCreate(DeviceBase):
    password: Optional[str] = None
    enable_secret: Optional[str] = None
    snmp_community: Optional[str] = None


class DeviceUpdate(BaseModel):
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    platform: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    enable_secret: Optional[str] = None
    snmp_community: Optional[str] = None
    site: Optional[str] = None
    tags: Optional[list[str]] = None
    snmp_version: Optional[str] = None


class DeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    hostname: str
    ip_address: str
    platform: str
    username: str
    device_type: Optional[str] = None
    snmp_version: str
    status: str
    last_seen: Optional[datetime] = None
    last_backup: Optional[datetime] = None
    serial_number: Optional[str] = None
    model: Optional[str] = None
    os_version: Optional[str] = None
    site: Optional[str] = None
    tags: Optional[list] = []
    created_at: datetime
    updated_at: datetime
    interfaces: list[InterfaceRead] = []


class DiscoverRequest(BaseModel):
    cidr: str
    username: str
    password: str
    enable_secret: Optional[str] = None
    snmp_community: Optional[str] = None
    snmp_version: str = "v2c"


class TaskResponse(BaseModel):
    task_id: str
    status: str = "pending"
