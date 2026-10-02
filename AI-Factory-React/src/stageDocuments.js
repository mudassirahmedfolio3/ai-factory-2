/** Stage → document paths produced by fz (and legacy) runs. */

/** Preferred docs for each UI stage index (0–10). */
export const STAGE_DOC_PRESETS = [
  {
    title: 'Product brief',
    paths: ['docs/product_brief.md', 'docs/clarifications.md'],
  },
  {
    title: 'Specification / PRD',
    paths: ['docs/prd.md', 'requirements/prd.md'],
  },
  {
    title: 'Architecture',
    paths: ['docs/architecture.md', 'docs/openapi.yaml', 'docs/schema.prisma'],
  },
  {
    title: 'Design system',
    paths: ['docs/design_system.md'],
  },
  {
    title: 'Delivery plan',
    paths: ['docs/backlog.md', 'docs/prd.md'],
  },
  {
    title: 'API contract',
    paths: ['docs/openapi.yaml', 'docs/architecture.md'],
  },
  {
    title: 'Design system',
    paths: ['docs/design_system.md', 'docs/openapi.yaml'],
  },
  {
    title: 'Release package',
    paths: [
      'docs/release_notes.md',
      'reports/release_round1.md',
      'releases/release_1_notes.md',
      'infra/README.md',
    ],
  },
  {
    title: 'QA report',
    paths: [], // filled from artifacts_index reports/qa*
    pathPrefixes: ['reports/qa'],
  },
  {
    title: 'Smoke results',
    paths: [],
    pathPrefixes: ['reports/', 'server/smoke'],
    pathIncludes: ['smoke'],
  },
  {
    title: 'Integration / handover',
    paths: [
      'docs/release_notes.md',
      'reports/release_round1.md',
      'releases/release_1_notes.md',
    ],
  },
];

/**
 * Build ordered candidate paths for a UI stage from presets + live index.
 * @param {number} stageIndex
 * @param {Array<{path?: string}>} artifactsIndex
 */
export function stageDocumentCandidates(stageIndex, artifactsIndex = []) {
  const preset = STAGE_DOC_PRESETS[stageIndex] || STAGE_DOC_PRESETS[0];
  const indexPaths = (artifactsIndex || []).map((a) => a.path).filter(Boolean);
  const fromIndex = [];

  if (preset.pathPrefixes?.length || preset.pathIncludes?.length) {
    for (const p of indexPaths) {
      const lower = p.toLowerCase();
      const prefixOk =
        !preset.pathPrefixes?.length ||
        preset.pathPrefixes.some((pre) => lower.startsWith(pre.toLowerCase()));
      const includeOk =
        !preset.pathIncludes?.length ||
        preset.pathIncludes.some((part) => lower.includes(part.toLowerCase()));
      if (prefixOk && includeOk && (p.endsWith('.md') || p.endsWith('.yaml') || p.endsWith('.yml'))) {
        fromIndex.push(p);
      }
    }
  }

  // Prefer preset paths that exist in the index, then remaining presets, then index hits.
  const preferred = [];
  const seen = new Set();
  for (const p of preset.paths || []) {
    if (indexPaths.includes(p) && !seen.has(p)) {
      preferred.push(p);
      seen.add(p);
    }
  }
  for (const p of preset.paths || []) {
    if (!seen.has(p)) {
      preferred.push(p);
      seen.add(p);
    }
  }
  for (const p of fromIndex) {
    if (!seen.has(p)) {
      preferred.push(p);
      seen.add(p);
    }
  }

  // Early stages: if nothing else, surface whatever docs already exist.
  if (!preferred.length && stageIndex <= 1) {
    for (const p of indexPaths) {
      if (p.startsWith('docs/') && (p.endsWith('.md') || p.endsWith('.yaml'))) {
        preferred.push(p);
      }
    }
  }

  return { title: preset.title, paths: preferred };
}
