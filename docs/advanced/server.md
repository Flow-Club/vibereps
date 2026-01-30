# Remote Server

::: warning IN PROGRESS
The remote server is **not yet deployed**. This documentation is for future reference. Currently, all exercise data is logged locally to `~/.vibereps/exercises.jsonl`.
:::

The optional remote server will provide stats, leaderboards, and streaks across multiple users.

## Features

- **REST API** - For local hook to POST exercise sessions
- **MCP HTTP Transport** - For Claude Code to query stats
- **Multi-user support** with API key authentication
- **SQLite/PostgreSQL** storage

## Quick Start

```bash
cd server
pip install -r requirements.txt
python main.py
```

Server runs at `http://localhost:8000`.

## Create a User

```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"username": "yourname"}'
```

Response includes your API key:

```json
{
  "username": "yourname",
  "api_key": "vr_abc123..."
}
```

## Configure Local Hook

Set environment variables:

```bash
export VIBEREPS_API_URL=http://localhost:8000
export VIBEREPS_API_KEY=vr_abc123...
```

Now exercise completions will be logged to the server.

## API Endpoints

### REST API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users` | POST | Create user, returns API key |
| `/api/log` | POST | Log exercise session |
| `/api/stats` | GET | Get user statistics |

### MCP Endpoint

The server exposes MCP tools at `/mcp`:

| Tool | Description |
|------|-------------|
| `log_exercise_session` | Log a completed session |
| `get_stats` | Get user's exercise statistics |
| `get_leaderboard` | View top users |
| `check_streak` | Check current streak |
| `get_progress_today` | Today's progress toward goals |

## Claude Code Integration

Add to your MCP settings (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "vibereps": {
      "type": "http",
      "url": "https://your-server.com/mcp",
      "headers": {
        "X-API-Key": "vr_abc123..."
      }
    }
  }
}
```

Now Claude can query your stats:

> "How many reps have I done this week?"
> "What's my current streak?"
> "Show me the leaderboard"

## Test MCP Endpoint

```bash
# List available tools
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

# Get stats (requires auth)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-Key: vr_abc123..." \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "get_stats", "arguments": {}}}'
```

## Deployment

### Environment Variables

```bash
DATABASE_URL=postgresql://user:pass@host/db  # Or use SQLite
SECRET_KEY=your-secret-key
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY server/ .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

### Production

For production, consider:
- PostgreSQL instead of SQLite
- Reverse proxy (nginx/caddy)
- HTTPS via Let's Encrypt
- Rate limiting
