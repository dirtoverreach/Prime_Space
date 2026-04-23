import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.tasks.celery_app import celery
from app.database import SessionLocal
from app.models.device import Device
from app.models.command_job import CommandJob, CommandJobResult


def _run_on_device(device, command: str) -> tuple[str, str, int]:
    """Returns (output, exit_status, duration_ms)."""
    from app.services.ssh_service import run_command
    start = time.time()
    try:
        output = run_command(device, command)
        duration_ms = int((time.time() - start) * 1000)
        return output, "success", duration_ms
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        return str(e), "error", duration_ms


@celery.task(bind=True, name="app.tasks.command_tasks.run_command_job")
def run_command_job(self, job_id: str):
    db = SessionLocal()
    job = None
    try:
        job = db.query(CommandJob).get(job_id)
        if not job:
            return {"error": "job not found"}

        job.status = "running"
        job.celery_task_id = self.request.id
        db.commit()

        devices = db.query(Device).filter(Device.id.in_(job.target_devices)).all()
        if not devices:
            job.status = "failed"
            job.completed_at = datetime.utcnow()
            db.commit()
            return {"error": "no devices found"}

        # Capture device_id as a plain string before threading — SQLAlchemy
        # ORM attributes can expire/corrupt when accessed across threads.
        num_workers = min(len(devices), 20)
        futures: dict = {}
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            for device in devices:
                device_id = str(device.id)  # plain string, not ORM attribute
                futures[executor.submit(_run_on_device, device, job.command)] = device_id

        for future, device_id in futures.items():
            output, exit_status, duration_ms = future.result()
            db.add(CommandJobResult(
                job_id=job.id,
                device_id=device_id,
                output=output,
                exit_status=exit_status,
                duration_ms=duration_ms,
            ))

        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()
        return {"job_id": job_id, "status": "completed", "device_count": len(devices)}

    except Exception as e:
        if job:
            job.status = "failed"
            job.completed_at = datetime.utcnow()
            db.commit()
        return {"error": str(e)}
    finally:
        db.close()
