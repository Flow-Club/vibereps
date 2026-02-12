# Architecture

## Overview

```
Local (Two UI Options)                         Remote Server (optional)
─────────────────────                          ─────────────────────────

Option A: Electron Menubar App
┌─────────────────────────────┐
│ VibeReps.app (port 8800)    │──┬── ~/.vibereps/exercises.jsonl
│ ├── session-manager.js      │  │
│ └── exercise_ui.html        │  └── POST /api/log ──▶ FastAPI
└─────────────────────────────┘                        (server/main.py)

Option B: Web Browser
┌─────────────────────────────┐
│ vibereps.py                 │──┬── ~/.vibereps/exercises.jsonl
│ (ports 8765-8774)           │  │
│ └── exercise_ui.html        │  └── POST /api/log ──▶ FastAPI
└─────────────────────────────┘

Usage Statistics
┌─────────────────────────────┐
│ vibereps-usage.py           │◀── ~/.vibereps/exercises.jsonl
│                             │◀── ccusage (Claude Code usage)
└─────────────────────────────┘

Claude Code ────────MCP over HTTP────▶  /mcp endpoint
                                        ├── get_stats
                                        ├── get_leaderboard
                                        ├── check_streak
                                        └── log_exercise_session
```

## Local Components

### Electron Menubar App (`electron/`)

Native macOS app with:
- `main.js`: Main process, Express server on port 8800, tray management
- `session-manager.js`: Tracks multiple Claude instances (10-min timeout)
- `preload.js`: Secure IPC bridge to renderer
- `assets/mediapipe/`: Bundled pose detection models (~44MB)

Session states: `active` → `waiting_exercise` → `exercising` → `complete`

### Exercise Tracker (`vibereps.py`)

A Python script that:
1. Launches a local HTTP server on ports 8765-8774
2. Serves `exercise_ui.html`
3. Handles exercise completion callbacks
4. Logs results to `~/.vibereps/exercises.jsonl` (always)
5. Posts results to remote server (if configured)

**Key functions**:
- `start_web_server()` - Starts the HTTP server
- `log_to_local()` - Saves exercise data to local JSONL file
- `log_to_remote()` - Sends data to remote API (optional)

### Exercise UI (`exercise_ui.html`)

A self-contained HTML file with:
- MediaPipe Pose integration (loaded from CDN)
- Camera access and video processing
- Real-time pose landmark visualization
- Exercise detection state machines
- Rep counting logic

**No build step required** - everything is in one file.

### Notification Handler (integrated in `vibereps.py`)

Signals the exercise UI when Claude finishes:
1. `vibereps.py` reads `Notification` event from stdin
2. POSTs to `http://localhost:8765/notify`
3. Exercise UI polls `/status` endpoint
4. Shows desktop notification when complete

## Data Flow

### PostToolUse Mode (Recommended)

```
1. Claude edits code
   ↓
2. PostToolUse hook triggers
   ↓
3. vibereps.py launches with ?quick=true
   ↓
4. User does quick exercises
   ↓
5. Exercise complete → Hook POSTs to remote server
   ↓
6. Claude finishes task → Notification hook triggers
   ↓
7. vibereps.py (notification handler) POSTs to /notify
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
