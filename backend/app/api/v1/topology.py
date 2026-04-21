from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_device_or_404
from app.models.device import Device
from app.schemas.device import TaskResponse
from app.services.topology_service import build_topology_graph

router = APIRouter(prefix="/topology", tags=["topology"])


@router.get("")
def get_topology(db: Session = Depends(get_db)):
    return build_topology_graph(db)


@router.post("/discover", response_model=TaskResponse)
def discover_topology(db: Session = Depends(get_db)):
    from app.tasks.celery_app import celery

    @celery.task(name="topology_discover_all")
    def _discover_all():
        from app.database import SessionLocal
        from app.services.topology_service import discover_neighbors, update_interface_neighbors
        inner_db = SessionLocal()
        try:
            devices = inner_db.query(Device).filter(Device.status == "reachable").all()
            for device in devices:
                try:
                    neighbors = discover_neighbors(device)
                    update_interface_neighbors(device, neighbors, inner_db)
                except Exception:
                    pass
        finally:
            inner_db.close()

    task = _discover_all.delay()
    return TaskResponse(task_id=task.id)


@router.get("/device/{device_id}/neighbors")
def get_neighbors(device: Device = Depends(get_device_or_404)):
    from app.services.topology_service import discover_neighbors
    return discover_neighbors(device)
