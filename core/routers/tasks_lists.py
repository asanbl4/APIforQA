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


async def find_tasks_list(list_id: int, db, user=None) -> TasksList | None:
    """
    function to get a tasks list by list_id
    pass the user if you need to check if the tasks list belongs to the user
    """
    result = await db.execute(
        select(TasksList)
        .where(TasksList.id == list_id)
        .options(selectinload(TasksList.user))
    )
    tasks_list = result.scalars().first()

    if not tasks_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tasks list not found"
        )

    if user:
        if tasks_list.user.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tasks list does not belong to the current user",
            )

    return tasks_list


async def if_list_title_already_exists(list_title: str, db) -> None:
    result = await db.execute(
        select(TasksList).where(TasksList.list_title == list_title)
    )
    existing_tasks_list = result.scalars().first()
    if existing_tasks_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tasks list with this title already exists",
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_tasks_list(
    tasks_list: TasksListCreate,
    token: str = Depends(token_dependency),
    db: AsyncSession = Depends(get_db_session),
):
    user = await auth.validate_token(token, db)
    await if_list_title_already_exists(tasks_list.list_title, db)

    new_tasks_list = TasksList(
        list_title=tasks_list.list_title,
        description=tasks_list.description,
        created_by=user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(new_tasks_list)
    await db.commit()
    await db.refresh(new_tasks_list)

    return {"message": "Tasks list created successfully", "tasks_list": new_tasks_list}


@router.get("/")
async def get_tasks_lists(
    token: str = Depends(token_dependency), db: AsyncSession = Depends(get_db_session)
):
    user = await auth.validate_token(token, db)
    del user

    result = await db.execute(select(TasksList))
    tasks_lists = result.scalars().all()
    return tasks_lists


@router.get("/{list_id}")
async def get_tasks_list(list_id: int, db: AsyncSession = Depends(get_db_session)):
    tasks_list = await find_tasks_list(list_id, db)

    result_tasks = await db.execute(
        select(Task).where(Task.related_task_list == list_id)
    )
    tasks = result_tasks.scalars().all()

    return {
        "tasks_list": {
            "id": tasks_list.id,
            "list_title": tasks_list.list_title,
            "description": tasks_list.description,
            "created_by": tasks_list.created_by,
            "created_at": tasks_list.created_at,
            "updated_at": tasks_list.updated_at,
            "deleted_at": tasks_list.deleted_at,
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
                "deleted_at": task.deleted_at,
            }
            for task in tasks
        ],
    }


@router.patch("/{list_id}")
async def patch_tasks_list(
    list_id: int,
    tasks_list: TasksListPatch,
    token: str = Depends(token_dependency),
    db: AsyncSession = Depends(get_db_session),
):
    user = await auth.validate_token(token, db)
    tasks_list = await find_tasks_list(list_id, db, user)

    await if_list_title_already_exists(tasks_list.list_title, db)

    ...

    return JSONResponse(status_code=200, content={"message": "ok"})


@router.delete("/{list_id}")
async def delete_tasks_list(
    list_id: int,
    token: str = Depends(token_dependency),
    db: AsyncSession = Depends(get_db_session),
):
    user = await auth.validate_token(token, db)
    tasks_list = await find_tasks_list(list_id, db, user)

    tasks_list.deleted_at = datetime.utcnow()
    db.add(tasks_list)
    await db.commit()
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "ok"})


@router.patch("/{list_id}/delete-tasks")
async def delete_tasks_tasks_list(
    list_id: int,
    token: str = Depends(token_dependency),
    db: AsyncSession = Depends(get_db_session),
):
    user = await auth.validate_token(token, db)
    tasks_list = await find_tasks_list(list_id, db, user)

    result_tasks = await db.execute(
        select(Task)
        .where(Task.related_task_list == list_id)
        .options(selectinload(Task.user))
    )
    tasks = result_tasks.scalars().all()

    for task in tasks:
        task.deleted_at = datetime.utcnow()
        db.add(task)

    await db.commit()

    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "ok"})


@router.put("/{list_id}/done-all")
async def delete_tasks_tasks_list(
    list_id: int,
    token: str = Depends(token_dependency),
    db: AsyncSession = Depends(get_db_session),
):
    user = await auth.validate_token(token, db)
    tasks_list = await find_tasks_list(list_id, db, user)

    if tasks_list.user.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task List not created by current User",
        )

    result_tasks = await db.execute(
        select(Task)
        .where(Task.related_task_list == list_id)
        .options(selectinload(Task.user))
    )
    tasks = result_tasks.scalars().all()

    for task in tasks:
        task.done = True
        db.add(task)

    await db.commit()

    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "ok"})
