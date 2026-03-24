# NixClaw

Multi-agent AI system built on [nixagent](https://github.com/technicalheist/nixagent) for autonomous task execution.

NixClaw breaks down complex tasks, dynamically creates specialized AI agents, and orchestrates them to deliver results — all with human-in-the-loop capabilities via Telegram.

Supports **5 AI providers** out of the box: OpenAI, Anthropic, Gemini, Vertex AI, and Qwen.

## Installation

```bash
pip install nixclaw
```

With optional extras:

```bash
pip install nixclaw[all]        # Everything (API, Telegram, storage)
pip install nixclaw[api]        # REST API (FastAPI)
pip install nixclaw[telegram]   # Telegram bot integration
pip install nixclaw[storage]    # Database persistence (SQLAlchemy)
```

## Quick Start

### As a CLI tool

```bash
# One-shot task
nixclaw "Analyze the project structure and list all Python files"

# Interactive mode
nixclaw --interactive

# Team mode with specific agent profiles
nixclaw --team CodeGenerator,Analyzer "Build a REST API for user management"

# Start REST API server
nixclaw --serve

# Start Telegram bot
nixclaw --telegram
```

### As a Python library

```python
import asyncio
from nixclaw import Orchestrator

async def main():
    orchestrator = Orchestrator()
    result = await orchestrator.run("Analyze the codebase and find potential bugs")
    print(result)
    await orchestrator.close()

asyncio.run(main())
```

#### Advanced: Direct agent control

```python
import asyncio
from nixclaw import AgentFactory

async def main():
    factory = AgentFactory.get_instance()
    agent = await factory.create_agent("CodeGenerator")
    result = await agent.run("Write a Python function to calculate fibonacci numbers")
    print(agent.get_result_text(result))
    await factory.cleanup_all()

asyncio.run(main())
```

## Configuration

Create a `.env` file in your project root (see [.env.example](.env.example) for all options):

```env
# Select your AI provider
PROVIDER=openai   # openai | anthropic | gemini | vertex | qwen

# OpenAI / OpenAI-compatible
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# Anthropic
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_MODEL=claude-3-opus-20240229

# Google Gemini
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Vertex AI
VERTEX_API_KEY=your_api_key_here
VERTEX_MODEL=gemini-2.5-flash-lite

# Qwen (uses email + password, no API key)
QWEN_EMAIL=your_email_here
QWEN_PASSWORD=your_password_here
QWEN_MODEL=qwen3.5-plus

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_USER_IDS=your_user_id
```

## AI Provider Support

| Provider | Auth | Notes |
|----------|------|-------|
| **OpenAI** | API key | Also works with Ollama, vLLM, and any OpenAI-compatible endpoint |
| **Anthropic** | API key | Claude family of models |
| **Gemini** | API key | Google Gemini via OpenAI-compatible endpoint |
| **Vertex AI** | API key | Google Cloud Vertex AI |
| **Qwen** | Email + Password | Alibaba Qwen via [chat.qwen.ai](https://chat.qwen.ai) |

Switch provider by setting `PROVIDER=<name>` in your `.env` file.

## Agent Profiles

NixClaw includes 6 specialist agent profiles:

| Profile | Description |
|---------|-------------|
| **CodeGenerator** | Generates, modifies, and refactors code |
| **Analyzer** | Analyzes code, data, and systems for insights |
| **Researcher** | Gathers information and synthesizes findings |
| **SystemAdmin** | Executes system commands and manages infrastructure |
| **Debugger** | Investigates and fixes bugs systematically |
| **General** | General-purpose agent for miscellaneous tasks |

## REST API

Start the API server:

```bash
nixclaw --serve --port 8000
```

Endpoints:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/tasks` | Submit a task |
| GET | `/api/v1/tasks/{id}` | Get task status |
| GET | `/api/v1/tasks` | List all tasks |
| POST | `/api/v1/tasks/{id}/cancel` | Cancel a task |
| GET | `/api/v1/agents/status` | Agent overview |
| GET | `/api/v1/health` | Health check |

## Telegram Integration

NixClaw supports two Telegram bots:

- **Primary bot** (`TELEGRAM_BOT_TOKEN`): Receives commands (`/task`, `/status`, `/agents`) and sends task notifications
- **Log bot** (`TELEGRAM_BOT_TOKEN_LOG`): Mirrors all output from CLI, API, and Telegram to a dedicated log channel

## Architecture

```
nixclaw/
├── agents/          # Agent system (orchestrator, factory, profiles)
├── tools/           # Built-in tools (file ops, shell, search)
├── core/            # Task manager, context, event bus, retry, security
├── storage/         # Database persistence (SQLAlchemy + SQLite)
├── api/             # REST API (FastAPI)
└── integrations/    # Telegram, webhooks, LLM client
```

## License

MIT

