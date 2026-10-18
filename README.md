# 🎬 MediaGrab - Universal Social Media Video & Audio Downloader

A full-stack, modern web application to download videos and extract MP3 audio from social media platforms with a single link.

---

## 🌟 Key Features

- **Multi-Platform Support**: Works with **YouTube** (Videos & Shorts), **Instagram** (Reels & Posts), **TikTok** (watermark-free), **Twitter / X**, **Facebook**, **Reddit**, **Pinterest**, **Vimeo**, and 1,000+ sites.
- **Multiple Video Qualities**: Choose from **4K Ultra HD**, **2K**, **1080p Full HD**, **720p HD**, **480p**, and **360p**.
- **Audio Only (MP3 Extractor)**: Direct extraction to **MP3 320 kbps** (Studio Quality), **192 kbps**, **128 kbps**, or original **M4A/AAC**.
- **Audio-Video Merging with FFmpeg**: Automatically merges high-resolution video streams with audio tracks, ensuring no muted videos.
- **Real-Time Progress Tracking**: Live percentage, download speed, and ETA indicators via async background workers.
- **Auto Cleanup**: Temporary files and cache are automatically cleaned up to save disk space.
- **Modern Glassmorphic Dark UI**: Built with Tailwind CSS, Lucide icons, responsive layout, and clipboard auto-paste.

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+
- Node.js (used by `yt-dlp` to solve JavaScript challenges)

### 2. Run the Application
In your terminal, navigate to the project directory and run:

```bash
cd "d:\WebSites\Expanse Calculator\social-video-downloader"
python run.py
```

The server will start and automatically open in your browser at:
👉 **`http://localhost:8000`**

---

## 📂 Project Structure

```
social-video-downloader/
├── backend/
│   ├── app.py           # FastAPI application endpoints & static routing
│   ├── downloader.py    # yt-dlp metadata extraction & background job worker
│   ├── cleanup.py       # Auto-delete temporary media files
│   └── config.py        # Environment paths & FFmpeg configuration
├── frontend/
│   ├── index.html       # Modern responsive UI
│   ├── css/
│   │   └── style.css    # Custom styles & animations
│   └── js/
│       └── app.js       # Client logic: API calls, tabs, progress modal
├── downloads/           # Temporary storage for remuxed files (auto-cleaned)
├── run.py               # One-click launcher
├── requirements.txt     # Dependencies list
└── README.md            # Documentation
```

---

## 📡 API Endpoints

- `GET /api/health` — Check engine, FFmpeg, and Node.js status.
- `POST /api/info` — Extract video title, thumbnail, duration, uploader, and all available video/audio qualities.
- `POST /api/download/start` — Initiate an asynchronous download and conversion job.
- `GET /api/download/status/{job_id}` — Check download progress, speed, and ETA.
- `GET /api/download/file/{job_id}` — Direct download link with attachment headers.
