#!/bin/sh
set -e

# Run database migrations
echo "Running database migrations..."
uv run alembic -c alembic/alembic.ini upgrade head

# Start the server
echo "Starting TrailerPark..."
exec uv run uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8000}"
