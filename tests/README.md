# VibeReps Integration Tests

Integration tests for the VibeReps exercise tracker using Playwright.

## Quick Start

```bash
# Install dependencies
npm install

# Run all tests
npm test

# Run tests with browser visible
npm run test:headed

# Run tests in debug mode
npm run test:debug

# Open Playwright UI
npm run test:ui
```

## Test Categories

### 1. Electron App Tests (`electron.spec.ts`)
- App builds and launches successfully
- HTTP server starts on port 8800
- API endpoints respond correctly
- Exercise logging works

### 2. MediaPipe Tests (`mediapipe.spec.ts`)
- MediaPipe scripts load correctly
- Camera permission handling
- Mock camera injection works

### 3. Detection Tests (`detection.spec.ts`)
- Squat detection counts reps correctly
- Jumping jack detection works
- Calf raise detection works
- Standing crunch detection works
- Edge cases (jitter, partial movements)

### 4. Hook Tests (`hooks.spec.ts`)
- `exercise_tracker.py` detects Electron app
- Session registration works
- Activity reporting works
- `notify_complete.py` sends notifications

## Mock Camera System

Tests use mock pose data instead of real webcam access for deterministic results.

### How it works:
1. MediaPipe is mocked via `injectMediaPipeMock(page)`
2. Pre-recorded pose sequences are played via `playPoseSequence(page, sequence)`
3. Each sequence simulates a person performing an exercise

### Adding new pose fixtures:
See `fixtures/poses/index.ts` for existing sequences. To add a new exercise:

```typescript
export const NEW_EXERCISE_ONE_REP: PoseSequence = {
  exercise: 'new_exercise',
  expectedReps: 1,
  frames: [
    { timestamp: 0, landmarks: createFullPose({ /* key points */ }) },
    // ... more frames
  ],
};
```

## Running Specific Tests

```bash
# Run only Electron tests
npx playwright test electron

# Run only detection tests
npx playwright test detection

# Run a specific test by name
npx playwright test -g "counts one rep"
```

## CI Integration

Tests run automatically on push/PR via GitHub Actions. See `.github/workflows/test.yml`.

The CI workflow:
1. Installs Electron app dependencies
2. Installs test dependencies
3. Runs Playwright tests
4. Uploads test reports as artifacts

## Troubleshooting

### Tests timeout waiting for Electron app
- Ensure port 8800 is not in use
- Check Electron app console for errors

### MediaPipe mock not working
- Make sure `injectMediaPipeMock()` is called before page loads
- Check browser console for mock registration messages

### Detection tests fail with wrong rep count
- Verify pose fixtures have correct landmark positions
- Check thresholds in exercise JSON configs match expected angles
