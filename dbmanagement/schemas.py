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


class ChatRoom(BaseModel):
    id: int
    target_user_id: int
    target_username: str
    last_message: str
