import re
import os
import uuid
import threading
import time
from pathlib import Path
from urllib.parse import urlparse
import yt_dlp

from .config import FFMPEG_PATH, NODE_PATH, DOWNLOADS_DIR

# Global job tracking for asynchronous downloads
ACTIVE_JOBS = {}
JOBS_LOCK = threading.Lock()

def sanitize_filename(name: str) -> str:
    """Remove invalid filename characters for Windows / cross-platform safety."""
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name)
    cleaned = re.sub(r'\s+', " ", cleaned).strip()
    return cleaned[:120] if cleaned else "video"

def format_duration(seconds: int | None) -> str:
    """Format duration in seconds to HH:MM:SS or MM:SS."""
    if not seconds:
        return "Unknown"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"

def format_bytes(bytes_num: int | float | None) -> str:
    """Format bytes into human-readable size."""
    if not bytes_num or bytes_num <= 0:
        return "Unknown size"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} TB"

def detect_platform(url: str) -> dict:
    """Detect social media platform from link domain."""
    domain = urlparse(url).netloc.lower()
    
    if "youtube.com" in domain or "youtu.be" in domain:
        return {"id": "youtube", "name": "YouTube", "icon": "youtube", "color": "#FF0000"}
    elif "instagram.com" in domain:
        return {"id": "instagram", "name": "Instagram", "icon": "instagram", "color": "#E1306C"}
    elif "tiktok.com" in domain:
        return {"id": "tiktok", "name": "TikTok", "icon": "tiktok", "color": "#00F2FE"}
    elif "twitter.com" in domain or "x.com" in domain:
        return {"id": "twitter", "name": "X / Twitter", "icon": "twitter", "color": "#1DA1F2"}
    elif "facebook.com" in domain or "fb.watch" in domain:
        return {"id": "facebook", "name": "Facebook", "icon": "facebook", "color": "#1877F2"}
    elif "reddit.com" in domain:
        return {"id": "reddit", "name": "Reddit", "icon": "reddit", "color": "#FF4500"}
    elif "pinterest.com" in domain or "pin.it" in domain:
        return {"id": "pinterest", "name": "Pinterest", "icon": "pinterest", "color": "#E60023"}
    elif "threads.net" in domain:
        return {"id": "threads", "name": "Threads", "icon": "threads", "color": "#000000"}
    else:
        return {"id": "general", "name": "Web Media", "icon": "video", "color": "#6366F1"}

def get_base_ydl_opts() -> dict:
    """Base options for yt-dlp including FFmpeg and JS runtime."""
    opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'remote_components': ['ejs:github'],
    }
    if FFMPEG_PATH:
        opts['ffmpeg_location'] = FFMPEG_PATH
    if NODE_PATH:
        opts['js_runtimes'] = {'node': {'path': NODE_PATH}}
    return opts

