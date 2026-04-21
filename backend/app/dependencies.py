from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.device import Device


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_device_or_404(device_id: str, db: Session = Depends(get_db)) -> Device:
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device
