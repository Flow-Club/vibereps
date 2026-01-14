# Getting Started

## One-Line Install

```bash
curl -sSL https://raw.githubusercontent.com/Flow-Club/vibereps/main/install.sh | bash
```

That's it! Restart Claude Code and you're ready to get jacked.

## Alternative: Install from Local Clone

```bash
git clone https://github.com/Flow-Club/vibereps.git
cd vibereps
./install.sh
```

## Uninstall

```bash
~/.vibereps/install.sh --uninstall
```

## Requirements

- **Python 3** (standard library only!)
- **Modern web browser** (Chrome, Firefox, Safari)
- **Webcam**
- **Internet connection** (for MediaPipe CDN)

## How It Works

VibeReps uses Claude Code [hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) to trigger exercises:

1. **PostToolUse hook**: When Claude edits a file, the exercise tracker launches
2. **You exercise**: Keep moving while Claude continues working
3. **Notification hook**: When Claude finishes, you get a desktop notification

The workflow looks like:

```
You: "Hey Claude, refactor this code"
    ↓
🏋️ Exercise tracker launches (5 squats)
    ↓
You exercise  ←→  Claude processes your request
    ↓
Exercise complete → "⏳ Claude is working..."
    ↓
Claude: "Here's your refactored code"
    ↓
🔔 Desktop notification: "Claude is ready!"
```

## Verify Installation

After installing, run `/hooks list` in Claude Code to verify the hooks are registered:

```
PostToolUse:
  - matcher: Write|Edit|MultiEdit
    command: ~/.vibereps/exercise_tracker.py post_tool_use '{}'

Notification:
  - matcher: (empty)
    command: ~/.vibereps/notify_complete.py '{}'
```

## Testing

You can test the tracker manually:

```bash
# Test quick mode with specific exercises
VIBEREPS_EXERCISES=squats,jumping_jacks ~/.vibereps/exercise_tracker.py post_tool_use '{}'

# Test notification (run in another terminal while tracker is open)
~/.vibereps/notify_complete.py '{}'
```

## Customize with Claude Code Skills

After installing, you can use these commands in Claude Code:

| Command | Description |
|---------|-------------|
| `/setup-vibereps` | Interactive setup wizard - customize exercises and triggers |
| `/test-tracker` | Launch, restart, or test the exercise tracker |
| `/add-exercise` | Add a new exercise type with pose detection |
| `/tune-detection` | Adjust detection thresholds if reps aren't counting correctly |

**Recommended:** Run `/setup-vibereps` to pick your preferred exercises instead of using the defaults.

## Next Steps

- [Configure exercises and reps](/guide/configuration)
- [Learn about available exercises](/exercises/)
- [Set up monitoring dashboard](/advanced/monitoring)
