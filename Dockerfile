# ============================================
# Build stage - install dependencies
# ============================================
FROM python:3.11-slim-bookworm as builder

# Set environment variables
ENV PYTHONDUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.6.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    PIP_CACHE_DIR='/var/cache/pip' \
    VENV_PATH="/opt/pysetup/.venv"

# Add Poetry to PATH
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -


# ============================================
# Dependencies stage - install Python packages
# ============================================
FROM builder as dependencies

WORKDIR /app

# Copy only the dependency files first to leverage Docker cache
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --no-root --no-dev --no-interaction --no-ansi -v \
    && find /usr/local \
        \( -type d -a -name test -o -name tests \) \
        -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
        -exec rm -rf '{}' +


# ============================================
# Development stage - for development with dev dependencies
# ============================================
FROM dependencies as development

# Install dev dependencies
RUN poetry install --no-interaction --no-ansi -v

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables for development
ENV ENVIRONMENT=development \
    DEBUG=true \
    RELOAD=true \
    WORKERS=1 \
    HOST=0.0.0.0 \
    PORT=8000

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
    PATH="/app/.local/bin:$PATH" \
    VENV_PATH="/opt/pysetup/.venv"

# Create app directory and set as working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && mkdir -p /app/logs /app/models \
    && chown -R appuser:appuser /app

# Copy virtual environment from builder
COPY --from=dependencies $VENV_PATH $VENV_PATH
ENV PATH="$VENV_PATH/bin:$PATH"

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Set environment variables for production
ENV ENVIRONMENT=production \
    DEBUG=false \
    RELOAD=false \
    WORKERS=4 \
    HOST=0.0.0.0 \
    PORT=8000

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