def extract_video_info(url: str) -> dict:
    """Extract metadata and available video/audio options from given URL."""
    ydl_opts = get_base_ydl_opts()
    ydl_opts['skip_download'] = True

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception as e:
            err_msg = str(e)
            if "Private video" in err_msg:
                raise ValueError("This video is private or restricted.")
            elif "Video unavailable" in err_msg:
                raise ValueError("Video is unavailable or has been removed.")
            else:
                raise ValueError(f"Could not fetch video info: {err_msg}")

    title = info.get("title") or "Unknown Video"
    thumbnail = info.get("thumbnail") or ""
    duration = info.get("duration")
    duration_str = format_duration(duration)
    uploader = info.get("uploader") or info.get("channel") or info.get("creator") or "Unknown Creator"
    platform = detect_platform(url)

    # Process formats
    raw_formats = info.get("formats", [])
    video_qualities = []
    
    # Check what heights are available
    available_heights = set()
    format_by_height = {}
    
    for f in raw_formats:
        h = f.get("height")
        vcodec = f.get("vcodec")
        if h and vcodec != "none":
            available_heights.add(h)
            # Store the format with the largest filesize or best bitrate for that height
            if h not in format_by_height or (f.get("filesize") or 0) > (format_by_height[h].get("filesize") or 0):
                format_by_height[h] = f

    standard_resolutions = [
        (2160, "4K Ultra HD", "2160p"),
        (1440, "2K Quad HD", "1440p"),
        (1080, "1080p Full HD", "1080p"),
        (720, "720p HD", "720p"),
        (480, "480p SD", "480p"),
        (360, "360p Fast", "360p"),
    ]

    for height, label, badge in standard_resolutions:
        # Check if this resolution is supported by the video
        matching_heights = [h for h in available_heights if h >= height * 0.9 and h <= height * 1.1]
        if matching_heights or (height == 720 and not available_heights):
            target_h = matching_heights[0] if matching_heights else height
            matched_f = format_by_height.get(target_h, {})
            
            # File size calculation
            size_bytes = matched_f.get("filesize") or matched_f.get("filesize_approx")
            if not size_bytes and duration and matched_f.get("tbr"):
                size_bytes = int((matched_f["tbr"] * 1024 / 8) * duration)

            video_qualities.append({
                "id": f"video_{height}p",
                "height": height,
                "label": label,
                "badge": badge,
                "ext": "mp4",
                "size_human": format_bytes(size_bytes),
                "is_best": (height == 1080) or (len(video_qualities) == 0)
            })

    # If no heights found (e.g. TikTok/Instagram single format), provide generic Best Quality
    if not video_qualities:
        filesize = info.get("filesize") or info.get("filesize_approx")
        video_qualities.append({
            "id": "video_best",
            "height": 1080,
            "label": "Original HD (Best Available)",
            "badge": "HD",
            "ext": "mp4",
            "size_human": format_bytes(filesize),
            "is_best": True
        })

    # Audio qualities
    audio_qualities = [
        {
            "id": "audio_mp3_320",
            "label": "MP3 Audio (320 kbps)",
            "badge": "MP3 High",
            "ext": "mp3",
            "bitrate": "320",
            "note": "Ultra High Quality",
            "size_human": format_bytes(int((320 * 1024 / 8) * duration)) if duration else "High Quality"
        },
        {
            "id": "audio_mp3_192",
            "label": "MP3 Audio (192 kbps)",
            "badge": "MP3 Standard",
            "ext": "mp3",
            "bitrate": "192",
            "note": "Standard Quality",
            "size_human": format_bytes(int((192 * 1024 / 8) * duration)) if duration else "Standard Quality"
        },
        {
            "id": "audio_mp3_128",
            "label": "MP3 Audio (128 kbps)",
            "badge": "MP3 Compact",
            "ext": "mp3",
            "bitrate": "128",
            "note": "Compact / Fast",
            "size_human": format_bytes(int((128 * 1024 / 8) * duration)) if duration else "Compact"
        },
        {
            "id": "audio_m4a",
            "label": "M4A Audio (Original Stream)",
            "badge": "M4A",
            "ext": "m4a",
            "bitrate": "best",
            "note": "Original AAC Stream",
            "size_human": "Direct Stream"
        }
    ]

    return {
        "url": url,
        "title": title,
        "thumbnail": thumbnail,
        "duration": duration,
        "duration_str": duration_str,
        "uploader": uploader,
        "platform": platform,
        "video_qualities": video_qualities,
        "audio_qualities": audio_qualities
    }

