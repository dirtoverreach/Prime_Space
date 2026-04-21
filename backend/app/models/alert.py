import uuid
from datetime import datetime
from sqlalchemy import String, Text, Enum, DateTime, ForeignKey, Float, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    metric: Mapped[str] = mapped_column(String(100), nullable=False)
    operator: Mapped[str] = mapped_column(
        Enum("gt", "lt", "gte", "lte", name="alert_operator_enum"), nullable=False
    )
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(
        Enum("info", "warning", "critical", name="alert_severity_enum"), default="warning"
    )
    device_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("devices.id"))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    alerts: Mapped[list["Alert"]] = relationship(back_populates="rule", cascade="all, delete-orphan")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id: Mapped[str] = mapped_column(String(36), ForeignKey("alert_rules.id"), nullable=False)
    device_id: Mapped[str] = mapped_column(String(36), ForeignKey("devices.id"), nullable=False)
    metric: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(
        Enum("info", "warning", "critical", name="alert_instance_severity_enum"), default="warning"
    )
    state: Mapped[str] = mapped_column(
        Enum("open", "acknowledged", "resolved", name="alert_state_enum"), default="open"
    )
    triggered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)

    rule: Mapped["AlertRule"] = relationship(back_populates="alerts")
    device: Mapped["Device"] = relationship(back_populates="alerts")
