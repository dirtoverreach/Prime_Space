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
def discover_topology():
    from app.tasks.topology_tasks import discover_all_neighbors
    task = discover_all_neighbors.delay()
    return TaskResponse(task_id=task.id)


@router.get("/device/{device_id}/neighbors")
def get_neighbors(device: Device = Depends(get_device_or_404)):
    from app.services.topology_service import discover_neighbors
    return discover_neighbors(device)
