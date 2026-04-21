from datetime import datetime
from app.tasks.celery_app import celery
from app.database import SessionLocal
from app.models.device import Device
from app.models.monitoring import DeviceMetric


@celery.task(name="app.tasks.monitoring_tasks.poll_all_devices")
def poll_all_devices():
    db = SessionLocal()
    try:
        devices = db.query(Device).filter(Device.status != "unreachable").all()
        results = {}
        for device in devices:
            try:
                result = _poll_device(device, db)
                results[device.id] = result
            except Exception as e:
                results[device.id] = {"error": str(e)}
        return results
    finally:
        db.close()


@celery.task(name="app.tasks.monitoring_tasks.poll_single_device")
def poll_single_device(device_id: str):
    db = SessionLocal()
    try:
        device = db.query(Device).get(device_id)
        if not device:
            return {"error": "device not found"}
        return _poll_device(device, db)
    finally:
        db.close()


def _poll_device(device, db) -> dict:
    from app.services import snmp_service
    from app.services.alert_service import evaluate_rules

    stats = snmp_service.poll_device(device)
    iface_stats = snmp_service.poll_interfaces(device)

    metric = DeviceMetric(
        device_id=device.id,
        cpu_percent=stats.get("cpu_percent"),
        mem_used_percent=stats.get("mem_used_percent"),
        uptime_seconds=stats.get("uptime_seconds"),
        interface_stats={iface["name"]: iface for iface in iface_stats},
    )
    db.add(metric)

    device.status = "reachable"
    device.last_seen = datetime.utcnow()
    db.commit()

    evaluate_rules(device, stats, db)

    return {
        "device_id": device.id,
        "cpu_percent": stats.get("cpu_percent"),
        "mem_used_percent": stats.get("mem_used_percent"),
        "uptime_seconds": stats.get("uptime_seconds"),
        "interface_count": len(iface_stats),
    }
