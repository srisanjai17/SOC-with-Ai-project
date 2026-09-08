# ═══════════════════════════════════════════════════════════════════
# SOC with AI — Production Dockerfile
# Multi-stage build for minimal image size and fast builds
# ═══════════════════════════════════════════════════════════════════

# ── Stage 1: Builder ──────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies for compiled packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for Docker layer caching
COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Production ──────────────────────────────────────────
FROM python:3.12-slim AS production

# Security: run as non-root user
RUN groupadd -r socuser && useradd -r -g socuser -d /app -s /sbin/nologin socuser

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Copy application code
COPY src/ ./src/
COPY static/ ./static/
COPY templates/ ./templates/
COPY config.yaml .
COPY server.py .
COPY demo.py .

# Create data directories
RUN mkdir -p /app/data /app/logs && \
    chown -R socuser:socuser /app

# Switch to non-root user
USER socuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SOC_HOST=0.0.0.0 \
    SOC_PORT=8000 \
    SOC_WORKERS=4 \
    PYTHONIOENCODING=utf-8

# Start command
CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8000"]


# ═══════════════════════════════════════════════════════════════════
# Development variant: docker build --target dev .
# ═══════════════════════════════════════════════════════════════════
FROM python:3.12-slim AS dev

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install dev dependencies
RUN pip install --no-cache-dir pytest httpx

COPY . .

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=0 \
    PYTHONIOENCODING=utf-8

CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8000", "--reload"]
