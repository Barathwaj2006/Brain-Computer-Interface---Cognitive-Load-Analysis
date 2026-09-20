# =====================================================================
# NeuroSim Production Web & Scientific API Container
# Multi-Process Architecture: Nginx Reverse Proxy + Python Backend
# =====================================================================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install system dependencies (Nginx, envsubst, curl, procps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    gettext-base \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install lightweight Python dependencies
COPY requirements-server.txt /app/
RUN pip install --no-cache-dir -r requirements-server.txt

# Copy application assets and codebase
COPY server.py nginx.conf.template entrypoint.sh /app/
COPY web/ /app/web/
COPY src/ /app/src/
COPY models/ /app/models/

# Set executable permissions and create required mount directories
RUN chmod +x /app/entrypoint.sh && \
    mkdir -p /app/db/backups /app/logs /app/reports

# Expose default HTTP/WebSocket unified port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
