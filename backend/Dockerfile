FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements from root and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code (keeping the relative structure backend/)
COPY ./backend ./backend

# Default directory for uploads/repos/data
RUN mkdir -p /app/data /app/data/hf_cache /app/backend/memory/storage

# Pre-download the SentenceTransformer model at build time.
# This is stored in /app/data/hf_cache which is mounted as a
# named Docker volume (hf_cache) — so rebuilds reuse the cached
# model and audits start instantly without network downloads.
ENV SENTENCE_TRANSFORMERS_HOME=/app/data/hf_cache
ENV HF_HOME=/app/data/hf_cache
RUN timeout 30s python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='/app/data/hf_cache')" \
    || echo "[WARN] Model pre-download timed out/failed — will download on first use."

# Expose backend port
EXPOSE 8000

# Default cmd runs FastAPI
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
