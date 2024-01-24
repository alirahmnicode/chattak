from typing import Any
from pydantic import BaseModel


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    last_online: str


class Contact(BaseModel):
    id: int
    username: str
    last_online: Any