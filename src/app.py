from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from database.database import Base, engine
from routes import post, user


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="FastAPI Blog",
    description="Blog com foco exclusivo ao melhor framework Backend: FastAPI!",
    version="1.0",
    lifespan=lifespan,
)

BASE_DIR = Path(__file__).parent

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/media", StaticFiles(directory=BASE_DIR / "media"), name="media")


@app.get("/api/helth", response_model=dict)
def get_api_status():
    return {"status": "Helth"}


app.include_router(user.router, prefix="/api/users")
app.include_router(post.router, prefix="/api/posts")
