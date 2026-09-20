#!/bin/bash
set -e

export PORT=${PORT:-8000}
export INTERNAL_HTTP_PORT=8001
export HTTP_PORT=${INTERNAL_HTTP_PORT}
export WS_PORT=8765

echo "=================================================="
echo " Starting NeuroSim Production Cloud Container"
echo " Public Port:        ${PORT}"
echo " Internal HTTP:      ${INTERNAL_HTTP_PORT}"
echo " Internal WebSocket: ${WS_PORT}"
echo "=================================================="

mkdir -p /app/db/backups /app/logs

# Substitute PORT, INTERNAL_HTTP_PORT, WS_PORT in nginx config
envsubst '${PORT} ${INTERNAL_HTTP_PORT} ${WS_PORT}' < /app/nginx.conf.template > /etc/nginx/conf.d/default.conf

# Start Python backend server in background
python /app/server.py --no-browser &
BACKEND_PID=$!

# Trap signals for graceful container shutdown
trap 'nginx -s quit; kill -TERM $BACKEND_PID 2>/dev/null || true; wait $BACKEND_PID 2>/dev/null || true; exit 0' SIGTERM SIGINT

# Start Nginx in foreground
nginx -g 'daemon off;'
