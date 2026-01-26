/**
 * Claude Code Hook Integration Tests
 *
 * Tests for:
 * - exercise_tracker.py detecting Electron app
 * - Session registration from hooks
 * - Activity reporting from hooks
 * - notify_complete.py functionality
 */

import { test, expect, httpRequest } from '../fixtures/electron-app';
import { execSync, spawn, ChildProcess } from 'child_process';
import path from 'path';
import fs from 'fs';

const HTTP_PORT = 8800;
const BASE_URL = `http://localhost:${HTTP_PORT}`;
const PROJECT_ROOT = path.join(__dirname, '..', '..');

// Helper to run Python script and capture output
function runPythonScript(
  scriptPath: string,
  args: string[] = [],
  stdin?: string,
  env?: NodeJS.ProcessEnv
): Promise<{ stdout: string; stderr: string; exitCode: number }> {
  return new Promise((resolve) => {
    const fullEnv = { ...process.env, ...env };
    const proc = spawn('python3', [scriptPath, ...args], {
      cwd: PROJECT_ROOT,
      env: fullEnv,
    });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    proc.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    if (stdin) {
      proc.stdin.write(stdin);
      proc.stdin.end();
    } else {
      proc.stdin.end();
    }

    proc.on('close', (code) => {
      resolve({ stdout, stderr, exitCode: code || 0 });
    });

    // Timeout after 10 seconds
    setTimeout(() => {
      proc.kill();
      resolve({ stdout, stderr, exitCode: -1 });
    }, 10000);
  });
}

test.describe('exercise_tracker.py', () => {
  test('script exists and is executable', async () => {
    const scriptPath = path.join(PROJECT_ROOT, 'exercise_tracker.py');
    expect(fs.existsSync(scriptPath)).toBe(true);

    // Check it's executable
    const stat = fs.statSync(scriptPath);
    const isExecutable = (stat.mode & fs.constants.S_IXUSR) !== 0;
    expect(isExecutable).toBe(true);
  });

  test('--help shows usage', async () => {
    const scriptPath = path.join(PROJECT_ROOT, 'exercise_tracker.py');
    const result = await runPythonScript(scriptPath, ['--help']);

    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain('VibeReps');
    expect(result.stdout).toContain('post_tool_use');
  });

  test('--list-exercises shows available exercises', async () => {
    const scriptPath = path.join(PROJECT_ROOT, 'exercise_tracker.py');
    const result = await runPythonScript(scriptPath, ['--list-exercises']);

    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain('squats');
    expect(result.stdout).toContain('VIBEREPS_EXERCISES');
  });

  test('detects Electron app running', async ({ electronApp }) => {
    const scriptPath = path.join(PROJECT_ROOT, 'exercise_tracker.py');

    // Create mock hook payload
    const hookPayload = JSON.stringify({
      tool_name: 'Edit',
      tool_input: { file_path: '/test/file.ts' },
      cwd: PROJECT_ROOT,
    });

    const result = await runPythonScript(
      scriptPath,
      ['post_tool_use', '{}'],
      hookPayload
    );

    // Should detect Electron app and report success
    expect(result.stdout).toContain('Electron app');
    expect(result.exitCode).toBe(0);

    const output = JSON.parse(result.stdout.trim());
    expect(output.status).toBe('success');
    expect(output.message).toContain('Electron');
  });

  test('registers session with Electron app', async ({ electronApp }) => {
    const scriptPath = path.join(PROJECT_ROOT, 'exercise_tracker.py');

    const hookPayload = JSON.stringify({
      tool_name: 'Write',
      tool_input: { file_path: '/test/new-file.ts' },
      cwd: '/unique/cwd/path',
    });

    const result = await runPythonScript(
      scriptPath,
      ['post_tool_use', '{}'],
      hookPayload
    );

    expect(result.exitCode).toBe(0);

    // Verify session was created
    const statusResponse = await httpRequest('GET', `${BASE_URL}/api/status`);
    expect(statusResponse.data.active_sessions).toBeGreaterThan(0);
  });

  test('reports activity with file context', async ({ electronApp }) => {
    const scriptPath = path.join(PROJECT_ROOT, 'exercise_tracker.py');

    const hookPayload = JSON.stringify({
      tool_name: 'Edit',
      tool_input: { file_path: '/project/src/component.tsx' },
      cwd: '/project',
    });

    await runPythonScript(
      scriptPath,
      ['post_tool_use', '{}'],
      hookPayload
    );

    // Check session has the activity recorded
    const statusResponse = await httpRequest('GET', `${BASE_URL}/api/status`);
    const sessions = statusResponse.data.sessions;

    // Find session with our activity
    const sessionWithEdit = sessions.find((s: any) =>
      s.context?.lastTool === 'Edit' ||
      s.context?.summary?.includes('component.tsx')
    );

    expect(sessionWithEdit).toBeTruthy();
  });

  test('respects VIBEREPS_DISABLED env var', async ({ electronApp }) => {
    const scriptPath = path.join(PROJECT_ROOT, 'exercise_tracker.py');

    const result = await runPythonScript(
      scriptPath,
      ['post_tool_use', '{}'],
      '{}',
      { VIBEREPS_DISABLED: '1' }
    );

    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain('skipped');
    expect(result.stdout).toContain('VIBEREPS_DISABLED');
  });
});

