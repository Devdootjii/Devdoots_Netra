# Engine Dockerfile — LOCAL use ke liye (webcam access)
# Ye file engine/ folder mein rakhi jayegi
# Run: docker run --device /dev/video0 -p 8001:8001 engine

FROM python:3.12-slim

# System dependencies (OpenCV ke liye)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements copy (root se — engine ka requirements shared hai)
COPY requirements.txt .
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Engine code + model weights copy
COPY . .

# .env file bhi copy (host se mount karna padega ya env pass karna padega)
ENV PORT=8001
EXPOSE 8001

CMD ["python", "netra_engine.py"]
