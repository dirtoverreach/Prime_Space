from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.config_backup import ConfigBackup, ConfigTemplate
from app.models.device import Device
from app.schemas.config_backup import (
    ConfigBackupRead, ConfigBackupDetail, BackupRequest, DiffResult,
    ConfigPushRequest, ConfigTemplateCreate, ConfigTemplateUpdate,
    ConfigTemplateRead, TemplateRenderRequest, TemplateDeployRequest,
)
from app.schemas.device import TaskResponse

router = APIRouter(prefix="/configs", tags=["configs"])


@router.get("/backups", response_model=list[ConfigBackupRead])
def list_backups(device_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(ConfigBackup).order_by(ConfigBackup.created_at.desc())
    if device_id:
        q = q.filter(ConfigBackup.device_id == device_id)
    return q.all()


@router.get("/backups/{backup_id}", response_model=ConfigBackupDetail)
def get_backup(backup_id: str, db: Session = Depends(get_db)):
    b = db.query(ConfigBackup).get(backup_id)
    if not b:
        raise HTTPException(404, "Backup not found")
    return b


@router.post("/backups", response_model=TaskResponse, status_code=202)
def trigger_backup(body: BackupRequest, db: Session = Depends(get_db)):
    from app.tasks.config_tasks import backup_device
    task = backup_device.delay(body.device_id, body.label)
    return TaskResponse(task_id=task.id)


@router.delete("/backups/{backup_id}", status_code=204)
def delete_backup(backup_id: str, db: Session = Depends(get_db)):
    b = db.query(ConfigBackup).get(backup_id)
    if not b:
        raise HTTPException(404, "Backup not found")
    db.delete(b)
    db.commit()


@router.get("/diff", response_model=DiffResult)
def diff_backups(a: str, b: str, db: Session = Depends(get_db)):
    backup_a = db.query(ConfigBackup).get(a)
    backup_b = db.query(ConfigBackup).get(b)
    if not backup_a or not backup_b:
        raise HTTPException(404, "One or both backups not found")
    from app.services.config_service import diff_configs
    return diff_configs(backup_a, backup_b)


@router.get("/diff/live/{device_id}", response_model=DiffResult)
def diff_live(device_id: str, db: Session = Depends(get_db)):
    device = db.query(Device).get(device_id)
    if not device:
        raise HTTPException(404, "Device not found")
    latest = db.query(ConfigBackup).filter_by(device_id=device_id).order_by(ConfigBackup.created_at.desc()).first()
    if not latest:
        raise HTTPException(404, "No backup found for device")
    from app.services.config_service import diff_live
    return diff_live(device, latest)


@router.post("/push", response_model=TaskResponse, status_code=202)
def push_config(body: ConfigPushRequest):
    from app.tasks.config_tasks import push_config_to_devices
    task = push_config_to_devices.delay(body.device_ids, body.config_snippet)
    return TaskResponse(task_id=task.id)


@router.get("/templates", response_model=list[ConfigTemplateRead])
def list_templates(db: Session = Depends(get_db)):
    return db.query(ConfigTemplate).all()


@router.post("/templates", response_model=ConfigTemplateRead, status_code=201)
def create_template(body: ConfigTemplateCreate, db: Session = Depends(get_db)):
    t = ConfigTemplate(**body.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.get("/templates/{template_id}", response_model=ConfigTemplateRead)
def get_template(template_id: str, db: Session = Depends(get_db)):
    t = db.query(ConfigTemplate).get(template_id)
    if not t:
        raise HTTPException(404, "Template not found")
    return t


@router.put("/templates/{template_id}", response_model=ConfigTemplateRead)
def update_template(template_id: str, body: ConfigTemplateUpdate, db: Session = Depends(get_db)):
    t = db.query(ConfigTemplate).get(template_id)
    if not t:
        raise HTTPException(404, "Template not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(t, field, value)
    db.commit()
    db.refresh(t)
    return t


@router.delete("/templates/{template_id}", status_code=204)
def delete_template(template_id: str, db: Session = Depends(get_db)):
    t = db.query(ConfigTemplate).get(template_id)
    if not t:
        raise HTTPException(404, "Template not found")
    db.delete(t)
    db.commit()


@router.post("/templates/{template_id}/render")
def render_template(template_id: str, body: TemplateRenderRequest, db: Session = Depends(get_db)):
    t = db.query(ConfigTemplate).get(template_id)
    if not t:
        raise HTTPException(404, "Template not found")
    from app.services.config_service import render_template as _render
    return {"rendered": _render(t, body.variables)}


@router.post("/templates/{template_id}/deploy", response_model=TaskResponse, status_code=202)
def deploy_template(template_id: str, body: TemplateDeployRequest, db: Session = Depends(get_db)):
    from app.tasks.config_tasks import deploy_template as _deploy
    task = _deploy.delay(template_id, body.device_ids, body.variables)
    return TaskResponse(task_id=task.id)
