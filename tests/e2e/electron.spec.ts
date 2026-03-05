import { test, expect } from '../fixtures/electron-app';

test.describe('Electron App', () => {
  test('HTTP server responds on port 8800', async ({ electronProcess, electronBaseUrl }) => {
    const response = await fetch(`${electronBaseUrl}/api/status`);
    expect(response.ok).toBeTruthy();
    const data = await response.json();
    expect(data).toHaveProperty('status');
  });

  test('GET /exercises returns exercise list', async ({ electronProcess, electronBaseUrl }) => {
    const response = await fetch(`${electronBaseUrl}/exercises`);
    expect(response.ok).toBeTruthy();
    const data = await response.json();
    expect(Array.isArray(data)).toBeTruthy();
    expect(data.length).toBeGreaterThan(0);
    // Each exercise should have an id
    expect(data[0]).toHaveProperty('id');
  });

  test('POST /api/session/register creates a session', async ({ electronProcess, electronBaseUrl }) => {
    const response = await fetch(`${electronBaseUrl}/api/session/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: 'test-session-001',
        cwd: '/tmp/test',
      }),
    });
    expect(response.ok).toBeTruthy();
    const data = await response.json();
    expect(data).toHaveProperty('success', true);
  });

  test('GET /api/status reflects registered session', async ({ electronProcess, electronBaseUrl }) => {
    // Register first
    await fetch(`${electronBaseUrl}/api/session/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: 'test-session-002', cwd: '/tmp/test' }),
    });

    const response = await fetch(`${electronBaseUrl}/api/status`);
    const data = await response.json();
    expect(data.active_sessions).toBeGreaterThanOrEqual(1);
  });

  test('POST /api/notify returns notification_shown field', async ({ electronProcess, electronBaseUrl }) => {
    const response = await fetch(`${electronBaseUrl}/api/notify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: 'Test notification' }),
    });
    expect(response.ok).toBeTruthy();
    const data = await response.json();
    expect(data).toHaveProperty('success', true);
    expect(data).toHaveProperty('notification_shown');
  });
});
