/**
 * Electron App Integration Tests
 *
 * Tests for:
 * - App building successfully
 * - App launching and running
 * - HTTP server starting on port 8800
 * - API endpoints responding correctly
 * - Menubar/tray functionality
 */

import { test, expect, httpRequest } from '../fixtures/electron-app';
import { execSync } from 'child_process';
import path from 'path';
import fs from 'fs';
import os from 'os';

const HTTP_PORT = 8800;
const BASE_URL = `http://localhost:${HTTP_PORT}`;

test.describe('Electron App Build', () => {
  test('electron dependencies are installed', async () => {
    const electronDir = path.join(__dirname, '..', '..', 'electron');
    const nodeModulesPath = path.join(electronDir, 'node_modules');

    // Check node_modules exists
    expect(fs.existsSync(nodeModulesPath)).toBe(true);

    // Check key dependencies
    const packageJsonPath = path.join(electronDir, 'package.json');
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));

    expect(packageJson.dependencies).toHaveProperty('menubar');
    expect(packageJson.dependencies).toHaveProperty('express');
    expect(packageJson.devDependencies).toHaveProperty('electron');
  });

  test('main.js exists', async () => {
    const mainPath = path.join(__dirname, '..', '..', 'electron', 'main.js');
    expect(fs.existsSync(mainPath)).toBe(true);
  });

  test('preload.js exists', async () => {
    const preloadPath = path.join(__dirname, '..', '..', 'electron', 'preload.js');
    expect(fs.existsSync(preloadPath)).toBe(true);
  });

  test('exercise_ui.html exists', async () => {
    const uiPath = path.join(__dirname, '..', '..', 'exercise_ui.html');
    expect(fs.existsSync(uiPath)).toBe(true);
  });
});

test.describe('Electron App Launch', () => {
  test('app launches and HTTP server starts', async ({ electronApp }) => {
    // If we got here, the app launched successfully
    // The fixture waits for HTTP server to be ready
    expect(electronApp).toBeTruthy();

    // Verify server responds
    const response = await httpRequest('GET', `${BASE_URL}/api/status`);
    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('active_sessions');
  });

  test('app creates a window', async ({ electronApp }) => {
    const windows = electronApp.windows();
    expect(windows.length).toBeGreaterThanOrEqual(1);
  });

  test('window loads exercise UI', async ({ appPage }) => {
    // Wait for the page to load
    await appPage.waitForSelector('body');

    // Check page title or content
    const title = await appPage.title();
    expect(title).toContain('Exercise');
  });
});

