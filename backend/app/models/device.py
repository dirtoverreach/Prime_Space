import uuid
from datetime import datetime
from sqlalchemy import String, Text, Enum, DateTime, ForeignKey, JSON, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hostname: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    platform: Mapped[str] = mapped_column(
        Enum("junos", "cisco_ios", "cisco_xe", "openwrt", name="platform_enum"), nullable=False
    )
    device_type: Mapped[str | None] = mapped_column(String(100))
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    password_encrypted: Mapped[str | None] = mapped_column(Text)
    enable_secret_encrypted: Mapped[str | None] = mapped_column(Text)
    snmp_community_encrypted: Mapped[str | None] = mapped_column(Text)
    snmp_version: Mapped[str] = mapped_column(
        Enum("v2c", "v3", name="snmp_version_enum"), default="v2c"
    )
    status: Mapped[str] = mapped_column(
        Enum("reachable", "unreachable", "unknown", name="device_status_enum"), default="unknown"
    )
    last_seen: Mapped[datetime | None] = mapped_column(DateTime)
    last_backup: Mapped[datetime | None] = mapped_column(DateTime)
    system_hostname: Mapped[str | None] = mapped_column(String(255))
    serial_number: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(100))
    os_version: Mapped[str | None] = mapped_column(String(255))
    site: Mapped[str | None] = mapped_column(String(255))
    tags: Mapped[list | None] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    interfaces: Mapped[list["Interface"]] = relationship(back_populates="device", cascade="all, delete-orphan", foreign_keys="Interface.device_id")
    config_backups: Mapped[list["ConfigBackup"]] = relationship(back_populates="device", cascade="all, delete-orphan")
    command_results: Mapped[list["CommandJobResult"]] = relationship(back_populates="device")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="device", cascade="all, delete-orphan")
    metrics: Mapped[list["DeviceMetric"]] = relationship(back_populates="device", cascade="all, delete-orphan")


class Interface(Base):
    __tablename__ = "interfaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id: Mapped[str] = mapped_column(String(36), ForeignKey("devices.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    admin_status: Mapped[str] = mapped_column(
        Enum("up", "down", name="if_admin_status_enum"), default="up"
    )
    oper_status: Mapped[str] = mapped_column(
        Enum("up", "down", name="if_oper_status_enum"), default="down"
    )
    speed_mbps: Mapped[int | None] = mapped_column(Integer)
    mtu: Mapped[int | None] = mapped_column(Integer)
    mac_address: Mapped[str | None] = mapped_column(String(20))
    neighbor_device_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("devices.id"))
    neighbor_interface: Mapped[str | None] = mapped_column(String(100))

    device: Mapped["Device"] = relationship(back_populates="interfaces", foreign_keys=[device_id])
