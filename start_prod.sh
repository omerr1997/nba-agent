#!/bin/bash
# Production startup script
# Builds the React frontend as static files and runs the FastAPI backend
# with multiple workers for concurrency.
#
# Usage:
#   CORS_ORIGINS=https://yourapp.com bash start_prod.sh

set -e

echo "🏗️  Building frontend for production..."
cd frontend
npm install --silent
npm run build
cd ..

echo "🚀 Starting production backend..."
echo "   Workers: ${WORKERS:-2}"
echo "   Port: ${PORT:-8000}"
echo "   CORS: ${CORS_ORIGINS:-*}"

poetry run uvicorn main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers "${WORKERS:-2}"
