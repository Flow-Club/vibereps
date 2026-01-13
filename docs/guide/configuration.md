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
- `chin_tucks` - Head position tracking (posture correction)

### Remote Server (Optional)

If you're running the VibeReps server for stats and leaderboards:

```bash
export VIBEREPS_API_URL=https://your-server.com
export VIBEREPS_API_KEY=your_api_key
```

### Prometheus Metrics (Optional)

For local Grafana dashboard integration:

```bash
export PUSHGATEWAY_URL=http://localhost:9091
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

## Change Server Port

The exercise tracker runs a local server on port 8765. To change it, edit `~/.vibereps/exercise_tracker.py`:

```python
self.port = 8765  # Change to your preferred port
```

## Next Steps

- [Learn about hooks configuration](/guide/hooks)
- [Customize detection sensitivity](/guide/customization)
