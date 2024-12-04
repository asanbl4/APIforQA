from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    username: str
    password: str
    confirm_password: str


class UserAuthorize(BaseModel):
    username: str
    password: str


class TasksListCreate(BaseModel):
    list_title: str
    description: Optional[str] = None


class TasksListPatch(BaseModel):
    list_title: str
    description: Optional[str] = None


class TaskCreate(BaseModel):
    task_title: str
    description: Optional[str] = None
    list_id: int
