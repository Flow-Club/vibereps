# Exercise Tracker for Claude Code

A fun way to encourage movement breaks while coding! This tool can be used either as a **Claude Code hook** or as an **MCP server**.

## Features

- 🏋️ Real-time exercise tracking using your webcam
- 💪 Supports squats, push-ups, and jumping jacks
- 🎯 Automatic rep counting using MediaPipe Pose detection
- 📊 Exercise history and streak tracking (MCP server)
- 🎨 Beautiful gradient UI

## Installation

### Prerequisites

```bash
# For the MCP server only:
pip install -r requirements.txt
```

The hook script uses only Python standard library and requires no additional dependencies!

## Option 1: Claude Code Hook Setup

The hook automatically triggers an exercise break when Claude Code completes a task.

### Step 1: Make the script executable

```bash
chmod +x exercise_tracker.py
```

### Step 2: Configure Claude Code Hook

Create or edit `~/.config/claude-code/hooks.json`:

```json
{
  "hooks": {
    "onTaskComplete": {
      "command": "/Users/flowclub/code/viberep/exercise_tracker.py",
      "args": ["task_complete", "{}"]
    }
  }
}
```

Or use a relative path if you prefer:

```json
{
  "hooks": {
    "onTaskComplete": {
      "command": "./exercise_tracker.py",
      "args": ["task_complete", "{}"]
    }
  }
}
```

### Step 3: Test the hook

```bash
# Run directly to test
./exercise_tracker.py task_complete '{}'
```

This should open your browser to http://localhost:8765 with the exercise tracker UI.

### How it works

1. When Claude Code completes a task, the hook triggers
2. A local web server starts on port 8765
3. Your browser opens automatically with the exercise UI
4. Grant webcam permissions
5. Select an exercise and start moving!
6. The tracker counts your reps using pose detection
7. Click "Finish Session" when done

## Option 2: MCP Server Setup

The MCP server provides exercise tracking tools that Claude can use to log sessions, check progress, and suggest exercises.

### Step 1: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure MCP in Claude Code

Add to your MCP settings (`~/.config/claude-code/mcp.json` or similar):

```json
{
  "mcpServers": {
    "exercise-tracker": {
      "command": "python",
      "args": ["/Users/flowclub/code/viberep/mcp_exercise_server.py"]
    }
  }
}
```

### Step 3: Test the MCP server

```bash
# Run the server directly
python mcp_exercise_server.py
```

### Available MCP Tools

Once configured, Claude can use these tools:

- `log_exercise_session` - Log a completed exercise session
- `get_exercise_stats` - Get statistics for day/week/month/all time
- `suggest_exercise` - Get an exercise suggestion based on history
- `update_goals` - Update daily exercise goals
- `check_streak` - Check your current exercise streak
- `get_progress_today` - See today's progress toward goals

### Available MCP Resources

- `exercise://stats/summary` - Overall exercise statistics
- `exercise://history/recent` - Last 20 exercise sessions
- `exercise://goals/current` - Current daily goals

### Example Usage

Ask Claude:

```
"Can you log my exercise session? I just did 15 squats in 2 minutes."
```

Claude will use the `log_exercise_session` tool to record it.

```
"What's my exercise streak?"
```

Claude will check your streak and provide motivation!

## Exercise Detection Details

### Squats
- Tracks hip-knee-ankle angle
- Rep counted when you go below 100° and return above 160°

### Push-ups
- Tracks shoulder-elbow-wrist angle
- Rep counted when you go below 90° and return above 150°

### Jumping Jacks
- Tracks arm position relative to shoulders
- Rep counted each time arms go above shoulders

## Customization

### Change Default Reps

Edit the `targetReps` in `exercise_tracker.py:208`:

```javascript
let targetReps = {squats: 15, pushups: 15, jumping_jacks: 30};
```

### Change Server Port

Edit `exercise_tracker.py:16`:

```python
self.port = 8765  # Change to your preferred port
```

### Adjust Detection Sensitivity

Edit the angle thresholds in the `detect*` functions:

```javascript
// Make squats require deeper squat
if (angle < 80 && exerciseState !== 'down') {  // Changed from 100
```

## Data Storage

The MCP server stores data in `~/.claude_exercise_data.json`:

```json
{
  "history": [
    {
      "timestamp": "2025-01-15T14:30:00",
      "exercise": "squats",
      "reps": 10,
      "duration": 45
    }
  ],
  "total_reps": {
    "squats": 150,
    "pushups": 120,
    "jumping_jacks": 200
  },
  "goals": {
    "daily_squats": 30,
    "daily_pushups": 30,
    "daily_jumping_jacks": 60
  }
}
```

## Troubleshooting

### Browser doesn't open automatically
- Manually navigate to http://localhost:8765
- Check if another process is using port 8765: `lsof -i :8765`

### Webcam access denied
- Grant permission in your browser when prompted
- Check browser settings to ensure camera access is allowed
- On macOS, check System Preferences > Security & Privacy > Camera

### MediaPipe not loading
- Check your internet connection (libraries load from CDN)
- Open browser console (F12) to see errors
- Try refreshing the page

### Exercises not being detected
- Ensure good lighting
- Position yourself so your full body is visible
- The camera should see you from head to feet (or head to hips for push-ups)
- Try moving closer or farther from the camera

### MCP server not connecting
- Verify mcp package is installed: `pip list | grep mcp`
- Check MCP configuration path is correct
- Look for errors in Claude Code's MCP logs

## Browser Compatibility

Tested and working on:
- Chrome/Edge (recommended)
- Firefox
- Safari

Requires:
- WebRTC support for camera access
- ES6+ JavaScript support

## Privacy

- All processing happens locally in your browser
- No video data is sent to any server
- Only rep counts and exercise type are logged (MCP server)
- Webcam feed is never recorded or stored

## Contributing

Ideas for improvements:
- Add more exercises (lunges, burpees, planks)
- Improve pose detection accuracy
- Add voice feedback
- Create workout routines
- Add leaderboards/achievements
- Integration with fitness trackers

## License

Feel free to use and modify as you like!

---

Stay healthy and keep coding! 💪🚀
