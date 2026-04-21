import uuid
from datetime import datetime
from sqlalchemy import String, Text, Enum, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ConfigBackup(Base):
    __tablename__ = "config_backups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id: Mapped[str] = mapped_column(String(36), ForeignKey("devices.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(
        Enum("scheduled", "manual", "pre_change", name="backup_source_enum"), default="manual"
    )
    label: Mapped[str | None] = mapped_column(String(255))
    created_by: Mapped[str] = mapped_column(String(255), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    device: Mapped["Device"] = relationship(back_populates="config_backups")


class ConfigTemplate(Base):
    __tablename__ = "config_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    platform: Mapped[str] = mapped_column(
        Enum("junos", "cisco_ios", "cisco_xe", "all", name="template_platform_enum"), default="all"
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[dict | None] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
