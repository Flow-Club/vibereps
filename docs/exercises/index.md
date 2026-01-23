# Exercises

VibeReps supports multiple exercise types, each using different detection methods.

## Available Exercises

| Exercise | Detection Method | Difficulty | Best For |
|----------|-----------------|------------|----------|
| [Squats](#squats) | Knee angle | Medium | Legs, glutes |
| [Push-ups](#push-ups) | Elbow angle | Hard | Chest, arms |
| [Jumping Jacks](#jumping-jacks) | Arm position | Easy | Cardio, warmup |
| [Standing Crunches](#standing-crunches) | Elbow-to-knee | Medium | Core, obliques |
| [Calf Raises](#calf-raises) | Heel lift | Easy | Calves |
| [Side Stretches](#side-stretches) | Torso tilt | Easy | Flexibility |
| [High Knees](#high-knees) | Knee position | Medium | Cardio |
| [Torso Twists](#torso-twists) | Shoulder twist | Easy | Core, mobility |
| [Arm Circles](#arm-circles) | Wrist tracking | Easy | Shoulders |
| [Shoulder Shrugs](#shoulder-shrugs) | Shoulder elevation | Easy | Neck, shoulders |
| [Neck Rotations](#neck-rotations) | Head rotation | Easy | Neck mobility |
| [Neck Tilts](#neck-tilts) | Head tilt | Easy | Neck stretch |

## Detection Methods

### Angle-Based

Uses `calculateAngle()` on joint landmarks:

- **Squats**: Hip-knee-ankle angle
- **Push-ups**: Shoulder-elbow-wrist angle
- **Crunches**: Shoulder-hip-knee compression

### Position-Based

Uses landmark Y coordinates:

- **Jumping Jacks**: Wrist Y relative to shoulders
- **High Knees**: Knee Y relative to hip
- **Calf Raises**: Heel lift from baseline

### Movement-Based

Uses relative landmark distances:

- **Torso Twists**: Shoulder twist relative to hips
- **Side Stretches**: Shoulder tilt from center
- **Arm Circles**: Wrist position through quadrants

---

## Squats

**Detection**: Knee angle (hip-knee-ankle)

| State | Threshold |
|-------|-----------|
| Down | < 120° |
| Up | > 150° |

**Tips**:
- Keep feet shoulder-width apart
- Go deep enough for knee to bend past 100°
- Stand fully upright to complete rep

---

## Push-ups

**Detection**: Elbow angle (shoulder-elbow-wrist)

| State | Threshold |
|-------|-----------|
| Down | < 90° |
| Up | > 150° |

**Tips**:
- Position camera to see your profile
- Touch chest to ground for "down"
- Fully extend arms for "up"

---

## Jumping Jacks

**Detection**: Wrist Y position relative to shoulders

| State | Threshold |
|-------|-----------|
| Arms Up | Wrists above shoulders |
| Arms Down | Wrists below shoulders |

**Tips**:
- Raise arms fully overhead
- Camera should see full body
- Move at a steady pace

---

## Standing Crunches

**Detection**: Elbow-to-knee proximity

**Tips**:
- Bring elbow to opposite knee
- Alternate sides
- Keep movements controlled

---

## Calf Raises

**Detection**: Heel lift from baseline

| State | Threshold |
|-------|-----------|
| Up | Heel lifted > threshold |
| Down | Heel at baseline |

**Tips**:
- Rise onto balls of feet
- Hold briefly at top
- Lower with control

---

## Side Stretches

**Detection**: Shoulder tilt from center

**Tips**:
- Reach arm overhead
- Lean to opposite side
- Alternate sides

---

## High Knees

**Detection**: Knee Y position relative to hip

**Tips**:
- Lift knee above hip height
- Alternate legs
- Keep a steady rhythm

---

## Torso Twists

**Detection**: Shoulder twist relative to hips

**Tips**:
- Keep hips facing forward
- Rotate shoulders side to side
- Move smoothly

---

## Arm Circles

**Detection**: Wrist position tracking through quadrants

**Tips**:
- Make large circles
- Keep arms extended
- Complete full rotations

---

## Shoulder Shrugs

**Detection**: Shoulder elevation

**Tips**:
- Raise shoulders toward ears
- Hold briefly at top
- Release with control

---

## Neck Rotations

**Detection**: Head rotation (tilt detection)

**Tips**:
- Turn head to look left or right
- Hold briefly at each side
- Return to center between reps
- Great for neck mobility and relieving screen-time stiffness

---

## Neck Tilts

**Detection**: Head tilt (ear toward shoulder)

**Tips**:
- Tilt ear toward shoulder (left or right)
- Keep shoulders relaxed and down
- Hold briefly for a gentle stretch
- Great for stretching the sides of the neck
