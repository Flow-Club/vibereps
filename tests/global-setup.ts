import { execSync } from 'child_process';
import path from 'path';
import fs from 'fs';

async function globalSetup() {
  const electronDir = path.join(__dirname, '..', 'electron');
  const nodeModulesPath = path.join(electronDir, 'node_modules');

  console.log('Global setup: Checking Electron app dependencies...');

  // Install electron dependencies if not present
  if (!fs.existsSync(nodeModulesPath)) {
    console.log('Installing Electron app dependencies...');
    execSync('npm install', { cwd: electronDir, stdio: 'inherit' });
  }

  console.log('Global setup complete.');
}

export default globalSetup;
