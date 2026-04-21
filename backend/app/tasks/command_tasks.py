from datetime import datetime
from app.tasks.celery_app import celery
from app.database import SessionLocal
from app.models.device import Device
from app.models.command_job import CommandJob, CommandJobResult


@celery.task(bind=True, name="app.tasks.command_tasks.run_command_job")
def run_command_job(self, job_id: str):
    import time
    from nornir import InitNornir
    from nornir_netmiko.tasks import netmiko_send_command
    from app.nornir_utils.inventory_plugin import DBInventory

    db = SessionLocal()
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

        inventory = DBInventory(devices)
        nr = InitNornir(runner={"plugin": "threaded", "options": {"num_workers": min(len(devices), 20)}})
        nr.inventory = inventory.load()

        start = time.time()
        results = nr.run(task=netmiko_send_command, command_string=job.command)
        elapsed_ms = int((time.time() - start) * 1000)

        for device in devices:
            result = results.get(device.hostname)
            if result and not result.failed:
                output = str(result[0].result)
                exit_status = "success"
            elif result and result.failed:
                output = str(result.exception) if result.exception else "Error"
                exit_status = "error"
            else:
                output = "No result"
                exit_status = "error"

            job_result = CommandJobResult(
                job_id=job.id,
                device_id=device.id,
                output=output,
                exit_status=exit_status,
                duration_ms=elapsed_ms,
            )
            db.add(job_result)

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
