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


@router.websocket("/{current_user_id}/{target_user_id}")
async def privet_message_websocket(
    websocket: WebSocket, current_user_id: int, target_user_id: int, db=Depends(get_db)
):
    """
    The client send message and the target user recieve the message.
    """
    user = crud.get_object(db=db, model=models.User, id=current_user_id)

    await manager.connect(websocket=websocket, user_id=current_user_id)

    try:
        while True:
            data = await websocket.receive_text()
            # create chat object for user and target user
            chat_obj = crud.create_chat(
                db=db, users_id=[current_user_id, target_user_id]
            )

            message = schemas.Message(
                text=data,
                is_seen=False,
                date_send=datetime.utcnow(),
                sender_id=user.id,
                chat_id=chat_obj.id,
            )
            crud.save_message(db=db, message=message)

            is_target_user_is_online = manager.is_user_online(user_id=target_user_id)
            if is_target_user_is_online:
                await manager.send_personal_message(data, target_user_id)

    except WebSocketDisconnect:
        manager.disconnect(user.id)


@router.websocket("/check_connection/{current_user_id}/{target_user_id}")
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
