import json
from jose import jwt, JWTError
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.connection_manager import manager
from app.core.security import SECRET_KEY, ALGORITHM
from app.db.database import AsyncSessionLocal  # session factory
from app.models.message import Message
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    """
    WebSocket connection endpoint.
    Client must connect to: ws://<host>/api/v1/ws?token=<TOKEN>
    TOKEN can be either 'Bearer <token>' or just the token.
    """
    # 1) Validate token and extract user_id
    if token is None:
        await websocket.close(code=1008)
        return

    token_value = token
    if token.startswith("Bearer "):
        token_value = token.split(" ", 1)[1]

    try:
        payload = jwt.decode(token_value, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, Exception):
        await websocket.close(code=1008)
        return

    # 2) Accept and register connection
    await manager.connect(user_id, websocket)

    try:
        # Keep the connection alive and handle incoming messages
        while True:
            text = await websocket.receive_text()
            try:
                data = json.loads(text)
            except Exception:
                # ignore bad JSON
                continue

            receiver_id = data.get("receiver_id")
            content = data.get("content", "").strip()
            if not receiver_id or not content:
                continue

            # 3) Save message into DB (create a new async session per message)
            async with AsyncSessionLocal() as db:  # type: AsyncSession
                new_msg = Message(sender_id=user_id, receiver_id=receiver_id, content=content)
                db.add(new_msg)
                await db.commit()
                await db.refresh(new_msg)

                out = {
                    "id": new_msg.id,
                    "sender_id": new_msg.sender_id,
                    "receiver_id": new_msg.receiver_id,
                    "content": new_msg.content,
                    "timestamp": new_msg.timestamp.isoformat()
                }

            # 4) Send to receiver if they are connected
            await manager.send_personal_message(json.dumps(out), receiver_id)

            # 5) Echo to the sender (so their UI shows the sent message immediately)
            await manager.send_personal_message(json.dumps(out), user_id)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception:
        # ensure cleanup on unexpected errors
        manager.disconnect(user_id)
        try:
            await websocket.close()
        except Exception:
            pass
