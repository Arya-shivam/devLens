const fs = require('fs');
const os = require('os');
const path = require('path');
const https = require('https');

const packageJson = require('./package.json');
const VERSION = 'v' + packageJson.version;
const REPO = 'Arya-shivam/devLens';

const binDir = path.join(__dirname, 'bin');
if (!fs.existsSync(binDir)) {
  fs.mkdirSync(binDir, { recursive: true });
}

function getAssetInfo() {
  const platform = os.platform();
  const arch = os.arch(); // Usually 'x64' or 'arm64'
  
  let osName = '';
  let ext = '';
  
  if (platform === 'win32') {
    osName = 'windows';
    ext = '.exe';
  } else if (platform === 'darwin') {
    osName = 'darwin';
  } else if (platform === 'linux') {
    osName = 'linux';
  } else {
    throw new Error(`Unsupported platform: ${platform}`);
  }

  // GitHub actions generally build on x86_64, which is x64 in Node.
  const assetName = `devlens-${osName}-amd64${ext}`;
  const binName = `dlens${ext}`;
  
  return { assetName, binName };
}

function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    https.get(url, (response) => {
      if (response.statusCode === 301 || response.statusCode === 302) {
        return downloadFile(response.headers.location, dest).then(resolve).catch(reject);
      }
      
      if (response.statusCode !== 200) {
        return reject(new Error(`Failed to download: ${response.statusCode} - ${response.statusMessage}`));
      }

      const file = fs.createWriteStream(dest);
      response.pipe(file);
      
      file.on('finish', () => {
        file.close();
        resolve();
      });
    }).on('error', (err) => {
      fs.unlink(dest, () => {});
      reject(err);
    });
  });
}

async function install() {
  try {
    const { assetName, binName } = getAssetInfo();
    const url = `https://github.com/${REPO}/releases/download/${VERSION}/${assetName}`;
    const dest = path.join(binDir, binName);
    
    console.log(`Downloading devLens from ${url}...`);
    await downloadFile(url, dest);
    
    // Make executable on unix
    if (os.platform() !== 'win32') {
      fs.chmodSync(dest, 0o755);
    }
    
    console.log('devLens installed successfully!');
  } catch (err) {
    console.error('Failed to install devLens automatically.');
    console.error(err.message);
    console.error('\nPlease install natively: pip install devlens-cli');
    process.exit(1);
  }
}

install();
