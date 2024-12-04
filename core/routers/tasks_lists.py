from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import selectinload
from sqlmodel import select
from fastapi.responses import JSONResponse

from core.schemas import TasksListCreate, TasksListPatch
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db_session
from core.models import TasksList, User, Task
from core.utils import auth
from core.utils.auth import token_dependency
from datetime import datetime

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_tasks_list(
        tasks_list: TasksListCreate,
        token: str = Depends(token_dependency),
        db: AsyncSession = Depends(get_db_session)
):
    user = await auth.validate_token(token, db)

    result = await db.execute(select(TasksList).where(TasksList.list_title == tasks_list.list_title))
    existing_tasks_list = result.scalars().first()
    if existing_tasks_list:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tasks list with this title already exists")

    new_tasks_list = TasksList(
        list_title=tasks_list.list_title,
        description=tasks_list.description,
        created_by=user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(new_tasks_list)
    await db.commit()
    await db.refresh(new_tasks_list)

    return {"message": "Tasks list created successfully", "tasks_list": new_tasks_list}


@router.get("/")
async def get_tasks_lists(
        token: str = Depends(token_dependency),
        db: AsyncSession = Depends(get_db_session)
):
    user = await auth.validate_token(token, db)
    del user

    result = await db.execute(select(TasksList))
    tasks_lists = result.scalars().all()
    return tasks_lists


@router.get("/{list_id}")
async def get_tasks_list(list_id: int, db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(TasksList).where(TasksList.id == list_id))
    tasks_list = result.scalars().first()

    if not tasks_list:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Tasks List not found")

    result_tasks = await db.execute(select(Task).where(Task.related_task_list == list_id))
    tasks = result_tasks.scalars().all()

    return {
        "tasks_list": {
            "id": tasks_list.id,
            "list_title": tasks_list.list_title,
            "description": tasks_list.description,
            "created_by": tasks_list.created_by,
            "created_at": tasks_list.created_at,
            "updated_at": tasks_list.updated_at,
        },
        "tasks": [
            {
                "id": task.id,
                "task_title": task.task_title,
                "description": task.description,
                "done": task.done,
                "created_by": task.created_by,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
            }
            for task in tasks
        ],
    }


@router.patch("/{list_id}")
async def patch_tasks_list(
        list_id: int,
        tasks_list: TasksListPatch,
        token: str = Depends(token_dependency),
        db: AsyncSession = Depends(get_db_session)
):
    user = auth.validate_token(token, db)

    result = await db.execute(select(TasksList).where(TasksList.id == list_id))
    tasks_list = result.scalars().first()
    if not tasks_list:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tasks List not found")

    result = await db.execute(select(TasksList).where(TasksList.list_title == tasks_list.list_title))
    existing_tasks_list = result.scalars().first()
    if existing_tasks_list:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tasks list with this title already exists")

    ...

    return JSONResponse(status_code=200, content={"message": "ok"})
