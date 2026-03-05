import { test, expect } from '@playwright/test';
import { injectMediaPipeMock, setPoseFrames, triggerPoseFrame, getRepCount } from '../mocks/mediapipe-mock';
import { SQUAT_3_REPS, SQUAT_SHALLOW, JUMPING_JACK_3_REPS } from '../fixtures/poses';

/**
 * Detection tests use the browser-based exercise_ui.html with mocked MediaPipe.
 * These tests verify the state machine and threshold logic count reps correctly.
 *
 * Note: These tests require a running local server or direct file access.
 * For now they're structured for the Electron app which serves the UI.
 */

const ELECTRON_URL = 'http://localhost:8800';

test.describe('Exercise Detection', () => {
  test.beforeEach(async ({ page }) => {
    await injectMediaPipeMock(page);
  });

  test('squats: 3 reps detected correctly', async ({ page }) => {
    await page.goto(`${ELECTRON_URL}/?exercise=squats&quick=true`);
    await page.waitForSelector('#counter');

    // Feed mock pose frames
    for (const frame of SQUAT_3_REPS.frames) {
      await triggerPoseFrame(page, frame);
      await page.waitForTimeout(50); // Simulate frame rate
    }

    const reps = await getRepCount(page);
    expect(reps).toBe(SQUAT_3_REPS.expectedReps);
  });

  test('squats: shallow movement does not count', async ({ page }) => {
    await page.goto(`${ELECTRON_URL}/?exercise=squats&quick=true`);
    await page.waitForSelector('#counter');

    for (const frame of SQUAT_SHALLOW.frames) {
      await triggerPoseFrame(page, frame);
      await page.waitForTimeout(50);
    }

    const reps = await getRepCount(page);
    expect(reps).toBe(SQUAT_SHALLOW.expectedReps);
  });

  test('jumping jacks: 3 reps detected correctly', async ({ page }) => {
    await page.goto(`${ELECTRON_URL}/?exercise=jumping_jacks&quick=true`);
    await page.waitForSelector('#counter');

    for (const frame of JUMPING_JACK_3_REPS.frames) {
      await triggerPoseFrame(page, frame);
      await page.waitForTimeout(50);
    }

    const reps = await getRepCount(page);
    expect(reps).toBe(JUMPING_JACK_3_REPS.expectedReps);
  });
});
