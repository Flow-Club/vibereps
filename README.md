# Vibe Reps

Get jacked before AI takes your job.

Push shift-tab, push up, push code.

---

## 🚀 One-Line Install

```bash
curl -sSL https://raw.githubusercontent.com/Flow-Club/vibereps/main/install.sh | bash
```

That's it! Restart Claude Code and you're ready to get jacked.

<details>
<summary><b>Alternative: Install from local clone</b></summary>

```bash
git clone https://github.com/Flow-Club/vibereps.git
cd vibereps
./install.sh
```

</details>

<details>
<summary><b>Uninstall</b></summary>

```bash
~/.vibereps/install.sh --uninstall
```

</details>

---

## 🎯 How It Works

**The workflow:** Claude edits a file → Do 5 quick exercises → Claude notifies you when ready

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

<details>
<summary><b>Manual setup (if not using installer)</b></summary>

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "VIBEREPS_EXERCISES=squats,jumping_jacks,standing_crunches,calf_raises,side_stretches /path/to/exercise_tracker.py post_tool_use '{}'"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/notify_complete.py '{}'"
          }
        ]
      }
    ]
  }
}
```

</details>

## 🏋️ Features

- **Real-time pose detection** using MediaPipe AI
- **Stand-up verification** - ensures you're fully visible before starting
- **Six exercise types:**
  - Squats (hip-knee-ankle angles)
  - Push-ups (shoulder-elbow-wrist angles)
  - Jumping jacks (arm position tracking)
  - Standing crunches (elbow-to-knee oblique work)
  - Calf raises (heel lift detection)
  - Side stretches (torso tilt tracking)
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

### Environment Variables (Optional)

```bash
# Choose which exercises to use (comma-separated, random selection each time)
export VIBEREPS_EXERCISES=squats,jumping_jacks   # Only squats and jumping jacks
export VIBEREPS_EXERCISES=squats,pushups,jumping_jacks,standing_crunches,calf_raises,side_stretches  # All exercises

# Remote VibeReps server (optional)
export VIBEREPS_API_URL=https://your-server.com
export VIBEREPS_API_KEY=your_api_key

# Local Prometheus Pushgateway (optional, for Grafana dashboard)
export PUSHGATEWAY_URL=http://localhost:9091
```

If `VIBEREPS_EXERCISES` is set, the tracker will randomly pick one exercise from the list and auto-start it (no manual selection needed).

### Customize Exercise Reps

Edit `exercise_ui.html` to change target reps:

```javascript
let targetReps = {squats: 10, pushups: 10, jumping_jacks: 20, standing_crunches: 10, calf_raises: 15, side_stretches: 10};      // Normal mode
let quickModeReps = {squats: 5, pushups: 5, jumping_jacks: 10, standing_crunches: 5, calf_raises: 8, side_stretches: 6};     // Quick mode
```

### Change Detection Sensitivity

Adjust angle thresholds in `exercise_ui.html` (in the detection functions):

```javascript
// Example: Make squats require deeper depth
if (angle < 80 && exerciseState !== 'down') {  // Default: 100
```

## 🧪 Testing

```bash
# Test quick mode with specific exercises
VIBEREPS_EXERCISES=squats,standing_crunches ./exercise_tracker.py post_tool_use '{}'

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

- `CLAUDE.md` - Technical architecture, remote server setup, and monitoring stack
- `exercise_ui.html` - UI and pose detection logic (customize reps and sensitivity here)
- `server/` - Remote server for multi-user stats, leaderboards, and MCP integration

## 💡 Tips

- **Too easy?** Increase reps in quick mode
- **Too hard?** Decrease reps or choose easier exercises
- **Want variety?** The tracker suggests exercises you haven't done recently
- **Track progress?** Set up the MCP server for stats and streaks

---

**Stay healthy and keep coding!** 💪🚀
