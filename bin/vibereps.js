#!/usr/bin/env node
/**
 * vibereps CLI
 * Usage:
 *   vibereps              - Start exercise tracker
 *   vibereps stats        - Show combined code + exercise stats
 *   vibereps notify       - Notify tracker that Claude is ready
 */

import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const [,, command = 'start', ...args] = process.argv;

switch (command) {
  case 'start':
  case 'user_prompt_submit':
  case 'post_tool_use':
  case 'task_complete':
    // Launch tracker
    const tracker = spawn('node', [
      path.join(__dirname, '..', 'src', 'tracker.js'),
      command,
      ...args
    ], {
      detached: true,
      stdio: 'inherit',
    });
    tracker.unref();
    break;

  case 'notify':
    // Notify tracker that Claude is ready
    fetch('http://localhost:8765/notify', { method: 'POST' })
      .then(() => console.log('Notified'))
      .catch(() => console.log('Tracker not running'));
    break;

  case 'stats':
    // Show combined stats (uses ccusage)
    const stats = spawn('node', [
      path.join(__dirname, '..', 'src', 'stats.js'),
      ...args
    ], {
      stdio: 'inherit',
    });
    break;

  default:
    console.log(`
vibereps - Exercise tracking for vibe coders

Commands:
  vibereps              Start exercise tracker
  vibereps stats        Show code + exercise stats
  vibereps notify       Notify tracker Claude is ready

Environment:
  VIBEREPS_EXERCISES    Comma-separated exercises (squats,pushups,...)
  VIBEREPS_DISABLED=1   Disable temporarily
`);
}
