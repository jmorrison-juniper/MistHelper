# Verify the skill lock

Each entry in `skills-lock.json` pins a full upstream commit in `ref`. The
`computedHash` value uses SHA-256 over every file in that skill folder. It does
not hash only `SKILL.md`.

Sort each relative file path with JavaScript `localeCompare`. For each path,
hash the path text followed by the file bytes. Add no separator. The paths are
relative to the skill folder.

Keep the Simplified Technical English precedence rule in `AGENTS.md`. That
tracked rule is canonical for this repository. Do not add the personal skill
copy to the project lock.

Run this check from the repository root. It reads each pinned revision from the
lock and compares every folder hash with `computedHash`. It requires GitHub CLI,
Node.js, and access to the public upstream repository.

```sh
node <<'NODE'
const { execFileSync } = require('node:child_process');
const { createHash } = require('node:crypto');
const fs = require('node:fs');

const lock = JSON.parse(fs.readFileSync('skills-lock.json', 'utf8'));
const entries = Object.entries(lock.skills);
const source = entries[0][1].source;
const ref = entries[0][1].ref;
const tree = JSON.parse(
  execFileSync('gh', ['api', `repos/${source}/git/trees/${ref}?recursive=1`], {
    encoding: 'utf8',
  }),
);
let failed = false;

for (const [name, entry] of entries) {
  if (entry.source !== source || entry.ref !== ref) {
    throw new Error(`${name}: source or ref differs from the first entry`);
  }
  const folder = entry.skillPath.slice(0, entry.skillPath.lastIndexOf('/'));
  const prefix = `${folder}/`;
  const paths = tree.tree
    .filter((file) => file.type === 'blob' && file.path.startsWith(prefix))
    .map((file) => file.path.slice(prefix.length))
    .sort((left, right) => left.localeCompare(right));
  const hash = createHash('sha256');
  for (const path of paths) {
    const fullPath = `${folder}/${path}`;
    const encoded = execFileSync(
      'gh',
      ['api', `repos/${source}/contents/${fullPath}?ref=${ref}`, '--jq', '.content'],
      { encoding: 'utf8' },
    );
    hash.update(path);
    hash.update(Buffer.from(encoded, 'base64'));
  }
  const actual = hash.digest('hex');
  console.log(`${name}: ${actual}`);
  if (actual !== entry.computedHash) failed = true;
}

if (failed) process.exitCode = 1;
NODE
```
