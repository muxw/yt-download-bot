#!/usr/bin/env python3
# coding: utf-8

"""
FastAPI web application for video downloading
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

from .downloader import WebDownloader, DownloadTask

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[task_id] = websocket

    def disconnect(self, task_id: str):
        self.active_connections.pop(task_id, None)

    async def send_progress(self, task_id: str, data: dict):
        if ws := self.active_connections.get(task_id):
            try:
                await ws.send_json(data)
            except Exception:
                self.disconnect(task_id)


manager = ConnectionManager()


# Cleanup task for old downloads
async def cleanup_old_files():
    """Periodically clean up old download files"""
    import shutil
    import time

    while True:
        await asyncio.sleep(3600)  # Run every hour
        try:
            temp_path = Path(os.getenv("TMPFILE_PATH", "/tmp"))
            for item in temp_path.glob("ytdl-web-*"):
                if time.time() - item.stat().st_ctime > 3600:  # 1 hour old
                    shutil.rmtree(item, ignore_errors=True)
                    logger.info(f"Cleaned up: {item}")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    cleanup_task = asyncio.create_task(cleanup_old_files())
    yield
    # Shutdown
    cleanup_task.cancel()


# Create FastAPI app
app = FastAPI(
    title="Video Downloader",
    description="Download videos from YouTube and other sites",
    version="1.0.0",
    lifespan=lifespan,
)


# Request/Response models
class VideoInfoRequest(BaseModel):
    url: str


class VideoInfoResponse(BaseModel):
    title: str
    duration: int
    thumbnail: str
    uploader: str
    formats: list[dict]


class DownloadRequest(BaseModel):
    url: str
    format_id: Optional[str] = None
    height: Optional[int] = None


class DownloadResponse(BaseModel):
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    speed: str
    eta: str
    filename: str
    error: str


# API Routes
@app.post("/api/info", response_model=VideoInfoResponse)
async def get_video_info(request: VideoInfoRequest):
    """Get video information and available formats"""
    try:
        downloader = WebDownloader(request.url)
        info = await asyncio.to_thread(downloader.get_video_info)
        return VideoInfoResponse(**info)
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/download", response_model=DownloadResponse)
async def start_download(request: DownloadRequest):
    """Start a download task"""
    task = WebDownloader.create_task(request.url)
    task.status = "started"

    # Start download in background
    asyncio.create_task(
        run_download(task.task_id, request.url, request.format_id, request.height)
    )

    return DownloadResponse(task_id=task.task_id, status="started")


async def run_download(task_id: str, url: str, format_id: Optional[str], height: Optional[int]):
    """Run download in background and update progress via WebSocket"""
    task = WebDownloader.get_task(task_id)
    if not task:
        return

    downloader = WebDownloader(url)
    loop = asyncio.get_event_loop()
    progress_queue = asyncio.Queue()

    def progress_callback(data: dict):
        task.status = data.get("status", "downloading")
        task.progress = data.get("progress", 0)
        task.speed = data.get("speed", "")
        task.eta = data.get("eta", "")

        # Thread-safe: put data in queue
        loop.call_soon_threadsafe(progress_queue.put_nowait, data)

    downloader.set_progress_callback(progress_callback)

    # Progress sender task
    async def send_progress_updates():
        while True:
            try:
                data = await asyncio.wait_for(progress_queue.get(), timeout=0.5)
                await manager.send_progress(task_id, data)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    progress_task = asyncio.create_task(send_progress_updates())

    try:
        task.status = "downloading"
        filepath = await asyncio.to_thread(downloader.download, format_id, height)

        task.status = "completed"
        task.progress = 100
        task.filepath = filepath
        task.filename = Path(filepath).name

        await manager.send_progress(task_id, {
            "status": "completed",
            "progress": 100,
            "filename": task.filename,
        })

    except Exception as e:
        task.status = "error"
        task.error = str(e)
        logger.error(f"Download error for task {task_id}: {e}")

        await manager.send_progress(task_id, {
            "status": "error",
            "error": str(e),
        })
    finally:
        progress_task.cancel()
        try:
            await progress_task
        except asyncio.CancelledError:
            pass


@app.get("/api/download/{task_id}", response_model=TaskStatusResponse)
async def get_download_status(task_id: str):
    """Get download task status"""
    task = WebDownloader.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatusResponse(
        task_id=task.task_id,
        status=task.status,
        progress=task.progress,
        speed=task.speed,
        eta=task.eta,
        filename=task.filename,
        error=task.error,
    )


@app.get("/api/file/{task_id}")
async def download_file(task_id: str):
    """Download the completed file"""
    task = WebDownloader.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Download not completed")

    if not task.filepath or not Path(task.filepath).exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=task.filepath,
        filename=task.filename,
        media_type="application/octet-stream",
    )


# WebSocket for real-time progress
@app.websocket("/ws/{task_id}")
async def websocket_progress(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time download progress"""
    await manager.connect(task_id, websocket)
    try:
        while True:
            # Keep connection alive, wait for messages
            data = await websocket.receive_text()
            # Client can send "ping" to keep alive
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(task_id)


# Serve static files and index.html
# Try to find static directory and index.html
static_dir = Path(__file__).parent / "static"
if not static_dir.exists():
    # Try project root
    static_dir = Path(__file__).parent.parent.parent / "static"

# Look for index.html in multiple locations
index_locations = [
    Path(__file__).parent / "static" / "index.html",  # web/static/index.html
    Path(__file__).parent.parent.parent / "index.html",  # project root
]

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main page"""
    for index_file in index_locations:
        if index_file.exists():
            return HTMLResponse(content=index_file.read_text())
    return HTMLResponse(content="<h1>Video Downloader</h1><p>Index file not found. Locations checked: {}</p>".format(
        ", ".join(str(p) for p in index_locations)
    ))


# Run with: uvicorn src.web.app:app --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
