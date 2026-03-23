# CLI Examples

NixClaw can be used directly from the terminal. All examples assume you have a `.env` file configured with your LLM API key.

## Installation

```bash
pip install nixclaw
```

## Quick Reference

```bash
# One-shot task
nixclaw "Your task here"

# Interactive mode
nixclaw --interactive

# Team mode
nixclaw --team CodeGenerator,Analyzer "Your task"

# Start REST API server
nixclaw --serve --port 8000

# Start Telegram bot
nixclaw --telegram

# Show help
nixclaw --help
```

## Examples

See the individual files in this directory for detailed examples.
