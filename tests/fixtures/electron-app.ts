import { test as base, _electron as electron, ElectronApplication, Page } from '@playwright/test';
import path from 'path';
import { spawn, ChildProcess } from 'child_process';
import http from 'http';

// Extend Playwright test with Electron app fixture
export interface ElectronFixtures {
  electronApp: ElectronApplication;
  appPage: Page;
  httpPort: number;
}

// Helper to wait for HTTP server to be ready
async function waitForHttpServer(port: number, timeout = 30000): Promise<boolean> {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    try {
      await new Promise<void>((resolve, reject) => {
        const req = http.get(`http://localhost:${port}/api/status`, (res) => {
          if (res.statusCode === 200) resolve();
          else reject(new Error(`Status ${res.statusCode}`));
        });
        req.on('error', reject);
        req.setTimeout(1000, () => {
          req.destroy();
          reject(new Error('Timeout'));
        });
      });
      return true;
    } catch {
      await new Promise(r => setTimeout(r, 500));
    }
  }
  return false;
}

// Helper to make HTTP requests
export async function httpRequest(
  method: string,
  url: string,
  body?: object
): Promise<{ status: number; data: any }> {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname + urlObj.search,
      method,
      headers: body ? { 'Content-Type': 'application/json' } : {},
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode || 0, data: data ? JSON.parse(data) : null });
        } catch {
          resolve({ status: res.statusCode || 0, data });
        }
      });
    });

    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

export const test = base.extend<ElectronFixtures>({
  httpPort: 8800, // VibeReps Electron app uses fixed port 8800

  electronApp: async ({}, use) => {
    const electronPath = path.join(__dirname, '..', '..', 'electron');
    const mainPath = path.join(electronPath, 'main.js');

    // Launch Electron app
    const app = await electron.launch({
      args: [mainPath],
      cwd: electronPath,
      env: {
        ...process.env,
        NODE_ENV: 'test',
      },
    });

    // Wait for HTTP server to be ready
    const serverReady = await waitForHttpServer(8800);
    if (!serverReady) {
      await app.close();
      throw new Error('Electron HTTP server did not start within timeout');
    }

    await use(app);

    // Cleanup
    await app.close();
  },

  appPage: async ({ electronApp }, use) => {
    // Get the first window (main window)
    const page = await electronApp.firstWindow();

    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');

    await use(page);
  },
});

export { expect } from '@playwright/test';
