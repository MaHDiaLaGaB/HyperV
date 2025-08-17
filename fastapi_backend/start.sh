#!/usr/bin/env bash
set -e

if [ -f /.dockerenv ]; then
  echo "🐳 Inside Docker: starting FastAPI"
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
  python watcher.py
else
  echo "🚀 Running locally with uv"
  uv run fastapi dev app/main.py --host 0.0.0.0 --port 8000 --reload &
  uv run python watcher.py
fi

wait
