#!/bin/bash
# Start the Procurement Intelligence Dashboard
# Sets up Python path and launches the dashboard

cd "$(dirname "$0")"
export PYTHONPATH="${PWD}:${PYTHONPATH}"

echo "Starting Procurement Intelligence Dashboard..."
echo "PYTHONPATH: $PYTHONPATH"
echo ""

python dashboard/app.py
