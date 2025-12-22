#!/bin/bash

# Azure App Service Startup Script - DEBUG VERSION

echo "=========================================="
echo "=== DEBUG: HSBC IWPB UW API Startup ==="
echo "=========================================="

echo ""
echo "=== DEBUG: Current working directory ==="
pwd

echo ""
echo "=== DEBUG: List /home/site/wwwroot ==="
ls -la /home/site/wwwroot/ || echo "ERROR: Cannot list /home/site/wwwroot"

echo ""
echo "=== DEBUG: List /home/site/wwwroot/src (if exists) ==="
ls -la /home/site/wwwroot/src/ 2>/dev/null || echo "WARNING: /home/site/wwwroot/src does not exist"

echo ""
echo "=== DEBUG: Check for pyproject.toml ==="
if [ -f /home/site/wwwroot/pyproject.toml ]; then
    echo "FOUND: pyproject.toml exists"
    cat /home/site/wwwroot/pyproject.toml
else
    echo "ERROR: pyproject.toml NOT FOUND!"
fi

echo ""
echo "=== DEBUG: Check for startup.sh ==="
if [ -f /home/site/wwwroot/startup.sh ]; then
    echo "FOUND: startup.sh exists"
else
    echo "WARNING: startup.sh not found in wwwroot"
fi

echo ""
echo "=== DEBUG: Python version ==="
python --version

echo ""
echo "=== DEBUG: Environment variables ==="
env | grep -E "PYTHON|HOME|PATH|WEBSITE|SCM" | sort

echo ""
echo "=== DEBUG: Disk space ==="
df -h /home

echo "=========================================="
echo "=== END DEBUG - Starting actual setup ==="
echo "=========================================="

cd /home/site/wwwroot

# Set Python path
export PYTHONPATH=/home/site/wwwroot:$PYTHONPATH

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install dependencies using uv from pyproject.toml
echo "Installing dependencies with uv..."
uv pip install --system ".[api]"

echo "Dependencies installed successfully"

# Start the application with uvicorn
echo "Starting uvicorn server..."
exec python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
