# Monitoring

The `monitoring/` directory contains a Docker Compose stack for visualizing Claude Code usage alongside exercise data.

## Components

| Component | Port | Purpose |
|-----------|------|---------|
| OTEL Collector | 4317 | Receives OpenTelemetry metrics |
| Prometheus | 9090 | Time-series database |
| Pushgateway | 9091 | Accepts custom metrics from hooks |
| Grafana | 3000 | Dashboard visualization |

## Quick Start

### 1. Enable Claude Code Telemetry

Add to your shell profile:

```bash
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### 2. Start the Stack

```bash
cd monitoring
docker-compose up -d
```

### 3. View Dashboard

Open `http://localhost:3000` (default: admin/admin)

A pre-configured dashboard is included.

## Available Metrics

### From Claude Code (via OTEL)

| Metric | Description |
|--------|-------------|
| `claude_code_session_count` | CLI sessions started |
| `claude_code_token_usage_tokens_total` | Tokens by type (input/output/cache) |
| `claude_code_cost_usage_usd_total` | Cost by model |
| `claude_code_lines_of_code_count_total` | Lines added/removed |
| `claude_code_code_edit_tool_decision_total` | Edit accepts/rejects |
| `claude_code_active_time_total_seconds_total` | CLI active time |

### From Hooks (via Pushgateway)

| Metric | Description |
|--------|-------------|
| `exercise_reps_total` | Exercise reps by type |
| `exercise_sessions_total` | Exercise session count |
| `claude_project_session_total` | Sessions by project/branch |

## Enable Pushgateway

Set the environment variable:

```bash
export PUSHGATEWAY_URL=http://localhost:9091
```

The exercise tracker will automatically push metrics on completion.

## Custom Dashboards

### Grafana Query Examples

**Reps per day**:
```promql
sum(increase(exercise_reps_total[24h])) by (exercise)
```

**Cost per session**:
```promql
rate(claude_code_cost_usage_usd_total[1h])
```

**Token usage**:
```promql
sum(rate(claude_code_token_usage_tokens_total[5m])) by (type)
```

## OTEL Configuration

Key environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_CODE_ENABLE_TELEMETRY` | 0 | Must be 1 to enable |
| `OTEL_METRIC_EXPORT_INTERVAL` | 60000 | Export interval (ms) |
| `OTEL_RESOURCE_ATTRIBUTES` | - | Custom labels |

### Add Custom Labels

```bash
export OTEL_RESOURCE_ATTRIBUTES="team=platform,env=dev"
```

## Troubleshooting

**No metrics appearing?**
1. Check telemetry is enabled: `echo $CLAUDE_CODE_ENABLE_TELEMETRY`
2. Verify collector is running: `docker ps | grep otel`
3. Check collector logs: `docker logs monitoring-otel-collector-1`

**Pushgateway not receiving data?**
1. Check URL is set: `echo $PUSHGATEWAY_URL`
2. Test connectivity: `curl http://localhost:9091/metrics`
3. Check exercise_tracker.py logs

## Reference

Full OTEL configuration options: https://code.claude.com/docs/en/monitoring-usage
