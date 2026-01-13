# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an exercise tracking system for Claude Code that encourages movement breaks during coding sessions.

**Local Components:**

- **Exercise Tracker Hook** (`exercise_tracker.py` + `exercise_ui.html`) - Launches exercise UI when you submit prompts or complete tasks
- **Notification Hook** (`notify_complete.py`) - Notifies you when Claude finishes while you're exercising

**Remote Server** (`server/`):

- REST API for logging exercises from the local hook
- MCP HTTP transport for Claude Code to query stats, leaderboards, streaks
- Multi-user support with API key authentication

Pose detection uses configurable engines (MediaPipe, TensorFlow.js, or simple) via browser webcam to count reps (squats, push-ups, jumping jacks). Video never leaves your browser.

## Architecture

```
Local                                   Remote Server
─────                                   ─────────────
exercise_tracker.py ──POST /api/log──▶  FastAPI (server/main.py)
exercise_ui.html                        ├── REST API (for hook)
                                        └── MCP HTTP (for Claude)

Claude Code ────────MCP over HTTP────▶  /mcp endpoint
                                        ├── get_stats
                                        ├── get_leaderboard
                                        ├── check_streak
                                        └── log_exercise_session
```

### Local Hook (`exercise_tracker.py` + `exercise_ui.html`)

- Launches a local HTTP server (port 8765) serving the UI from `exercise_ui.html`
- Supports two modes:
  - **Quick Mode** (`user_prompt_submit`): 5 reps while Claude works
  - **Normal Mode** (`task_complete`): 10+ reps after Claude finishes
- On exercise completion, POSTs to remote server (if configured via `VIBEREPS_API_URL`)
- The HTML file contains all UI logic and MediaPipe integration (loaded from CDN)
- Exercise detection happens entirely client-side using pose landmark angles

### Notification System (`notify_complete.py`)

- Triggered by `PostMessage` hook when Claude sends a message
- Sends HTTP POST to `http://localhost:8765/notify` to signal completion
- Exercise tracker UI polls `/status` endpoint to detect when Claude is ready
- Shows desktop notification and updates UI when complete

### Remote Server (`server/main.py`)

- **REST API** (`/api/*`) - For local hook to POST exercise sessions
- **MCP HTTP Transport** (`/mcp`) - For Claude Code to query stats
- SQLite/PostgreSQL storage with user accounts and API keys
- Provides tools: `log_exercise_session`, `get_stats`, `get_leaderboard`, `check_streak`, `get_progress_today`

## Key Implementation Details

### Detection Engines

The system supports three pose detection engines, configurable via `./configure.py`:

| Engine | Accuracy | Speed | Dependencies | Use Case |
|--------|----------|-------|--------------|----------|
| **MediaPipe** | Best | Medium | CDN (requires internet) | Default, most accurate |
| **TensorFlow** | Good | Fast | CDN (caches offline) | Low latency, works offline |
| **Simple** | Basic | Fastest | None | Minimal resources, older devices |

Configuration stored in `config.json`:
```json
{
  "detection_engine": "mediapipe",
  "detection_engines": {
    "mediapipe": { "model_complexity": 1 },
    "tensorflow": { "model_type": "lightning" },
    "simple": { "smoothing": true }
  }
}
```

### Exercise Detection Logic

Located in `exercise_ui.html`:
- **Squats**: Hip-knee-ankle angle < 100° (down) → > 160° (up) = 1 rep
- **Push-ups**: Shoulder-elbow-wrist angle < 90° (down) → > 150° (up) = 1 rep
- **Jumping Jacks**: Arms above shoulders (up) → below (down) = 1 rep
- State machine prevents double-counting with `exerciseState` tracking

### Data Flow

**Quick Mode:**

1. User submits prompt → `UserPromptSubmit` hook triggers
2. `exercise_tracker.py` launches with `?quick=true` parameter
3. User does 5 quick exercises while Claude works
4. Exercise complete → Hook POSTs to remote server → UI polls `/status`
5. Claude sends message → `PostMessage` hook triggers
6. `notify_complete.py` POSTs to `/notify` endpoint
7. UI detects completion, shows notification, user returns to Claude

**Normal Mode:**

Browser → POST `/complete` → Hook POSTs to remote → Exit

**Claude Queries:**

Claude Code → MCP HTTP request → Remote server → JSON response

## Testing & Development

### Run the Remote Server

```bash
cd server
pip install -r requirements.txt
python main.py
```

Server runs at http://localhost:8000. Create a user to get an API key:

```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"username": "yourname"}'
```

### Test Local Hook (Quick Mode)

```bash
# Set environment variables for remote logging
export VIBEREPS_API_URL=http://localhost:8000
export VIBEREPS_API_KEY=your_api_key_here

# Test the exercise tracker
./exercise_tracker.py user_prompt_submit '{}'

# In another terminal, test the notification
./notify_complete.py '{}'
```

