#!/usr/bin/env bash
# Example: Team mode — multiple agents collaborating
# An LLM picks which agent speaks at each step

# Two agents: one writes code, one reviews it
nixclaw --team CodeGenerator,Analyzer \
    "Write a Python function to validate email addresses, then review it for edge cases"

# Three agents: code, analyze, debug
nixclaw --team CodeGenerator,Analyzer,Debugger \
    "Create a file parser that reads CSV files. Review for bugs and fix any issues."

# Researcher + Analyzer for non-coding tasks
nixclaw --team Researcher,Analyzer \
    "Research best practices for Python project structure and summarize findings"

# Available profiles:
#   CodeGenerator  — writes and refactors code
#   Analyzer       — reviews code and provides insights
#   Researcher     — gathers and synthesizes information
#   SystemAdmin    — executes system commands
#   Debugger       — finds and fixes bugs
#   General        — general-purpose assistant
