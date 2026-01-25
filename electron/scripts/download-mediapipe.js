#!/usr/bin/env node

/**
 * Download MediaPipe Pose models for offline use
 *
 * This script downloads all the necessary MediaPipe files from jsDelivr CDN
 * and saves them to the assets/mediapipe directory.
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

const POSE_VERSION = '0.5.1675469404';
const CAMERA_UTILS_VERSION = '0.3.1640029074';

const BASE_URL = 'https://cdn.jsdelivr.net/npm/@mediapipe';
const OUTPUT_DIR = path.join(__dirname, '..', 'assets', 'mediapipe');

// Files to download for @mediapipe/pose
const POSE_FILES = [
  'pose.js',
  'pose_solution_packed_assets_loader.js',
  'pose_solution_simd_wasm_bin.js',
  'pose_solution_packed_assets.data',
  'pose_solution_simd_wasm_bin.wasm',
  'pose_landmark_full.tflite',
  'pose_landmark_lite.tflite',
  'pose_landmark_heavy.tflite',
  'pose_web.binarypb'
];

// Files to download for @mediapipe/camera_utils
const CAMERA_FILES = [
  'camera_utils.js'
];

async function downloadFile(url, destPath) {
  return new Promise((resolve, reject) => {
    console.log(`Downloading: ${url}`);

    const file = fs.createWriteStream(destPath);

    https.get(url, (response) => {
      // Follow redirects
      if (response.statusCode === 301 || response.statusCode === 302) {
        file.close();
        fs.unlinkSync(destPath);
        return downloadFile(response.headers.location, destPath).then(resolve).catch(reject);
      }

      if (response.statusCode !== 200) {
        file.close();
        fs.unlinkSync(destPath);
        reject(new Error(`HTTP ${response.statusCode} for ${url}`));
        return;
      }

      response.pipe(file);

      file.on('finish', () => {
        file.close();
        const stats = fs.statSync(destPath);
        console.log(`  -> Saved: ${destPath} (${formatBytes(stats.size)})`);
        resolve();
      });

      file.on('error', (err) => {
        fs.unlinkSync(destPath);
        reject(err);
      });
    }).on('error', (err) => {
      file.close();
      if (fs.existsSync(destPath)) {
        fs.unlinkSync(destPath);
      }
      reject(err);
    });
  });
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

async function main() {
  console.log('Downloading MediaPipe models for offline use...\n');

  // Create output directories
  const poseDir = path.join(OUTPUT_DIR, 'pose');
  const cameraDir = path.join(OUTPUT_DIR, 'camera_utils');

  fs.mkdirSync(poseDir, { recursive: true });
  fs.mkdirSync(cameraDir, { recursive: true });

  let totalSize = 0;
  let downloaded = 0;
  let failed = 0;

  // Download pose files
  console.log(`Downloading @mediapipe/pose@${POSE_VERSION}...`);
  for (const file of POSE_FILES) {
    const url = `${BASE_URL}/pose@${POSE_VERSION}/${file}`;
    const destPath = path.join(poseDir, file);

    try {
      await downloadFile(url, destPath);
      totalSize += fs.statSync(destPath).size;
      downloaded++;
    } catch (err) {
      console.error(`  -> Failed: ${file} - ${err.message}`);
      failed++;
    }
  }

  // Download camera_utils files
  console.log(`\nDownloading @mediapipe/camera_utils@${CAMERA_UTILS_VERSION}...`);
  for (const file of CAMERA_FILES) {
    const url = `${BASE_URL}/camera_utils@${CAMERA_UTILS_VERSION}/${file}`;
    const destPath = path.join(cameraDir, file);

    try {
      await downloadFile(url, destPath);
      totalSize += fs.statSync(destPath).size;
      downloaded++;
    } catch (err) {
      console.error(`  -> Failed: ${file} - ${err.message}`);
      failed++;
    }
  }

  console.log('\n' + '='.repeat(50));
  console.log(`Downloaded: ${downloaded} files (${formatBytes(totalSize)})`);
  if (failed > 0) {
    console.log(`Failed: ${failed} files`);
  }
  console.log(`Output: ${OUTPUT_DIR}`);

  // Create a version file
  const versionInfo = {
    pose: POSE_VERSION,
    camera_utils: CAMERA_UTILS_VERSION,
    downloadedAt: new Date().toISOString()
  };
  fs.writeFileSync(
    path.join(OUTPUT_DIR, 'version.json'),
    JSON.stringify(versionInfo, null, 2)
  );
  console.log('\nCreated version.json');

  if (failed > 0) {
    process.exit(1);
  }
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
