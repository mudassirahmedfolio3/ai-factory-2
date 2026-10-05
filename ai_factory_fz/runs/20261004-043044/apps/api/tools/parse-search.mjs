import fs from 'fs';
import path from 'path';
import os from 'os';

const t = fs.readFileSync(path.join(os.tmpdir(), 'stanpro-search.html'), 'utf8');
const media = [...new Set([...t.matchAll(/media\.nl\?[^"'&\s]+/g)].map((m) => m[0]))];
console.log('media count', media.length);
media.slice(0, 10).forEach((u) => console.log(u));

const productCards = [...t.matchAll(/href="(\/[^"]+)"[^>]*>[\s\S]*?View product/gi)];
console.log('product hrefs', productCards.length);

const netsuite = [
  ...new Set(
    [...t.matchAll(/https:\/\/628731-sb2\.app\.netsuite\.com[^"'\\s]+/g)].map(
      (m) => m[0].replace(/&amp;/g, '&'),
    ),
  ),
];
console.log('netsuite urls', netsuite.length);
netsuite.slice(0, 5).forEach((u) => console.log(u));
