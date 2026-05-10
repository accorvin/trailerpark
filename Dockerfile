# Stage 1: Build frontend
FROM node:22-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python app
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install Python dependencies
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy backend source
COPY backend/ ./

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# Create data directory (will be overridden by Railway volume mount)
RUN mkdir -p /app/data

# Copy start script
COPY scripts/start-server.sh ./start-server.sh
RUN chmod +x ./start-server.sh

EXPOSE 8000

CMD ["./start-server.sh"]
