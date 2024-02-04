from datetime import datetime
import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates

from .connection_manager import ConnectionManager
from dbmanagement import crud, schemas
from dependencies.dependencies import get_db
from utilities.user_auth import get_current_user


router = APIRouter()
manager = ConnectionManager()
templates = Jinja2Templates(directory="templates")


@router.get("/pm/{target_user_id}")
async def privet_message(request: Request, target_user_id: int, db=Depends(get_db)):
    token = request.cookies.get("access_token").split(" ")[1]
    user = await get_current_user(token=token, db=db)
    target_user = crud.get_user_by_id(db=db, user_id=target_user_id)

    return templates.TemplateResponse(
        request=request,
        name="privet_message.html",
        context={
            "user": user,
            "target_user": {"id": target_user_id, "username": target_user.username},
        },
    )


@router.websocket("/ws/{current_user_id}/{target_user_id}")
async def privet_message_websocket(
    websocket: WebSocket, current_user_id: int, target_user_id: int, db=Depends(get_db)
):
    """
    The client send message and the target user recieve the message.
    """
    user = crud.get_user_by_id(db=db, user_id=current_user_id)

    await manager.connect(websocket=websocket, user_id=current_user_id)

    try:
        while True:
            data = await websocket.receive_text()
            # create chat object for user and target user 
            user_chat = crud.create_chat(
                db=db, user_id=current_user_id, target_user_id=target_user_id
            )
            target_user_chat = crud.create_chat(
                db=db, user_id=target_user_id, target_user_id=current_user_id
            )
            message = schemas.MessageCreate(
                text=data,
                is_seen=False,
                date_send=datetime.utcnow(),
                owner_id=user.id,
                chat_id=user_chat.id,
            )
            crud.save_message(db=db, message=message)

            is_target_user_is_online = manager.is_user_online(user_id=target_user_id)
            if is_target_user_is_online:
                await manager.send_personal_message(data, target_user_id)

    except WebSocketDisconnect:
        manager.disconnect(user.id)
        await manager.broadcast(f"Client #{user.username} left the chat")



# @router.websocket("/ws/{current_user_id}/{target_user_id}")
# async def privet_message_websocket(
#     websocket: WebSocket, current_user_id: int, target_user_id: int, db=Depends(get_db)
# ):
#     """
#     The client send message and the target user recieve the message.
#     """
#     user = crud.get_user_by_id(db=db, user_id=current_user_id)

#     await manager.connect(websocket=websocket, user_id=current_user_id)

#     try:
#         while True:
#             data = await websocket.receive_text()
#             print(json.loads(data)["message"])
#             # is_target_user_is_online = manager.is_user_online(user_id=target_user_id)
#             # if is_target_user_is_online:
#             #     await manager.send_personal_message(data, target_user_id)

#     except WebSocketDisconnect:
#         manager.disconnect(user.id)
#         await manager.broadcast(f"Client #{user.username} left the chat")