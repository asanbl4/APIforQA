from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from core.schemas import TaskCreate
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db_session
from core.models import Task, TasksList, User
from core.utils import auth
from core.utils.auth import token_dependency
from datetime import datetime

router = APIRouter()


@router.post("/")
async def create_task(
        task: TaskCreate,
        token: str = Depends(token_dependency),
        db: AsyncSession = Depends(get_db_session)
):
    user = await auth.validate_token(token, db)
    new_task = Task(
        task_title=task.task_title,
        description=task.description,
        related_task_list=task.list_id,
        created_by=user.id
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return {"message": "Tasks list created successfully", "task": new_task}


