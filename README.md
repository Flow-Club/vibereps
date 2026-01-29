# Vibe Reps

Tend to your quads while you tend to your Claudes.

Do exercises and think a little yourself while you wait for Claude.

> "It's the era of tending to your Claudes."
> — [Boris Cherny](https://x.com/bcherny), creator of Claude Code, on [Greg Isenberg's podcast](https://x.com/gregisenberg)

<p align="center">
  <img src="assets/xkcd_waiting_for_claude.png" alt="xkcd: Waiting for Claude" width="500">
  <br>
  <sub>Based on <a href="https://xkcd.com/303/">xkcd #303</a> by Randall Munroe (CC BY-NC 2.5)</sub>
</p>

---

## 🚀 One-Line Install

```bash
curl -sSL https://raw.githubusercontent.com/Flow-Club/vibereps/main/install.sh | bash
```

Then restart Claude Code and run **`/setup-vibereps`** to choose your exercises.

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

## 🖥️ Menubar App (Electron)

For a more integrated experience, use the **VibeReps menubar app**:

- Always-on menubar presence with exercise/usage stats
- Random exercise auto-selection
- Native desktop notifications
- Multi-instance Claude session tracking
- Offline mode with bundled MediaPipe *(coming soon)*

### Install Menubar App

```bash
cd electron
./install.sh
```

This will:
1. Build the native macOS app
2. Install to /Applications
3. Optionally configure Claude Code hooks

Or build a distributable DMG:
```bash
cd electron
npm install
npm run build:dmg
# Output: electron/dist/VibeReps-1.0.0.dmg
```

<details>
<summary><b>Menubar App Features</b></summary>

- **Stats in menu**: Today's reps and Claude Code usage at a glance
- **Auto-refresh**: Stats update after each exercise
- **Random exercise**: Opens with a random exercise (quick mode)
- **Session tracking**: Tracks multiple Claude instances
- **Start at login**: Add to Login Items for always-on tracking

</details>

---

## 🎯 How It Works

**The workflow:** Claude edits a file → Exercise until Claude is done → Get notified when ready

```
You: "Hey Claude, refactor this code"
    ↓
🏋️ Exercise tracker launches
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
            "command": "VIBEREPS_EXERCISES=squats,jumping_jacks,standing_crunches,calf_raises,side_stretches /path/to/exercise_tracker.py post_tool_use '{}'",
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
            "command": "/path/to/notify_complete.py '{}'",
            "async": true
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
- **13 exercise types** including:
  - Squats, push-ups, jumping jacks
  - Standing crunches, calf raises, side stretches
  - High knees, torso twists, arm circles
  - Shoulder shrugs, neck rotations, neck tilts (posture correction)
- **Two modes:**
  - Quick mode: Keep exercising while Claude works ⚡
  - Normal mode: 10+ reps for breaks
- **Desktop notifications** when Claude is ready
- **No installation required** - uses Python standard library
- **Privacy-focused** - all video processing happens locally in browser

## 📋 Requirements

**Browser Version:**
- Python 3 (standard library only!)
- Modern web browser (Chrome, Firefox, Safari)
- Webcam
- Internet connection (for MediaPipe CDN)

**Menubar App (Electron):**
- macOS 10.15+
- Node.js 18+ (for building)
- Webcam
- No internet required (MediaPipe bundled)

## 🔧 Configuration

### Environment Variables (Optional)

```bash
# Choose which exercises to use (comma-separated, random selection each time)
export VIBEREPS_EXERCISES=squats,jumping_jacks   # Only squats and jumping jacks
export VIBEREPS_EXERCISES=squats,pushups,jumping_jacks,standing_crunches,calf_raises,side_stretches  # All exercises

# --dangerously-skip-leg-day (filters out squats, calf raises, high knees, jumping jacks)
export VIBEREPS_DANGEROUSLY_SKIP_LEG_DAY=1

# Remote VibeReps server (coming soon - not yet deployed)
# export VIBEREPS_API_URL=https://your-server.com
# export VIBEREPS_API_KEY=your_api_key

# Disable tracking entirely
export VIBEREPS_DISABLED=1

# UI mode (for non-interactive install)
export VIBEREPS_UI_MODE=electron  # or webapp

# Trigger mode (when exercises start)
export VIBEREPS_TRIGGER_MODE=edit-only  # (recommended) trigger when Claude edits files
export VIBEREPS_TRIGGER_MODE=prompt     # (experimental) also trigger on prompt submit
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

**Menubar app camera not working?**
- Check System Settings > Privacy & Security > Camera
- Ensure VibeReps has camera permission
- Try: `tccutil reset Camera com.vibereps.app`

**Menubar app not showing stats?**
- Click "Refresh Stats" in the menu
- Ensure exercises are being logged to `~/.vibereps/exercises.jsonl`
- For Claude usage, ensure `ccusage` is installed: `npm install -g ccusage`

## 🤖 Claude Code Skills

VibeReps includes built-in skills you can run in Claude Code:

| Command | Description |
|---------|-------------|
| `/setup-vibereps` | Interactive setup wizard - customize exercises and triggers |
| `/test-tracker` | Launch, restart, or test the exercise tracker |
| `/add-exercise` | Add a new exercise type with pose detection |
| `/tune-detection` | Adjust detection thresholds if reps aren't counting correctly |

**Example:** After installing, run `/setup-vibereps` in Claude Code to pick your preferred exercises.

## 📊 Usage Statistics

Track your Claude Code usage alongside exercise data with `vibereps-usage.py`.

Built on top of [**ccusage**](https://github.com/ryoppippi/ccusage) by [@ryoppippi](https://github.com/ryoppippi) - a fantastic tool for tracking Claude Code token usage and costs. Our usage script was inspired by ccusage's clean table format and adds exercise tracking alongside your coding stats.

```bash
./vibereps-usage.py
```

<p align="center">
  <img src="assets/vibereps-usage.gif" alt="vibereps-usage demo" width="800">
</p>

Combines ccusage output with your exercise log into a single table:

```
┌────────────┬───────────────────────────────────────┬───────────┬───────────┬───────────────┬──────────────┬───────────────┬─────────────┬───────────────────────────┐
│ Date       │ Models                                │     Input │    Output │ Cache Create  │   Cache Read │ Total Tokens  │        Cost │ Exercises                 │
├────────────┼───────────────────────────────────────┼───────────┼───────────┼───────────────┼──────────────┼───────────────┼─────────────┼───────────────────────────┤
│ 2026-01-27 │ - opus-4-5                            │   890,234 │    45,678 │     1,234,567 │    8,901,234 │    11,071,713 │     $12.34  │ 45 Squats, 30 Jumping     │
│            │ - sonnet-4-5                          │           │           │               │              │               │             │ Jacks, 20 Calf Raises     │
├────────────┼───────────────────────────────────────┼───────────┼───────────┼───────────────┼──────────────┼───────────────┼─────────────┼───────────────────────────┤
│ 2026-01-28 │ - opus-4-5                            │   456,789 │    23,456 │       567,890 │    4,567,890 │     5,616,025 │      $6.78  │ 25 Squats, 15 Standing    │
│            │                                       │           │           │               │              │               │             │ Crunches                  │
├────────────┼───────────────────────────────────────┼───────────┼───────────┼───────────────┼──────────────┼───────────────┼─────────────┼───────────────────────────┤
│ Total      │                                       │ 1,347,023 │    69,134 │     1,802,457 │   13,469,124 │    16,687,738 │     $19.12  │ 70 Squats, 30 Jumping     │
│            │                                       │           │           │               │              │               │             │ Jacks, 20 Calf Raises,    │
│            │                                       │           │           │               │              │               │             │ 15 Standing Crunches      │
└────────────┴───────────────────────────────────────┴───────────┴───────────┴───────────────┴──────────────┴───────────────┴─────────────┴───────────────────────────┘
```

### Options

```bash
# Filter by date range (passed to ccusage)
./vibereps-usage.py --since 2026-01-01
./vibereps-usage.py --since 2026-01-20 --until 2026-01-27

# Show only exercises (no Claude usage)
./vibereps-usage.py --exercises-only
```

### Requirements

- [ccusage](https://github.com/ryoppippi/ccusage): `npm install -g ccusage`
- Exercise data logged to `~/.vibereps/exercises.jsonl` (automatic when using hooks)

## 📚 More Info

- `CLAUDE.md` - Technical architecture and implementation details
- `exercise_ui.html` - UI and pose detection logic (customize reps and sensitivity here)
- `server/` - Remote server for multi-user stats, leaderboards, and MCP integration *(coming soon)*

## 💡 Tips

- **Too easy?** Increase reps or choose harder exercises
- **Too hard?** Decrease reps or choose easier exercises
- **Want variety?** The tracker suggests exercises you haven't done recently
- **Track progress?** Use `./vibereps-usage.py` to see stats alongside Claude Code usage

---

**Stay healthy and keep coding!** 💪🚀
