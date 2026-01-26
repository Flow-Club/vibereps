import { Page } from '@playwright/test';

// MediaPipe pose landmark indices
export const POSE_LANDMARKS = {
  NOSE: 0,
  LEFT_EYE_INNER: 1,
  LEFT_EYE: 2,
  LEFT_EYE_OUTER: 3,
  RIGHT_EYE_INNER: 4,
  RIGHT_EYE: 5,
  RIGHT_EYE_OUTER: 6,
  LEFT_EAR: 7,
  RIGHT_EAR: 8,
  MOUTH_LEFT: 9,
  MOUTH_RIGHT: 10,
  LEFT_SHOULDER: 11,
  RIGHT_SHOULDER: 12,
  LEFT_ELBOW: 13,
  RIGHT_ELBOW: 14,
  LEFT_WRIST: 15,
  RIGHT_WRIST: 16,
  LEFT_PINKY: 17,
  RIGHT_PINKY: 18,
  LEFT_INDEX: 19,
  RIGHT_INDEX: 20,
  LEFT_THUMB: 21,
  RIGHT_THUMB: 22,
  LEFT_HIP: 23,
  RIGHT_HIP: 24,
  LEFT_KNEE: 25,
  RIGHT_KNEE: 26,
  LEFT_ANKLE: 27,
  RIGHT_ANKLE: 28,
  LEFT_HEEL: 29,
  RIGHT_HEEL: 30,
  LEFT_FOOT_INDEX: 31,
  RIGHT_FOOT_INDEX: 32,
};

export interface PoseLandmark {
  x: number;
  y: number;
  z: number;
  visibility: number;
}

export interface PoseFrame {
  timestamp: number;
  landmarks: PoseLandmark[];
}

export interface PoseSequence {
  exercise: string;
  frames: PoseFrame[];
  expectedReps: number;
}

// Create a default landmark with high visibility
function createLandmark(x: number, y: number, z = 0, visibility = 0.99): PoseLandmark {
  return { x, y, z, visibility };
}

// Create a full 33-landmark pose from key points
export function createFullPose(keyPoints: Partial<Record<keyof typeof POSE_LANDMARKS, { x: number; y: number; z?: number }>>): PoseLandmark[] {
  // Start with default standing pose
  const landmarks: PoseLandmark[] = [];

  // Default standing pose landmarks
  const defaultPose: Record<number, { x: number; y: number; z: number }> = {
    [POSE_LANDMARKS.NOSE]: { x: 0.5, y: 0.15, z: 0 },
    [POSE_LANDMARKS.LEFT_EYE_INNER]: { x: 0.48, y: 0.13, z: 0 },
    [POSE_LANDMARKS.LEFT_EYE]: { x: 0.47, y: 0.13, z: 0 },
    [POSE_LANDMARKS.LEFT_EYE_OUTER]: { x: 0.46, y: 0.13, z: 0 },
    [POSE_LANDMARKS.RIGHT_EYE_INNER]: { x: 0.52, y: 0.13, z: 0 },
    [POSE_LANDMARKS.RIGHT_EYE]: { x: 0.53, y: 0.13, z: 0 },
    [POSE_LANDMARKS.RIGHT_EYE_OUTER]: { x: 0.54, y: 0.13, z: 0 },
    [POSE_LANDMARKS.LEFT_EAR]: { x: 0.44, y: 0.14, z: 0 },
    [POSE_LANDMARKS.RIGHT_EAR]: { x: 0.56, y: 0.14, z: 0 },
    [POSE_LANDMARKS.MOUTH_LEFT]: { x: 0.48, y: 0.18, z: 0 },
    [POSE_LANDMARKS.MOUTH_RIGHT]: { x: 0.52, y: 0.18, z: 0 },
    [POSE_LANDMARKS.LEFT_SHOULDER]: { x: 0.4, y: 0.25, z: 0 },
    [POSE_LANDMARKS.RIGHT_SHOULDER]: { x: 0.6, y: 0.25, z: 0 },
    [POSE_LANDMARKS.LEFT_ELBOW]: { x: 0.35, y: 0.4, z: 0 },
    [POSE_LANDMARKS.RIGHT_ELBOW]: { x: 0.65, y: 0.4, z: 0 },
    [POSE_LANDMARKS.LEFT_WRIST]: { x: 0.35, y: 0.55, z: 0 },
    [POSE_LANDMARKS.RIGHT_WRIST]: { x: 0.65, y: 0.55, z: 0 },
    [POSE_LANDMARKS.LEFT_PINKY]: { x: 0.33, y: 0.57, z: 0 },
    [POSE_LANDMARKS.RIGHT_PINKY]: { x: 0.67, y: 0.57, z: 0 },
    [POSE_LANDMARKS.LEFT_INDEX]: { x: 0.34, y: 0.58, z: 0 },
    [POSE_LANDMARKS.RIGHT_INDEX]: { x: 0.66, y: 0.58, z: 0 },
    [POSE_LANDMARKS.LEFT_THUMB]: { x: 0.36, y: 0.56, z: 0 },
    [POSE_LANDMARKS.RIGHT_THUMB]: { x: 0.64, y: 0.56, z: 0 },
    [POSE_LANDMARKS.LEFT_HIP]: { x: 0.45, y: 0.55, z: 0 },
    [POSE_LANDMARKS.RIGHT_HIP]: { x: 0.55, y: 0.55, z: 0 },
    [POSE_LANDMARKS.LEFT_KNEE]: { x: 0.45, y: 0.72, z: 0 },
    [POSE_LANDMARKS.RIGHT_KNEE]: { x: 0.55, y: 0.72, z: 0 },
    [POSE_LANDMARKS.LEFT_ANKLE]: { x: 0.45, y: 0.9, z: 0 },
    [POSE_LANDMARKS.RIGHT_ANKLE]: { x: 0.55, y: 0.9, z: 0 },
    [POSE_LANDMARKS.LEFT_HEEL]: { x: 0.44, y: 0.92, z: 0 },
    [POSE_LANDMARKS.RIGHT_HEEL]: { x: 0.56, y: 0.92, z: 0 },
    [POSE_LANDMARKS.LEFT_FOOT_INDEX]: { x: 0.43, y: 0.95, z: 0 },
    [POSE_LANDMARKS.RIGHT_FOOT_INDEX]: { x: 0.57, y: 0.95, z: 0 },
  };

  // Create all 33 landmarks
  for (let i = 0; i < 33; i++) {
    const def = defaultPose[i] || { x: 0.5, y: 0.5, z: 0 };
    landmarks.push(createLandmark(def.x, def.y, def.z));
  }

  // Override with provided key points
  for (const [name, point] of Object.entries(keyPoints)) {
    const index = POSE_LANDMARKS[name as keyof typeof POSE_LANDMARKS];
    if (index !== undefined && point) {
      landmarks[index] = createLandmark(point.x, point.y, point.z || 0);
    }
  }

  return landmarks;
}

