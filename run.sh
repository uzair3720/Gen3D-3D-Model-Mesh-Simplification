#!/bin/bash
# Start the Gen3D Inspector, then open http://127.0.0.1:5000 in a browser.
cd "$(dirname "$0")"
.venv/bin/python app/server.py
