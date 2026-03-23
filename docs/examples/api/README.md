# REST API Examples

NixClaw includes a FastAPI server for HTTP-based task submission.

## Start the Server

```bash
nixclaw --serve              # Default port 8000
nixclaw --serve --port 3000  # Custom port
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/tasks` | Submit a task for background execution |
| `GET` | `/api/v1/tasks/{id}` | Get task status and result |
| `GET` | `/api/v1/tasks` | List all tasks |
| `POST` | `/api/v1/tasks/{id}/cancel` | Cancel a running task |
| `GET` | `/api/v1/agents/status` | Agent pool status |
| `GET` | `/api/v1/health` | System health check |

## Interactive Docs

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
