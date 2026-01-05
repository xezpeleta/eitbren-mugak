#!/bin/bash
# Simple HTTP server for testing the website locally

cd "$(dirname "$0")"
echo "Starting HTTP server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""
python3 -m http.server 8000
