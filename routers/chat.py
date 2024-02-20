from datetime import datetime
from typing import Annotated, List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Request,
    status,
)
from fastapi.templating import Jinja2Templates

from .connection_manager import ConnectionManager
from dbmanagement import crud, models, schemas
from dependencies.dependencies import get_db
from utilities.user_auth import get_current_user


router = APIRouter()
manager = ConnectionManager()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_model=List[schemas.ChatRoom])
def get_user_chats(
    current_user: Annotated[schemas.User, Depends(get_current_user)], db=Depends(get_db)
):
    user_chats = crud.get_user_chats(db=db, user_id=current_user.id)
    return user_chats


@router.get("/user/{target_user_id}", response_model=schemas.ChatRoom)
def get_user_chat(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
    target_user_id: int,
    db=Depends(get_db),
):
    chat_room = crud.get_user_chat(
        db=db, user_id=current_user.id, target_user_id=target_user_id
    )
    return chat_room


@router.get("/messages/", response_model=List[schemas.Message])
async def get_chat_messages(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
    chat_id: int,
    db=Depends(get_db),
):
    user_chat_ids = [chat.id for chat in current_user.chats]

    if chat_id in user_chat_ids:
        chat = crud.get_object(db=db, model=models.Chat, id=chat_id)
        return chat.messages
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/pm/{target_user_id}")
async def privet_message(request: Request, target_user_id: int, db=Depends(get_db)):
    token = request.cookies.get("access_token").split(" ")[1]
    user = await get_current_user(token=token, db=db)
    target_user = crud.get_object(db=db, model=models.User, id=target_user_id)

    return templates.TemplateResponse(
        request=request,
        name="privet_message.html",
        context={
            "user": user,
            "target_user": {"id": target_user_id, "username": target_user.username},
        },
    )


@router.websocket("/server/check_connection/{current_user_id}/{target_user_id}")
async def is_user_online(
    websocket: WebSocket, current_user_id: int, target_user_id: int
):
    await manager.set_connection_socket(websocket=websocket, user_id=current_user_id)
    is_online = manager.is_user_online(target_user_id)
    await websocket.send_text(f"{is_online}")
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        if is_online:
            await manager.send_connection_info(f"False", target_user_id)


@router.websocket("/server/connect/{user_id}/{target_user_id}")
async def chat_websocket(
    websocket: WebSocket, user_id: int, target_user_id: int, db=Depends(get_db)
):
    """
    The client send message and the target user receive the message.
    message, receiver_id
    """

    await manager.set_chat_socket(
        websocket=websocket, user_id=user_id, target_user_id=target_user_id
    )

    try:
        while True:
            sender_user = crud.get_object(db=db, model=models.User, id=user_id)
            data = await websocket.receive_json()
            # create chat object for user and target user
            message_text = data["message"]
            receiver_id = int(data["receiver_id"])
            sender_id = int(data["sender_id"])
            chat_obj = crud.create_chat(db=db, users_id=[user_id, receiver_id])

            message = schemas.Message(
                text=message_text,
                is_seen=False,
                date_send=datetime.utcnow(),
                sender_id=sender_id,
                chat_id=chat_obj.id,
            )
            crud.save_message(db=db, message=message)

            user_notification_socket = manager.user_has_notification_socket(
                target_user_id=target_user_id
            )
            user_chat_socket = manager.has_user_chat_socket(
                user_id=user_id, target_user_id=target_user_id
            )

            if user_chat_socket:
                await manager.send_personal_message(message_text, receiver_id, user_id)
            elif user_notification_socket:
                await manager.send_notification(
                    text=message_text,
                    receiver_id=receiver_id,
                    sender_id=sender_id,
                    sender_username=sender_user.username,
                )

    except WebSocketDisconnect:
        manager.disconnect(user_id)


@router.websocket("/server/notification/{user_id}")
async def notification_socket(websocket: WebSocket, user_id: int):
    await manager.set_notification_socket(websocket=websocket, user_id=user_id)

    try:
        while True:
            await websocket.receive_text()
    except ConnectionError:
        pass
