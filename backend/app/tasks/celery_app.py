from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery = Celery(
    "prime_space",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.discovery_tasks",
        "app.tasks.monitoring_tasks",
        "app.tasks.config_tasks",
        "app.tasks.command_tasks",
        "app.tasks.topology_tasks",
    ],
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

celery.conf.beat_schedule = {
    "poll-all-devices": {
        "task": "app.tasks.monitoring_tasks.poll_all_devices",
        "schedule": settings.snmp_poll_interval_seconds,
    },
    "nightly-config-backup": {
        "task": "app.tasks.config_tasks.backup_all_devices",
        "schedule": crontab(hour=2, minute=0),
    },
}
