#!/bin/bash

# Kill background processes on exit
trap "kill 0" EXIT

echo "🚀 Starting NBA Agent System..."

# Start Backend (FastAPI)
echo "📦 Starting Backend (FastAPI) on port 8000..."
poetry run uvicorn api.main_app:app --reload --port 8000 &

# Start Frontend (Vite)
echo "🌐 Starting Frontend (Vite) on port 5173..."
cd frontend && npm run dev &

# Wait for both processes
wait
