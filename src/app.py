from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import settings
from database.database import engine
from routes import post_routes, user_routes


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="FastAPI Blog",
    description="Blog com foco exclusivo ao melhor framework Backend: FastAPI!",
    version="1.0",
    lifespan=lifespan,
)


app.mount("/static", StaticFiles(directory=settings.base_dir / "static"), name="static")
app.mount("/media", StaticFiles(directory=settings.base_dir / "media"), name="media")


@app.get("/api/helth", response_model=dict)
def get_api_status():
    return {"status": "Helth"}


app.include_router(user_routes.router, prefix="/api/users")
app.include_router(post_routes.router, prefix="/api/posts")
