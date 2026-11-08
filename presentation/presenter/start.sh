#!/bin/sh
# Opens the slides window (OBS captures this) and the script window (only you see this).
cd "$(dirname "$0")/.."
python3 -m http.server 8765 --bind 127.0.0.1 >/dev/null 2>&1 &
SERVER=$!
trap 'kill $SERVER' EXIT INT TERM
sleep 1
U=http://127.0.0.1:8765/presenter/index.html
# One profile for both windows, or they cannot talk to each other. The flags stop macOS
# freezing the slides window when the script window covers it.
FLAGS="--user-data-dir=/tmp/presenter-brave --disable-backgrounding-occluded-windows --disable-renderer-backgrounding --disable-background-timer-throttling --autoplay-policy=no-user-gesture-required"
open -na "Brave Browser" --args $FLAGS --app="$U?view=audience" --window-size=1280,720
sleep 3
open -na "Brave Browser" --args $FLAGS --app="$U" --window-size=1400,850
echo "Presenter running. Press Ctrl-C here when you have finished recording."
wait $SERVER
