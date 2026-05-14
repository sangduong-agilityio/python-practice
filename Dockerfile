# Stage 1: build dependencies in an isolated layer so they are cached
# separately from application code. Re-installing deps only happens when
# pyproject.toml changes, not on every code edit.
FROM python:3.13-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml .
# Install runtime deps only (exclude dev tools like pytest/ruff from the image)
RUN uv pip install --system --no-cache -e "."

# Stage 2: lean runtime image -- no build tools, smaller attack surface.
FROM python:3.13-slim AS runtime

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source last
COPY . .

# Ensure the startup script is executable
RUN chmod +x /app/start.sh

# Run as a non-root user to follow the principle of least privilege.
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Use the startup script to handle migrations + server execution
CMD ["/app/start.sh"]