import os
import shutil
from pathlib import Path

# Paths
BACKEND_DIR = Path(__file__).resolve().parent
BASE_DIR = BACKEND_DIR.parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
FRONTEND_DIR = BASE_DIR / "frontend"

# Ensure directories exist
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)

# Locate FFmpeg binary
def get_ffmpeg_path():
    # First check system PATH
    ffmpeg_system = shutil.which("ffmpeg")
    if ffmpeg_system:
        return ffmpeg_system
    
    # Fallback to imageio_ffmpeg
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None

FFMPEG_PATH = get_ffmpeg_path()
NODE_PATH = shutil.which("node")

# Server settings
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))
MAX_FILE_AGE_SECONDS = 3600  # Clean files older than 1 hour
