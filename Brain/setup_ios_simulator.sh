#!/usr/bin/env bash
# One-off setup for the ios_sim INPUT_BACKEND: boots the simulator, starts the
# Appium server if needed, and opens the 2048 web game in Safari on it.
set -euo pipefail

SIMULATOR_UDID="FB9FD78D-8C2B-4B7F-8219-DC99CFC4F4CC"  # iPhone 17, iOS 26.5
APPIUM_PORT=4723
GAME_URL="https://play2048.co"

if ! xcrun simctl list devices booted | grep -q "$SIMULATOR_UDID"; then
    echo "Booting simulator $SIMULATOR_UDID..."
    xcrun simctl boot "$SIMULATOR_UDID"
    open -a Simulator
    sleep 3
else
    echo "Simulator already booted."
fi

if ! pgrep -f "appium --port $APPIUM_PORT" > /dev/null; then
    echo "Starting Appium server on port $APPIUM_PORT..."
    nohup appium --port "$APPIUM_PORT" > /tmp/appium_server.log 2>&1 &
    disown
    sleep 3
else
    echo "Appium server already running."
fi

echo "Opening $GAME_URL in Safari on the simulator..."
xcrun simctl openurl "$SIMULATOR_UDID" "$GAME_URL"

echo "Done. Simulator is ready with 2048 loaded in Safari."
