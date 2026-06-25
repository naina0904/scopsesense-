import asyncio
import logging

from fastapi import (
    FastAPI,
    WebSocket,
    Depends,
    HTTPException,
    Request
)

from fastapi.responses import JSONResponse

from backend.auth.jwt_utils import get_current_user
from backend.api.auth_routes import router as auth_router
from backend.api.confirmation_routes import router as confirmation_router

from fastapi.middleware.cors import (
    CORSMiddleware
)

from backend.api.routes import (
    router
)

from backend.api.delay_analysis_routes import (
    router as delay_analysis_router
)

from backend.websocket.manager import (
    manager
)

from backend.websocket.progress_manager import (
    progress_manager
)

# ===================================
# DATABASE
# ===================================

from backend.storage.database import (
    engine,
    Base
)

from backend.storage.models import *
from backend.storage.models_extended import *


# ===================================
# APP
# ===================================

app = FastAPI(
    title="ScopeSense v2"
)


# ===================================
# CREATE DATABASE TABLES
# ===================================

Base.metadata.create_all(
    bind=engine
)


# ===================================
# CORS
# ===================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ===================================
# GLOBAL EXCEPTION HANDLER
# ===================================

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "message": str(exc)}
    )

# ===================================
# ROUTES
# ===================================

app.include_router(router)
app.include_router(delay_analysis_router)
app.include_router(auth_router)
app.include_router(confirmation_router)


# ===================================
# WEBSOCKET
# ===================================

@app.websocket("/ws/audit/{task_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    task_id: str
):
    await manager.connect(
        task_id,
        websocket
    )

    await progress_manager.replay(
        task_id
    )

    try:
        while True:
            await websocket.receive_text()
    except Exception:
        manager.disconnect(
            task_id
        )


# ===================================
# REDIS PUB/SUB → WEBSOCKET BRIDGE
# ===================================
# The Celery worker cannot directly push to WebSockets
# because it runs in a separate process with no event
# loop. Instead it publishes to a Redis channel.
# This coroutine subscribes and forwards events to
# the appropriate WebSocket connection.

async def _redis_pubsub_listener():
    """
    Subscribe to all scopesense:ws:* channels and
    forward published JSON payloads to WebSocket clients.
    Runs as a background task for the lifetime of the API.
    """

    import json
    import os
    import asyncio

    try:
        import redis.asyncio as aioredis
    except ImportError:
        # redis package not available — skip
        return

    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    while True:
        try:
            client = aioredis.Redis.from_url(
                url,
                decode_responses=True
            )

            pubsub = client.pubsub()

            await pubsub.psubscribe("scopesense:ws:*")

            # Use extremely stable polling loop instead of buggy listen() async generator
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0
                )

                if message is None:
                    await asyncio.sleep(0.1)
                    continue

                channel: str = message.get(
                    "channel",
                    ""
                )

                # Extract task_id from channel name:
                # "scopesense:ws:<task_id>"
                parts = channel.split(":", 2)

                if len(parts) < 3:
                    continue

                task_id = parts[2]

                try:
                    payload = json.loads(
                        message["data"]
                    )
                    await manager.send_message(
                        task_id,
                        payload
                    )
                except Exception:
                    pass

        except Exception as e:
            # Gracefully log connection issues and retry
            print(f"[REDIS PUBSUB] Error encountered: {e}. Retrying in 2 seconds...")
            await asyncio.sleep(2)


# ===================================
# STARTUP
# ===================================

@app.on_event("startup")
async def startup_event():
    print(
        "Starting ScopeSense v2 backend..."
    )

    # Register the running event loop so that
    # progress_manager can schedule WebSocket sends
    # from sync contexts (e.g., threads).
    loop = asyncio.get_event_loop()
    progress_manager.register_event_loop(loop)

    # Start Redis Pub/Sub → WebSocket bridge
    asyncio.create_task(
        _redis_pubsub_listener()
    )


# ===================================
# ROOT
# ===================================

@app.get("/")
def root():
    return {
        "message":
            "ScopeSense v2 API Running"
    }
