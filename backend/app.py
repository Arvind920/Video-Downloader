import os
from contextlib import asynccontextmanager
from pathlib import Path
from pydantic import BaseModel, HttpUrl
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import FRONTEND_DIR, DOWNLOADS_DIR, FFMPEG_PATH, NODE_PATH
from .downloader import extract_video_info, start_download_job, get_job_status
from .cleanup import start_cleanup_task

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start cleanup worker
    start_cleanup_task()
    yield
    # Shutdown

app = FastAPI(
    title="Universal Social Media Video & Audio Downloader",
    description="High performance video and audio downloader for YouTube, Instagram, TikTok, Twitter/X, Facebook, and more.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local development or external integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoInfoRequest(BaseModel):
    url: str

class DownloadStartRequest(BaseModel):
    url: str
    type: str  # "video" or "audio"
    quality_id: str

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "ffmpeg_available": bool(FFMPEG_PATH),
        "ffmpeg_path": FFMPEG_PATH,
        "node_available": bool(NODE_PATH),
    }

@app.post("/api/info")
async def get_info(payload: VideoInfoRequest):
    url = payload.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Please provide a valid video URL.")
    
    try:
        data = extract_video_info(url)
        return JSONResponse(content=data)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract video: {str(e)}")

@app.post("/api/download/start")
async def start_download(payload: DownloadStartRequest):
    url = payload.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Missing URL.")
    if payload.type not in ["video", "audio"]:
        raise HTTPException(status_code=400, detail="Invalid media type. Must be 'video' or 'audio'.")
    
    try:
        job_id = start_download_job(url, payload.type, payload.quality_id)
        return {"job_id": job_id, "status": "queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate download: {str(e)}")

@app.get("/api/download/status/{job_id}")
async def check_status(job_id: str):
    job = get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or expired.")
    
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "percent": job["percent"],
        "speed": job["speed"],
        "eta": job["eta"],
        "message": job["message"],
        "filename": job.get("filename"),
        "file_size": job.get("file_size"),
        "error": job.get("error"),
        "download_url": f"/api/download/file/{job_id}" if job["status"] == "ready" else None
    }

@app.get("/api/download/file/{job_id}")
async def serve_file(job_id: str):
    job = get_job_status(job_id)
    if not job or job["status"] != "ready":
        raise HTTPException(status_code=404, detail="File is not ready or has expired.")
    
    file_path = Path(job["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested file was not found on server.")
    
    filename = job.get("filename") or file_path.name
    # Guess media type
    media_type = "video/mp4" if filename.endswith(".mp4") else "audio/mpeg" if filename.endswith(".mp3") else "audio/mp4"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )

@app.get("/robots.txt", include_in_schema=False)
async def get_robots():
    robots_path = FRONTEND_DIR / "robots.txt"
    if robots_path.exists():
        return FileResponse(robots_path, media_type="text/plain")
    return HTTPException(status_code=404, detail="robots.txt not found")

@app.get("/sitemap.xml", include_in_schema=False)
async def get_sitemap():
    sitemap_path = FRONTEND_DIR / "sitemap.xml"
    if sitemap_path.exists():
        return FileResponse(sitemap_path, media_type="application/xml")
    return HTTPException(status_code=404, detail="sitemap.xml not found")

# Mount frontend static files
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

