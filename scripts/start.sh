#!/usr/bin/env bash
set -e

# TrailerPark startup script for Unix
cd "$(dirname "$0")/.."

# Load port from .env or use default
PORT=8000
if [ -f backend/.env ]; then
    PORT_LINE=$(grep "^PORT=" backend/.env 2>/dev/null || true)
    if [ -n "$PORT_LINE" ]; then
        PORT="${PORT_LINE#PORT=}"
    fi
fi

echo "Starting TrailerPark on port $PORT..."

RESTART_COUNT=0
MAX_RESTARTS=5

while [ $RESTART_COUNT -lt $MAX_RESTARTS ]; do
    cd backend
    uv run uvicorn src.main:app --host 0.0.0.0 --port "$PORT" && break
    EXIT_CODE=$?
    cd ..

    RESTART_COUNT=$((RESTART_COUNT + 1))
    echo "TrailerPark crashed (exit code $EXIT_CODE). Restart $RESTART_COUNT/$MAX_RESTARTS..."
    sleep 5
done

if [ $RESTART_COUNT -ge $MAX_RESTARTS ]; then
    echo "TrailerPark has crashed $MAX_RESTARTS times. Giving up."
    echo "Check data/logs/trailerpark.log for details."
    exit 1
fi
