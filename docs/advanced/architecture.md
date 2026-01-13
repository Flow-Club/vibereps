# Architecture

## Overview

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

## Local Components

### Exercise Tracker (`exercise_tracker.py`)

A Python script that:
1. Launches a local HTTP server on port 8765
2. Serves `exercise_ui.html`
3. Handles exercise completion callbacks
4. Posts results to remote server (if configured)

**Key methods**:
- `serve()` - Starts the HTTP server
- `handle_complete()` - Processes exercise completion
- `post_to_server()` - Sends data to remote API

### Exercise UI (`exercise_ui.html`)

A self-contained HTML file with:
- MediaPipe Pose integration (loaded from CDN)
- Camera access and video processing
- Real-time pose landmark visualization
- Exercise detection state machines
- Rep counting logic

**No build step required** - everything is in one file.

### Notification Hook (`notify_complete.py`)

Signals the exercise UI when Claude finishes:
1. POSTs to `http://localhost:8765/notify`
2. Exercise UI polls `/status` endpoint
3. Shows desktop notification when complete

## Data Flow

### PostToolUse Mode (Recommended)

```
1. Claude edits code
   ↓
2. PostToolUse hook triggers
   ↓
3. exercise_tracker.py launches with ?quick=true
   ↓
4. User does quick exercises
   ↓
5. Exercise complete → Hook POSTs to remote server
   ↓
6. Claude finishes task → Notification hook triggers
   ↓
7. notify_complete.py POSTs to /notify
   ↓
8. UI shows notification, user returns to Claude
```

### Exercise Detection Flow

```
1. Camera captures frame
   ↓
2. MediaPipe extracts pose landmarks (33 points)
   ↓
3. Detection function calculates angles/positions
   ↓
4. State machine updates (ready → down → up)
   ↓
5. Rep counter increments on state transitions
   ↓
6. UI updates with new count
```

## State Machine

Each exercise uses a simple state machine:

```
     ┌──────────────────────────────────┐
     │                                  │
     ▼                                  │
  ┌─────┐      ┌──────┐      ┌────┐     │
  │ready│ ───▶ │ down │ ───▶ │ up │ ────┘
  └─────┘      └──────┘      └────┘
                              │
                              │ repCount++
                              ▼
```

### Hysteresis

Different thresholds for transitions prevent jitter:

```javascript
// Squats example
DOWN_THRESHOLD = 100°  // Must reach 100° to enter "down"
UP_THRESHOLD = 160°    // Must reach 160° to complete rep

// The 60° gap prevents false triggers from small movements
```

## Privacy

- **All video processing is client-side** in the browser
- No video data is transmitted or stored
- Only rep counts go to the server
- Local server only listens on `localhost:8765`
- Camera stream never leaves your machine
