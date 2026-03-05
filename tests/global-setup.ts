import { execSync } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

export default function globalSetup() {
  const electronDir = path.resolve(__dirname, '..', 'electron');
  const nodeModules = path.join(electronDir, 'node_modules');

  if (!fs.existsSync(nodeModules)) {
    console.log('Installing Electron dependencies...');
    execSync('npm install', { cwd: electronDir, stdio: 'inherit' });
  }
}
