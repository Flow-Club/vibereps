# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an exercise tracking system for Claude Code that encourages movement breaks during coding sessions. It has three deployment modes:

1. **Quick Mode Hook** (`exercise_tracker.py` + `notify_complete.py`) - Launches quick exercises when you submit a prompt, then notifies when Claude is ready
2. **Task Complete Hook** (`exercise_tracker.py`) - Triggers exercise breaks after Claude completes tasks
3. **MCP Server** (`mcp_exercise_server.py`) - Provides exercise tracking tools Claude can use to log sessions and track progress

All modes use MediaPipe Pose detection via browser webcam to count exercise repetitions (squats, push-ups, jumping jacks).

## Architecture

### Hook System (`exercise_tracker.py`)
- Launches a local HTTP server (port 8765) with embedded HTML/JS UI
- `ExerciseHTTPHandler` serves the single-page app and handles completion callbacks via POST to `/complete`
- Supports two modes:
  - **Quick Mode** (`user_prompt_submit`): 5 reps, server stays running, polls for Claude completion
  - **Normal Mode** (`task_complete`): 10+ reps, server waits for user completion then exits
- The HTML contains all UI logic and MediaPipe integration (loaded from CDN)
- Exercise detection happens entirely client-side using pose landmark angles

### Notification System (`notify_complete.py`)
- Triggered by `PostMessage` hook when Claude sends a message
- Sends HTTP POST to `http://localhost:8765/notify` to signal completion
- Exercise tracker UI polls `/status` endpoint to detect when Claude is ready
- Shows desktop notification and updates UI when complete

### MCP Server (`mcp_exercise_server.py`)
- Standard MCP server using stdio transport
- Stores data in `~/.claude_exercise_data.json` with exercise history, goals, and total reps
- Provides 6 tools: `log_exercise_session`, `get_exercise_stats`, `suggest_exercise`, `update_goals`, `check_streak`, `get_progress_today`
- Provides 3 resources: `exercise://stats/summary`, `exercise://history/recent`, `exercise://goals/current`
- Calculates streaks, suggests exercises based on variety, and provides progressive difficulty adjustment

## Key Implementation Details

### Exercise Detection Logic
Located in the embedded HTML of `exercise_tracker.py`:
- **Squats**: Hip-knee-ankle angle < 100° (down) → > 160° (up) = 1 rep
- **Push-ups**: Shoulder-elbow-wrist angle < 90° (down) → > 150° (up) = 1 rep
- **Jumping Jacks**: Arms above shoulders (up) → below (down) = 1 rep
- State machine prevents double-counting with `exerciseState` tracking

### Data Flow
**Quick Mode:**
1. User submits prompt → `UserPromptSubmit` hook triggers
2. `exercise_tracker.py` launches with `?quick=true` parameter
3. User does 5 quick exercises while Claude works
4. Exercise complete → UI polls `/status` endpoint every second
5. Claude sends message → `PostMessage` hook triggers
6. `notify_complete.py` POSTs to `/notify` endpoint
7. UI detects completion, shows notification, user returns to Claude

**Normal Mode:**
Browser → POST `/complete` → Hook script → Exit

**MCP Mode:**
Claude → Tool call → Update JSON → Return result

## Testing & Development

### Test Quick Mode
```bash
# Test the exercise tracker in quick mode
./exercise_tracker.py user_prompt_submit '{}'

# In another terminal, test the notification
./notify_complete.py '{}'
```
Opens browser to http://localhost:8765?quick=true, then notification signals completion.

### Test Normal Mode
```bash
./exercise_tracker.py task_complete '{}'
```
Opens browser to http://localhost:8765 with full exercise UI.

### Test the MCP Server
```bash
python mcp_exercise_server.py
```
Runs stdio server (needs MCP client to interact).

### Install MCP Dependencies
```bash
pip install -r requirements.txt  # Only installs 'mcp' package
```

## Configuration

### Recommended: Quick Mode Hook Setup
Exercise while Claude works! Add both hooks to `~/.config/claude-code/hooks.json`:
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/exercise_tracker.py",
            "args": ["user_prompt_submit", "{}"]
          }
        ]
      }
    ],
    "PostMessage": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/notify_complete.py",
            "args": ["{}"]
          }
        ]
      }
    ]
  }
}
```

### Alternative: Task Complete Hook
Exercise breaks after Claude finishes:
```json
{
  "hooks": {
    "PostToolUse": {
      "task_complete": {
        "command": "/path/to/exercise_tracker.py",
        "args": ["task_complete", "{}"]
      }
    }
  }
}
```

### MCP Setup
Add to MCP settings:
```json
{
  "mcpServers": {
    "exercise-tracker": {
      "command": "python",
      "args": ["/path/to/mcp_exercise_server.py"]
    }
  }
}
```

## Customization Points

### Change Target Reps
Edit `targetReps` (normal mode) or `quickModeReps` (quick mode) objects in `exercise_tracker.py` line ~214-215 (inside HTML template):
```javascript
let targetReps = {squats: 10, pushups: 10, jumping_jacks: 20};
let quickModeReps = {squats: 5, pushups: 5, jumping_jacks: 10};
```

### Change Detection Sensitivity
Modify angle thresholds in `detectSquat`, `detectPushup`, `detectJumpingJack` functions (inside HTML template).

### Change Server Port
Edit `self.port = 8765` in `ExerciseTrackerHook.__init__` (line ~16).

### Adjust Goals
Use MCP tool `update_goals` or directly edit `~/.claude_exercise_data.json`.

## Dependencies

- **Hook**: Python 3 standard library only (http.server, webbrowser, threading)
- **MCP Server**: `mcp>=0.9.0` package
- **Browser**: MediaPipe Pose and Camera Utils loaded from CDN (requires internet)

## Privacy & Security

- All video processing happens client-side in browser (JavaScript)
- No video data transmitted or stored
- MCP server only stores rep counts and timestamps locally
- Hook server only listens on localhost:8765
- Both scripts are safe to run in standard Python environments
- IMPORTANT: Always add a blank line after headings in markdown files