# Hooks Configuration

VibeReps uses [Claude Code hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) to trigger exercises at the right moments.

## Default Setup

The installer adds these hooks to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "VIBEREPS_EXERCISES=squats,jumping_jacks,standing_crunches,calf_raises,side_stretches ~/.vibereps/exercise_tracker.py post_tool_use '{}'",
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
            "command": "~/.vibereps/notify_complete.py '{}'",
            "async": true
          }
        ]
      }
    ]
  }
}
```

## Async Execution

Hooks run asynchronously with `"async": true`, meaning they don't block Claude's execution. This is ideal for the exercise tracker since it runs independently while Claude continues working.

## Smart Prompt Detection

In `user_prompt_submit` mode, the tracker analyzes prompts to skip those unlikely to result in code edits:

**Triggers on action words:** fix, add, implement, create, update, change, modify, refactor, etc.

**Skips question words:** what, why, how, explain, describe, show, etc.

## Hook Types

### PostToolUse (Recommended)

Triggers after Claude uses a tool. The `matcher` filters which tools trigger the hook:

- `Write|Edit|MultiEdit` - Only when Claude edits files (recommended)
- `Write` - Only when Claude creates new files
- `.*` - Every tool use (very frequent, not recommended)

**Advantages:**
- Exercises happen while Claude is still working
- You stay active during code reviews
- Doesn't interrupt research/reading tasks

### UserPromptSubmit (Alternative)

Triggers when you submit a prompt:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "~/.vibereps/exercise_tracker.py user_prompt_submit '{}'"
          }
        ]
      }
    ]
  }
}
```

**Note:** This triggers on every prompt, including simple questions. May interrupt research tasks.

### Notification

Triggers when Claude sends a notification (task complete, waiting for input):

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "idle_prompt|permission_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "~/.vibereps/notify_complete.py '{}'",
            "async": true
          }
        ]
      }
    ]
  }
}
```

This signals the exercise UI that Claude is ready, showing a desktop notification. The matcher `idle_prompt|permission_prompt` ensures notifications trigger when Claude finishes or needs input.

## Verify Hooks

Run `/hooks list` in Claude Code to see registered hooks.

## Troubleshooting

**Hooks not triggering?**

1. Check hooks are registered: `/hooks list`
2. Make scripts executable: `chmod +x ~/.vibereps/*.py`
3. Verify paths are correct (use absolute paths)
4. Check for JSON syntax errors in settings.json

**Too many exercises?**

Change the matcher to be more specific:
- `Write` - Only new files
- `Edit` - Only edits to existing files
