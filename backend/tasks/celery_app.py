import os
from celery import Celery

# =================================================
# CELERY APP
# =================================================

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery = Celery(

    "scopesense",

    broker=REDIS_URL,

    backend=REDIS_URL,

    # Explicitly declare where tasks live so Celery
    # registers them at worker startup regardless of
    # autodiscover behaviour.
    include=["backend.tasks.audit_tasks"]
)

# =================================================
# CELERY CONFIG
# =================================================

celery.conf.update(

    task_serializer="json",

    accept_content=["json"],

    result_serializer="json",

    timezone="UTC",

    enable_utc=True,

    task_track_started=True,

    result_expires=3600,

    worker_send_task_events=True,

    task_send_sent_event=True,
)