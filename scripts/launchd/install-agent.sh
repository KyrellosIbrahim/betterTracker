#!/bin/bash
# Install (or reinstall) the BetterTracker backend LaunchAgent so Steam session
# capture runs at login and restarts on crash. Idempotent — safe to re-run after
# pulling changes.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../../backend" && pwd)"
RUN_SCRIPT="$SCRIPT_DIR/run_capture.sh"
LABEL="com.bettertracker.backend"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG_DIR="$HOME/Library/Logs/bettertracker"
DOMAIN="gui/$(id -u)"

# Preflight: the agent is useless without the venv the backend runs in.
if [ ! -x "$BACKEND_DIR/venv/bin/uvicorn" ]; then
  echo "error: $BACKEND_DIR/venv/bin/uvicorn not found — create the venv and 'make install' first." >&2
  exit 1
fi

mkdir -p "$LOG_DIR" "$HOME/Library/LaunchAgents"
chmod +x "$RUN_SCRIPT"

# Render the template with this machine's absolute paths. '|' delimiter so paths
# with '/' don't need escaping.
sed \
  -e "s|__RUN_SCRIPT__|$RUN_SCRIPT|g" \
  -e "s|__BACKEND_DIR__|$BACKEND_DIR|g" \
  -e "s|__LOG_DIR__|$LOG_DIR|g" \
  "$SCRIPT_DIR/$LABEL.plist.template" > "$PLIST"

plutil -lint "$PLIST"

# Replace any existing instance, then load + enable. bootout is best-effort
# (it errors if not currently loaded).
launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
launchctl bootstrap "$DOMAIN" "$PLIST"
launchctl enable "$DOMAIN/$LABEL"

echo "Installed $LABEL"
echo "  backend : $BACKEND_DIR"
echo "  logs    : $LOG_DIR/backend.log"
echo "  status  : launchctl print $DOMAIN/$LABEL"
