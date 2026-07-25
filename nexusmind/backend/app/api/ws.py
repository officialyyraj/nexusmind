"""WebSocket endpoint handlers."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.streaming.ws_manager import get_connection_manager

router = APIRouter()


@router.websocket("/ws/sessions/{session_id}")
async def websocket_session(
    websocket: WebSocket,
    session_id: str,
) -> None:
    """WebSocket endpoint for session streaming."""
    manager = get_connection_manager()
    await manager.connect(websocket, session_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Handle different message types
            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg_type == "subscribe":
                # Client subscribing to specific events
                await websocket.send_json({
                    "type": "subscribed",
                    "events": data.get("events", []),
                })
            else:
                # Echo back for now - actual handling would be implemented
                await websocket.send_json({
                    "type": "echo",
                    "data": data,
                })

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