### Test Local Hook (Normal Mode)

```bash
./exercise_tracker.py task_complete '{}'
```

### Test MCP Endpoint

```bash
# List available tools
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

# Get stats (requires auth)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "get_stats", "arguments": {}}}'
```

## Configuration

### 1. Environment Variables (Local Hook)

Set these to enable remote logging:

```bash
export VIBEREPS_API_URL=https://your-server.com
export VIBEREPS_API_KEY=your_api_key_here
```

### 2. Hook Setup

Exercise while Claude works! Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "type": "command",
        "command": "/path/to/exercise_tracker.py user_prompt_submit '{}'"
      }
    ],
    "PostMessage": [
      {
        "type": "command",
        "command": "/path/to/notify_complete.py '{}'"
      }
    ]
  }
}
```

### 3. Claude Code MCP Setup (Remote)

Add to your MCP settings to give Claude access to stats:

```json
{
  "mcpServers": {
    "vibereps": {
      "type": "http",
      "url": "https://your-server.com/mcp",
      "headers": {
        "X-API-Key": "your_api_key_here"
      }
    }
  }
}
```

Then Claude can use tools like `get_leaderboard`, `check_streak`, etc.

## Customization Points

### Change Detection Engine

Run the configuration script to switch between detection engines:
```bash
./configure.py                    # Interactive configuration
./configure.py --engine mediapipe # Direct selection
./configure.py --show             # View current config
```

### Change Target Reps

Edit `targetReps` (normal mode) or `quickModeReps` (quick mode) objects in `exercise_ui.html`:
```javascript
let targetReps = {squats: 10, pushups: 10, jumping_jacks: 20};
let quickModeReps = {squats: 5, pushups: 5, jumping_jacks: 10};
```

### Change Detection Sensitivity

Modify angle thresholds in `detectSquat`, `detectPushup`, `detectJumpingJack` functions in `exercise_ui.html`.

### Change Server Port

Edit `self.port = 8765` in `ExerciseTrackerHook.__init__` in `exercise_tracker.py`.

### Adjust Goals

Goals are stored per-user in the remote database. Default: 50 reps/day, 3 sessions/day.

## Dependencies

- **Local Hook**: Python 3 standard library only (http.server, webbrowser, threading)
- **Remote Server**: FastAPI, SQLAlchemy, uvicorn, mcp (see `server/requirements.txt`)
- **Browser Detection Engines**:
  - MediaPipe: Loaded from CDN (requires internet)
  - TensorFlow.js: Loaded from CDN, caches for offline use
  - Simple: No external dependencies

## Local Monitoring Stack

The `monitoring/` directory contains a Docker Compose stack for visualizing Claude Code usage metrics alongside exercise data.

### Components

- **OTEL Collector** - Receives OpenTelemetry metrics from Claude Code
- **Prometheus** - Time-series database for metrics storage
- **Pushgateway** - Accepts custom metrics from hooks (exercises, project tracking)
- **Grafana** - Dashboard visualization (pre-configured dashboard included)

### Setup

```bash
# Enable Claude Code telemetry (add to shell profile)
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Start monitoring stack
cd monitoring
docker-compose up -d

# View Grafana dashboard
open http://localhost:3000  # Default: admin/admin
```

### Available Metrics

**From Claude Code (via OTEL):**
- `claude_code_session_count` - CLI sessions started
- `claude_code_token_usage_tokens_total` - Tokens by type (input/output/cache)
- `claude_code_cost_usage_usd_total` - Cost by model
- `claude_code_lines_of_code_count_total` - Lines added/removed
- `claude_code_code_edit_tool_decision_total` - Edit accepts/rejects
- `claude_code_active_time_total_seconds_total` - CLI active time

**From Hooks (via Pushgateway):**
- `exercise_reps_total` - Exercise reps by type
- `exercise_sessions_total` - Exercise session count
- `claude_project_session_total` - Sessions by project/branch

### Reference

For complete OTEL configuration options, see: https://code.claude.com/docs/en/monitoring-usage

Key environment variables:
- `CLAUDE_CODE_ENABLE_TELEMETRY=1` - Required to enable telemetry
- `OTEL_METRIC_EXPORT_INTERVAL=10000` - Export interval in ms (default 60000)
- `OTEL_RESOURCE_ATTRIBUTES` - Add custom labels (e.g., `team=platform`)

## Privacy & Security

- All video processing happens client-side in browser (JavaScript)
- No video data transmitted or stored - only rep counts go to server
- Local hook server only listens on localhost:8765
- Remote server uses API key authentication
- Exercise data (reps, timestamps) stored on remote server for stats/leaderboards
- Telemetry is opt-in and never includes sensitive data (API keys, file contents)