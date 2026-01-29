---
name: vibereps
description: Exercise tracker for Claude Code - encourages movement breaks during coding. Launches pose-detection UI when Claude edits files. Tracks squats, jumping jacks, calf raises and more.
---

# Vibereps - Exercise Tracker for Claude Code

Movement breaks while you code. When Claude edits files, vibereps launches a pose-detection exercise UI. Do a few squats or stretches while Claude works, then get notified when it's ready.

## Quick Install

Run the installer to set up hooks and choose exercises:

```bash
curl -fsSL https://raw.githubusercontent.com/flowclub/vibereps/main/install.sh | bash
```

This installs the menubar app by default. For browser-only: `bash -s -- --webapp`

Or use `/setup-vibereps` for an interactive guided setup.

## How It Works

1. Claude edits a file → Exercise tracker launches
2. Do a quick exercise (5 reps) while Claude works
3. Get notified when Claude is ready

All pose detection happens locally in your browser via MediaPipe. No video data is transmitted.

## Available Skills

After installing, you have access to these skills:

| Skill | Description |
|-------|-------------|
| `/setup-vibereps` | Interactive setup wizard |
| `/test-tracker` | Test and launch the exercise UI |
| `/add-exercise` | Create custom exercise types |
| `/tune-detection` | Adjust detection thresholds |

## Supported Exercises

**Standing**: squats, jumping_jacks, calf_raises, push_ups, high_knees, standing_crunches, side_stretches, torso_twists, arm_circles

**Seated**: shoulder_shrugs, neck_tilts, neck_rotations

## Manual Setup

If you prefer manual configuration, add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "VIBEREPS_EXERCISES=squats,jumping_jacks ~/.vibereps/exercise_tracker.py post_tool_use '{}'",
        "async": true
      }]
    }],
    "Notification": [{
      "matcher": "idle_prompt|permission_prompt",
      "hooks": [{
        "type": "command",
        "command": "~/.vibereps/notify_complete.py '{}'",
        "async": true
      }]
    }]
  }
}
```

## Requirements

- Python 3.8+
- Modern browser with webcam access
- macOS, Linux, or Windows

## Links

- [GitHub](https://github.com/flowclub/vibereps)
- [Documentation](https://github.com/flowclub/vibereps/tree/main/docs)
