import fs from 'fs';
import path from 'path';

const slugs = [
  'smart-series-item',
  'solar-street-light',
  'recessed-step-light-001-12w-black',
  'recessed-step-light-003-3w-black',
  'outdoor-step-light-004-3w-brushed-nickel',
  'wall-step-light-005-8w-black-name',
  'fll-flood-light',
  '200000000-223',
  'recessed-step-light-057-15w-matte-black',
  'path-light-017-20w-bronze',
  'deck-light-014-5w-matte-black',
  'stair-light-007-20w-silver',
];

async function mediaForSlug(slug) {
  const url = `https://stanpro2.folio3.site/${slug}`;
  const res = await fetch(url);
  const t = await res.text();
  const ids = [
    ...new Set([...t.matchAll(/media\.nl\?id=(\d+)/g)].map((m) => m[1])),
  ];
  const full = [
    ...new Set(
      [...t.matchAll(/https:\/\/628731-sb2\.app\.netsuite\.com\/core\/media\/media\.nl\?[^"'\\s]+/g)].map(
        (m) => m[0].replace(/&amp;/g, '&'),
      ),
    ),
  ];
  return { slug, url, ids, full };
}

const results = [];
for (const slug of slugs) {
  try {
    const row = await mediaForSlug(slug);
    results.push(row);
    console.log(slug, 'ids', row.ids.join(','));
  } catch (e) {
    console.log(slug, 'error', e.message);
  }
}

fs.writeFileSync(
  path.join(process.cwd(), 'tools', 'stanpro-media-sample.json'),
  JSON.stringify(results, null, 2),
);
