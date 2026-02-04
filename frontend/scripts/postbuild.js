const fs = require('fs');
const path = require('path');

// Copy static files to standalone directory
const copyRecursive = (src, dest) => {
  const exists = fs.existsSync(src);
  const stats = exists && fs.statSync(src);
  const isDirectory = exists && stats.isDirectory();

  if (isDirectory) {
    if (!fs.existsSync(dest)) {
      fs.mkdirSync(dest, { recursive: true });
    }
    fs.readdirSync(src).forEach((childItemName) => {
      copyRecursive(
        path.join(src, childItemName),
        path.join(dest, childItemName)
      );
    });
  } else {
    fs.copyFileSync(src, dest);
  }
};

console.log('Copying static files to standalone directory...');

// Copy .next/static to .next/standalone/.next/static
const staticSrc = path.join(process.cwd(), '.next', 'static');
const staticDest = path.join(process.cwd(), '.next', 'standalone', '.next', 'static');

if (fs.existsSync(staticSrc)) {
  copyRecursive(staticSrc, staticDest);
  console.log('✓ Copied .next/static');
}

// Copy public to .next/standalone/public
const publicSrc = path.join(process.cwd(), 'public');
const publicDest = path.join(process.cwd(), '.next', 'standalone', 'public');

if (fs.existsSync(publicSrc)) {
  copyRecursive(publicSrc, publicDest);
  console.log('✓ Copied public');
}

console.log('✓ Standalone build ready!');
