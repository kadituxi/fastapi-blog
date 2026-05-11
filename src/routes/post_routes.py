from typing import Optional, Annotated

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database.database import get_db
from models.models import Post
from schemas.post_schemas import PostCreateSchema, PostResponseSchema, PostUpdateSchema
from utils.auth import CurrentUser

router = APIRouter(tags=["Posts"])


@router.get("/", response_model=list[PostResponseSchema])
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    stmt = select(Post).options(selectinload(Post.author))
    result = await db.execute(stmt)
    posts = result.scalars().all()
    return posts


@router.post(
    "/", response_model=PostResponseSchema, status_code=status.HTTP_201_CREATED
)
async def create_post(
    payload: PostCreateSchema,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    post = Post(**payload.model_dump())
    post.user_id = current_user.id
    db.add(post)
    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post


@router.put("/{post_id}", response_model=PostResponseSchema)
async def update_post(
    payload: PostUpdateSchema,
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = await db.execute(
        select(Post).options(selectinload(Post.author)).where(Post.id == post_id)
    )
    post = stmt.scalar_one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Found"
        )
    if payload.user_id != post.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User UNAUTHORIZED"
        )
    if payload.title and payload.title != post.title:
        post.title = payload.title
    if payload.content and payload.content != post.content:
        post.content = payload.content
    await db.commit()
    await db.refresh(post)
    return post


@router.get("/{post_id}", response_model=Optional[PostResponseSchema])
async def get_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    stmt = select(Post).options(selectinload(Post.author)).where(Post.id == post_id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Found")


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    stmt = select(Post).where(Post.id == post_id)
    result = await db.execute(stmt)
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Found"
        )
    await db.delete(post)
    await db.commit()
