import uuid
from datetime import datetime
from sqlalchemy import String, Text, Enum, DateTime, ForeignKey, JSON, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CommandJob(Base):
    __tablename__ = "command_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    command: Mapped[str] = mapped_column(Text, nullable=False)
    target_devices: Mapped[list] = mapped_column(JSON, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(255), default="system")
    celery_task_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        Enum("pending", "running", "completed", "failed", name="job_status_enum"), default="pending"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    results: Mapped[list["CommandJobResult"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class CommandJobResult(Base):
    __tablename__ = "command_job_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("command_jobs.id"), nullable=False)
    device_id: Mapped[str] = mapped_column(String(36), ForeignKey("devices.id"), nullable=False)
    output: Mapped[str | None] = mapped_column(Text)
    exit_status: Mapped[str] = mapped_column(
        Enum("success", "error", "timeout", name="result_exit_status_enum"), default="success"
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    completed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    job: Mapped["CommandJob"] = relationship(back_populates="results")
    device: Mapped["Device"] = relationship(back_populates="command_results")
