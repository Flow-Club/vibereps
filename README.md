# Vibe Reps

Get jacked before AI takes your job.

Push shift-tab, push up, push code.

---

## 🎯 Quick Start

### Strategy 1: Exercise While Claude Works (Recommended)

**The workflow:** You submit prompt → Do 5 quick exercises → Claude notifies you when ready

1. **Set up the hooks using Claude Code's `/hooks` command:**

   ```
   /hooks add UserPromptSubmit exercise_start /full/path/to/exercise_tracker.py user_prompt_submit {}
   /hooks add PostMessage claude_ready /full/path/to/notify_complete.py {}
   ```

   Replace `/full/path/to/` with your actual path (e.g., `/Users/flowclub/code/vibereps/`)

2. **Test it:**

   ```bash
   # Terminal 1: Start exercise tracker
   ./exercise_tracker.py user_prompt_submit '{}'

   # Terminal 2: Simulate Claude completion
   ./notify_complete.py '{}'
   ```

3. **Use it:**
   - Submit any prompt to Claude Code
   - Exercise tracker opens automatically with quick exercises (5 reps)
   - Do your exercises while Claude works
   - Get a desktop notification when Claude is ready!

### How It Works

```
You: "Hey Claude, refactor this code"
    ↓
🏋️ Exercise tracker launches (5 squats)
    ↓
You exercise ← → Claude processes your request
    ↓
Exercise complete → "⏳ Claude is working..."
    ↓
Claude: "Here's your refactored code"
    ↓
🔔 Desktop notification: "Claude is ready!"
    ↓
You return to check the response
```

## 🏋️ Features

- **Real-time pose detection** using MediaPipe AI
- **Three exercise types:**
  - Squats (hip-knee-ankle angles)
  - Push-ups (shoulder-elbow-wrist angles)
  - Jumping jacks (arm position tracking)
- **Two modes:**
  - Quick mode: 5 reps while Claude works ⚡
  - Normal mode: 10+ reps for breaks
- **Desktop notifications** when Claude is ready
- **No installation required** - uses Python standard library
- **Privacy-focused** - all video processing happens locally in browser

## 📋 Requirements

- Python 3 (standard library only!)
- Modern web browser (Chrome, Firefox, Safari)
- Webcam
- Internet connection (for MediaPipe CDN)

## 🔧 Configuration

### Manual Hook Setup (Alternative)

If you prefer editing the config file directly, add to `~/.config/claude-code/hooks.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/full/path/to/exercise_tracker.py",
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
            "command": "/full/path/to/notify_complete.py",
            "args": ["{}"]
          }
        ]
      }
    ]
  }
}
```

See `hooks.json.example` for a template.

### Customize Exercise Reps

Edit `exercise_tracker.py` line ~214-215:

```javascript
let quickModeReps = {squats: 10, umping_jacks: 10};
```

### Change Detection Sensitivity

Make squats require deeper depth in `exercise_tracker.py`:

```javascript

if (angle < 80 && exerciseState !== 'down') {  // Default: 100
```

## 🧪 Testing

```bash
# Test quick mode
./exercise_tracker.py user_prompt_submit '{}'

# Test notification (run in another terminal while tracker is open)
./notify_complete.py '{}'

# Test normal mode
./exercise_tracker.py task_complete '{}'
```

## 🚨 Troubleshooting

**Hooks not triggering?**

```bash
# Check hooks are registered
/hooks list

# Make scripts executable
chmod +x exercise_tracker.py notify_complete.py

# Verify paths are correct (use absolute paths)
which python3  # Use this path if needed
```

**Camera permission denied?**
- Grant permission when browser prompts
- macOS: System Preferences > Security & Privacy > Camera
- Browser settings: Check camera permissions for localhost

**Exercises not detecting?**
- Ensure good lighting
- Position camera to see full body (head to feet)
- Stand 3-6 feet from camera
- Check browser console (F12) for errors

**Desktop notifications not showing?**
- Grant notification permission when prompted
- Check browser notification settings
- Check system notification preferences

## 📚 More Info

- `CLAUDE.md` - Technical architecture and development guide
- `EXERCISE_TRACKER_SETUP.md` - Detailed setup instructions
- `mcp_exercise_server.py` - MCP server for progress tracking (optional)

## 💡 Tips

- **Too easy?** Increase reps in quick mode
- **Too hard?** Decrease reps or choose easier exercises
- **Want variety?** The tracker suggests exercises you haven't done recently
- **Track progress?** Set up the MCP server for stats and streaks

---

**Stay healthy and keep coding!** 💪🚀
