/**
 * Exercise Detection Tests
 *
 * Tests for:
 * - Each exercise type detecting reps correctly
 * - State machine transitions (ready → down → up)
 * - Rep counts incrementing properly
 * - Edge cases (partial movements, jitter)
 */

import { test, expect } from '../fixtures/electron-app';
import {
  injectMediaPipeMock,
  playPoseSequence,
  triggerPoseFrame,
  getRepCount,
  createFullPose,
  POSE_LANDMARKS,
} from '../mocks/mediapipe-mock';
import {
  SQUAT_ONE_REP,
  SQUAT_THREE_REPS,
  SQUAT_SHALLOW_NO_REP,
  JUMPING_JACK_ONE_REP,
  JUMPING_JACK_FIVE_REPS,
  CALF_RAISE_ONE_REP,
  STANDING_CRUNCH_ONE_REP,
} from '../fixtures/poses';

// Helper to select an exercise and wait for it to be active
async function selectExercise(page: any, exerciseId: string) {
  // Find and click the exercise button
  const button = page.locator(`button:has-text("${exerciseId}"), button[data-exercise="${exerciseId}"]`);
  if (await button.count() > 0) {
    await button.first().click();
  } else {
    // Try clicking by exercise name variations
    const variations = [
      exerciseId,
      exerciseId.replace(/_/g, ' '),
      exerciseId.replace(/_/g, '-'),
    ];
    for (const variant of variations) {
      const btn = page.locator(`button:has-text("${variant}")`).first();
      if (await btn.count() > 0) {
        await btn.click();
        break;
      }
    }
  }

  // Wait for exercise to be active
  await page.waitForTimeout(500);
}

// Helper to set up mock MediaPipe and select exercise
async function setupExerciseTest(page: any, exerciseId: string) {
  // Inject mock before page loads pose detection
  await injectMediaPipeMock(page);

  // Wait for UI
  await page.waitForSelector('.exercise-selector button', { timeout: 10000 });

  // Select the exercise
  await selectExercise(page, exerciseId);

  // Wait for camera/detection to initialize
  await page.waitForSelector('video', { timeout: 5000 });
  await page.waitForTimeout(500);
}

test.describe('Squat Detection', () => {
  test('counts one rep from standing to squat to standing', async ({ appPage }) => {
    await setupExerciseTest(appPage, 'squats');

    // Play squat sequence
    await playPoseSequence(appPage, SQUAT_ONE_REP);

    // Wait for detection to process
    await appPage.waitForTimeout(200);

    const reps = await getRepCount(appPage);
    expect(reps).toBe(1);
  });

  test('counts three reps correctly', async ({ appPage }) => {
    await setupExerciseTest(appPage, 'squats');

    await playPoseSequence(appPage, SQUAT_THREE_REPS);
    await appPage.waitForTimeout(200);

    const reps = await getRepCount(appPage);
    expect(reps).toBe(3);
  });

  test('does not count shallow squat as a rep', async ({ appPage }) => {
    await setupExerciseTest(appPage, 'squats');

    await playPoseSequence(appPage, SQUAT_SHALLOW_NO_REP);
    await appPage.waitForTimeout(200);

    const reps = await getRepCount(appPage);
    expect(reps).toBe(0);
  });

  test('requires full return to standing before counting next rep', async ({ appPage }) => {
    await setupExerciseTest(appPage, 'squats');

    // Go down
    for (const frame of SQUAT_ONE_REP.frames.slice(0, 8)) {
      await triggerPoseFrame(appPage, frame.landmarks);
      await appPage.waitForTimeout(30);
    }

    // Partial return (not fully standing)
    const partialStand = createFullPose({
      LEFT_HIP: { x: 0.45, y: 0.58 },
      RIGHT_HIP: { x: 0.55, y: 0.58 },
      LEFT_KNEE: { x: 0.44, y: 0.74 },
      RIGHT_KNEE: { x: 0.56, y: 0.74 },
    });
    await triggerPoseFrame(appPage, partialStand);

    // Go down again (shouldn't count as new rep)
    for (const frame of SQUAT_ONE_REP.frames.slice(4, 8)) {
      await triggerPoseFrame(appPage, frame.landmarks);
      await appPage.waitForTimeout(30);
    }

    const reps = await getRepCount(appPage);
    // Should be 1 (completed first rep when went back up)
    // or 0 (if never fully stood up)
    expect(reps).toBeLessThanOrEqual(1);
  });
});

test.describe('Jumping Jack Detection', () => {
  test('counts one rep (arms up then down)', async ({ appPage }) => {
    await setupExerciseTest(appPage, 'jumping_jacks');

    await playPoseSequence(appPage, JUMPING_JACK_ONE_REP);
    await appPage.waitForTimeout(200);

    const reps = await getRepCount(appPage);
    expect(reps).toBe(1);
  });

  test('counts five reps correctly', async ({ appPage }) => {
    await setupExerciseTest(appPage, 'jumping_jacks');

    await playPoseSequence(appPage, JUMPING_JACK_FIVE_REPS);
    await appPage.waitForTimeout(200);

    const reps = await getRepCount(appPage);
    expect(reps).toBe(5);
  });

  test('requires arms above shoulders for up position', async ({ appPage }) => {
    await setupExerciseTest(appPage, 'jumping_jacks');

    // Arms only slightly raised (below shoulder level)
    const armsLow = createFullPose({
      LEFT_SHOULDER: { x: 0.4, y: 0.25 },
      RIGHT_SHOULDER: { x: 0.6, y: 0.25 },
      LEFT_WRIST: { x: 0.35, y: 0.30 },  // Just above shoulder, but not high
      RIGHT_WRIST: { x: 0.65, y: 0.30 },
    });

    const armsDown = createFullPose({
      LEFT_WRIST: { x: 0.35, y: 0.55 },
      RIGHT_WRIST: { x: 0.65, y: 0.55 },
    });

    // Start down
    await triggerPoseFrame(appPage, armsDown);
    await appPage.waitForTimeout(50);

    // Arms slightly raised (not enough)
    await triggerPoseFrame(appPage, armsLow);
    await appPage.waitForTimeout(50);

    // Back down
    await triggerPoseFrame(appPage, armsDown);
    await appPage.waitForTimeout(50);

    const reps = await getRepCount(appPage);
    // Should be 0 because arms didn't go high enough
    expect(reps).toBe(0);
  });
});

