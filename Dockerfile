# ── Titanic EDA — Production Dockerfile ───────────────────────────────────────
# Multi-stage build: builder stage installs deps; final stage is lean.

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="your-email@example.com"
LABEL description="Titanic EDA API — FastAPI + Pandas + Seaborn"

# Non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy source code
COPY --chown=appuser:appuser . .

# Create output directories and set permissions
RUN mkdir -p output/charts output/reports output/cleaned_data data && \
    chown -R appuser:appuser /app

# Switch to non-root
USER appuser

# Matplotlib non-interactive backend (also set in visualizations.py)
ENV MPLBACKEND=Agg
ENV APP_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Health check — probes the /api/health endpoint every 30 s
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

# Gunicorn with Uvicorn workers for production
CMD ["gunicorn", "app:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
