import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../..');
const manifestPath = path.join(
  repoRoot,
  'apps/api/prisma/data/catalog-image-manifest.json',
);

const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));

const outDirs = [
  path.join(repoRoot, 'app/assets/catalog/images'),
  path.join(repoRoot, 'apps/api/static/catalog/images'),
];

for (const dir of outDirs) {
  fs.mkdirSync(dir, { recursive: true });
}

async function downloadOne(entry) {
  const res = await fetch(entry.sourceUrl);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status} for ${entry.filename}`);
  }
  const buf = Buffer.from(await res.arrayBuffer());
  for (const dir of outDirs) {
    fs.writeFileSync(path.join(dir, entry.filename), buf);
  }
}

for (const entry of manifest.images) {
  process.stdout.write(`Downloading ${entry.filename}... `);
  await downloadOne(entry);
  console.log('ok');
}

console.log(`Wrote ${manifest.images.length} files to ${outDirs.join(' and ')}`);
