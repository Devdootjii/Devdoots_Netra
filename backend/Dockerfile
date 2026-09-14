# Backend Dockerfile — Render deployment ke liye
# Ye file backend/ folder mein rakhi jayegi

FROM python:3.12-slim

# System dependencies (OpenCV ke liye)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements pehle copy (Docker caching — layers reuse hote hain)
COPY requirements.txt .
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Backend code copy
COPY . .

# Render PORT env var use karta hai
ENV PORT=8000
EXPOSE 8000

# Uvicorn start — Render ka PORT env var respect karo
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
