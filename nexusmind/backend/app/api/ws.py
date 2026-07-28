"""WebSocket endpoint handlers."""

import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.streaming.ws_manager import get_connection_manager
from app.utils.security import (
    decode_access_token_strict,
    ExpiredTokenError,
    InvalidTokenError,
    MalformedTokenError,
)
from app.db.database import async_session_maker
from app.db.session import Session

router = APIRouter()

# WebSocket close codes
WS_CLOSE_NORMAL = 1000
WS_CLOSE_UNAUTHORIZED = 4001
WS_CLOSE_FORBIDDEN = 4003
WS_CLOSE_NOT_FOUND = 4004
WS_CLOSE_INTERNAL_ERROR = 4011


async def authenticate_websocket(
    websocket: WebSocket,
    session_id: str,
) -> tuple[bool, int, str | None]:
    """
    Authenticate WebSocket connection.
    
    Returns:
        tuple: (success, close_code, user_id or error message)
    """
    # Extract token from query parameters
    token = websocket.query_params.get("token")
    
    if not token:
        return False, WS_CLOSE_UNAUTHORIZED, "Missing authentication token"
    
    # Validate JWT token
    try:
        payload = decode_access_token_strict(token)
    except ExpiredTokenError:
        return False, WS_CLOSE_UNAUTHORIZED, "Token has expired"
    except MalformedTokenError:
        return False, WS_CLOSE_UNAUTHORIZED, "Invalid token format"
    except InvalidTokenError as e:
        return False, WS_CLOSE_UNAUTHORIZED, f"Invalid token: {str(e)}"
    
    # Get user ID from token
    user_id = payload.get("sub")
    if not user_id:
        return False, WS_CLOSE_UNAUTHORIZED, "Invalid token payload"
    
    # Validate session_id format
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return False, WS_CLOSE_NOT_FOUND, "Invalid session ID format"
    
    # Verify session exists and user owns it
    async for db in async_session_maker():
        result = await db.execute(
            select(Session).where(Session.id == session_uuid)
        )
        session = result.scalar_one_or_none()
        
        if session is None:
            return False, WS_CLOSE_NOT_FOUND, "Session not found"
        
        if session.user_id is None:
            # No owner required for sessions without user
            return True, WS_CLOSE_NORMAL, user_id
        
        if str(session.user_id) != user_id:
            return False, WS_CLOSE_FORBIDDEN, "Access denied: you do not own this session"
        
        return True, WS_CLOSE_NORMAL, user_id
    
    return False, WS_CLOSE_INTERNAL_ERROR, "Database connection error"


@router.websocket("/ws/sessions/{session_id}")
async def websocket_session(
    websocket: WebSocket,
    session_id: str,
) -> None:
    """WebSocket endpoint for session streaming with authentication."""
    
    # Authenticate before accepting connection
    auth_success, close_code, auth_result = await authenticate_websocket(
        websocket, session_id
    )
    
    if not auth_success:
        # Reject connection with appropriate close code
        await websocket.close(code=close_code, reason=auth_result)
        return
    
    # Connection authenticated - proceed with session
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
