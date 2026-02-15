#!/bin/bash
# Run bot manually (for development/testing)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load env if exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Validate required vars
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ BOT_TOKEN not set!"
    echo "Create .env file or run: export BOT_TOKEN='your_token'"
    exit 1
fi

if [ -z "$GATEWAY_TOKEN" ]; then
    echo "❌ GATEWAY_TOKEN not set!"
    echo "Create .env file or run: export GATEWAY_TOKEN='your_token'"
    exit 1
fi

echo "🥗 Starting Nutrition Bot v2..."
python3 main.py
