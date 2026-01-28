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

All pose detection uses MediaPipe via browser webcam to count reps (squats, push-ups, jumping jacks). Video never leaves your browser.

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
  - **Quick Mode** (`post_tool_use`): Exercises cycle until Claude finishes
  - **Normal Mode** (`task_complete`): 10+ reps after Claude finishes
- On exercise completion, POSTs to remote server (if configured via `VIBEREPS_API_URL`)
- The HTML file contains all UI logic and MediaPipe integration (loaded from CDN)
- Exercise detection happens entirely client-side using pose landmark angles

### Notification System (`notify_complete.py`)

- Triggered by `Notification` hook when Claude finishes a task
- Sends HTTP POST to `http://localhost:8765/notify` to signal completion
- Exercise tracker UI polls `/status` endpoint to detect when Claude is ready
- Shows desktop notification and updates UI when complete

### Electron Menubar App (`electron/`)

Native macOS app providing:
- Always-on menubar presence with stats
- Multi-instance Claude session tracking via SessionManager
- Native notifications
- Bundled MediaPipe for offline use
- Express HTTP API on port 8800

Key files:
- `main.js`: Main process, Express server, tray management
- `session-manager.js`: Tracks Claude instances (10-min timeout)
- `preload.js`: Secure IPC bridge

### Remote Server (`server/main.py`)

- **REST API** (`/api/*`) - For local hook to POST exercise sessions
- **MCP HTTP Transport** (`/mcp`) - For Claude Code to query stats
- SQLite/PostgreSQL storage with user accounts and API keys
- Provides tools: `log_exercise_session`, `get_stats`, `get_leaderboard`, `check_streak`, `get_progress_today`

## Key Implementation Details

### Exercise Detection Logic

Located in `exercise_ui.html`. Rep counting uses MediaPipe pose landmarks with a state machine approach.

#### Detection Methods

**Angle-based exercises** (use `calculateAngle()` on joint landmarks):
- **Squats**: Knee angle (hip-knee-ankle) - down < 100°, up > 160°
- **Push-ups**: Elbow angle (shoulder-elbow-wrist) - down < 90°, up > 150°
- **Crunches**: Hip angle (shoulder-hip-knee) compression detection

**Position-based exercises** (use landmark Y coordinates):
- **Jumping Jacks**: Wrist Y position relative to shoulders
- **High Knees**: Knee Y position relative to hip
- **Calf Raises**: Heel lift relative to baseline position

**Movement-based exercises** (use relative landmark distances):
- **Torso Twists**: Shoulder twist amount relative to hips
- **Side Stretches**: Shoulder tilt from center
- **Arm Circles**: Wrist position tracking through quadrants

#### State Machine

Each exercise uses `exerciseState` variable with 2-3 states:

```text
ready → down → up (increment rep) → down → ...
```

#### Hysteresis Thresholds

Separate thresholds for down vs up transitions prevent double-counting:

```javascript
// Example: Squats use different angles for each transition
if (angle < DOWN_ANGLE && exerciseState !== 'down') {
    exerciseState = 'down';
} else if (angle > UP_ANGLE && exerciseState === 'down') {
    exerciseState = 'up';
    repCount++;
}
```

For position-based exercises, the "reset" threshold is typically 30-40% of the trigger threshold.

#### Supported Exercises

| Exercise | Detection Method | Down Threshold | Up Threshold |
|----------|-----------------|----------------|--------------|
| Squats | Knee angle | < 120° | > 150° |
| Push-ups | Elbow angle | < 90° | > 150° |
| Jumping Jacks | Wrist Y vs shoulders | Below shoulders | Above shoulders |
| High Knees | Knee Y vs hip | - | Knee above hip |
| Calf Raises | Heel lift | Baseline | > threshold |
| Standing Crunches | Elbow-knee distance | < 0.3 (normalized) | > threshold |
| Side Stretches | Shoulder tilt | Center | > threshold |
| Torso Twists | Shoulder twist | Center | > threshold |
| Arm Circles | Wrist angle | Quadrant tracking | Full circle |
| Shoulder Shrugs | Shoulder elevation | Baseline | > threshold |
| Neck Rotations | Head rotation | Center | > threshold |
| Neck Tilts | Head tilt | Center | > threshold |

#### Adding New Exercises