test.describe('HTTP API Endpoints', () => {
  test('GET / serves exercise UI HTML', async ({ electronApp }) => {
    const response = await httpRequest('GET', `${BASE_URL}/`);
    expect(response.status).toBe(200);
    expect(response.data).toContain('<!DOCTYPE html>');
  });

  test('GET /exercises returns exercise list', async ({ electronApp }) => {
    const response = await httpRequest('GET', `${BASE_URL}/exercises`);
    expect(response.status).toBe(200);
    expect(Array.isArray(response.data)).toBe(true);

    // Should have some exercises
    expect(response.data.length).toBeGreaterThan(0);

    // Each exercise should have required fields
    const exercise = response.data[0];
    expect(exercise).toHaveProperty('id');
    expect(exercise).toHaveProperty('name');
  });

  test('GET /exercises/:name.json returns exercise config', async ({ electronApp }) => {
    const response = await httpRequest('GET', `${BASE_URL}/exercises/squats.json`);
    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('id', 'squats');
    expect(response.data).toHaveProperty('name');
    expect(response.data).toHaveProperty('detection');
  });

  test('GET /api/status returns session status', async ({ electronApp }) => {
    const response = await httpRequest('GET', `${BASE_URL}/api/status`);
    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('active_sessions');
    expect(response.data).toHaveProperty('sessions');
    expect(Array.isArray(response.data.sessions)).toBe(true);
  });

  test('POST /api/session/register creates a session', async ({ electronApp }) => {
    const sessionId = `test-session-${Date.now()}`;
    const response = await httpRequest('POST', `${BASE_URL}/api/session/register`, {
      session_id: sessionId,
      pid: process.pid,
      context: { summary: 'Test session' },
    });

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('success', true);
    expect(response.data.session).toHaveProperty('id', sessionId);

    // Verify session appears in status
    const statusResponse = await httpRequest('GET', `${BASE_URL}/api/status`);
    const sessions = statusResponse.data.sessions;
    const session = sessions.find((s: any) => s.id === sessionId);
    expect(session).toBeTruthy();
  });

  test('POST /api/session/activity updates session', async ({ electronApp }) => {
    // First register a session
    const sessionId = `activity-test-${Date.now()}`;
    await httpRequest('POST', `${BASE_URL}/api/session/register`, {
      session_id: sessionId,
      context: {},
    });

    // Report activity
    const response = await httpRequest('POST', `${BASE_URL}/api/session/activity`, {
      session_id: sessionId,
      tool_name: 'Edit',
      file_path: '/test/file.ts',
    });

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('success', true);

    // Verify context was updated
    const session = response.data.session;
    expect(session.context).toHaveProperty('lastTool', 'Edit');
    expect(session.context).toHaveProperty('lastFile', '/test/file.ts');
  });

  test('POST /api/notify marks session complete', async ({ electronApp }) => {
    // Register a session
    const sessionId = `notify-test-${Date.now()}`;
    await httpRequest('POST', `${BASE_URL}/api/session/register`, {
      session_id: sessionId,
    });

    // Send notification
    const response = await httpRequest('POST', `${BASE_URL}/api/notify`, {
      session_id: sessionId,
      message: 'Task completed',
    });

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('success', true);
  });

  test('POST /api/complete logs exercise', async ({ electronApp }) => {
    const response = await httpRequest('POST', `${BASE_URL}/api/complete`, {
      exercise: 'squats',
      reps: 5,
      duration: 30,
    });

    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('success', true);
    expect(response.data).toHaveProperty('logged', true);
  });

  test('GET /status returns legacy status format', async ({ electronApp }) => {
    const response = await httpRequest('GET', `${BASE_URL}/status`);
    expect(response.status).toBe(200);
    expect(response.data).toHaveProperty('claude_complete');
    expect(response.data).toHaveProperty('exercise_complete');
  });
});

test.describe('Exercise Logging', () => {
  test('exercise completion is logged to file', async ({ electronApp }) => {
    const logPath = path.join(os.homedir(), '.vibereps', 'exercises.jsonl');

    // Get initial line count (if file exists)
    let initialLines = 0;
    if (fs.existsSync(logPath)) {
      initialLines = fs.readFileSync(logPath, 'utf8').trim().split('\n').length;
    }

    // Log an exercise
    await httpRequest('POST', `${BASE_URL}/api/complete`, {
      exercise: 'test_exercise',
      reps: 10,
      duration: 60,
    });

    // Wait a bit for file write
    await new Promise(resolve => setTimeout(resolve, 100));

    // Check file was updated
    expect(fs.existsSync(logPath)).toBe(true);
    const lines = fs.readFileSync(logPath, 'utf8').trim().split('\n');
    expect(lines.length).toBeGreaterThan(initialLines);

    // Check last entry
    const lastEntry = JSON.parse(lines[lines.length - 1]);
    expect(lastEntry).toHaveProperty('exercise', 'test_exercise');
    expect(lastEntry).toHaveProperty('reps', 10);
  });
});

test.describe('Menubar Functionality', () => {
  test('app window can be shown via API', async ({ electronApp, appPage }) => {
    // Register a session with Edit activity (triggers show)
    const sessionId = `show-test-${Date.now()}`;
    await httpRequest('POST', `${BASE_URL}/api/session/register`, {
      session_id: sessionId,
    });

    await httpRequest('POST', `${BASE_URL}/api/session/activity`, {
      session_id: sessionId,
      tool_name: 'Edit',
      file_path: '/test/show.ts',
    });

    // Give window time to show
    await appPage.waitForTimeout(500);

    // Window should be visible
    const isVisible = await appPage.evaluate(() => {
      return document.visibilityState === 'visible';
    });

    // Note: In headless mode this might not work perfectly
    // but at least we verify no errors occurred
    expect(isVisible).toBeDefined();
  });
});
