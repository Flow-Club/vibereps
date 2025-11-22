# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an exercise tracking system for Claude Code that encourages movement breaks during coding sessions. It has two deployment modes:

1. **Claude Code Hook** (`exercise_tracker.py`) - Automatically triggers exercise breaks when Claude completes tasks
2. **MCP Server** (`mcp_exercise_server.py`) - Provides exercise tracking tools Claude can use to log sessions and track progress

Both use MediaPipe Pose detection via browser webcam to count exercise repetitions (squats, push-ups, jumping jacks).

## Architecture

### Hook System (`exercise_tracker.py`)
- Launches a local HTTP server (port 8765) with embedded HTML/JS UI
- `ExerciseHTTPHandler` serves the single-page app and handles completion callbacks via POST to `/complete`
- The HTML contains all UI logic and MediaPipe integration (loaded from CDN)
- Exercise detection happens entirely client-side using pose landmark angles
- Server waits for completion signal before shutting down

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
Hook mode: Browser → POST `/complete` → Hook script → Exit
MCP mode: Claude → Tool call → Update JSON → Return result

## Testing & Development

### Test the Hook
```bash
./exercise_tracker.py task_complete '{}'
```
Opens browser to http://localhost:8765 with exercise UI.

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

### Hook Setup
Add to `~/.config/claude-code/hooks.json`:
```json
{
  "hooks": {
    "onTaskComplete": {
      "command": "/path/to/exercise_tracker.py",
      "args": ["task_complete", "{}"]
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
Edit `targetReps` object in `exercise_tracker.py` line ~208 (inside HTML template).

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
