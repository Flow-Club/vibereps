# Local Monitoring Stack

View Claude Code metrics locally with Prometheus + Grafana.

## Quick Start

```bash
# Start the monitoring stack
docker-compose up -d

# Configure Claude Code to export metrics
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

## Access

- **Grafana**: http://localhost:3030 (admin / vibereps)
- **Prometheus**: http://localhost:9090
- **Gym Whiteboard**: Open `monitoring/whiteboard.html` directly in browser

### Gym Whiteboard Dashboard

A custom gym-style chalkboard showing tokens, code stats, and exercise reps.

```bash
# Just open the file directly
open monitoring/whiteboard.html      # macOS
xdg-open monitoring/whiteboard.html  # Linux
```

The dashboard fetches data from Prometheus (CORS enabled) and auto-refreshes every 30 seconds.

## Available Metrics

Claude Code exports these metrics (prefixed with `claude_code_`):

- `session_count` - Number of sessions
- `tokens_input` / `tokens_output` - Token usage
- `tokens_cache_read` / `tokens_cache_write` - Cache usage
- `lines_of_code_accepted` - Code accepted
- `cost_usd` - Cost (API billing only)
- `commits_count` / `pull_requests_count` - Git activity

## Stop

```bash
docker-compose down
```

## Persist Data

Data is stored in Docker volumes. To reset:

```bash
docker-compose down -v
```
