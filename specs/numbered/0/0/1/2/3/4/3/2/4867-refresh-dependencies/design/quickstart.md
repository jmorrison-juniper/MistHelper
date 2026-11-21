# Dependency Refresh Quickstart

## Prerequisites

- Python 3.15.2 is available.
- UV is available.
- npm is available.
- The branch worktree is clean.

## Root Python Refresh

```powershell
uv lock --upgrade
uv export --locked --no-hashes --no-emit-project --output-file requirements.txt
uv export --locked --no-hashes --no-emit-project --extra dev --output-file requirements-dev.txt
uv lock --check
```

## Ops Platform Refresh

```powershell
Set-Location mist-ops-platform
uv lock --upgrade
uv export --locked --no-hashes --no-emit-project --output-file requirements.txt
uv export --locked --no-hashes --no-emit-project --extra dev --output-file requirements-dev.txt
```

## Ops Portal Refresh

```powershell
Set-Location ops-portal
npx npm-check-updates -u
npm install --legacy-peer-deps
npm ci --legacy-peer-deps
npm run typecheck
npm run lint
npm test
npm audit --audit-level=high
```

## Verification

Run the root lint, type, test, security, and dependency guards.
Run the Mist Ops Platform pytest and Ruff gates.
Run the package parity and lock guards.
Do not commit a stale export or an unverified package major update.
