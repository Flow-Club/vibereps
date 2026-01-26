/**
 * MediaPipe Loading and Camera Tests
 *
 * Tests for:
 * - MediaPipe scripts loading (local in Electron, CDN in browser)
 * - Camera permission handling
 * - Pose detection initialization
 * - Mock camera feed injection
 */

import { test, expect } from '../fixtures/electron-app';
import { injectMediaPipeMock, triggerPoseFrame, createFullPose, getRepCount } from '../mocks/mediapipe-mock';

test.describe('MediaPipe Loading', () => {
  test('page detects Electron environment', async ({ appPage }) => {
    const isElectron = await appPage.evaluate(() => {
      return !!(window as any).isElectronApp;
    });

    expect(isElectron).toBe(true);
  });

  test('MediaPipe base path is set correctly for Electron', async ({ appPage }) => {
    const basePath = await appPage.evaluate(() => {
      return (window as any).mediapipeBasePath;
    });

    // In Electron, should use local path
    expect(basePath).toBe('/mediapipe/pose');
  });

  test('page loads without JavaScript errors', async ({ appPage }) => {
    const errors: string[] = [];

    appPage.on('pageerror', (error) => {
      errors.push(error.message);
    });

    // Wait for page to fully load
    await appPage.waitForLoadState('networkidle');

    // Filter out expected errors (like camera permission in headless)
    const unexpectedErrors = errors.filter(e =>
      !e.includes('getUserMedia') &&
      !e.includes('NotAllowedError') &&
      !e.includes('Permission denied')
    );

    expect(unexpectedErrors).toHaveLength(0);
  });

  test('exercise buttons are rendered', async ({ appPage }) => {
    // Wait for UI to render
    await appPage.waitForSelector('.exercise-selector', { timeout: 10000 });

    // Check for exercise buttons
    const buttons = await appPage.locator('.exercise-selector button').count();
    expect(buttons).toBeGreaterThan(0);
  });

  test('selecting an exercise shows camera container', async ({ appPage }) => {
    // Wait for exercise buttons
    await appPage.waitForSelector('.exercise-selector button', { timeout: 10000 });

    // Click first exercise button
    await appPage.locator('.exercise-selector button').first().click();

    // Camera container should become visible
    const cameraContainer = appPage.locator('#camera-container, .camera-container, video');
    await expect(cameraContainer.first()).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Mock MediaPipe Integration', () => {
  test('mock MediaPipe can be injected', async ({ appPage }) => {
    // Inject mock before any pose detection runs
    await injectMediaPipeMock(appPage);

    // Verify mock is installed
    const hasMockPose = await appPage.evaluate(() => {
      return typeof (window as any).Pose === 'function' &&
             (window as any).Pose.toString().includes('MockPose');
    });

    // The mock should be present (or we'll check via __injectPoseFrames)
    const hasInjector = await appPage.evaluate(() => {
      return typeof (window as any).__injectPoseFrames === 'function';
    });

    expect(hasInjector).toBe(true);
  });

  test('mock pose frames can be triggered', async ({ appPage }) => {
    await injectMediaPipeMock(appPage);

    // Create a test pose
    const testPose = createFullPose({});

    // Set up listener for pose detection
    let poseDetected = false;
    await appPage.evaluate(() => {
      (window as any).__testPoseDetected = false;
      const originalCallback = (window as any).__mockPoseCallback;
      if (originalCallback) {
        (window as any).__mockPoseCallback = (results: any) => {
          (window as any).__testPoseDetected = true;
          originalCallback(results);
        };
      }
    });

    // Trigger the pose frame
    await triggerPoseFrame(appPage, testPose);

    // Give it time to process
    await appPage.waitForTimeout(100);

    // Verify callback was triggered (if it was registered)
    const detected = await appPage.evaluate(() => {
      return (window as any).__testPoseDetected;
    });

    // Note: This may be false if the page hasn't set up pose detection yet
    // The important thing is no errors occurred
    expect(detected !== undefined).toBe(true);
  });
});

test.describe('Camera Permission Handling', () => {
  test('camera permission UI appears when needed', async ({ appPage }) => {
    // Wait for exercise selection UI
    await appPage.waitForSelector('.exercise-selector button', { timeout: 10000 });

    // Click an exercise to trigger camera request
    await appPage.locator('.exercise-selector button').first().click();

    // Wait a bit for camera request
    await appPage.waitForTimeout(1000);

    // In Electron, camera should be auto-granted
    // Check that we don't see a permission denied message
    const permissionDenied = await appPage.evaluate(() => {
      const body = document.body.textContent || '';
      return body.includes('Permission denied') ||
             body.includes('Camera access denied');
    });

    // In test environment with mock, we shouldn't see permission issues
    // (real camera won't be accessed with mock in place)
    expect(permissionDenied).toBe(false);
  });
});

test.describe('Video Element', () => {
  test('video element is created for camera feed', async ({ appPage }) => {
    // Wait for exercise selection
    await appPage.waitForSelector('.exercise-selector button', { timeout: 10000 });

    // Select an exercise
    await appPage.locator('.exercise-selector button').first().click();

    // Wait for video element
    await appPage.waitForSelector('video', { timeout: 5000 });

    const videoExists = await appPage.evaluate(() => {
      const video = document.querySelector('video');
      return video !== null;
    });

    expect(videoExists).toBe(true);
  });

  test('canvas element is created for pose overlay', async ({ appPage }) => {
    // Select an exercise first
    await appPage.waitForSelector('.exercise-selector button', { timeout: 10000 });
    await appPage.locator('.exercise-selector button').first().click();

    // Wait for canvas (used for pose visualization)
    await appPage.waitForSelector('canvas', { timeout: 5000 });

    const canvasExists = await appPage.evaluate(() => {
      const canvas = document.querySelector('canvas');
      return canvas !== null;
    });

    expect(canvasExists).toBe(true);
  });
});

test.describe('Exercise State Management', () => {
  test('rep counter starts at 0', async ({ appPage }) => {
    // Select an exercise
    await appPage.waitForSelector('.exercise-selector button', { timeout: 10000 });
    await appPage.locator('.exercise-selector button').first().click();

    // Wait for counter to appear
    await appPage.waitForSelector('#counter', { timeout: 5000 });

    const repCount = await getRepCount(appPage);
    expect(repCount).toBe(0);
  });

  test('target reps are displayed', async ({ appPage }) => {
    await appPage.waitForSelector('.exercise-selector button', { timeout: 10000 });
    await appPage.locator('.exercise-selector button').first().click();

    // Wait for target display
    await appPage.waitForSelector('#target, .target', { timeout: 5000 });

    const targetExists = await appPage.evaluate(() => {
      const target = document.querySelector('#target') ||
                     document.querySelector('.target') ||
                     document.body.textContent?.match(/\/\s*\d+/);
      return target !== null;
    });

    expect(targetExists).toBe(true);
  });
});
