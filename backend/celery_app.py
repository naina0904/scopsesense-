# =================================================
# CELERY APP — CANONICAL SINGLETON
# =================================================
# This module is the single source of truth for the
# Celery application instance. All imports must
# reference backend.tasks.celery_app to avoid
# creating a duplicate Celery app which breaks task
# routing and result tracking.
# =================================================

from backend.tasks.celery_app import celery  # noqa: F401 — re-export

__all__ = ["celery"]