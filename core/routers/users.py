from datetime import timedelta, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.models import User, TasksList
from core.database import get_db_session
from core.schemas import UserCreate, UserAuthorize, TasksListCreate
from core.utils import auth
from uuid import UUID


router = APIRouter()


async def create_default_tasks_list(list_title: str, user: User, db):
    new_tasks_list = TasksList(
        list_title=list_title,
        description=None,
        created_by=user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(new_tasks_list)
    await db.commit()
    await db.refresh(new_tasks_list)


@router.get("/")
async def get_users(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users


@router.post("/register")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db_session)):
    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords must match"
        )

    result = await db.execute(select(User).where(User.username == user.username))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User already exists",
        )

    hashed_password = User.hash_password(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    await create_default_tasks_list(
        list_title=f"{user.username}'s default task-list", user=new_user, db=db
    )

    return new_user


@router.post("/confirm/{confirmation_uuid}")
async def confirm_user(
    confirmation_uuid: UUID, db: AsyncSession = Depends(get_db_session)
):
    result = await db.execute(
        select(User).where(User.confirmation_uuid == confirmation_uuid)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.confirmed:
        return JSONResponse(
            status_code=status.HTTP_208_ALREADY_REPORTED,
            content={"message": "User already confirmed"},
        )

    user.confirmed = True
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"message": f"User {user.username} confirmed"},
    )


@router.post("/auth")
async def authorize_user(
    user: UserAuthorize, db: AsyncSession = Depends(get_db_session)
):
    result = await db.execute(select(User).where(User.username == user.username))
    fetched_user = result.scalars().first()

    if not fetched_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not auth.verify_password(user.password, fetched_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password"
        )

    if not fetched_user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not confirmed"
        )

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": fetched_user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
