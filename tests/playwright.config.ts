import { defineConfig } from '@playwright/test';
import path from 'path';

export default defineConfig({
  testDir: './e2e',
  timeout: 120000, // 2 minutes per test (Electron can be slow to start)
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Run tests sequentially for Electron
  reporter: [
    ['list'],
    ['html', { open: 'never' }],
  ],
  use: {
    trace: 'on-first-retry',
    video: 'on-first-retry',
  },
  projects: [
    {
      name: 'electron',
      testMatch: '**/*.spec.ts',
    },
  ],
  // Global setup to ensure Electron app is built before tests
  globalSetup: path.join(__dirname, 'global-setup.ts'),
});
