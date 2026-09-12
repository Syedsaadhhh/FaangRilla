#!/usr/bin/env bash
# OpenDoor Relay - Run Local Environment (POSIX Bash)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Starting OpenDoor Relay Backend on http://127.0.0.1:8000..."
"$ROOT_DIR/backend/.venv/bin/python" -m uvicorn opendoor_relay.api.app:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

echo "Starting OpenDoor Relay Frontend on http://127.0.0.1:5173..."
(cd "$ROOT_DIR/frontend" && npm run dev) &
FRONTEND_PID=$!

cleanup() {
  echo "Stopping services..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo ""
echo "OpenDoor Relay is running!"
echo "  - Frontend: http://localhost:5173"
echo "  - Backend API: http://127.0.0.1:8000"
echo "Press Ctrl+C to stop all services."
wait
