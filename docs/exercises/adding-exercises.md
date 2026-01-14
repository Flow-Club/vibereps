# Adding New Exercises

You can add custom exercises by creating JSON config files in the `exercises/` directory.

## Exercise Config Structure

Create a new file like `exercises/my_exercise.json`:

```json
{
  "id": "my_exercise",
  "name": "My Exercise",
  "description": "Description shown to user",
  "category": "strength",

  "reps": {
    "normal": 10,
    "quick": 5
  },

  "detection": {
    "type": "angle",
    "landmarks": {
      "joint": [11, 13, 15],
      "joint_alt": [12, 14, 16],
      "_names": ["left_shoulder/elbow/wrist", "right_shoulder/elbow/wrist"]
    },
    "thresholds": {
      "down": 90,
      "up": 150
    },
    "states": ["ready", "up", "down"],
    "countOn": "up"
  },

  "instructions": {
    "ready": "Get ready...",
    "down": "Go down!",
    "up": "Come back up!"
  }
}
```

## Detection Types

### `angle`

Measures the angle between three landmark points (joint indices):

```json
{
  "type": "angle",
  "landmarks": {
    "joint": [23, 25, 27],
    "joint_alt": [24, 26, 28],
    "_names": ["left_hip/knee/ankle", "right_hip/knee/ankle"]
  },
  "thresholds": {
    "down": 120,
    "up": 150
  },
  "states": ["ready", "up", "down"],
  "countOn": "up"
}
```

The angle is calculated at the middle landmark (index 25/26 = knee in this example).

### `position_relative`

Tracks Y-coordinate of landmarks relative to reference landmarks:

```json
{
  "type": "position_relative",
  "landmarks": {
    "target": [15, 16],
    "reference": [11, 12],
    "_names": ["wrists", "shoulders"]
  },
  "condition": "above",
  "states": ["ready", "up", "down"],
  "countOn": "up"
}
```

### `distance`

Measures distance between landmark pairs (e.g., elbow to opposite knee):

```json
{
  "type": "distance",
  "landmarks": {
    "pairs": [
      {"from": 13, "to": 26, "_names": ["left_elbow", "right_knee"]},
      {"from": 14, "to": 25, "_names": ["right_elbow", "left_knee"]}
    ]
  },
  "thresholds": {
    "trigger": 0.3
  },
  "mode": "either",
  "states": ["ready", "up", "down"],
  "countOn": "up"
}
```

### `height_relative`

Tracks vertical position of one landmark relative to another:

```json
{
  "type": "height_relative",
  "landmarks": {
    "target": [29, 30],
    "reference": [31, 32],
    "_names": ["heels", "toes"]
  },
  "thresholds": {
    "trigger": 0.015
  },
  "states": ["ready", "up", "down"],
  "countOn": "up"
}
```

### `position_baseline`

Tracks movement from a baseline position (captured at start):

```json
{
  "type": "position_baseline",
  "landmarks": {
    "target": [0],
    "reference": [11, 12],
    "_names": ["nose", "shoulders"]
  },
  "axis": "x",
  "thresholds": {
    "trigger": 0.02,
    "release": 0.006
  },
  "states": ["ready", "forward", "tucked"],
  "countOn": "forward"
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
