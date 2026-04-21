from datetime import datetime
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.device import Device
from app.models.monitoring import DeviceMetric
from app.schemas.monitoring import DeviceMetricRead, MetricHistoryEntry
from app.schemas.device import TaskResponse

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# Simple in-memory WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, message: dict):
        import json
        for ws in list(self.active):
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                self.active.remove(ws)


manager = ConnectionManager()


@router.get("/stats", response_model=list[DeviceMetricRead])
def get_all_stats(db: Session = Depends(get_db)):
    devices = db.query(Device).all()
    results = []
    for device in devices:
        latest = db.query(DeviceMetric).filter_by(device_id=device.id).order_by(DeviceMetric.collected_at.desc()).first()
        if latest:
            results.append(latest)
    return results


@router.get("/stats/{device_id}", response_model=DeviceMetricRead)
def get_device_stats(device_id: str, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    metric = db.query(DeviceMetric).filter_by(device_id=device_id).order_by(DeviceMetric.collected_at.desc()).first()
    if not metric:
        raise HTTPException(404, "No metrics found for device")
    return metric


@router.get("/stats/{device_id}/history", response_model=list[MetricHistoryEntry])
def get_metric_history(
    device_id: str,
    metric: str = "cpu_percent",
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(DeviceMetric).filter_by(device_id=device_id).order_by(DeviceMetric.collected_at.asc())
    if from_dt:
        q = q.filter(DeviceMetric.collected_at >= from_dt)
    if to_dt:
        q = q.filter(DeviceMetric.collected_at <= to_dt)
    return [
        MetricHistoryEntry(
            collected_at=m.collected_at,
            cpu_percent=m.cpu_percent,
            mem_used_percent=m.mem_used_percent,
            uptime_seconds=m.uptime_seconds,
        )
        for m in q.all()
    ]


@router.get("/interfaces/{device_id}")
def get_interface_stats(device_id: str, db: Session = Depends(get_db)):
    latest = db.query(DeviceMetric).filter_by(device_id=device_id).order_by(DeviceMetric.collected_at.desc()).first()
    if not latest or not latest.interface_stats:
        return []
    return list(latest.interface_stats.values())


@router.post("/poll/{device_id}", response_model=TaskResponse)
def poll_device(device_id: str):
    from app.tasks.monitoring_tasks import poll_single_device
    task = poll_single_device.delay(device_id)
    return TaskResponse(task_id=task.id)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