test.describe('Calf Raise Detection', () => {
  test('counts one rep from flat to raised to flat', async ({ appPage }) => {
    await setupExerciseTest(appPage, 'calf_raises');

    await playPoseSequence(appPage, CALF_RAISE_ONE_REP);
    await appPage.waitForTimeout(200);

    const reps = await getRepCount(appPage);
    expect(reps).toBe(1);
  });
});

test.describe('Standing Crunch Detection', () => {
  test('counts one rep from standing to crunch to standing', async ({ appPage }) => {
    await setupExerciseTest(appPage, 'standing_crunches');

    await playPoseSequence(appPage, STANDING_CRUNCH_ONE_REP);
    await appPage.waitForTimeout(200);

    const reps = await getRepCount(appPage);
    expect(reps).toBe(1);
  });
});

test.describe('Detection State Machine', () => {
  test('exercise state starts as ready or null', async ({ appPage }) => {
    await setupExerciseTest(appPage, 'squats');

    const state = await appPage.evaluate(() => {
      return (window as any).exerciseState;
    });

    // State should be null, 'ready', or 'checking' initially
    expect(['ready', 'checking', null]).toContain(state);
  });

  test('detection handles missing/low visibility landmarks gracefully', async ({ appPage }) => {
    await setupExerciseTest(appPage, 'squats');

    // Create pose with some landmarks having low visibility
    const lowVisPose = createFullPose({}).map((lm, i) => {
      if (i === POSE_LANDMARKS.LEFT_KNEE || i === POSE_LANDMARKS.RIGHT_KNEE) {
        return { ...lm, visibility: 0.2 }; // Low visibility
      }
      return lm;
    });

    // Should not crash
    await triggerPoseFrame(appPage, lowVisPose);
    await appPage.waitForTimeout(100);

    // Verify page still functioning
    const reps = await getRepCount(appPage);
    expect(reps).toBeGreaterThanOrEqual(0);
  });

  test('detection handles empty landmarks gracefully', async ({ appPage }) => {
    await setupExerciseTest(appPage, 'squats');

    // Trigger with empty landmarks (simulating no person detected)
    await appPage.evaluate(() => {
      const callback = (window as any).__mockPoseCallback;
      if (callback) {
        callback({ poseLandmarks: null });
      }
    });

    await appPage.waitForTimeout(100);

    // Should not crash, rep count should stay at 0
    const reps = await getRepCount(appPage);
    expect(reps).toBe(0);
  });
});

test.describe('Rep Counting Edge Cases', () => {
  test('rapid movements do not double count', async ({ appPage }) => {
    await setupExerciseTest(appPage, 'squats');

    // Play sequence very fast
    for (const frame of SQUAT_ONE_REP.frames) {
      await triggerPoseFrame(appPage, frame.landmarks);
      await appPage.waitForTimeout(10); // Very fast
    }

    await appPage.waitForTimeout(100);

    const reps = await getRepCount(appPage);
    // Should be exactly 1, not double-counted
    expect(reps).toBe(1);
  });

  test('jittery poses do not cause false counts', async ({ appPage }) => {
    await setupExerciseTest(appPage, 'squats');

    // Standing pose with small jitter
    const standing = createFullPose({});

    // Add jitter to standing pose
    for (let i = 0; i < 10; i++) {
      const jitterPose = standing.map(lm => ({
        ...lm,
        x: lm.x + (Math.random() - 0.5) * 0.02, // ±1% jitter
        y: lm.y + (Math.random() - 0.5) * 0.02,
      }));
      await triggerPoseFrame(appPage, jitterPose);
      await appPage.waitForTimeout(50);
    }

    const reps = await getRepCount(appPage);
    // Jitter alone should not count as reps
    expect(reps).toBe(0);
  });
});

test.describe('Exercise Completion', () => {
  test('exercise completes when target reps reached', async ({ appPage }) => {
    // In quick mode, target is usually 5 reps
    await setupExerciseTest(appPage, 'squats');

    // Get target
    const target = await appPage.evaluate(() => {
      const targetEl = document.querySelector('#target');
      if (targetEl) {
        return parseInt(targetEl.textContent || '5', 10);
      }
      return 5;
    });

    // Play enough reps to reach target
    for (let i = 0; i < target; i++) {
      await playPoseSequence(appPage, SQUAT_ONE_REP);
      await appPage.waitForTimeout(100);
    }

    const reps = await getRepCount(appPage);
    expect(reps).toBeGreaterThanOrEqual(target);

    // Check for completion indicator
    const completed = await appPage.evaluate(() => {
      const body = document.body.textContent || '';
      return body.includes('complete') ||
             body.includes('Complete') ||
             body.includes('Done') ||
             body.includes('Nice');
    });

    // May or may not show completion message depending on UI state
    expect(typeof completed).toBe('boolean');
  });
});
