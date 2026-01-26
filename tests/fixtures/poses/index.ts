/**
 * Mock pose sequences for exercise detection testing
 *
 * These sequences simulate actual human movements for each exercise type,
 * allowing deterministic testing of the detection algorithms.
 */

import { PoseSequence, PoseLandmark, POSE_LANDMARKS, createFullPose } from '../../mocks/mediapipe-mock';

// Helper to interpolate between two poses
function interpolatePose(from: PoseLandmark[], to: PoseLandmark[], t: number): PoseLandmark[] {
  return from.map((landmark, i) => ({
    x: landmark.x + (to[i].x - landmark.x) * t,
    y: landmark.y + (to[i].y - landmark.y) * t,
    z: landmark.z + (to[i].z - landmark.z) * t,
    visibility: Math.min(landmark.visibility, to[i].visibility),
  }));
}

// Generate frames between two poses
function generateTransition(from: PoseLandmark[], to: PoseLandmark[], steps: number, startTime: number): { timestamp: number; landmarks: PoseLandmark[] }[] {
  const frames = [];
  for (let i = 0; i <= steps; i++) {
    frames.push({
      timestamp: startTime + i * 50, // 50ms per frame
      landmarks: interpolatePose(from, to, i / steps),
    });
  }
  return frames;
}

// Standing pose (neutral)
const STANDING_POSE = createFullPose({
  LEFT_SHOULDER: { x: 0.4, y: 0.25 },
  RIGHT_SHOULDER: { x: 0.6, y: 0.25 },
  LEFT_ELBOW: { x: 0.35, y: 0.4 },
  RIGHT_ELBOW: { x: 0.65, y: 0.4 },
  LEFT_WRIST: { x: 0.35, y: 0.55 },
  RIGHT_WRIST: { x: 0.65, y: 0.55 },
  LEFT_HIP: { x: 0.45, y: 0.55 },
  RIGHT_HIP: { x: 0.55, y: 0.55 },
  LEFT_KNEE: { x: 0.45, y: 0.72 },
  RIGHT_KNEE: { x: 0.55, y: 0.72 },
  LEFT_ANKLE: { x: 0.45, y: 0.9 },
  RIGHT_ANKLE: { x: 0.55, y: 0.9 },
});

// ============================================
// SQUAT POSES
// ============================================

// Deep squat pose - knees bent ~90 degrees
const SQUAT_DOWN_POSE = createFullPose({
  LEFT_SHOULDER: { x: 0.4, y: 0.35 },  // Lower due to squat
  RIGHT_SHOULDER: { x: 0.6, y: 0.35 },
  LEFT_ELBOW: { x: 0.35, y: 0.45 },
  RIGHT_ELBOW: { x: 0.65, y: 0.45 },
  LEFT_WRIST: { x: 0.4, y: 0.5 },
  RIGHT_WRIST: { x: 0.6, y: 0.5 },
  LEFT_HIP: { x: 0.45, y: 0.6 },
  RIGHT_HIP: { x: 0.55, y: 0.6 },
  // Knees forward and bent
  LEFT_KNEE: { x: 0.42, y: 0.75 },
  RIGHT_KNEE: { x: 0.58, y: 0.75 },
  LEFT_ANKLE: { x: 0.45, y: 0.9 },
  RIGHT_ANKLE: { x: 0.55, y: 0.9 },
});

// Shallow squat (should not count as a rep)
const SQUAT_SHALLOW_POSE = createFullPose({
  LEFT_SHOULDER: { x: 0.4, y: 0.28 },
  RIGHT_SHOULDER: { x: 0.6, y: 0.28 },
  LEFT_HIP: { x: 0.45, y: 0.57 },
  RIGHT_HIP: { x: 0.55, y: 0.57 },
  LEFT_KNEE: { x: 0.44, y: 0.73 },
  RIGHT_KNEE: { x: 0.56, y: 0.73 },
  LEFT_ANKLE: { x: 0.45, y: 0.9 },
  RIGHT_ANKLE: { x: 0.55, y: 0.9 },
});

export const SQUAT_ONE_REP: PoseSequence = {
  exercise: 'squats',
  expectedReps: 1,
  frames: [
    // Start standing
    ...generateTransition(STANDING_POSE, STANDING_POSE, 3, 0),
    // Go down into squat
    ...generateTransition(STANDING_POSE, SQUAT_DOWN_POSE, 5, 150),
    // Hold at bottom
    ...generateTransition(SQUAT_DOWN_POSE, SQUAT_DOWN_POSE, 2, 400),
    // Stand back up
    ...generateTransition(SQUAT_DOWN_POSE, STANDING_POSE, 5, 500),
    // End standing
    ...generateTransition(STANDING_POSE, STANDING_POSE, 2, 750),
  ],
};

