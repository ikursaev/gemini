#!/bin/bash
set -e

# Kill existing processes
echo "Killing existing Celery workers and Uvicorn processes..."
pkill -f "celery -A app.tasks worker" || true
fuser -k 8000/tcp || true
pkill -f "uvicorn app.main:app" || true

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Start Redis server (if not already running)
echo "Starting Redis server..."
sudo service redis-server start || true

# Start Celery worker in the background
echo "Starting Celery worker..."
celery -A app.tasks worker --loglevel=info &> celery_worker.log &

# Start FastAPI application
echo "Starting FastAPI application..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
