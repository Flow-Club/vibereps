#!/usr/bin/env node
/**
 * Exercise Tracker - Node.js version
 * Launches exercise UI and handles completion callbacks
 */

import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { exec } from 'node:child_process';
import open from 'open';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = process.env.VIBEREPS_PORT || 8765;
const EXERCISES = process.env.VIBEREPS_EXERCISES || '';
const DISABLED = process.env.VIBEREPS_DISABLED || '';
const API_URL = process.env.VIBEREPS_API_URL || '';
const API_KEY = process.env.VIBEREPS_API_KEY || '';
const PUSHGATEWAY_URL = process.env.PUSHGATEWAY_URL || 'http://localhost:9091';

// Check if disabled
if (DISABLED) {
  console.log(JSON.stringify({ status: 'skipped', message: 'VIBEREPS_DISABLED is set' }));
  process.exit(0);
}

// Get hook type and context from args
const [,, hookType = 'user_prompt_submit', contextJson = '{}'] = process.argv;
const isQuickMode = ['user_prompt_submit', 'post_tool_use'].includes(hookType);

// Load exercise configs
const exercisesDir = path.join(__dirname, '..', 'exercises');
let exerciseList = [];
try {
  const files = fs.readdirSync(exercisesDir).filter(f => f.endsWith('.json') && !f.startsWith('_'));
  exerciseList = files.map(f => {
    const config = JSON.parse(fs.readFileSync(path.join(exercisesDir, f), 'utf-8'));
    return { id: config.id, name: config.name, file: f };
  });
} catch (e) {
  // Fallback to hardcoded list
  exerciseList = [
    { id: 'squats', name: 'Squats' },
    { id: 'pushups', name: 'Push-ups' },
    { id: 'jumping_jacks', name: 'Jumping Jacks' },
  ];
}

// Filter exercises if VIBEREPS_EXERCISES is set
let availableExercises = exerciseList;
if (EXERCISES) {
  const allowed = EXERCISES.split(',').map(s => s.trim());
  availableExercises = exerciseList.filter(e => allowed.includes(e.id));
}

// State
let claudeReady = false;
let sessionComplete = false;

// Create HTTP server
const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);

  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // Routes
  if (url.pathname === '/' || url.pathname === '/index.html') {
    // Serve exercise UI
    const uiPath = path.join(__dirname, '..', 'exercise_ui.html');
    const html = fs.readFileSync(uiPath, 'utf-8');
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(html);
  }
  else if (url.pathname === '/exercises') {
    // Return available exercises
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(availableExercises));
  }
  else if (url.pathname.startsWith('/exercises/') && url.pathname.endsWith('.json')) {
    // Serve exercise config
    const filename = path.basename(url.pathname);
    const configPath = path.join(exercisesDir, filename);
    try {
      const config = fs.readFileSync(configPath, 'utf-8');
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(config);
    } catch (e) {
      res.writeHead(404);
      res.end('Not found');
    }
  }
  else if (url.pathname === '/status') {
    // Check if Claude is ready
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ claude_ready: claudeReady }));
  }
  else if (url.pathname === '/notify' && req.method === 'POST') {
    // Claude finished
    claudeReady = true;
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'notified' }));
  }
  else if (url.pathname === '/complete' && req.method === 'POST') {
    // Exercise session complete
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      try {
        const data = JSON.parse(body);
        handleComplete(data);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'success' }));
      } catch (e) {
        res.writeHead(400);
        res.end(JSON.stringify({ error: e.message }));
      }
    });
  }
  else {
    res.writeHead(404);
    res.end('Not found');
  }
});

// Handle exercise completion
async function handleComplete(data) {
  const { exercise, reps, duration } = data;
  console.log(`✓ Completed ${reps} ${exercise} in ${duration}s`);

  // Push to Prometheus Pushgateway
  if (PUSHGATEWAY_URL) {
    try {
      const metrics = [
        `exercise_reps_total{exercise="${exercise}"} ${reps}`,
        `exercise_sessions_total{exercise="${exercise}"} 1`,
      ].join('\n');

      const pushReq = http.request(`${PUSHGATEWAY_URL}/metrics/job/vibereps/exercise/${exercise}`, {
        method: 'POST',
        headers: { 'Content-Type': 'text/plain' },
      });
      pushReq.write(metrics);
      pushReq.end();
    } catch (e) {
      // Ignore pushgateway errors
    }
  }

  // Post to remote API
  if (API_URL && API_KEY) {
    try {
      const apiReq = http.request(`${API_URL}/api/log`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
        },
      });
      apiReq.write(JSON.stringify({ exercise, reps, duration }));
      apiReq.end();
    } catch (e) {
      // Ignore API errors
    }
  }

  sessionComplete = true;

  // Shutdown after a delay
  setTimeout(() => {
    server.close();
    process.exit(0);
  }, 1000);
}

// Open browser window
function openWindow() {
  const url = `http://localhost:${PORT}/?quick=${isQuickMode}`;

  // Try Chrome app mode first (smaller window)
  const chromeArgs = [
    `--app=${url}`,
    '--window-size=340,520',
    '--window-position=50,50',
    '--user-data-dir=/tmp/vibereps-chrome',
  ];

  if (process.platform === 'darwin') {
    exec(`"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ${chromeArgs.join(' ')}`, (err) => {
      if (err) open(url); // Fallback to default browser
    });
  } else {
    open(url);
  }
}

// Start server
server.listen(PORT, () => {
  console.log(JSON.stringify({ status: 'success', message: 'Exercise tracker launched in background' }));
  openWindow();

  // Timeout after 10 minutes
  setTimeout(() => {
    if (!sessionComplete) {
      console.log('⏱️ Session timeout');
      server.close();
      process.exit(0);
    }
  }, 10 * 60 * 1000);
});
