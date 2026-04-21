from app.tasks.celery_app import celery


@celery.task(name="app.tasks.topology_tasks.discover_all_neighbors")
def discover_all_neighbors():
    from app.database import SessionLocal
    from app.models.device import Device
    from app.services.topology_service import discover_neighbors, update_interface_neighbors

    db = SessionLocal()
    results = {}
    try:
        devices = db.query(Device).filter(Device.status == "reachable").all()
        for device in devices:
            try:
                neighbors = discover_neighbors(device)
                update_interface_neighbors(device, neighbors, db)
                results[device.hostname] = {"neighbors": len(neighbors)}
            except Exception as e:
                results[device.hostname] = {"error": str(e)}
        return results
    finally:
        db.close()
