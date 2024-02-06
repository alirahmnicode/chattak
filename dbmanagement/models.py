from __future__ import annotations
from typing import List

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Table
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func

from .database import Base


chat_users = Table(
    "chat_users",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("chat_id", ForeignKey("chats.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, index=True, unique=True)
    password = Column(String)
    last_online = Column(DateTime, nullable=True)
    join_date = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship("Message", back_populates="owner")
    chats: Mapped[List[Chat]] = relationship(
        secondary=chat_users, back_populates="users"
    )
    contacts = relationship("Contact", back_populates="owner")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    target_user_id = Column(Integer)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="contacts")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    text = Column(String)
    is_seen = Column(Boolean, default=False)
    date_send = Column(DateTime(timezone=True), server_default=func.now())
    sender_id = Column(Integer, ForeignKey("users.id"))
    chat_id = Column(Integer, ForeignKey("chats.id"))

    owner = relationship("User", back_populates="messages")
    chat = relationship("Chat", back_populates="messages")


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True)

    messages = relationship("Message", back_populates="chat")
    users: Mapped[List[User]] = relationship(
        secondary=chat_users, back_populates="chats"
    )
