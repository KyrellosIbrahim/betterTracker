#!/bin/bash
# Stop and remove the BetterTracker backend LaunchAgent.
set -euo pipefail

LABEL="com.bettertracker.backend"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"

launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || echo "(agent was not loaded)"
rm -f "$PLIST"

echo "Removed $LABEL (logs under ~/Library/Logs/bettertracker are kept)"
