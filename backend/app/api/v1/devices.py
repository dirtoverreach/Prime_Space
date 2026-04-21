from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_device_or_404
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceRead, DiscoverRequest, TaskResponse
from app.security.credentials import encrypt

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceRead])
def list_devices(
    platform: str | None = None,
    status: str | None = None,
    site: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Device)
    if platform:
        q = q.filter(Device.platform == platform)
    if status:
        q = q.filter(Device.status == status)
    if site:
        q = q.filter(Device.site == site)
    return q.all()


@router.post("", response_model=DeviceRead, status_code=201)
def create_device(body: DeviceCreate, db: Session = Depends(get_db)):
    existing = db.query(Device).filter(
        (Device.hostname == body.hostname) | (Device.ip_address == body.ip_address)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Device with this hostname or IP already exists")

    from app.services.driver_factory import PLATFORM_TO_NETMIKO
    device = Device(
        hostname=body.hostname,
        ip_address=body.ip_address,
        platform=body.platform,
        username=body.username,
        device_type=PLATFORM_TO_NETMIKO.get(body.platform),
        password_encrypted=encrypt(body.password) if body.password else None,
        enable_secret_encrypted=encrypt(body.enable_secret) if body.enable_secret else None,
        snmp_community_encrypted=encrypt(body.snmp_community) if body.snmp_community else None,
        snmp_version=body.snmp_version,
        site=body.site,
        tags=body.tags or [],
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.get("/{device_id}", response_model=DeviceRead)
def get_device(device: Device = Depends(get_device_or_404)):
    return device


@router.put("/{device_id}", response_model=DeviceRead)
def update_device(body: DeviceUpdate, device: Device = Depends(get_device_or_404), db: Session = Depends(get_db)):
    for field, value in body.model_dump(exclude_none=True).items():
        if field == "password":
            device.password_encrypted = encrypt(value)
        elif field == "enable_secret":
            device.enable_secret_encrypted = encrypt(value)
        elif field == "snmp_community":
            device.snmp_community_encrypted = encrypt(value)
        else:
            setattr(device, field, value)
    db.commit()
    db.refresh(device)
    return device


@router.delete("/{device_id}", status_code=204)
def delete_device(device: Device = Depends(get_device_or_404), db: Session = Depends(get_db)):
    db.delete(device)
    db.commit()


@router.post("/discover", response_model=TaskResponse)
def discover_devices(body: DiscoverRequest, db: Session = Depends(get_db)):
    from app.tasks.discovery_tasks import discover_network
    task = discover_network.delay(
        body.cidr, body.username, body.password,
        body.enable_secret or "", body.snmp_community or "public", body.snmp_version
    )
    return TaskResponse(task_id=task.id)


@router.post("/{device_id}/sync", response_model=TaskResponse)
def sync_device(device: Device = Depends(get_device_or_404)):
    from app.tasks.discovery_tasks import sync_device_facts
    task = sync_device_facts.delay(device.id)
    return TaskResponse(task_id=task.id)


@router.get("/{device_id}/interfaces")
def get_interfaces(device: Device = Depends(get_device_or_404)):
    return device.interfaces


@router.get("/{device_id}/facts")
def get_facts(device: Device = Depends(get_device_or_404)):
    return {
        "hostname": device.hostname,
        "model": device.model,
        "serial_number": device.serial_number,
        "os_version": device.os_version,
        "platform": device.platform,
        "status": device.status,
        "last_seen": device.last_seen,
    }
