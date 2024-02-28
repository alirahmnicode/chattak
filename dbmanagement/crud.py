from typing import List
from sqlalchemy.orm import Session
from fastapi.exceptions import RequestValidationError

from . import models, schemas
from utilities.user_auth import get_password_hash


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    new_user = models.User(username=user.username, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_user_contacts(db: Session, user_id) -> List[schemas.Contact]:
    user = get_object(db=db, model=models.User, id=user_id)
    contact_list = []

    for contact in user.contacts:
        contact_info = get_contact_info(db=db, contact_id=contact.target_user_id)
        contact_list.append(contact_info)
    return contact_list


def create_user_contact(db: Session, owner_id, contact_id) -> schemas.Contact:
    target_user = get_object(db=db, model=models.User, id=contact_id)

    if target_user is None:
        raise RequestValidationError("Cannot find a user with the id!")

    user_contact = get_object(
        db=db, model=models.Contact, owner_id=owner_id, target_user_id=contact_id
    )

    if user_contact is None:
        new_contact = models.Contact(target_user_id=contact_id, owner_id=owner_id)
        db.add(new_contact)
        db.commit()
        db.refresh(new_contact)
        contact = get_contact_info(db=db, contact_id=contact_id)
        return contact
    else:
        raise RequestValidationError("The contact is already exist!")


def get_contact_info(db: Session, contact_id) -> schemas.Contact:
    user = get_object(db=db, model=models.User, id=contact_id)
    contact = schemas.Contact(
        id=user.id, username=user.username, last_online=user.last_online
    )
    return contact


def save_message(db: Session, message: schemas.Message) -> schemas.Message:
    new_message = models.Message(**message.dict())
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message


def create_chat(db: Session, user_id: int, target_user_id: int) -> int:
    user = get_object(db=db, model=models.User, id=user_id)
    target_user = get_object(db=db, model=models.User, id=target_user_id)

    user_chat_ids = [chat.id for chat in user.chats]
    target_user_chat_ids = [chat.id for chat in target_user.chats]

    shared_chat = list(set(user_chat_ids).intersection(target_user_chat_ids))

    if shared_chat:
        return shared_chat[0]
    else:
        chat = models.Chat()
        chat.users.append(user)
        chat.users.append(target_user)
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return chat.id


def get_user_chats(db: Session, user_id: int) -> List[schemas.ChatRoom]:
    chats = (
        db.query(models.Chat)
        .filter(models.Chat.users.any(models.User.id.in_([user_id])))
        .all()
    )
    chat_list = []

    for chat in chats:
        # find target user
        for user in chat.users:
            if user.id != user_id:
                target_user_id = user.id
                target_username = user.username
                
        # get last chat's message
        last_message = chat.messages[-1].text if chat.messages else ""

        chat_obj = schemas.ChatRoom(
            id=chat.id,
            target_user_id=target_user_id,
            target_username=target_username,
            last_message=last_message,
        )
        chat_list.append(chat_obj)

    return chat_list


def get_user_chat(db: Session, user_id, target_user_id):
    chat = (
        db.query(models.Chat)
        .filter(models.Chat.users.any(models.User.id.in_([user_id, target_user_id])))
        .first()
    )
    target_username = get_object(db=db, model=models.User, id=target_user_id).username
    chat_obj = schemas.ChatRoom(
        id=chat.id,
        target_user_id=target_user_id,
        target_username=target_username,
        last_message="",
    )
    return chat_obj


def get_chat_by_id(db: Session, chat_id: int):
    return db.query(models.Chat).filter_by(id=chat_id).first()


def get_object(db: Session, model, **kwargs):
    """kwargs must be model attributes."""
    return db.query(model).filter_by(**kwargs).first()


def get_objects(db: Session, model, **kwargs):
    """kwargs must be model attributes."""
    return db.query(model).filter_by(**kwargs)


def search_user(db: Session, username: str) -> schemas.User:
    users = db.query(models.User).filter(
        models.User.username.like("%" + username + "%")
    )
    return users


def get_all_user(db: Session):
    return db.query(models.User).all()


def seen_messages(db: Session, chat_id: int, user_id: int) -> bool:
    chat = get_object(db=db, model=models.Chat, id=chat_id)

    if chat:
        for message in chat.messages:
            if message.sender_id != user_id and message.is_seen is False:
                message.is_seen = True
                db.commit()
        return True
    else:
        return False
