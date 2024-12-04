from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime
import bcrypt


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    confirmation_uuid: UUID = Field(default_factory=uuid4, unique=True)
    confirmed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)

    tasks_lists: List["TasksList"] = Relationship(back_populates="user")
    tasks: List["Task"] = Relationship(back_populates="user")

    @classmethod
    def hash_password(cls, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")


class TasksList(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    list_title: str = Field(unique=True, nullable=False)
    description: Optional[str] = Field(default=None)
    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)

    tasks: List["Task"] = Relationship(back_populates="tasks_list")
    user: User = Relationship(back_populates="tasks_lists")


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_title: str = Field(nullable=False)
    description: Optional[str] = Field(default=None)
    done: bool = Field(default=False)
    related_task_list: int = Field(foreign_key="taskslist.id")
    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)

    user: User = Relationship(back_populates="tasks")
    tasks_list: TasksList = Relationship(back_populates="tasks")

