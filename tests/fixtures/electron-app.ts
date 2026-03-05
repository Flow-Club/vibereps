import { test as base } from '@playwright/test';
import { ChildProcess, spawn } from 'child_process';
import * as path from 'path';
import * as http from 'http';

const ELECTRON_PORT = 8800;
const STARTUP_TIMEOUT = 30_000;
const POLL_INTERVAL = 500;

async function waitForServer(port: number, timeout: number): Promise<void> {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    try {
      await new Promise<void>((resolve, reject) => {
        const req = http.get(`http://localhost:${port}/api/status`, (res) => {
          res.resume();
          resolve();
        });
        req.on('error', reject);
        req.setTimeout(1000, () => { req.destroy(); reject(new Error('timeout')); });
      });
      return;
    } catch {
      await new Promise((r) => setTimeout(r, POLL_INTERVAL));
    }
  }
  throw new Error(`Server on port ${port} did not start within ${timeout}ms`);
}

export type ElectronFixtures = {
  electronProcess: ChildProcess;
  electronBaseUrl: string;
};

export const test = base.extend<ElectronFixtures>({
  electronProcess: async ({}, use) => {
    const electronDir = path.resolve(__dirname, '..', '..', 'electron');
    const electronBin = path.join(electronDir, 'node_modules', '.bin', 'electron');

    const proc = spawn(electronBin, ['.'], {
      cwd: electronDir,
      env: { ...process.env, NODE_ENV: 'test' },
      stdio: 'pipe',
    });

    proc.stdout?.on('data', (data) => {
      if (process.env.DEBUG) console.log(`[electron] ${data}`);
    });
    proc.stderr?.on('data', (data) => {
      if (process.env.DEBUG) console.error(`[electron] ${data}`);
    });

    await waitForServer(ELECTRON_PORT, STARTUP_TIMEOUT);

    await use(proc);

    proc.kill('SIGTERM');
    // Wait for graceful shutdown
    await new Promise<void>((resolve) => {
      proc.on('exit', () => resolve());
      setTimeout(() => { proc.kill('SIGKILL'); resolve(); }, 5000);
    });
  },

  electronBaseUrl: async ({}, use) => {
    await use(`http://localhost:${ELECTRON_PORT}`);
  },
});

export { expect } from '@playwright/test';
