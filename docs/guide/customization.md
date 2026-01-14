# Customization

## Detection Sensitivity

Each exercise has thresholds that determine when a rep counts. Adjust these in `~/.vibereps/exercise_ui.html`.

### Angle-Based Exercises

For squats, push-ups, and other angle-based exercises, edit the JSON config files in `~/.vibereps/exercises/`:

```json
// exercises/squats.json - adjust thresholds
{
  "detection": {
    "thresholds": {
      "down": 120,  // Default: 120° (lower = deeper squat required)
      "up": 150     // Default: 150°
    }
  }
}
```

Or for push-ups (`exercises/pushups.json`):
```json
{
  "detection": {
    "thresholds": {
      "down": 90,   // Elbow angle for "down" position
      "up": 150     // Elbow angle for "up" position
    }
  }
}
```

### Position-Based Exercises

For jumping jacks, high knees, and calf raises:

```javascript
// Example: Make jumping jacks easier
// Lower the threshold for arm height
if (wristY < shoulderY - 0.05) {  // Default is shoulder level
  // Arms are "up"
}
```

## Exercise State Machine

Each exercise uses a state machine with 2-3 states:

```
ready → down → up (increment rep) → down → ...
```

### Hysteresis

Separate thresholds prevent double-counting. In the JSON config:

```json
{
  "detection": {
    "thresholds": {
      "down": 120,  // Angle to enter "down" state
      "up": 150     // Angle to exit "down" state
    }
  }
}
```

The gap between thresholds (120° to 150°) prevents noise from triggering false reps. Increase the gap if you're getting double-counts.

## UI Customization

### Colors

Edit the CSS in `exercise_ui.html`:

```css
:root {
  --primary-color: #4CAF50;
  --background: #1a1a1a;
  --text-color: #ffffff;
}
```

### Layout

The UI is a single HTML file. Modify the structure as needed - it's self-contained with no build step.

## Tips

- **Too easy?** Lower the down threshold (e.g., 100° instead of 120° for squats)
- **Too hard?** Raise the down threshold or lower rep counts in the JSON config
- **Double counting?** Increase the gap between down/up thresholds
- **Not counting?** Ensure good lighting and full body visibility
