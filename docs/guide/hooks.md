# Hooks Configuration

VibeReps uses [Claude Code hooks](https://docs.anthropic.com/en/docs/claude-code/hooks) to trigger exercises at the right moments.

## Trigger Modes

VibeReps supports two trigger modes:

| Mode | Description | Best for |
|------|-------------|----------|
| **edit-only** (recommended) | Exercises trigger when Claude edits files | Reliable, predictable behavior |
| **prompt** (experimental) | Also triggers on prompt submit, using AI to guess if edits are likely | More exercise opportunities, but may have false positives |

Set via environment variable:
```bash
export VIBEREPS_TRIGGER_MODE=edit-only  # recommended
export VIBEREPS_TRIGGER_MODE=prompt     # experimental
```

## Default Setup (edit-only)

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
- Reliable - only triggers when edits actually happen

### UserPromptSubmit (Experimental) :test_tube:

::: warning Experimental
This mode uses heuristics to guess whether your prompt will result in code edits. It may trigger exercises for prompts that don't actually lead to edits, or miss prompts that do. We recommend starting with edit-only mode.
:::

Triggers when you submit a prompt, but uses smart detection to filter out questions and research tasks:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "~/.vibereps/exercise_tracker.py user_prompt_submit '{}'",
            "async": true
          }
        ]
      }
    ]
  }
}
```

#### Smart Prompt Detection

The tracker analyzes your prompt to guess if it will result in code edits:

**Triggers on action words:** fix, add, implement, create, update, change, modify, refactor, build, develop, integrate, migrate, improve, optimize

**Skips question patterns:**
- Prompts starting with: what, why, how, where, when, which, who, does, is, are, can, could, would, should
- Prompts ending with `?` (unless they contain strong action words like "Can you fix...")

**Examples:**
| Prompt | Triggers? | Reason |
|--------|-----------|--------|
| "Fix the login bug" | ✅ Yes | Contains "fix" |
| "Add a logout button" | ✅ Yes | Contains "add" |
| "Can you refactor this?" | ✅ Yes | Contains "refactor" |
| "What does this function do?" | ❌ No | Question without action word |
| "How does the auth system work?" | ❌ No | Question without action word |
| "Explain the codebase" | ❌ No | Research task |

#### Combining Both Modes

When you choose "prompt" mode during install, VibeReps adds **both** hooks - so exercises trigger on file edits (reliable) AND on prompts that look like they'll result in edits (experimental bonus).

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

**Exercises triggering for questions? (prompt mode)**

If you're using experimental prompt mode and getting too many false positives:

1. Switch to edit-only mode: remove the `UserPromptSubmit` hook from settings.json
2. Or reinstall with: `VIBEREPS_TRIGGER_MODE=edit-only ~/.vibereps/install.sh`
