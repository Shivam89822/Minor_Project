from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, nullable=True)
    password = Column(String)

from sqlalchemy import Column, Integer, String, ForeignKey


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    user_email = Column(String, ForeignKey("users.email"))

from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_url = Column(String)

    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    user_email = Column(String, ForeignKey("users.email"))


class Assistant(Base):
    __tablename__ = "assistants"
    __table_args__ = {"sqlite_autoincrement": True}

    id = Column(Integer, primary_key=True, index=True)
    assistant_id = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    status = Column(String, default="training")
    source_count = Column(Integer, default=0)
    user_email = Column(String, ForeignKey("users.email"))
    last_error = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship(
        "ChatMessage",
        backref="assistant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = {"sqlite_autoincrement": True}

    id = Column(Integer, primary_key=True, index=True)
    assistant_id = Column(Integer, ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False)
    role = Column(String)
    text = Column(String)
    matches_json = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
