from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List
import json
from datetime import datetime

from app.core.database import async_session_maker
from app.core.security import decode_token
from app.models import User, ChatRoom, Message
from sqlalchemy import select


# Connection manager
class ConnectionManager:
    def __init__(self):
        # room_id -> set of websockets
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # websocket -> user_id
        self.user_connections: Dict[WebSocket, int] = {}

    async def connect(self, websocket: WebSocket, room_id: int, user_id: int):
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        
        self.active_connections[room_id].append(websocket)
        self.user_connections[websocket] = user_id

    def disconnect(self, websocket: WebSocket, room_id: int):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
            
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        
        if websocket in self.user_connections:
            del self.user_connections[websocket]

    async def broadcast(self, room_id: int, message: dict, exclude_websocket: WebSocket = None):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                if connection != exclude_websocket:
                    try:
                        await connection.send_json(message)
                    except:
                        pass


manager = ConnectionManager()


async def get_websocket_current_user(websocket: WebSocket) -> User:
    """Authenticate WebSocket connection via token query param."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        raise Exception("Missing token")
    
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001)
        raise Exception("Invalid token")
    
    username = payload.get("sub")
    if not username:
        await websocket.close(code=4001)
        raise Exception("Invalid token")
    
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            await websocket.close(code=4001)
            raise Exception("User not found or inactive")
        
        return user


async def save_message_to_db(room_id: int, sender_id: int, content: str, message_type: str = "text"):
    """Save message to database."""
    async with async_session_maker() as session:
        # Update room timestamp
        result = await session.execute(select(ChatRoom).where(ChatRoom.id == room_id))
        room = result.scalar_one_or_none()
        
        if room:
            room.updated_at = datetime.utcnow()
        
        # Create message
        message = Message(
            room_id=room_id,
            sender_id=sender_id,
            content=content,
            message_type=message_type
        )
        
        session.add(message)
        await session.commit()
        
        return message


async def websocket_endpoint(websocket: WebSocket, room_id: int):
    """WebSocket endpoint for real-time chat."""
    user = None
    
    try:
        # Authenticate
        user = await get_websocket_current_user(websocket)
        
        # Verify room access
        async with async_session_maker() as session:
            result = await session.execute(select(ChatRoom).where(ChatRoom.id == room_id))
            room = result.scalar_one_or_none()
            
            if not room:
                await websocket.send_json({"error": "Chat room not found"})
                await websocket.close(code=4004)
                return
            
            if room.buyer_id != user.id and room.seller_id != user.id:
                await websocket.send_json({"error": "Not authorized"})
                await websocket.close(code=4003)
                return
        
        # Connect
        await manager.connect(websocket, room_id, user.id)
        
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "content": "Connected to chat",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Listen for messages
        while True:
            try:
                # Use receive() with timeout for heartbeat
                msg = await websocket.receive_text()
            except Exception:
                # Connection closed
                break
            
            try:
                message_data = json.loads(msg)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
                continue
            
            # Handle ping
            if message_data.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
                continue
            
            msg_type = message_data.get("type", "text")
            content = message_data.get("content", "")
            
            if not content:
                continue
            
            # Save to DB
            message = await save_message_to_db(room_id, user.id, content, msg_type)
            
            # Broadcast to room
            broadcast_data = {
                "id": message.id,
                "type": msg_type,
                "content": content,
                "sender_id": user.id,
                "sender_username": user.username,
                "timestamp": message.created_at.isoformat()
            }
            
            await manager.broadcast(room_id, broadcast_data, exclude_websocket=websocket)
            
            # Also send to sender for confirmation
            await websocket.send_json({
                "status": "sent",
                "message_id": message.id,
                **broadcast_data
            })
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if user:
            manager.disconnect(websocket, room_id)
