# ──────────────────────────────────────────────
# Halol Crypto AI — Dockerfile
# Multi-stage build for minimal production image
# ──────────────────────────────────────────────

FROM python:3.12-slim AS base

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Non-root user for security
RUN useradd -m -u 1001 halol && chown -R halol:halol /app
USER halol

# Data directory for SQLite
RUN mkdir -p /app/data

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SQLITE_PATH=/app/data/halol_crypto.db \
    LOG_FILE=/app/data/halol_crypto.log \
    PORT=8080

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "bot.py"]
