# Configuration

## Environment Variables

Set these in your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

### Exercise Selection

```bash
# Choose which exercises to use (comma-separated)
# A random exercise is picked from this list each time
export VIBEREPS_EXERCISES=squats,jumping_jacks,standing_crunches,calf_raises,side_stretches
```

Available exercises:
- `squats` - Knee angle tracking
- `pushups` - Elbow angle tracking
- `jumping_jacks` - Arm position tracking
- `standing_crunches` - Elbow-to-knee oblique work
- `calf_raises` - Heel lift detection
- `side_stretches` - Torso tilt tracking
- `high_knees` - Knee position tracking
- `torso_twists` - Shoulder twist tracking
- `arm_circles` - Wrist position tracking
- `shoulder_shrugs` - Shoulder elevation tracking
- `neck_rotations` - Head rotation tracking (neck mobility)
- `neck_tilts` - Head tilt tracking (neck stretch)

### Remote Server (Optional)

If you're running the VibeReps server for stats and leaderboards:

```bash
export VIBEREPS_API_URL=https://your-server.com
export VIBEREPS_API_KEY=your_api_key
```

### Disable Tracking

```bash
# Temporarily disable VibeReps
export VIBEREPS_DISABLED=1
```

### Installation Preferences

Set during install or change later:

```bash
# UI mode: electron (menubar) or webapp (browser)
export VIBEREPS_UI_MODE=electron

# Trigger mode: edit-only or prompt (experimental)
export VIBEREPS_TRIGGER_MODE=edit-only
```

### Usage Tracking

Exercise data is automatically logged to `~/.vibereps/exercises.jsonl`. View combined Claude Code + exercise stats with:

```bash
./vibereps-usage.py
```

## Customize Rep Targets

Edit the JSON config files in `~/.vibereps/exercises/` to change target reps:

```json
// Example: exercises/squats.json
{
  "reps": {
    "normal": 10,  // task_complete mode
    "quick": 5     // post_tool_use mode
  }
}
```

Each exercise has its own JSON file with rep targets. See `exercises/` directory for all available configs.

## Server Ports

VibeReps uses a two-tier port architecture:

- **Electron app**: Fixed port 8800
- **Webapp (browser)**: Ports 8765-8774 (dynamic allocation)

The webapp automatically finds an available port in the range. To change the base port for the webapp, edit `~/.vibereps/exercise_tracker.py`:

```python
self.port = 8765  # Base port (will try 8765-8774)
```

## Next Steps

- [Learn about hooks configuration](/guide/hooks)
- [Customize detection sensitivity](/guide/customization)
