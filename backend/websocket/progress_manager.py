import asyncio
import base64
import json
import os
import threading
from datetime import datetime, date

from backend.websocket.manager import (
    manager
)

try:

    import redis as redis_lib

except Exception:

    redis_lib = None


# =================================================
# JSON ENCODER
# =================================================
# Handles types that the standard encoder cannot
# serialize: datetime → ISO-8601 string, bytes →
# base64 string, anything else → str().

class _SafeEncoder(json.JSONEncoder):

    def default(self, obj):

        if isinstance(obj, (datetime, date)):
            return obj.isoformat()

        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode("utf-8")

        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


def _safe_dumps(obj):
    """json.dumps using _SafeEncoder."""
    return json.dumps(obj, cls=_SafeEncoder)


# =================================================
# PROGRESS MANAGER
# =================================================
# Designed for a split-process Docker architecture:
#
#   backend-api  (FastAPI / event loop running)
#   backend-worker (Celery / sync, no event loop)
#
# State is stored in Redis so both processes share it.
# Events are published via Redis Pub/Sub so the API
# process can push them to WebSocket clients.
# =================================================


class ProgressManager:

    # =================================================
    # INIT
    # =================================================

    def __init__(self):

        # In-memory fallback (single-process mode)
        self._progress_local = {}
        self._logs_local = {}
        self._results_local = {}
        self._events_local = {}

        # Event loop reference — set by the API process
        # after startup so that sync callers can schedule
        # coroutines safely.
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_lock = threading.Lock()

        # Redis connection
        self.redis_client = None
        self._init_redis()

    def _init_redis(self):

        if not redis_lib:
            return

        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        try:

            client = redis_lib.Redis.from_url(
                url,
                decode_responses=True
            )

            client.ping()

            self.redis_client = client

        except Exception:

            self.redis_client = None

    # =================================================
    # EVENT LOOP REGISTRATION
    # =================================================
    # Call this from the FastAPI startup event so the
    # progress manager knows which loop is running and
    # can schedule WebSocket sends from sync contexts.

    def register_event_loop(
        self,
        loop: asyncio.AbstractEventLoop
    ):

        with self._loop_lock:
            self._loop = loop

    # =================================================
    # UPDATE PROGRESS
    # =================================================

    def update(

        self,

        task_id,

        stage,

        percentage
    ):

        data = {
            "stage": str(stage),
            "percentage": percentage
        }

        self._set_redis(
            self._progress_key(task_id),
            data
        )

        self._progress_local[task_id] = data

        payload = {
            "type":    "progress_update",
            "task_id": task_id,
            "progress": data
        }

        self._broadcast(task_id, payload)

    # =================================================
    # ADD LOG
    # =================================================

    def add_log(

        self,

        task_id,

        message
    ):

        if task_id not in self._logs_local:
            self._logs_local[task_id] = []

        self._logs_local[task_id].append(message)

        # Append to Redis list
        if self.redis_client:

            try:

                key = self._log_key(task_id)

                self.redis_client.rpush(key, message)
                self.redis_client.expire(key, 86400)

            except Exception:
                pass

        payload = {
            "type":    "log_update",
            "task_id": task_id,
            "message": message
        }

        self._broadcast(task_id, payload)

    # =================================================
    # GET PROGRESS
    # =================================================

    def get_progress(

        self,

        task_id
    ):

        progress = self._get_redis(
            self._progress_key(task_id)
        )

        if not progress:

            progress = self._progress_local.get(
                task_id,
                {"stage": "Pending", "percentage": 0}
            )

        # Logs
        if self.redis_client:

            try:

                logs = self.redis_client.lrange(
                    self._log_key(task_id),
                    0,
                    -1
                )

            except Exception:

                logs = self._logs_local.get(task_id, [])

        else:

            logs = self._logs_local.get(task_id, [])

        # Result
        result = self._get_redis(
            self._result_key(task_id)
        )

        if not result:
            result = self._results_local.get(task_id)

        return {
            "progress": progress,
            "logs":     logs,
            "result":   result,
            "events":   self.get_events(task_id)
        }

    # =================================================
    # SET RESULT
    # =================================================

    def set_result(

        self,

        task_id,

        result
    ):

        self._results_local[task_id] = result

        self._set_redis(
            self._result_key(task_id),
            result
        )

        payload = {
            "type":    "audit_result",
            "task_id": task_id,
            "result":  result
        }

        self._broadcast(task_id, payload)

    # =================================================
    # EVENT REPLAY
    # =================================================

    def get_events(

        self,

        task_id
    ):

        if self.redis_client:

            try:

                raw = self.redis_client.lrange(
                    self._event_key(task_id),
                    0,
                    -1
                )

                return [
                    json.loads(e)
                    for e in raw
                ]

            except Exception:
                pass

        return self._events_local.get(task_id, [])

    async def replay(

        self,

        task_id
    ):

        for event in self.get_events(task_id):

            await manager.send_message(
                task_id,
                event
            )

    # =================================================
    # BROADCAST
    # =================================================

    def _broadcast(

        self,

        task_id,

        payload
    ):

        self._store_event(task_id, payload)

        # ----------------------------------------------------------
        # Strategy 1: Running event loop in THIS process (API side).
        # ----------------------------------------------------------
        with self._loop_lock:
            loop = self._loop

        if loop and loop.is_running():

            asyncio.run_coroutine_threadsafe(
                manager.send_message(task_id, payload),
                loop
            )

            return

        # ----------------------------------------------------------
        # Strategy 2: Worker process — no event loop.
        # Publish to Redis Pub/Sub channel; the API process
        # subscribes and forwards to WebSocket clients.
        # ----------------------------------------------------------
        if self.redis_client:

            try:

                self.redis_client.publish(
                    f"scopesense:ws:{task_id}",
                    _safe_dumps(payload)
                )

            except Exception as e:
                print(f"[PROGRESS_MANAGER] Redis publish error: {e}")

    def _store_event(

        self,

        task_id,

        payload
    ):

        if task_id not in self._events_local:
            self._events_local[task_id] = []

        self._events_local[task_id].append(payload)

        if self.redis_client:

            try:

                key = self._event_key(task_id)

                self.redis_client.rpush(
                    key,
                    _safe_dumps(payload)
                )

                self.redis_client.ltrim(key, -200, -1)
                self.redis_client.expire(key, 86400)

            except Exception as e:
                print(f"[PROGRESS_MANAGER] _store_event Redis error: {e}")

    # =================================================
    # REDIS HELPERS
    # =================================================

    def _set_redis(self, key, value):

        if not self.redis_client:
            return

        try:

            self.redis_client.set(
                key,
                _safe_dumps(value),
                ex=86400
            )

        except Exception:
            pass

    def _get_redis(self, key):

        if not self.redis_client:
            return None

        try:

            raw = self.redis_client.get(key)

            return json.loads(raw) if raw else None

        except Exception:

            return None

    def _safe_dumps(self, obj):
        """Instance-level alias for module-level _safe_dumps."""
        return _safe_dumps(obj)

    # =================================================
    # KEY HELPERS
    # =================================================

    def _progress_key(self, task_id):
        return f"scopesense:progress:{task_id}"

    def _log_key(self, task_id):
        return f"scopesense:logs:{task_id}"

    def _result_key(self, task_id):
        return f"scopesense:result:{task_id}"

    def _event_key(self, task_id):
        return f"scopesense:audit_events:{task_id}"


progress_manager = ProgressManager()
