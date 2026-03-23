#!/usr/bin/env bash
# Example: Real-world task examples you can run with NixClaw

# --- Code tasks ---
nixclaw "Write a Python script that monitors CPU usage every 5 seconds and logs it to a file"

nixclaw "Create a Flask hello-world app with a /health endpoint"

nixclaw --team CodeGenerator,Analyzer \
    "Write a Python class for a binary search tree with insert, search, and delete methods. Review it."

# --- Analysis tasks ---
nixclaw "Read pyproject.toml and list all dependencies with their version constraints"

nixclaw "Search for all TODO comments in the codebase and summarize them"

nixclaw "Analyze the project directory structure and suggest improvements"

# --- System tasks ---
nixclaw "Check disk usage on all mounted partitions"

nixclaw "List all running Python processes"

nixclaw "Show the last 20 lines of /var/log/syslog"

# --- Research tasks ---
nixclaw "Explain the difference between asyncio.gather and asyncio.wait in Python"

nixclaw "What are the OWASP top 10 security risks? Summarize each in one sentence"
