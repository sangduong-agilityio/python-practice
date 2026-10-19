# ============================================================
# Dockerfile — Multi-stage build for production
# ============================================================
#
# Stage 1 (builder): Install Python dependencies into a virtual environment.
# Stage 2 (runtime): Copy only the venv and app code — no build tools needed.
#
# Multi-stage builds keep the final image small and more secure
# by excluding compilers and other build-time tools.

# ---- Stage 1: Builder ----
FROM python:3.13-slim AS builder

# Prevent Python from writing .pyc files and buffer stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install build dependencies (needed to compile asyncpg and bcrypt wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition first — Docker caches this layer.
# If pyproject.toml doesn't change, this expensive pip install step
# is skipped on subsequent builds (great for CI speed).
COPY pyproject.toml ./

# Create a virtual environment and install all dependencies into it
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && pip install -e ".[dev]"


# ---- Stage 2: Runtime ----
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Only runtime libraries needed (libpq for asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application source code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Create a non-root user for security — running as root in containers is risky
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

# Expose the port Uvicorn will listen on
EXPOSE 8000

# Start command: run migrations first, then start the server
# Using shell form so we can chain commands with &&
CMD alembic upgrade head && \
    uvicorn app.main:app \
      --host 0.0.0.0 \
      --port 8000 \
      --workers 2 \
      --log-level info