export const SQUAT_THREE_REPS: PoseSequence = {
  exercise: 'squats',
  expectedReps: 3,
  frames: [
    // Start standing
    { timestamp: 0, landmarks: STANDING_POSE },
    // Rep 1
    ...generateTransition(STANDING_POSE, SQUAT_DOWN_POSE, 4, 50),
    ...generateTransition(SQUAT_DOWN_POSE, STANDING_POSE, 4, 250),
    // Rep 2
    ...generateTransition(STANDING_POSE, SQUAT_DOWN_POSE, 4, 500),
    ...generateTransition(SQUAT_DOWN_POSE, STANDING_POSE, 4, 700),
    // Rep 3
    ...generateTransition(STANDING_POSE, SQUAT_DOWN_POSE, 4, 950),
    ...generateTransition(SQUAT_DOWN_POSE, STANDING_POSE, 4, 1150),
  ],
};

export const SQUAT_SHALLOW_NO_REP: PoseSequence = {
  exercise: 'squats',
  expectedReps: 0,
  frames: [
    { timestamp: 0, landmarks: STANDING_POSE },
    ...generateTransition(STANDING_POSE, SQUAT_SHALLOW_POSE, 4, 50),
    ...generateTransition(SQUAT_SHALLOW_POSE, STANDING_POSE, 4, 250),
  ],
};

// ============================================
// JUMPING JACK POSES
// ============================================

// Arms up, legs apart
const JUMPING_JACK_UP_POSE = createFullPose({
  LEFT_SHOULDER: { x: 0.35, y: 0.25 },
  RIGHT_SHOULDER: { x: 0.65, y: 0.25 },
  // Arms up above shoulders
  LEFT_ELBOW: { x: 0.25, y: 0.15 },
  RIGHT_ELBOW: { x: 0.75, y: 0.15 },
  LEFT_WRIST: { x: 0.2, y: 0.05 },   // Above shoulders
  RIGHT_WRIST: { x: 0.8, y: 0.05 },
  LEFT_HIP: { x: 0.4, y: 0.55 },
  RIGHT_HIP: { x: 0.6, y: 0.55 },
  // Legs apart
  LEFT_KNEE: { x: 0.35, y: 0.72 },
  RIGHT_KNEE: { x: 0.65, y: 0.72 },
  LEFT_ANKLE: { x: 0.3, y: 0.9 },
  RIGHT_ANKLE: { x: 0.7, y: 0.9 },
});

// Arms down, legs together
const JUMPING_JACK_DOWN_POSE = createFullPose({
  LEFT_SHOULDER: { x: 0.4, y: 0.25 },
  RIGHT_SHOULDER: { x: 0.6, y: 0.25 },
  // Arms down at sides
  LEFT_ELBOW: { x: 0.35, y: 0.4 },
  RIGHT_ELBOW: { x: 0.65, y: 0.4 },
  LEFT_WRIST: { x: 0.35, y: 0.55 },  // Below shoulders
  RIGHT_WRIST: { x: 0.65, y: 0.55 },
  LEFT_HIP: { x: 0.45, y: 0.55 },
  RIGHT_HIP: { x: 0.55, y: 0.55 },
  // Legs together
  LEFT_KNEE: { x: 0.47, y: 0.72 },
  RIGHT_KNEE: { x: 0.53, y: 0.72 },
  LEFT_ANKLE: { x: 0.47, y: 0.9 },
  RIGHT_ANKLE: { x: 0.53, y: 0.9 },
});

export const JUMPING_JACK_ONE_REP: PoseSequence = {
  exercise: 'jumping_jacks',
  expectedReps: 1,
  frames: [
    // Start down
    ...generateTransition(JUMPING_JACK_DOWN_POSE, JUMPING_JACK_DOWN_POSE, 2, 0),
    // Jump up
    ...generateTransition(JUMPING_JACK_DOWN_POSE, JUMPING_JACK_UP_POSE, 3, 100),
    // Hold up
    { timestamp: 250, landmarks: JUMPING_JACK_UP_POSE },
    // Back down (completes the rep)
    ...generateTransition(JUMPING_JACK_UP_POSE, JUMPING_JACK_DOWN_POSE, 3, 300),
  ],
};