// Inject mock MediaPipe into page
export async function injectMediaPipeMock(page: Page): Promise<void> {
  await page.addInitScript(() => {
    // Store frames to play
    (window as any).__mockPoseFrames = [];
    (window as any).__mockPoseCallback = null;
    (window as any).__mockPoseIndex = 0;

    // Mock Pose class
    class MockPose {
      private resultsCallback: ((results: any) => void) | null = null;

      constructor(config: any) {
        console.log('[MockPose] Created with config:', config);
      }

      setOptions(options: any) {
        console.log('[MockPose] setOptions:', options);
      }

      onResults(callback: (results: any) => void) {
        this.resultsCallback = callback;
        (window as any).__mockPoseCallback = callback;
        console.log('[MockPose] onResults callback registered');
      }

      async send(input: any) {
        // When send is called, we play the next frame from our mock data
        const frames = (window as any).__mockPoseFrames;
        const index = (window as any).__mockPoseIndex;

        if (frames.length > 0 && this.resultsCallback) {
          const frame = frames[index % frames.length];
          this.resultsCallback({
            poseLandmarks: frame.landmarks,
            image: input.image,
          });
          (window as any).__mockPoseIndex = index + 1;
        }
      }

      initialize() {
        return Promise.resolve();
      }

      close() {
        console.log('[MockPose] closed');
      }
    }

    // Mock Camera class
    class MockCamera {
      constructor(videoElement: HTMLVideoElement, config: any) {
        console.log('[MockCamera] Created');
        // Immediately call onFrame periodically to simulate camera
        if (config.onFrame) {
          setInterval(async () => {
            await config.onFrame({ video: videoElement });
          }, 100); // 10 FPS
        }
      }

      start() {
        console.log('[MockCamera] started');
        return Promise.resolve();
      }

      stop() {
        console.log('[MockCamera] stopped');
      }
    }

    // Replace global Pose and Camera
    (window as any).Pose = MockPose;
    (window as any).Camera = MockCamera;

    // Helper to inject frames
    (window as any).__injectPoseFrames = (frames: any[]) => {
      (window as any).__mockPoseFrames = frames;
      (window as any).__mockPoseIndex = 0;
      console.log('[MockPose] Injected', frames.length, 'frames');
    };

    // Helper to trigger a single frame
    (window as any).__triggerPoseFrame = (landmarks: any[]) => {
      const callback = (window as any).__mockPoseCallback;
      if (callback) {
        callback({ poseLandmarks: landmarks });
      }
    };
  });
}

// Play a sequence of pose frames in the page
export async function playPoseSequence(page: Page, sequence: PoseSequence): Promise<void> {
  await page.evaluate((frames) => {
    (window as any).__injectPoseFrames(frames);
  }, sequence.frames);

  // Trigger each frame with a small delay
  for (const frame of sequence.frames) {
    await page.evaluate((landmarks) => {
      (window as any).__triggerPoseFrame(landmarks);
    }, frame.landmarks);
    await page.waitForTimeout(50); // 50ms between frames
  }
}

// Trigger a single pose frame
export async function triggerPoseFrame(page: Page, landmarks: PoseLandmark[]): Promise<void> {
  await page.evaluate((lm) => {
    (window as any).__triggerPoseFrame(lm);
  }, landmarks);
}

// Get current rep count from the page
export async function getRepCount(page: Page): Promise<number> {
  return await page.evaluate(() => {
    const counter = document.getElementById('counter');
    return counter ? parseInt(counter.textContent || '0', 10) : 0;
  });
}

// Get exercise state from the page
export async function getExerciseState(page: Page): Promise<string | null> {
  return await page.evaluate(() => {
    return (window as any).exerciseState || null;
  });
}
