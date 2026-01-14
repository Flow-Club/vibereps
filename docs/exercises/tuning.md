# Detection Tuning

If exercises aren't counting correctly, you can tune the detection parameters.

## Common Issues

### Not Counting Reps

**Symptoms**: You do the exercise but reps don't increment.

**Causes**:
- Thresholds too strict
- Poor lighting
- Camera angle wrong
- Body not fully visible

**Solutions**:
1. Check camera can see your full body
2. Improve lighting
3. Adjust thresholds in the exercise JSON config (`~/.vibereps/exercises/squats.json`):

```json
{
  "detection": {
    "thresholds": {
      "down": 130,  // Increase to make easier (default: 120)
      "up": 145     // Decrease to make easier (default: 150)
    }
  }
}
```

### Double Counting

**Symptoms**: One rep counts as 2 or more.

**Causes**:
- Thresholds too close together
- Movement too fast
- Jittery pose detection

**Solutions**:
1. Increase gap between down/up thresholds in the JSON config:

```json
{
  "detection": {
    "thresholds": {
      "down": 110,  // Lower = stricter "down" detection
      "up": 160     // Higher = stricter "up" detection (bigger gap = less jitter)
    }
  }
}
```

2. Move slower and more deliberately through the exercise motion.

### Wrong Exercise Detected

**Symptoms**: System thinks you're doing a different movement.

**Solutions**:
- Position camera for the specific exercise (front for jumping jacks, side for push-ups)
- Ensure only one exercise is active at a time

## Debugging

### Log Landmark Values

Add console logging to see raw values:

```javascript
function detectSquat(landmarks) {
  const angle = calculateAngle(
    landmarks[23], // left hip
    landmarks[25], // left knee
    landmarks[27]  // left ankle
  );

  console.log('Knee angle:', angle, 'State:', exerciseState);

  // ... rest of detection logic
}
```

### Visualize Landmarks

The UI already draws pose landmarks. Enable visibility labels:

```javascript
// In the draw function
ctx.fillText(`${i}: ${landmark.visibility.toFixed(2)}`, x, y);
```

### Check Confidence

Filter low-confidence detections:

```javascript
if (landmarks[25].visibility < 0.5) {
  // Knee not visible enough, skip frame
  return;
}
```

## Advanced Tuning

### EMA Smoothing

Reduce jitter with exponential moving average:

```javascript
let smoothedAngle = 0;
const SMOOTHING = 0.3; // 0 = no smoothing, 1 = max smoothing

function getSmoothedAngle(rawAngle) {
  smoothedAngle = SMOOTHING * smoothedAngle + (1 - SMOOTHING) * rawAngle;
  return smoothedAngle;
}
```

### Body-Scale Normalization

Normalize distances by shoulder width:

```javascript
function getShoulderWidth(landmarks) {
  const left = landmarks[11];  // left shoulder
  const right = landmarks[12]; // right shoulder
  return Math.sqrt(
    Math.pow(left.x - right.x, 2) +
    Math.pow(left.y - right.y, 2)
  );
}

// Use relative thresholds
const threshold = 0.1 * getShoulderWidth(landmarks);
```

## Per-Exercise Tips

| Exercise | Camera Position | Common Issue | Fix |
|----------|----------------|--------------|-----|
| Squats | Front or side | Not deep enough | Lower down threshold |
| Push-ups | Side view | Arms not visible | Adjust camera angle |
| Jumping Jacks | Front view | Arms not high enough | Lower arm threshold |
| Calf Raises | Side view | Small movement | Lower heel threshold |
