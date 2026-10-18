import os
import uvicorn
import sys
import webbrowser
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

if __name__ == "__main__":
    # Render and cloud hosts dynamically assign PORT and require 0.0.0.0
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    is_dev = os.getenv("ENV", "development").lower() == "development" and not os.getenv("RENDER")

    print("=" * 60)
    print("🚀 MediaGrab - Universal Social Media Video & Audio Downloader")
    print(f"🌐 Server binding on: {host}:{port}")
    print("=" * 60)

    # Auto-open browser only on local desktop machines
    if is_dev and (host in ["127.0.0.1", "0.0.0.0", "localhost"]):
        try:
            webbrowser.open(f"http://localhost:{port}")
        except Exception:
            pass

    uvicorn.run("backend.app:app", host=host, port=port, reload=is_dev)
