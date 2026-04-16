#!/usr/bin/env bash
# ============================================================
# RAG Pipeline — Start both services in one terminal
# Usage: bash start.sh
# ============================================================
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
UI="$ROOT/ui"

# ---- Check .env ----
if [ ! -f "$BACKEND/.env" ]; then
  echo "[warn] $BACKEND/.env not found — copying from .env.example"
  cp "$BACKEND/.env.example" "$BACKEND/.env"
  echo "[warn] Edit $BACKEND/.env and add your API key, then re-run."
  exit 1
fi

# ---- Backend ----
echo "[start] Launching FastAPI backend on :8000 …"
cd "$BACKEND"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# ---- Frontend ----
echo "[start] Launching Next.js UI on :3000 …"
cd "$UI"

if [ ! -f ".env.local" ]; then
  cp ".env.local.example" ".env.local"
fi

if [ ! -d "node_modules" ]; then
  echo "[start] Installing UI dependencies …"
  npm install
fi

npm run dev &
UI_PID=$!

echo ""
echo "  Backend : http://localhost:8000/docs"
echo "  UI      : http://localhost:3000"
echo ""
echo "  Press Ctrl+C to stop both services."

trap "kill $BACKEND_PID $UI_PID 2>/dev/null; echo 'Stopped.'" INT TERM
wait
