import fs from 'fs';
import path from 'path';

const t = fs.readFileSync(path.join(process.cwd(), 'tools', 'stanpro-sample.html'), 'utf8');
const full = [...t.matchAll(/https:\/\/628731-sb2\.app\.netsuite\.com\/core\/media\/media\.nl\?[^"'\\]+/g)].map(
  (m) => m[0].replace(/&amp;/g, '&'),
);
console.log('count', full.length);
full.forEach((u) => console.log(u));
