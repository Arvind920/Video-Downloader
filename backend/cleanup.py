import time
import threading
from pathlib import Path
from .config import DOWNLOADS_DIR, MAX_FILE_AGE_SECONDS
from .downloader import ACTIVE_JOBS, JOBS_LOCK

def cleanup_worker():
    """Periodically delete temporary download files and old active jobs."""
    while True:
        try:
            now = time.time()
            # Clean directory files
            if DOWNLOADS_DIR.exists():
                for file_path in DOWNLOADS_DIR.iterdir():
                    if file_path.is_file():
                        try:
                            file_age = now - file_path.stat().st_mtime
                            if file_age > MAX_FILE_AGE_SECONDS:
                                file_path.unlink(missing_ok=True)
                        except Exception:
                            pass

            # Clean memory job records
            with JOBS_LOCK:
                expired_keys = [
                    jid for jid, info in ACTIVE_JOBS.items()
                    if now - info.get("created_at", now) > MAX_FILE_AGE_SECONDS
                ]
                for k in expired_keys:
                    del ACTIVE_JOBS[k]

        except Exception:
            pass

        # Check every 10 minutes
        time.sleep(600)

def start_cleanup_task():
    """Start cleanup daemon thread."""
    t = threading.Thread(target=cleanup_worker, daemon=True)
    t.start()
