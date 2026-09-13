"""Celery application, broker config, and Beat schedule (T026, R-09).

Defines the Celery app used by both workers and Beat scheduler.
Three queues: default, sync, deploy.
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from src.shared.config.settings import get_settings

settings = get_settings()

app = Celery("mist_ops")

app.config_from_object(
    {
        "broker_url": settings.redis_url,
        "result_backend": settings.redis_url,
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "timezone": "UTC",
        "enable_utc": True,
        "task_track_started": True,
        "task_acks_late": True,
        "worker_prefetch_multiplier": 1,
        "task_default_queue": "default",
        "task_routes": {
            "src.worker.tasks.sync_tasks.*": {"queue": "sync"},
            "src.worker.tasks.deploy_tasks.*": {"queue": "deploy"},
            "src.worker.tasks.notify_tasks.*": {"queue": "default"},
            "src.worker.tasks.audit_tasks.*": {"queue": "default"},
            "src.worker.tasks.check_tasks.*": {"queue": "deploy"},
        },
    }
)

# Register task modules
app.conf.include = [
    "src.worker.tasks.sync_tasks",
    "src.worker.tasks.deploy_tasks",
    "src.worker.tasks.notify_tasks",
    "src.worker.tasks.audit_tasks",
    "src.worker.tasks.check_tasks",
]

# Beat schedule — periodic tasks
app.conf.beat_schedule = {
    "inventory-sync-every-5-min": {
        "task": "src.worker.tasks.sync_tasks.sync_all_inventory",
        "schedule": settings.sync_interval_seconds,
        "options": {"queue": "sync"},
    },
    "retention-cleanup-nightly": {
        "task": "src.worker.tasks.audit_tasks.run_retention_cleanup",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "default"},
    },
    "daily-backup": {
        "task": "src.worker.tasks.sync_tasks.run_daily_backup",
        "schedule": crontab(hour=3, minute=0),
        "options": {"queue": "default"},
    },
}