Exercise configs are defined in `exercises/` JSON files. Each config specifies:
- `detection.type`: `angle`, `position`, `movement`, etc.
- `detection.joints`: Which landmarks to track
- `detection.thresholds`: Down/up values for state transitions
- `instructions`: User feedback messages for each state

### Data Flow

**PostToolUse Mode (recommended):**

1. Claude edits code → `PostToolUse` hook triggers (matcher: `Write|Edit`)
2. `exercise_tracker.py` launches with `?quick=true` parameter
3. User does quick exercises while reviewing changes
4. Exercise complete → Hook POSTs to remote server
5. Claude finishes task → `Notification` hook triggers
6. `notify_complete.py` POSTs to `/notify` endpoint
7. UI detects completion, shows notification, user returns to Claude

**Normal Mode:**

Browser → POST `/complete` → Hook POSTs to remote → Exit

**Legacy UserPromptSubmit Mode:**

Triggers on every prompt submission (more frequent, may interrupt research tasks).

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

# Disable tracking entirely
export VIBEREPS_DISABLED=1

# UI mode: electron (menubar) or webapp (browser)
export VIBEREPS_UI_MODE=electron

# Trigger mode: edit-only or prompt
export VIBEREPS_TRIGGER_MODE=edit-only
```

### 2. Hook Setup

Exercise after code edits! Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "VIBEREPS_EXERCISES=squats,jumping_jacks,calf_raises /path/to/exercise_tracker.py post_tool_use '{}'",
            "async": true
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "idle_prompt|permission_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/notify_complete.py '{}'",
            "async": true
          }
        ]
      }
    ]
  }
}
```

The `VIBEREPS_EXERCISES` environment variable controls which exercises are available.

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

### Change Target Reps

Edit the JSON config files in `exercises/` directory. Each exercise has its own file:
```json
// exercises/squats.json
{
  "reps": {
    "normal": 10,  // task_complete mode
    "quick": 5     // post_tool_use mode
  }
}
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
- **Browser**: MediaPipe Pose and Camera Utils loaded from CDN (requires internet)

## Usage Tracking

View Claude Code usage alongside exercise data with `vibereps-usage.py`.

### Quick Start

```bash
# View combined usage and exercise data
./vibereps-usage.py

# Pass arguments through to ccusage
./vibereps-usage.py --since 2026-01-01
```

### How It Works

1. Exercise completions are logged to `~/.vibereps/exercises.jsonl`
2. `vibereps-usage.py` combines this with `ccusage` output (reads `~/.claude/statsig/usage.jsonl`)
3. Both data sources are grouped by date for a unified view

### Exercise Log Format

```json
{"timestamp": "2026-01-13T10:30:00", "exercise": "squats", "reps": 5, "duration": 45, "mode": "quick"}
```

### Requirements

- [ccusage](https://github.com/ryoppippi/ccusage) - `npm install -g ccusage`

## Privacy & Security

- All video processing happens client-side in browser (JavaScript)
- No video data transmitted or stored - only rep counts go to server
- Local hook server only listens on localhost:8765
- Remote server uses API key authentication
- Exercise data (reps, timestamps) stored on remote server for stats/leaderboards
- Telemetry is opt-in and never includes sensitive data (API keys, file contents)

## Known Limitations

### Detection Accuracy

The current implementation is functional but has room for improvement:

- **No keypoint smoothing**: Raw MediaPipe landmarks are used directly without low-pass filtering (EMA), which can cause jitter on marginal poses
- **No confidence gating**: Frames with low landmark confidence are not filtered out, potentially causing false counts
- **No body-scale normalization**: Thresholds are absolute values rather than normalized by body proportions (e.g., shoulder width), so detection may vary with camera distance
- **Main thread inference**: Pose detection runs on the main thread rather than a Web Worker, which can affect UI responsiveness on slower devices
- **Camera angle sensitivity**: Detection is tuned for front-facing camera; side views may be less accurate

### Potential Improvements

If detection feels unreliable, consider:

1. **Add EMA smoothing** to landmark positions before angle calculation
2. **Gate on confidence** - skip frames where landmark visibility < 0.5
3. **Normalize distances** by shoulder width or torso length
4. **Move inference to Worker** with OffscreenCanvas for better performance
5. **Add calibration step** to capture user's range of motion
