import { Page } from '@playwright/test';

/**
 * Mock MediaPipe Pose and Camera classes.
 * Injects via page.addInitScript() before real MediaPipe loads.
 */

export const MEDIAPIPE_MOCK_SCRIPT = `
(() => {
  // Store injected pose frames for deterministic testing
  window.__mockPoseFrames = [];
  window.__mockFrameIndex = 0;
  window.__mockOnResults = null;

  // Mock Pose class
  class MockPose {
    constructor(config) {
      this.config = config;
    }

    setOptions(options) {}

    onResults(callback) {
      window.__mockOnResults = callback;
    }

    async send({ image }) {
      // When send() is called, deliver the next mock frame if available
      if (window.__mockPoseFrames.length > 0 && window.__mockOnResults) {
        const frame = window.__mockPoseFrames[window.__mockFrameIndex % window.__mockPoseFrames.length];
        window.__mockFrameIndex++;
        window.__mockOnResults({
          poseLandmarks: frame,
          poseWorldLandmarks: frame,
          image: image,
        });
      }
    }

    initialize() {
      return Promise.resolve();
    }

    close() {}
  }

  // Mock Camera class
  class MockCamera {
    constructor(video, config) {
      this.video = video;
      this.config = config;
      this._running = false;
      this._interval = null;
    }

    start() {
      this._running = true;
      // Drive frame loop at ~10 FPS
      this._interval = setInterval(() => {
        if (this._running && this.config.onFrame) {
          this.config.onFrame();
        }
      }, 100);
      return Promise.resolve();
    }

    stop() {
      this._running = false;
      if (this._interval) {
        clearInterval(this._interval);
        this._interval = null;
      }
    }
  }

  // Helper: inject a single pose frame from test code
  window.__triggerPoseFrame = (landmarks) => {
    if (window.__mockOnResults) {
      window.__mockOnResults({
        poseLandmarks: landmarks,
        poseWorldLandmarks: landmarks,
        image: document.createElement('canvas'),
      });
    }
  };

  // Replace globals before real scripts load
  window.Pose = MockPose;
  window.Camera = MockCamera;
})();
`;

/**
 * Inject the MediaPipe mock into a page before navigation.
 */
export async function injectMediaPipeMock(page: Page): Promise<void> {
  await page.addInitScript(MEDIAPIPE_MOCK_SCRIPT);
}

/**
 * Set the mock pose frame sequence for deterministic replay.
 */
export async function setPoseFrames(page: Page, frames: any[][]): Promise<void> {
  await page.evaluate((f) => {
    (window as any).__mockPoseFrames = f;
    (window as any).__mockFrameIndex = 0;
  }, frames);
}

/**
 * Trigger a single pose frame with the given landmarks.
 */
export async function triggerPoseFrame(page: Page, landmarks: any[]): Promise<void> {
  await page.evaluate((lm) => {
    (window as any).__triggerPoseFrame(lm);
  }, landmarks);
}

/**
 * Read the current rep count from the DOM.
 */
export async function getRepCount(page: Page): Promise<number> {
  const text = await page.locator('#counter').textContent();
  return parseInt(text || '0', 10);
}
