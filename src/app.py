from fastapi import FastAPI

app = FastAPI(
    title="FastAPI Blog",
    description="My first complete project using FastAPI",
    version="1.0",
)


@app.get("/helth")
def get_api_status():
    return {"status": "Helth"}
