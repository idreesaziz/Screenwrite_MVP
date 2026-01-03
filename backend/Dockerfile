# Backend Dockerfile - FastAPI Python App
# Optimized for GCP Cloud Run deployment

FROM python:3.12-slim AS base

# Install system dependencies required by packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    # For pydub (audio processing)
    ffmpeg \
    # For pypotrace (image tracing)
    libpotrace-dev \
    potrace \
    # For Pillow
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    # For rembg / onnxruntime
    libgomp1 \
    # General build tools
    build-essential \
    pkg-config \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# ---- Dependencies ----
FROM base AS deps
WORKDIR /app

# Install uv for fast Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# ---- Production ----
FROM base AS production
WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy virtual environment from deps stage
COPY --from=deps /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY . .

# Cloud Run uses port 8080 by default
ENV PORT=8080
EXPOSE 8080

# Run FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "600"]
