import asyncio
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Query
import json

router = APIRouter(prefix="/ws", tags=["websocket"])

_active_connections: Set[WebSocket] = set()
_channels: dict[str, Set[WebSocket]] = {}


async def connect_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    _active_connections.add(websocket)


async def disconnect_websocket(websocket: WebSocket) -> None:
    _active_connections.discard(websocket)
    for conns in _channels.values():
        conns.discard(websocket)


async def broadcast_event(job_id: str, event_data: dict) -> None:
    message = json.dumps(event_data, default=str)
    dead = set()
    for ws in _active_connections:
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)
    for ws in dead:
        await disconnect_websocket(ws)


@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket, job_id: str = Query(None)):
    await connect_websocket(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                cmd = msg.get("type")
                if cmd == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "job_id": job_id}))
            except Exception:
                pass
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        await disconnect_websocket(websocket)
