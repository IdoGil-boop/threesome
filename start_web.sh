#!/usr/bin/env bash
# Start the Threesome web server

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install dependencies if needed
pip install -q fastapi uvicorn pydantic

echo "Starting Threesome web server..."
echo "Open your browser to: http://localhost:8000"
echo ""

cd web
python server.py

