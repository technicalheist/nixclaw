#!/usr/bin/env bash
set -euo pipefail

echo "Setting up NixClaw..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate and install
echo "Installing dependencies..."
.venv/bin/pip install -r requirements.txt

# Copy .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "IMPORTANT: Edit .env with your API keys before running."
fi

# Create working directories
mkdir -p /tmp/agent_workdir /tmp/autogen-agent

echo ""
echo "Setup complete!"
echo "  1. Edit .env with your LLM API key"
echo "  2. Run: .venv/bin/python -m nixclaw --interactive"
echo ""
