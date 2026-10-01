export const GATE_HOLD = 48;

export const gates = [
  { index: 1, kind: 'spec', label: 'Review specification' },
  { index: 3, kind: 'design', label: 'Review mockups' },
  { index: 7, kind: 'deploy', label: 'Review build' },
  { index: 9, kind: 'smoke', label: 'Review smoke tests' },
];

export const gateIndexes = gates.map((gate) => gate.index);

export const sourceFiles = [
  {
    path: 'nova/package.json',
    code: `{
  "name": "nova",
  "private": true,
  "version": "1.0.0",
  "scripts": { "start": "node src/app.js" }
}
`,
  },
  {
    path: 'nova/src/app.js',
    code: `import { router } from './api.js';

const port = process.env.PORT || 8080;
router.listen(port, () => {
  console.log(\`NOVA listening on \${port}\`);
});
`,
  },
  {
    path: 'nova/src/api.js',
    code: `import { requireUser } from './auth.js';

export const items = [];

export function listItems(request) {
  const user = requireUser(request);
  return items.filter((item) => item.owner === user.id);
}

export function createItem(request, name) {
  const user = requireUser(request);
  const item = { id: String(items.length + 1), name, owner: user.id };
  items.push(item);
  return item;
}
`,
  },
  {
    path: 'nova/src/auth.js',
    code: `export function requireUser(request) {
  const header = request.headers.authorization || '';
  const token = header.replace('Bearer ', '');
  if (!token) throw new Error('Sign-in required');
  return { id: 'demo-user', name: 'Demo member' };
}
`,
  },
  {
    path: 'nova/README.md',
    code: `# NOVA

Workspace app produced by AI Factory.

- \`src/app.js\` starts the service
- \`src/auth.js\` checks the session
- \`src/api.js\` lists and creates items
`,
  },
];

export const smokeFeatures = [
  {
    feature: 'Startup',
    tests: [
      { name: 'Application boots', result: 'Pass' },
      { name: 'Health check responds', result: 'Pass' },
    ],
  },
  {
    feature: 'Sign-in',
    tests: [
      { name: 'Valid member can sign in', result: 'Pass' },
      { name: 'Wrong password is rejected', result: 'Pass' },
    ],
  },
  {
    feature: 'Core path',
    tests: [
      { name: 'Create an item', result: 'Pass' },
      { name: 'Item appears in the list', result: 'Pass' },
      { name: 'Save and unsave an item', result: 'Pass' },
    ],
  },
  {
    feature: 'Critical APIs',
    tests: [
      { name: 'Auth endpoint', result: 'Pass' },
      { name: 'Items endpoint', result: 'Pass' },
    ],
  },
];

export function specDocument(project) {
  const brief = project?.text?.trim() || 'A workspace where people organize their work in one place.';
  return `# NOVA product specification

## Customer brief
${brief}

## Users
- Member, who creates and saves items
- Guest, who can only see the sign-in screen

## Stories
1. As a member, I can sign in and land in my workspace.
2. As a member, I can create an item and see it in my list.
3. As a member, I can save an item and find it later.

## Acceptance criteria
- Sign-in rejects an unknown password and explains why.
- A new item shows up in the list without a reload.
- Saved items stay available after the member returns.

## Rules
- Scope is the workspace, the item list and saved items.
- Billing, admin roles and public sharing are out of scope.
`;
}

export function smokeReport() {
  const lines = ['# NOVA smoke report', ''];
  for (const group of smokeFeatures) {
    lines.push(`## ${group.feature}`, '');
    for (const test of group.tests) lines.push(`- ${test.result}: ${test.name}`);
    lines.push('');
  }
  return lines.join('\n');
}

export const mockups = [
  { id: 'home', name: 'Home' },
  { id: 'signin', name: 'Sign in' },
  { id: 'items', name: 'Items' },
  { id: 'profile', name: 'Profile' },
];
