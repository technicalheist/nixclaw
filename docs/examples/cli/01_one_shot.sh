#!/usr/bin/env bash
# Example: One-shot task execution
# Run a single task and get the result

# Simple task
nixclaw "List all Python files in the current directory"

# With streaming disabled (just print final result)
nixclaw --no-stream "What is 2 + 2?"

# Using python -m
python -m nixclaw "Explain what a REST API is in 3 sentences"
