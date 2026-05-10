from datetime import timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.database import get_db
from models.models import User
from schemas.post import UserResponseSchema
from schemas.user import UserCreateSchema, UserUpdateSchema, TokenSchema
from utils.auth import (
    create_access_token,
    oauth2_scheme,
    verify_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(tags=["User"])


@router.post(
    "/", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_user(
    payload: UserCreateSchema, db: Annotated[AsyncSession, Depends(get_db)]
):
    user = User(**payload.model_dump())
    user.password = hash_password(user.password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/token", response_model=TokenSchema)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = select(User).where(User.email == form_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found"
        )
    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User UNAUTHORIZED"
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        {"sub": user.id}, expires_delta=access_token_expires
    )
    return TokenSchema(access_token=access_token)


@router.get("/{user_id}", response_model=Optional[UserResponseSchema])
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found"
        )
    return user


@router.patch("/", response_model=UserResponseSchema)
async def partitial_user_update(
    payload: UserUpdateSchema, db: Annotated[AsyncSession, Depends(get_db)]
):
    stmt = select(User).where(User.id == payload.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found"
        )
    user_data = payload.model_dump(exclude_unset=True)
    user_data.pop("user_id", None)
    for k, v in user_data.items():
        setattr(user, k, v)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found"
        )
    await db.delete(user)
    await db.commit()


@router.get("/me", response_model=UserResponseSchema)
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    user_id = verify_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="User Not Found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    stmt = select(User).where(User.id == user_id_int)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User Not Found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
