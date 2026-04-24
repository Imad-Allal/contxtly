#!/usr/bin/env bash
# Build the extension and package dist/ as a Chrome Web Store zip.
# Usage: ./package.zip.sh

set -euo pipefail

cd "$(dirname "$0")"

VERSION="$(node -p "require('./manifest.json').version")"
OUT="contxtly-v${VERSION}.zip"

echo "→ Building (prod)..."
npm run build

echo "→ Stripping 'key' from dist/manifest.json (not allowed on CWS)..."
node -e "
  const fs = require('fs');
  const p = 'dist/manifest.json';
  const m = JSON.parse(fs.readFileSync(p, 'utf8'));
  delete m.key;
  fs.writeFileSync(p, JSON.stringify(m, null, 2) + '\n');
"

echo "→ Cleaning previous bundle..."
rm -f "$OUT"

echo "→ Zipping dist/ → $OUT"
cd dist
zip -qr "../$OUT" .
cd ..

SIZE="$(du -h "$OUT" | cut -f1)"
COUNT="$(unzip -l "$OUT" | tail -1 | awk '{print $2}')"
echo "✓ $OUT  ($SIZE, $COUNT files)"
