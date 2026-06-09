#!/usr/bin/env bash
# Starts the HANDOFF Streamlit app and opens it in the default browser.

set -e
cd "$(dirname "$0")"

python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py --server.headless false --browser.serverAddress localhost

