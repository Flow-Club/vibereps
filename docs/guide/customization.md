# Customization

## Detection Sensitivity

Each exercise has thresholds that determine when a rep counts. Adjust these in `~/.vibereps/exercise_ui.html`.

### Angle-Based Exercises

For squats, push-ups, and other angle-based exercises:

```javascript
// Example: Make squats require deeper depth
// Default: down < 100°, up > 160°
if (angle < 80 && exerciseState !== 'down') {  // Deeper squat required
  exerciseState = 'down';
} else if (angle > 160 && exerciseState === 'down') {
  exerciseState = 'up';
  repCount++;
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

Separate thresholds prevent double-counting:

```javascript
// Different thresholds for down vs up transitions
const DOWN_THRESHOLD = 100;  // Angle to enter "down" state
const UP_THRESHOLD = 160;    // Angle to exit "down" state

if (angle < DOWN_THRESHOLD && state !== 'down') {
  state = 'down';
} else if (angle > UP_THRESHOLD && state === 'down') {
  state = 'up';
  repCount++;
}
```

The gap between thresholds (100° to 160°) prevents noise from triggering false reps.

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

- **Too easy?** Lower the down threshold (e.g., 80° instead of 100° for squats)
- **Too hard?** Raise the down threshold or lower rep counts
- **Double counting?** Increase the gap between down/up thresholds
- **Not counting?** Ensure good lighting and full body visibility
