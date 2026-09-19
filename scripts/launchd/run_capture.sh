#!/bin/bash
# ExecStart for the com.bettertracker.backend LaunchAgent.
#
# Keeps the Steam session poller alive: sessions are only recorded while uvicorn
# is up and can never be backfilled, so this is the highest-value part of the
# project (see ROADMAP.md "Phase 0").
#
# Location-independent: the backend dir is resolved relative to this script, so
# the committed file has no machine-specific paths.
set -uo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../backend" && pwd)"
cd "$BACKEND_DIR"

VENV="$BACKEND_DIR/venv"

# Apply committed (already-reviewed) migrations before serving. Non-fatal: the
# game_sessions table is stable, so a health-migration hiccup must not stop
# capture from starting.
if [ -x "$VENV/bin/alembic" ]; then
  "$VENV/bin/alembic" upgrade head || echo "[run_capture] alembic upgrade failed; starting anyway"
fi

# `exec` so launchd tracks uvicorn directly (KeepAlive + signal handling).
# No --reload (that's for development). Single worker on purpose: extra workers
# would each start their own Steam poller and record duplicate sessions.
exec "$VENV/bin/uvicorn" main:app --host 127.0.0.1 --port 8000
