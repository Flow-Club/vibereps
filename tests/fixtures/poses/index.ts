/**
 * Pre-recorded pose landmark sequences for testing exercise detection.
 *
 * MediaPipe pose has 33 landmarks. Key indices:
 * 11/12 = left/right shoulder
 * 13/14 = left/right elbow
 * 15/16 = left/right wrist
 * 23/24 = left/right hip
 * 25/26 = left/right knee
 * 27/28 = left/right ankle
 */

interface Landmark {
  x: number;
  y: number;
  z: number;
  visibility: number;
}

type PoseFrame = Landmark[];

export interface PoseSequence {
  name: string;
  frames: PoseFrame[];
  expectedReps: number;
}

/** Create a full 33-landmark pose with specified overrides. */
function createFullPose(overrides: Record<number, Partial<Landmark>> = {}): PoseFrame {
  const defaultPose: PoseFrame = Array.from({ length: 33 }, (_, i) => ({
    x: 0.5,
    y: 0.5,
    z: 0,
    visibility: 0.99,
  }));

  // Set a realistic standing position
  // Head/face (0-10)
  defaultPose[0] = { x: 0.5, y: 0.15, z: 0, visibility: 0.99 }; // nose
  // Shoulders (11-12)
  defaultPose[11] = { x: 0.4, y: 0.3, z: 0, visibility: 0.99 }; // left shoulder
  defaultPose[12] = { x: 0.6, y: 0.3, z: 0, visibility: 0.99 }; // right shoulder
  // Elbows (13-14)
  defaultPose[13] = { x: 0.35, y: 0.45, z: 0, visibility: 0.99 }; // left elbow
  defaultPose[14] = { x: 0.65, y: 0.45, z: 0, visibility: 0.99 }; // right elbow
  // Wrists (15-16)
  defaultPose[15] = { x: 0.35, y: 0.55, z: 0, visibility: 0.99 }; // left wrist
  defaultPose[16] = { x: 0.65, y: 0.55, z: 0, visibility: 0.99 }; // right wrist
  // Hips (23-24)
  defaultPose[23] = { x: 0.45, y: 0.55, z: 0, visibility: 0.99 }; // left hip
  defaultPose[24] = { x: 0.55, y: 0.55, z: 0, visibility: 0.99 }; // right hip
  // Knees (25-26)
  defaultPose[25] = { x: 0.45, y: 0.72, z: 0, visibility: 0.99 }; // left knee
  defaultPose[26] = { x: 0.55, y: 0.72, z: 0, visibility: 0.99 }; // right knee
  // Ankles (27-28)
  defaultPose[27] = { x: 0.45, y: 0.9, z: 0, visibility: 0.99 }; // left ankle
  defaultPose[28] = { x: 0.55, y: 0.9, z: 0, visibility: 0.99 }; // right ankle

  // Apply overrides
  for (const [idx, override] of Object.entries(overrides)) {
    defaultPose[Number(idx)] = { ...defaultPose[Number(idx)], ...override };
  }

  return defaultPose;
}

/** Interpolate between two poses over N steps. */
function generateTransition(start: PoseFrame, end: PoseFrame, steps: number): PoseFrame[] {
  const frames: PoseFrame[] = [];
  for (let i = 0; i <= steps; i++) {
    const t = i / steps;
    frames.push(
      start.map((lm, idx) => ({
        x: lm.x + (end[idx].x - lm.x) * t,
        y: lm.y + (end[idx].y - lm.y) * t,
        z: lm.z + (end[idx].z - lm.z) * t,
        visibility: lm.visibility,
      }))
    );
  }
  return frames;
}

// -- Squat poses --

const STANDING = createFullPose();

// Deep squat: knees bent to ~90 degrees
const SQUAT_DOWN = createFullPose({
  23: { x: 0.45, y: 0.50, z: 0, visibility: 0.99 }, // left hip drops
  24: { x: 0.55, y: 0.50, z: 0, visibility: 0.99 }, // right hip drops
  25: { x: 0.35, y: 0.65, z: 0, visibility: 0.99 }, // left knee forward and out
  26: { x: 0.65, y: 0.65, z: 0, visibility: 0.99 }, // right knee forward and out
  27: { x: 0.45, y: 0.80, z: 0, visibility: 0.99 }, // left ankle below knee
  28: { x: 0.55, y: 0.80, z: 0, visibility: 0.99 }, // right ankle below knee
});

// Shallow squat (shouldn't count)
const SHALLOW_SQUAT = createFullPose({
  25: { x: 0.44, y: 0.7, z: 0.05, visibility: 0.99 },
  26: { x: 0.56, y: 0.7, z: 0.05, visibility: 0.99 },
});

function makeSquatRep(): PoseFrame[] {
  return [
    ...generateTransition(STANDING, SQUAT_DOWN, 5),
    ...generateTransition(SQUAT_DOWN, STANDING, 5),
  ];
}

export const SQUAT_3_REPS: PoseSequence = {
  name: 'squats-3-reps',
  frames: [
    ...STANDING ? [STANDING, STANDING, STANDING] : [], // Warm-up frames
    ...makeSquatRep(),
    ...makeSquatRep(),
    ...makeSquatRep(),
  ],
  expectedReps: 3,
};

export const SQUAT_SHALLOW: PoseSequence = {
  name: 'squats-shallow',
  frames: [
    STANDING, STANDING, STANDING,
    ...generateTransition(STANDING, SHALLOW_SQUAT, 5),
    ...generateTransition(SHALLOW_SQUAT, STANDING, 5),
  ],
  expectedReps: 0,
};

// -- Jumping Jack poses --

const ARMS_DOWN = createFullPose(); // Default standing = arms down

const ARMS_UP = createFullPose({
  // Wrists above shoulders
  15: { x: 0.3, y: 0.15, z: 0, visibility: 0.99 }, // left wrist up
  16: { x: 0.7, y: 0.15, z: 0, visibility: 0.99 }, // right wrist up
  13: { x: 0.35, y: 0.2, z: 0, visibility: 0.99 }, // left elbow up
  14: { x: 0.65, y: 0.2, z: 0, visibility: 0.99 }, // right elbow up
});

function makeJumpingJackRep(): PoseFrame[] {
  return [
    ...generateTransition(ARMS_DOWN, ARMS_UP, 4),
    ...generateTransition(ARMS_UP, ARMS_DOWN, 4),
  ];
}

export const JUMPING_JACK_3_REPS: PoseSequence = {
  name: 'jumping-jacks-3-reps',
  frames: [
    ARMS_DOWN, ARMS_DOWN, ARMS_DOWN,
    ...makeJumpingJackRep(),
    ...makeJumpingJackRep(),
    ...makeJumpingJackRep(),
  ],
  expectedReps: 3,
};
