from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
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