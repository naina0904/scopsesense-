import json
import os

try:

    import redis as redis_lib

except Exception:

    redis_lib = None


# =================================================
# TASK TRACKER
# =================================================
# Lightweight status store backed by Redis so both
# the API and Worker containers share state.
# The in-memory dict is kept as a fallback for
# single-process execution.
# =================================================

_TASK_STATUS_LOCAL = {}

_redis_client = None


def _get_redis():

    global _redis_client

    if _redis_client is not None:
        return _redis_client

    if not redis_lib:
        return None

    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    try:

        client = redis_lib.Redis.from_url(
            url,
            decode_responses=True
        )

        client.ping()

        _redis_client = client

        return _redis_client

    except Exception:

        return None


def _task_key(task_id: str) -> str:

    return f"scopesense:task_status:{task_id}"


def update_task_status(

    task_id,

    status
):
    """
    Update task status in Redis (and local fallback).
    Safe to call from a sync Celery worker — no event
    loop required.
    """

    _TASK_STATUS_LOCAL[task_id] = status

    r = _get_redis()

    if r:

        try:

            r.set(
                _task_key(task_id),
                json.dumps(status),
                ex=86400
            )

        except Exception:
            pass


def get_task_status(

    task_id
):
    """
    Retrieve task status from Redis or local fallback.
    """

    r = _get_redis()

    if r:

        try:

            raw = r.get(_task_key(task_id))

            if raw:
                return json.loads(raw)

        except Exception:
            pass

    return _TASK_STATUS_LOCAL.get(task_id, "Pending")