export const JUMPING_JACK_FIVE_REPS: PoseSequence = {
  exercise: 'jumping_jacks',
  expectedReps: 5,
  frames: (() => {
    const frames: { timestamp: number; landmarks: PoseLandmark[] }[] = [];
    for (let i = 0; i < 5; i++) {
      const baseTime = i * 400;
      frames.push(
        ...generateTransition(JUMPING_JACK_DOWN_POSE, JUMPING_JACK_UP_POSE, 3, baseTime),
        ...generateTransition(JUMPING_JACK_UP_POSE, JUMPING_JACK_DOWN_POSE, 3, baseTime + 200),
      );
    }
    return frames;
  })(),
};

// ============================================
// CALF RAISE POSES
// ============================================

const CALF_RAISE_DOWN_POSE = createFullPose({
  LEFT_HEEL: { x: 0.44, y: 0.92 },
  RIGHT_HEEL: { x: 0.56, y: 0.92 },
  LEFT_ANKLE: { x: 0.45, y: 0.9 },
  RIGHT_ANKLE: { x: 0.55, y: 0.9 },
});

const CALF_RAISE_UP_POSE = createFullPose({
  // Heels raised
  LEFT_HEEL: { x: 0.44, y: 0.88 },
  RIGHT_HEEL: { x: 0.56, y: 0.88 },
  LEFT_ANKLE: { x: 0.45, y: 0.87 },
  RIGHT_ANKLE: { x: 0.55, y: 0.87 },
});

export const CALF_RAISE_ONE_REP: PoseSequence = {
  exercise: 'calf_raises',
  expectedReps: 1,
  frames: [
    // Start flat
    ...generateTransition(CALF_RAISE_DOWN_POSE, CALF_RAISE_DOWN_POSE, 3, 0),
    // Raise heels
    ...generateTransition(CALF_RAISE_DOWN_POSE, CALF_RAISE_UP_POSE, 4, 150),
    // Hold up
    { timestamp: 350, landmarks: CALF_RAISE_UP_POSE },
    // Lower heels (completes rep)
    ...generateTransition(CALF_RAISE_UP_POSE, CALF_RAISE_DOWN_POSE, 4, 400),
  ],
};

// ============================================
// STANDING CRUNCH POSES
// ============================================

const STANDING_CRUNCH_UP_POSE = createFullPose({
  LEFT_ELBOW: { x: 0.35, y: 0.35 },
  RIGHT_ELBOW: { x: 0.65, y: 0.35 },
  LEFT_KNEE: { x: 0.45, y: 0.72 },
  RIGHT_KNEE: { x: 0.55, y: 0.72 },
});

// Elbow and knee close together (crunch position)
const STANDING_CRUNCH_DOWN_POSE = createFullPose({
  // Right elbow comes down
  LEFT_ELBOW: { x: 0.35, y: 0.35 },
  RIGHT_ELBOW: { x: 0.55, y: 0.5 },
  // Right knee comes up
  LEFT_KNEE: { x: 0.45, y: 0.72 },
  RIGHT_KNEE: { x: 0.55, y: 0.55 },  // Knee raised toward elbow
});

export const STANDING_CRUNCH_ONE_REP: PoseSequence = {
  exercise: 'standing_crunches',
  expectedReps: 1,
  frames: [
    // Start upright
    ...generateTransition(STANDING_CRUNCH_UP_POSE, STANDING_CRUNCH_UP_POSE, 2, 0),
    // Crunch
    ...generateTransition(STANDING_CRUNCH_UP_POSE, STANDING_CRUNCH_DOWN_POSE, 4, 100),
    // Hold
    { timestamp: 300, landmarks: STANDING_CRUNCH_DOWN_POSE },
    // Return up (completes rep)
    ...generateTransition(STANDING_CRUNCH_DOWN_POSE, STANDING_CRUNCH_UP_POSE, 4, 350),
  ],
};

// Export all sequences
export const POSE_SEQUENCES = {
  SQUAT_ONE_REP,
  SQUAT_THREE_REPS,
  SQUAT_SHALLOW_NO_REP,
  JUMPING_JACK_ONE_REP,
  JUMPING_JACK_FIVE_REPS,
  CALF_RAISE_ONE_REP,
  STANDING_CRUNCH_ONE_REP,
};
