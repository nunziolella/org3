# Stage 1: Build Frontend Web App
FROM node:20-alpine AS frontend-builder
WORKDIR /app/web
COPY web/package.json ./
RUN npm install
COPY web/ ./
RUN npm run build

# Stage 2: Production Python API & Sovereign Control Plane
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install local org3 package
COPY pyproject.toml ./
COPY org3/ ./org3/
RUN pip install --no-cache-dir -e .

# Copy built frontend assets
COPY --from=frontend-builder /app/web/dist ./web/dist

ENV PORT=8005 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

EXPOSE 8005

CMD ["sh", "-c", "uvicorn org3.api.main:app --host 0.0.0.0 --port ${PORT:-8005}"]
