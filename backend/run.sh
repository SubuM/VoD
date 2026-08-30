#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-8000}"
echo "Serving on http://127.0.0.1:$PORT  (Ctrl+C to stop)"
exec ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --reload --app-dir .