import fs from 'fs';
import path from 'path';
import os from 'os';

const htmlPath = path.join(os.tmpdir(), 'stanpro.html');
const t = fs.readFileSync(htmlPath, 'utf8');
const patterns = [
  /https?:\/\/[^\s"'<>]+/gi,
  /\/media\/[^\s"'<>]+/gi,
  /itemimages[^\s"'<>]*/gi,
];
for (const re of patterns) {
  const hits = [...new Set([...t.matchAll(re)].map((m) => m[0]))];
  console.log('pattern', re, 'count', hits.length);
  hits.filter((h) => /img|image|media|\.png|\.jpg/i.test(h)).slice(0, 15).forEach((u) => console.log(' ', u));
}
