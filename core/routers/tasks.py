from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import select
from fastapi.responses import JSONResponse

from core.schemas import TaskCreate, TaskPatch
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db_session
from core.models import Task, TasksList, User
from core.utils import auth
from core.utils.auth import token_dependency
from datetime import datetime

router = APIRouter()


async def find_task(task_id: int, db, user=None) -> Task | None:
    """
    function to get a task by list_id
    pass the user if you need to check if the task belongs to the user
    """
    query = select(Task).where(Task.id == task_id).options(
        selectinload(Task.user),
        selectinload(Task.tasks_list)
    )
    result = await db.execute(query)
    task = result.scalars().first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if user:
        if task.user.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Task does not belong to the current user"
            )

    return task


@router.post("/create")
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

    return {"message": "Task created successfully", "task": new_task}


@router.patch("/{task_id}/update")
async def patch_task(
        task_id: int,
        task: TaskPatch,
        token: str = Depends(token_dependency),
        db: AsyncSession = Depends(get_db_session)
):
    user = await auth.validate_token(token, db)
    existing_task = await find_task(task_id, db, user)

    existing_task.task_title = task.task_title
    existing_task.description = task.description
    existing_task.tasks_list.id = task.list_id

    db.add(existing_task)
    await db.commit()
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Task updated successfully"})


@router.patch("/{task_id}/done")
async def done_task(
        task_id: int,
        token: str = Depends(token_dependency),
        db: AsyncSession = Depends(get_db_session)
):
    user = await auth.validate_token(token, db)
    task = await find_task(task_id, db)

    task.done = True

    db.add(task)
    await db.commit()
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Task done"})