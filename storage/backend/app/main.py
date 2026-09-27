from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import PROCESSED_DIR, settings
from .routers.api import router as api_router
from .routers.media import router as media_router
from .services.job_manager import job_manager

app = FastAPI(title=settings.app_name, version="1.0.0", description="YOLO11-powered video analytics for border surveillance research and SIH demonstration.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(media_router)
app.mount("/processed", StaticFiles(directory=str(PROCESSED_DIR)), name="processed")


@app.get("/")
def root():
    return {"name": settings.app_name, "docs": "/docs", "status": "online"}


@app.websocket("/ws/jobs/{job_id}")
async def job_socket(websocket: WebSocket, job_id: str):
    await websocket.accept()
    try:
        while True:
            job = job_manager.get(job_id)
            if not job:
                await websocket.send_json({"status": "NOT_FOUND"})
                return
            await websocket.send_json(job.__dict__)
            if job.status in {"COMPLETED", "FAILED"}:
                return
            await __import__("asyncio").sleep(0.5)
    except WebSocketDisconnect:
        return
