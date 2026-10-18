FROM python:3.11-slim

# Install system dependencies: ffmpeg, nodejs, curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    nodejs \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Ensure downloads directory exists
RUN mkdir -p downloads

# Environment variables
ENV PORT=8000
ENV HOST=0.0.0.0
ENV ENV=production
ENV RENDER=true

EXPOSE 8000

# Start server
CMD ["python", "run.py"]
