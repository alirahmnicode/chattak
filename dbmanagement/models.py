from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, index=True, unique=True)
    email = Column(String, unique=True)
    password = Column(String)
    last_online = Column(DateTime, nullable=True)
    join_date = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship("Message", back_populates="owner")
    chat_rooms = relationship("Chat", back_populates="owner")
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
    owner_id = Column(Integer, ForeignKey("users.id"))
    chat_id = Column(Integer, ForeignKey("chats.id"))

    owner = relationship("User", back_populates="messages")
    chat = relationship("Chat", back_populates="messages")


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    target_user_id = Column(Integer)

    messages = relationship("Message", back_populates="chat")
    owner = relationship("User", back_populates="chat_rooms")