def _download_worker(job_id: str, url: str, item_type: str, quality_id: str):
    """Background worker to download, merge, and convert media using yt-dlp."""
    try:
        with JOBS_LOCK:
            ACTIVE_JOBS[job_id]["status"] = "processing"
            ACTIVE_JOBS[job_id]["message"] = "Fetching stream information..."

        def progress_hook(d):
            status = d.get('status')
            with JOBS_LOCK:
                if job_id not in ACTIVE_JOBS:
                    return
                if status == 'downloading':
                    total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                    downloaded = d.get('downloaded_bytes') or 0
                    percent = 0
                    if total_bytes > 0:
                        percent = round((downloaded / total_bytes) * 100, 1)
                    
                    speed = d.get('speed')
                    speed_str = f"{format_bytes(speed)}/s" if speed else ""
                    eta = d.get('eta')
                    eta_str = f"{eta}s" if eta else ""

                    ACTIVE_JOBS[job_id]["status"] = "downloading"
                    ACTIVE_JOBS[job_id]["percent"] = percent
                    ACTIVE_JOBS[job_id]["speed"] = speed_str
                    ACTIVE_JOBS[job_id]["eta"] = eta_str
                    ACTIVE_JOBS[job_id]["message"] = f"Downloading: {percent}% at {speed_str}"
                elif status == 'finished':
                    ACTIVE_JOBS[job_id]["status"] = "merging"
                    ACTIVE_JOBS[job_id]["percent"] = 95
                    ACTIVE_JOBS[job_id]["message"] = "Merging streams & finalizing file with FFmpeg..."

        ydl_opts = get_base_ydl_opts()
        ydl_opts['progress_hooks'] = [progress_hook]

        # Extract basic info first using full base opts
        with yt_dlp.YoutubeDL(get_base_ydl_opts()) as ydl:
            pre_info = ydl.extract_info(url, download=False)
            raw_title = pre_info.get('title') or 'video'
            safe_title = sanitize_filename(raw_title)

        if item_type == "audio":
            # Determine bitrate and extension
            ext = "mp3"
            bitrate = "320"
            if "192" in quality_id:
                bitrate = "192"
            elif "128" in quality_id:
                bitrate = "128"
            elif "m4a" in quality_id:
                ext = "m4a"

            file_stem = f"{safe_title}_{bitrate}kbps" if ext == "mp3" else f"{safe_title}"
            out_template = str(DOWNLOADS_DIR / f"{job_id}_{file_stem}.%(ext)s")

            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['outtmpl'] = out_template

            if ext == "mp3":
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': bitrate,
                }]
            else:
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                }]

        else:
            # Video download with audio merge
            ext = "mp4"
            height = 1080
            if "2160p" in quality_id:
                height = 2160
            elif "1440p" in quality_id:
                height = 1440
            elif "1080p" in quality_id:
                height = 1080
            elif "720p" in quality_id:
                height = 720
            elif "480p" in quality_id:
                height = 480
            elif "360p" in quality_id:
                height = 360

            file_stem = f"{safe_title}_{height}p"
            out_template = str(DOWNLOADS_DIR / f"{job_id}_{file_stem}.%(ext)s")

            ydl_opts['format'] = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
            ydl_opts['merge_output_format'] = 'mp4'
            ydl_opts['outtmpl'] = out_template

        # Perform actual download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find the generated file in DOWNLOADS_DIR matching job_id
        final_file = None
        for p in DOWNLOADS_DIR.glob(f"{job_id}_*"):
            if p.is_file() and not p.name.endswith(".part"):
                final_file = p
                break

        if final_file and final_file.exists():
            clean_name = final_file.name[len(job_id) + 1:]
            with JOBS_LOCK:
                ACTIVE_JOBS[job_id]["status"] = "ready"
                ACTIVE_JOBS[job_id]["percent"] = 100
                ACTIVE_JOBS[job_id]["file_path"] = str(final_file)
                ACTIVE_JOBS[job_id]["filename"] = clean_name
                ACTIVE_JOBS[job_id]["file_size"] = format_bytes(final_file.stat().st_size)
                ACTIVE_JOBS[job_id]["message"] = "Download ready!"
        else:
            raise FileNotFoundError("Output file could not be generated.")

    except Exception as e:
        with JOBS_LOCK:
            ACTIVE_JOBS[job_id]["status"] = "error"
            ACTIVE_JOBS[job_id]["message"] = f"Failed to download: {str(e)}"
            ACTIVE_JOBS[job_id]["error"] = str(e)

def start_download_job(url: str, item_type: str, quality_id: str) -> str:
    """Start an async download job and return unique job ID."""
    job_id = str(uuid.uuid4())
    with JOBS_LOCK:
        ACTIVE_JOBS[job_id] = {
            "job_id": job_id,
            "url": url,
            "type": item_type,
            "quality_id": quality_id,
            "status": "queued",
            "percent": 0,
            "speed": "",
            "eta": "",
            "message": "Initializing download queue...",
            "file_path": None,
            "filename": None,
            "created_at": time.time(),
            "error": None
        }

    thread = threading.Thread(
        target=_download_worker,
        args=(job_id, url, item_type, quality_id),
        daemon=True
    )
    thread.start()
    return job_id

def get_job_status(job_id: str) -> dict | None:
    """Retrieve current state of a download job."""
    with JOBS_LOCK:
        return ACTIVE_JOBS.get(job_id)
