from datetime import datetime, UTC, timedelta
from pathlib import Path
from typing import Optional, Annotated

from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from database import Base, engine, get_db
from models import Post, User
from schemas import PostCreateSchema, PostResponseSchema

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FastAPI Blog",
    description="Blog com foco exclusivo ao melhor framework Backend: FastAPI!",
    version="1.0",
)

BASE_DIR = Path(__file__).parent

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/media", StaticFiles(directory=BASE_DIR / "media"), name="media")

templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/api/helth")
def get_api_status():
    return {"status": "Helth"}


@app.get("/api/posts", response_model=list[PostResponseSchema])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    # stmt = db.execute(select(Post).join(User, User.id == Post.user_id))
    stmt = db.execute(
        select(Post).options(joinedload(Post.author))
    )  # Evita o problema N + 1
    posts = stmt.scalars().all()
    return posts


@app.post(
    "/api/posts", response_model=PostResponseSchema, status_code=status.HTTP_201_CREATED
)
def create_post(payload: PostCreateSchema, db: Annotated[Session, Depends(get_db)]):
    post = Post(**payload.model_dump())
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    stmt = db.execute(select(Post).where(Post.id == post_id))
    post = stmt.scalar_one_or_none()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Found"
        )
    db.delete(post)
    db.commit()


@app.get("/api/posts/{post_id}", response_model=Optional[PostResponseSchema])
def get_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    stmt = db.execute(select(Post).where(Post.id == post_id))
    post = stmt.scalar_one_or_none()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Found")


@app.get("/", include_in_schema=False, name="home")
def home_page(request: Request, db: Annotated[Session, Depends(get_db)]):
    stmt = db.execute(select(Post).order_by(Post.created_at))
    posts = stmt.scalars()
    return templates.TemplateResponse(
        request, "index.html", {"title": "Home", "posts": posts}
    )


@app.get("/posts/{post_id}", include_in_schema=False, name="post_detail")
def post_detail(
    request: Request, post_id: int, db: Annotated[Session, Depends(get_db)]
):
    stmt = db.execute(select(Post).where(Post.id == post_id))
    post = stmt.scalar_one_or_none()
    if post:
        return templates.TemplateResponse(
            request, "post_detail.html", {"title": post.title, "post": post}
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post Not Found")


@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code, content={"detail": message}
        )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors},
        )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
    )
