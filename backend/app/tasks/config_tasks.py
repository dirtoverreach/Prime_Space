from app.tasks.celery_app import celery
from app.database import SessionLocal
from app.models.device import Device
from app.models.config_backup import ConfigTemplate


@celery.task(name="app.tasks.config_tasks.backup_all_devices")
def backup_all_devices():
    db = SessionLocal()
    try:
        devices = db.query(Device).filter(Device.status == "reachable").all()
        results = {}
        for device in devices:
            try:
                results[device.id] = backup_device_internal(device, db)
            except Exception as e:
                results[device.id] = {"error": str(e)}
        return results
    finally:
        db.close()


@celery.task(name="app.tasks.config_tasks.backup_device")
def backup_device(device_id: str, label: str | None = None):
    db = SessionLocal()
    try:
        device = db.query(Device).get(device_id)
        if not device:
            return {"error": "device not found"}
        return backup_device_internal(device, db, label=label)
    finally:
        db.close()


def backup_device_internal(device, db, label=None) -> dict:
    from app.services.config_service import pull_config
    backup = pull_config(device, db, source="scheduled", label=label)
    return {"backup_id": backup.id, "checksum": backup.checksum}


@celery.task(name="app.tasks.config_tasks.push_config_to_devices")
def push_config_to_devices(device_ids: list[str], config_snippet: str):
    db = SessionLocal()
    results = {}
    try:
        for device_id in device_ids:
            device = db.query(Device).get(device_id)
            if not device:
                results[device_id] = {"error": "not found"}
                continue
            try:
                from app.services.config_service import push_config
                output = push_config(device, config_snippet)
                results[device_id] = {"status": "success", "output": output}
            except Exception as e:
                results[device_id] = {"status": "error", "error": str(e)}
    finally:
        db.close()
    return results


@celery.task(name="app.tasks.config_tasks.deploy_template")
def deploy_template(template_id: str, device_ids: list[str], variables: dict):
    db = SessionLocal()
    try:
        template = db.query(ConfigTemplate).get(template_id)
        if not template:
            return {"error": "template not found"}
        from app.services.config_service import render_template, push_config
        rendered = render_template(template, variables)
        results = {}
        for device_id in device_ids:
            device = db.query(Device).get(device_id)
            if not device:
                results[device_id] = {"error": "not found"}
                continue
            try:
                output = push_config(device, rendered)
                results[device_id] = {"status": "success", "output": output}
            except Exception as e:
                results[device_id] = {"status": "error", "error": str(e)}
        return results
    finally:
        db.close()