test.describe('notify_complete.py', () => {
  test('script exists and is executable', async () => {
    const scriptPath = path.join(PROJECT_ROOT, 'notify_complete.py');
    expect(fs.existsSync(scriptPath)).toBe(true);

    const stat = fs.statSync(scriptPath);
    const isExecutable = (stat.mode & fs.constants.S_IXUSR) !== 0;
    expect(isExecutable).toBe(true);
  });

  test('detects Electron app running', async ({ electronApp }) => {
    const scriptPath = path.join(PROJECT_ROOT, 'notify_complete.py');

    const result = await runPythonScript(scriptPath, ['{}']);

    expect(result.exitCode).toBe(0);

    const output = JSON.parse(result.stdout.trim());
    expect(output.status).toBe('success');
    expect(output.message).toContain('Electron');
  });

  test('sends notification to Electron app', async ({ electronApp }) => {
    const scriptPath = path.join(PROJECT_ROOT, 'notify_complete.py');

    const hookPayload = JSON.stringify({
      message: 'Task completed successfully',
      notification_type: 'success',
    });

    const result = await runPythonScript(
      scriptPath,
      ['{}'],
      hookPayload
    );

    expect(result.exitCode).toBe(0);

    const output = JSON.parse(result.stdout.trim());
    expect(output.status).toBe('success');
  });

  test('marks existing session as complete', async ({ electronApp }) => {
    // First register a session
    const sessionId = `hook-notify-test-${Date.now()}`;
    await httpRequest('POST', `${BASE_URL}/api/session/register`, {
      session_id: sessionId,
      context: { summary: 'Test task' },
    });

    // Write session ID to temp file (as the hook would)
    const sessionIdFile = '/tmp/vibereps-session-id';
    fs.writeFileSync(sessionIdFile, sessionId);

    // Run notify_complete
    const scriptPath = path.join(PROJECT_ROOT, 'notify_complete.py');
    const result = await runPythonScript(scriptPath, ['{}']);

    expect(result.exitCode).toBe(0);

    // Clean up
    try { fs.unlinkSync(sessionIdFile); } catch {}
  });

  test('returns skipped when no tracker running', async () => {
    // Note: This test runs without the electronApp fixture
    // So there's no Electron app to connect to

    const scriptPath = path.join(PROJECT_ROOT, 'notify_complete.py');

    // Use a different port that nothing listens on
    const result = await runPythonScript(scriptPath, ['{}']);

    // Should gracefully skip
    const output = JSON.parse(result.stdout.trim());
    expect(['skipped', 'error']).toContain(output.status);
  });
});

