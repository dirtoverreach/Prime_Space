from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.command_job import CommandJob
from app.schemas.command_job import CommandJobCreate, CommandJobRead, CommandJobSummary

router = APIRouter(prefix="/commands", tags=["commands"])


@router.post("/jobs", response_model=CommandJobSummary, status_code=202)
def submit_job(body: CommandJobCreate, db: Session = Depends(get_db)):
    job = CommandJob(
        command=body.command,
        target_devices=body.target_devices,
        requested_by=body.requested_by,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    from app.tasks.command_tasks import run_command_job
    task = run_command_job.delay(job.id)
    job.celery_task_id = task.id
    db.commit()
    db.refresh(job)
    return job


@router.get("/jobs", response_model=list[CommandJobSummary])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(CommandJob).order_by(CommandJob.created_at.desc()).limit(100).all()


@router.get("/jobs/{job_id}", response_model=CommandJobRead)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(CommandJob).get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.delete("/jobs/{job_id}", status_code=204)
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(CommandJob).get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status not in ("pending",):
        raise HTTPException(400, f"Cannot cancel job in state: {job.status}")
    job.status = "failed"
    db.commit()
