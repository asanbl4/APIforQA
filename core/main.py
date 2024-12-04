from fastapi.exceptions import RequestValidationError
from sqlmodel import SQLModel, select

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from core.routers import users, tasks_lists, tasks
from core.models import User
from core.database import get_db_session, engine
from core.schemas import UserCreate
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(tasks_lists.router, prefix="/tasks-lists", tags=["Tasks Lists"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    del request, exc
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Invalid input data"},
    )


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


@app.get("/")
async def root():
    return {"message": "Hello World"}
