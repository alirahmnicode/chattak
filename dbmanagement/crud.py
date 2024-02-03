from typing import List
from sqlalchemy.orm import Session
from fastapi.exceptions import RequestValidationError

from . import models, schemas
from utilities.user_auth import get_password_hash


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    new_user = models.User(
        username=user.username, email=user.email, password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_user_by_username(db: Session, username):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_id(db: Session, user_id):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_contacts(db: Session, user_id) -> List[schemas.Contact]:
    user = get_user_by_id(db=db, user_id=user_id)
    contact_list = []

    for contact in user.contacts:
        contact_info = get_contact_info(db=db, contact_id=contact.target_user_id)
        contact_list.append(contact_info)
    return contact_list


def create_user_contact(db: Session, owner_id, contact_id) -> schemas.Contact:
    # check if the target user is not exist in user contacts
    user_contact = db.query(models.Contact).filter(
        models.Contact.owner_id == owner_id, models.Contact.target_user_id == contact_id
    ).first()

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
    user = get_user_by_id(db=db, user_id=contact_id)
    contact = schemas.Contact(
        id=user.id, username=user.username, last_online=user.last_online
    )
    return contact


def save_message(db: Session, message: schemas.MessageCreate) -> schemas.Message:
    new_message = models.Message(**message.dict())
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message


def create_chat(db: Session, user_id: int, target_user_id: int):
    chat = (
        db.query(models.Chat)
        .filter(
            models.Chat.owner_id == user_id,
            models.Chat.target_user_id == target_user_id,
        )
        .first()
    )
    if chat is None:
        chat = models.Chat(owner_id=user_id, target_user_id=target_user_id)
        db.add(chat)
        db.commit()
        db.refresh(chat)
    return chat
