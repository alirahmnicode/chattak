from typing import Any
from pydantic import BaseModel


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    last_online: Any


class Contact(BaseModel):
    id: int
    username: str
    last_online: Any


class MessageBase(BaseModel):
    text: str
    is_seen: bool
    date_send: Any


class Message(MessageBase):
    sender_id: int
    chat_id: int


class UserChat(BaseModel):
    """id and username is for target user not current user"""
    user_id: int
    username: str