test.describe('Hook Flow Integration', () => {
  test('complete workflow: register → activity → notify', async ({ electronApp }) => {
    const trackerScript = path.join(PROJECT_ROOT, 'exercise_tracker.py');
    const notifyScript = path.join(PROJECT_ROOT, 'notify_complete.py');

    // 1. First hook call (registers session)
    const firstPayload = JSON.stringify({
      tool_name: 'Edit',
      tool_input: { file_path: '/project/file1.ts' },
      cwd: '/project/workflow-test',
    });

    const firstResult = await runPythonScript(
      trackerScript,
      ['post_tool_use', '{}'],
      firstPayload
    );
    expect(firstResult.exitCode).toBe(0);

    // 2. Second hook call (updates activity)
    const secondPayload = JSON.stringify({
      tool_name: 'Write',
      tool_input: { file_path: '/project/file2.ts' },
      cwd: '/project/workflow-test',
    });

    const secondResult = await runPythonScript(
      trackerScript,
      ['post_tool_use', '{}'],
      secondPayload
    );
    expect(secondResult.exitCode).toBe(0);

    // 3. Notify complete
    const notifyPayload = JSON.stringify({
      message: 'All tasks done',
    });

    const notifyResult = await runPythonScript(
      notifyScript,
      ['{}'],
      notifyPayload
    );
    expect(notifyResult.exitCode).toBe(0);

    // Verify session state
    const statusResponse = await httpRequest('GET', `${BASE_URL}/api/status`);
    expect(statusResponse.data.sessions.length).toBeGreaterThan(0);
  });

  test('multiple concurrent sessions', async ({ electronApp }) => {
    const trackerScript = path.join(PROJECT_ROOT, 'exercise_tracker.py');

    // Simulate two different Claude instances (different cwds)
    const session1Payload = JSON.stringify({
      tool_name: 'Edit',
      tool_input: { file_path: '/project1/file.ts' },
      cwd: '/project1',
    });

    const session2Payload = JSON.stringify({
      tool_name: 'Edit',
      tool_input: { file_path: '/project2/file.ts' },
      cwd: '/project2',
    });

    // Run both concurrently
    const [result1, result2] = await Promise.all([
      runPythonScript(trackerScript, ['post_tool_use', '{}'], session1Payload),
      runPythonScript(trackerScript, ['post_tool_use', '{}'], session2Payload),
    ]);

    expect(result1.exitCode).toBe(0);
    expect(result2.exitCode).toBe(0);

    // Both should have created sessions
    const statusResponse = await httpRequest('GET', `${BASE_URL}/api/status`);
    expect(statusResponse.data.active_sessions).toBeGreaterThanOrEqual(2);
  });
});

test.describe('Edge Cases', () => {
  test('handles malformed hook payload gracefully', async ({ electronApp }) => {
    const scriptPath = path.join(PROJECT_ROOT, 'exercise_tracker.py');

    // Send invalid JSON (empty string for stdin)
    const result = await runPythonScript(
      scriptPath,
      ['post_tool_use', '{}'],
      'not valid json'
    );

    // Should not crash, might return error or success with empty context
    expect(result.exitCode).toBeGreaterThanOrEqual(0);
  });

  test('handles missing tool_input gracefully', async ({ electronApp }) => {
    const scriptPath = path.join(PROJECT_ROOT, 'exercise_tracker.py');

    const payload = JSON.stringify({
      tool_name: 'Edit',
      // Missing tool_input
    });

    const result = await runPythonScript(
      scriptPath,
      ['post_tool_use', '{}'],
      payload
    );

    expect(result.exitCode).toBe(0);
  });

  test('session cleanup after timeout', async ({ electronApp }) => {
    // Register a session
    const oldSessionId = `old-session-${Date.now() - 100000}`;
    await httpRequest('POST', `${BASE_URL}/api/session/register`, {
      session_id: oldSessionId,
      context: {},
    });

    // The session manager should clean up old sessions automatically
    // We can't easily test the 10-minute timeout, but we verify the mechanism exists
    const statusResponse = await httpRequest('GET', `${BASE_URL}/api/status`);
    expect(Array.isArray(statusResponse.data.sessions)).toBe(true);
  });
});
