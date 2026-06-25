from fastapi import WebSocket

import base64
import json
from datetime import datetime, date


class _SafeEncoder(json.JSONEncoder):
    """Handles datetime and bytes so WebSocket sends never fail silently."""

    def default(self, obj):

        if isinstance(obj, (datetime, date)):
            return obj.isoformat()

        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode("utf-8")

        try:
            return super().default(obj)
        except TypeError:
            return str(obj)


class ConnectionManager:

    # =================================================
    # INIT
    # =================================================

    def __init__(self):

        self.active_connections = {}

    # =================================================
    # CONNECT
    # =================================================

    async def connect(

        self,

        task_id,

        websocket: WebSocket
    ):

        await websocket.accept()

        if task_id not in self.active_connections:

            self.active_connections[
                task_id
            ] = []

        self.active_connections[
            task_id
        ].append(websocket)

    # =================================================
    # DISCONNECT
    # =================================================

    def disconnect(

        self,

        task_id
    ):

        self.active_connections.pop(

            task_id,

            None
        )

    # =================================================
    # SEND MESSAGE
    # =================================================

    async def send_message(

        self,

        task_id,

        message
    ):

        websockets = (

            self.active_connections.get(
                task_id,
                []
            )
        )

        disconnected = []

        for websocket in websockets:

            try:

                await websocket.send_text(

                    json.dumps(
                        message,
                        cls=_SafeEncoder
                    )
                )

            except:

                disconnected.append(
                    websocket
                )

        if disconnected:

            self.active_connections[
                task_id
            ] = [

                websocket

                for websocket in websockets

                if websocket not in disconnected
            ]

            if not self.active_connections[
                task_id
            ]:

                self.disconnect(
                    task_id
                )


manager = ConnectionManager()
