# ============================================
# Build stage - install dependencies
# ============================================
FROM python:3.11-slim-bookworm as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_CACHE_DIR='/var/cache/pip'

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --upgrade pip

# ============================================
# Dependencies stage - install Python packages
# ============================================
FROM builder as dependencies

WORKDIR /app

# Copy dependency lists
COPY requirements.txt requirements.txt

# Install runtime dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# Development stage - for development with dev dependencies
# ============================================
FROM dependencies as development

# Install development-only dependencies
COPY requirements-dev.txt requirements-dev.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# Create non-root user
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /home/appuser -s /bin/bash appuser && \
    mkdir -p /home/appuser/.config/matplotlib /home/appuser/.streamlit /tmp/prometheus && \
    chown -R appuser:appuser /home/appuser /app /tmp/prometheus

# Switch to non-root user
ENV HOME=/home/appuser

USER appuser

# Set environment variables for development
ENV ENVIRONMENT=development \
    DEBUG=true \
    RELOAD=true \
    WORKERS=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    MPLCONFIGDIR=/home/appuser/.config/matplotlib \
    PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# ============================================
# Production stage - minimal image with only runtime dependencies
# ============================================
FROM python:3.11-slim-bookworm as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app" \
    PATH="/app/.local/bin:$PATH"

# Create app directory and set as working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /home/appuser -s /bin/bash appuser && \
    mkdir -p /home/appuser/.config/matplotlib /home/appuser/.streamlit /tmp/prometheus && \
    mkdir -p /app/logs /app/models && \
    chown -R appuser:appuser /home/appuser /app /tmp/prometheus

# Copy installed Python packages from dependencies stage
COPY --from=dependencies /usr/local /usr/local

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
ENV HOME=/home/appuser

USER appuser

# Set environment variables for production
ENV ENVIRONMENT=production \
    DEBUG=false \
    RELOAD=false \
    WORKERS=4 \
    HOST=0.0.0.0 \
    PORT=8000 \
    MPLCONFIGDIR=/home/appuser/.config/matplotlib \
    PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus

# Expose the port the app runs on
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application with Gunicorn
CMD ["gunicorn", "app.main:app", \
    "--workers", "4", \
    "--worker-class", "uvicorn.workers.UvicornWorker", \
    "--bind", "0.0.0.0:8000", \
    "--timeout", "120", \
    "--keep-alive", "2", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--log-level", "info"]
