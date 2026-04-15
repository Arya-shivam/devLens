#!/usr/bin/env node
const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const ext = os.platform() === 'win32' ? '.exe' : '';
const binPath = path.join(__dirname, 'bin', `dlens${ext}`);

if (!fs.existsSync(binPath)) {
  console.error(`Error: devLens executable not found at ${binPath}`);
  console.error('Please try reinstalling the package: npm install -g devlens');
  process.exit(1);
}

const args = process.argv.slice(2);

const result = spawnSync(binPath, args, {
  stdio: 'inherit',
  windowsHide: true
});

if (result.error) {
  console.error(`Failed to execute devLens: ${result.error.message}`);
  process.exit(1);
}

process.exit(result.status ?? 0);
