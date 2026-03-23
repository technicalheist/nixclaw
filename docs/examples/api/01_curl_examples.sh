#!/usr/bin/env bash
# API examples using curl
# First start the server: nixclaw --serve

BASE="http://localhost:8000/api/v1"

echo "=== Health Check ==="
curl -s "$BASE/health" | python3 -m json.tool

echo -e "\n=== Submit a Task ==="
TASK_RESPONSE=$(curl -s -X POST "$BASE/tasks" \
    -H "Content-Type: application/json" \
    -d '{"task": "List all files in /tmp", "priority": "normal"}')
echo "$TASK_RESPONSE" | python3 -m json.tool

# Extract task_id
TASK_ID=$(echo "$TASK_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['task_id'])")
echo "Task ID: $TASK_ID"

echo -e "\n=== Poll Task Status ==="
sleep 2
curl -s "$BASE/tasks/$TASK_ID" | python3 -m json.tool

echo -e "\n=== List All Tasks ==="
curl -s "$BASE/tasks" | python3 -m json.tool

echo -e "\n=== Agent Status ==="
curl -s "$BASE/agents/status" | python3 -m json.tool

echo -e "\n=== Submit with Team Profiles ==="
curl -s -X POST "$BASE/tasks" \
    -H "Content-Type: application/json" \
    -d '{
        "task": "Write a hello world script in Python",
        "priority": "high",
        "agent_profiles": ["CodeGenerator"]
    }' | python3 -m json.tool

echo -e "\n=== Submit with Webhook Callback ==="
curl -s -X POST "$BASE/tasks" \
    -H "Content-Type: application/json" \
    -d '{
        "task": "Check disk usage",
        "callback_url": "https://your-server.com/webhook"
    }' | python3 -m json.tool

echo -e "\n=== Cancel a Task ==="
curl -s -X POST "$BASE/tasks/$TASK_ID/cancel" | python3 -m json.tool
