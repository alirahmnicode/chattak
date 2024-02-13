from typing import List
from sqlalchemy import and_, select
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
        contact = get_contact_info(db=db, contact_id=new_contact.id)
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


def create_chat(db: Session, users_id: List[int]):
    dont_exist = False

    for id in users_id:
        chat = (
            db.query(models.Chat)
            .filter(models.Chat.users.any(models.User.id.in_([id])))
            .first()
        )
        if chat is None:
            dont_exist = True

    if dont_exist is None:
        chat = models.Chat()

        for user_id in users_id:
            user = get_object(db=db, model=models.User, id=user_id)
            chat.users.append(user)

        db.add(chat)
        db.commit()
        db.refresh(chat)
    return chat


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
        chat_obj = schemas.ChatRoom(
            id=chat.id,
            target_user_id=target_user_id,
            target_username=target_username,
        )
        chat_list.append(chat_obj)

    return chat_list


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
