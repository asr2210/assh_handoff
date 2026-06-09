#!/usr/bin/env bash
# Double-click launcher for macOS.
# Starts the HANDOFF Streamlit app and opens it in the default browser.

set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found."
  read -r -p "Press Enter to close."
  exit 1
fi

python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py --server.headless false --browser.serverAddress localhost

