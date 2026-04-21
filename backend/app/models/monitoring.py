import uuid
from datetime import datetime
from sqlalchemy import String, Enum, DateTime, ForeignKey, Float, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class DeviceMetric(Base):
    __tablename__ = "device_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id: Mapped[str] = mapped_column(String(36), ForeignKey("devices.id"), nullable=False)
    cpu_percent: Mapped[float | None] = mapped_column(Float)
    mem_used_percent: Mapped[float | None] = mapped_column(Float)
    uptime_seconds: Mapped[float | None] = mapped_column(Float)
    interface_stats: Mapped[dict | None] = mapped_column(JSON)
    collected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    device: Mapped["Device"] = relationship(back_populates="metrics")
