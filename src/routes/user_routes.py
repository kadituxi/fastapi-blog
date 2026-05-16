from datetime import datetime, timedelta, UTC
from typing import Annotated, Optional

from fastapi import (
    APIRouter,
    Depends,
    status,
    HTTPException,
    UploadFile,
    BackgroundTasks,
)
from fastapi.security import OAuth2PasswordRequestForm
from PIL import UnidentifiedImageError
from sqlalchemy import select, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from config import settings
from database.database import get_db
from models.models import User, PasswordResetToken
from schemas.post_schemas import UserResponseSchema
from schemas.user_schemas import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenSchema,
    UserCreateSchema,
    UserUpdateSchema,
)
from utils.email import send_password_reset_email
from utils.auth import (
    create_access_token,
    CurrentUser,
    generate_reset_token,
    hash_password,
    hash_reset_token,
    verify_password,
)
from utils.image import delete_profile_image, process_image_file

router = APIRouter(tags=["User"])


@router.post(
    "/", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_user(
    payload: UserCreateSchema, db: Annotated[AsyncSession, Depends(get_db)]
):
    stmt = select(User).where(User.email == payload.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        stmt = select(User).where(User.username == payload.username)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        )
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
        {"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return TokenSchema(access_token=access_token)


@router.get("/me", response_model=UserResponseSchema)
async def get_current_user(current_user: CurrentUser):
    return current_user


@router.post("/forgot-passowrd", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    print(payload)
    stmt = select(User).where(User.email == payload.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        await db.execute(
            sql_delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
        )
        token = generate_reset_token()
        token_hash = hash_reset_token(token)
        expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.reset_token_expire_minutes
        )
        reset_token = PasswordResetToken(
            user_id=user.id, token_hash=token_hash, expires_at=expires_at
        )
        db.add(reset_token)
        await db.commit()
        background_tasks.add_task(
            send_password_reset_email,
            to_email=user.email,
            username=user.username,
            token=token,
        )
    return {
        "message": "If an account exists with this email, you will receive password reset instructions"
    }


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest, db: Annotated[AsyncSession, Depends(get_db)]
):
    token_hash = hash_reset_token(payload.token)
    stmt = select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    result = await db.execute(stmt)
    reset_token = result.scalar_one_or_none()
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    if reset_token.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        await db.delete(reset_token)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        )
    stmt = select(User).where(User.id == reset_token.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Ivalid or expired token"
        )
    user.password = hash_password(payload.new_password)
    await db.execute(
        sql_delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
    )
    await db.commit()
    return {
        "message": "Password reset successfully. You can now log in with your new password."
    }


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


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found"
        )
    old_filename = user.image_file
    await db.delete(user)
    await db.commit()
    if old_filename:
        delete_profile_image(old_filename)


@router.patch("/{user_id}/picture", response_model=UserResponseSchema)
async def update_profile_picture(
    user_id: int,
    file: UploadFile,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user's picture",
        )
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {settings.max_upload_size_bytes // (1024 * 1024)}MB",
        )
    try:
        new_filename = await run_in_threadpool(process_image_file, content)
    except UnidentifiedImageError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file. Please upload a valid image (JPEG, PNG, GIF, WebP)",
        ) from err
    old_filename = current_user.image_file
    current_user.image_file = new_filename
    await db.commit()
    await db.refresh(current_user)
    if old_filename:
        delete_profile_image(old_filename)
    return current_user


@router.delete("/{user_id}/picture", response_model=UserResponseSchema)
async def delete_user_picture(
    user_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user's picture",
        )
    old_filename = current_user.image_file
    if not old_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No profile picture to delete",
        )
    current_user.image_file = None
    await db.commit()
    await db.refresh(current_user)
    delete_profile_image(old_filename)
    return current_user
