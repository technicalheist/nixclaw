#!/usr/bin/env bash
# Example: Start the REST API server
# Tasks can be submitted via HTTP after this

# Default port (8000)
nixclaw --serve

# Custom port
nixclaw --serve --port 3000

# Then use curl to interact (see api/ examples for details):
# curl http://localhost:8000/api/v1/health
# curl -X POST http://localhost:8000/api/v1/tasks -H "Content-Type: application/json" -d '{"task": "List files"}'
