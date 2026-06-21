from fastapi import FastAPI

from server.app.api import router as api_router
from server.app.websocket import router as websocket_router


app = FastAPI(title="Python Online Tetris Server")
app.include_router(api_router)
app.include_router(websocket_router)


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok"}

