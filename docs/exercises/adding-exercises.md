# Adding New Exercises

You can add custom exercises by creating JSON config files in the `exercises/` directory.

## Exercise Config Structure

Create a new file like `exercises/my_exercise.json`:

```json
{
  "name": "My Exercise",
  "id": "my_exercise",
  "description": "Description shown to user",
  "detection": {
    "type": "angle",
    "joints": ["shoulder", "elbow", "wrist"],
    "thresholds": {
      "down": 90,
      "up": 150
    }
  },
  "instructions": {
    "ready": "Get ready...",
    "down": "Go down!",
    "up": "Come back up!"
  },
  "targetReps": {
    "normal": 10,
    "quick": 5
  }
}
```

## Detection Types

### `angle`

Measures the angle between three joints:

```json
{
  "type": "angle",
  "joints": ["hip", "knee", "ankle"],
  "thresholds": {
    "down": 100,
    "up": 160
  }
}
```

The angle is calculated at the middle joint (knee in this example).

### `position`

Tracks Y-coordinate of a landmark relative to another:

```json
{
  "type": "position",
  "landmark": "wrist",
  "reference": "shoulder",
  "thresholds": {
    "trigger": -0.1,
    "reset": 0.05
  }
}
```

Negative values mean the landmark is above the reference.

### `movement`

Tracks movement patterns like twists or circles:

```json
{
  "type": "movement",
  "pattern": "twist",
  "landmarks": ["left_shoulder", "right_shoulder"],
  "reference": ["left_hip", "right_hip"],
  "thresholds": {
    "trigger": 0.15,
    "reset": 0.05
  }
}
```

## Available Landmarks

MediaPipe provides these landmarks:

**Upper Body**:
- `nose`, `left_eye`, `right_eye`
- `left_ear`, `right_ear`
- `left_shoulder`, `right_shoulder`
- `left_elbow`, `right_elbow`
- `left_wrist`, `right_wrist`

**Lower Body**:
- `left_hip`, `right_hip`
- `left_knee`, `right_knee`
- `left_ankle`, `right_ankle`
- `left_heel`, `right_heel`

## Testing Your Exercise

1. Add your JSON config to `exercises/`
2. Add the exercise ID to `VIBEREPS_EXERCISES`:
   ```bash
   export VIBEREPS_EXERCISES=my_exercise
   ```
3. Test the tracker:
   ```bash
   ./exercise_tracker.py post_tool_use '{}'
   ```
4. Adjust thresholds based on detection accuracy

## Tips

- **Start with wide thresholds** and narrow them down
- **Test with different body types** and camera angles
- **Add hysteresis** (gap between trigger and reset) to prevent double-counting
- **Log landmark values** to the console for debugging
