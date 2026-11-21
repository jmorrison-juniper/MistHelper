# Dependency Refresh Research

## Decision 1: Refresh Root Python Packages

**Decision**: Use UV to upgrade the root lock, then export exact runtime and development requirement lists.

**Rationale**: UV resolves direct constraints and transitive dependencies with the selected Python 3.15 interpreter.
The exports remain compatible with pip-based CI and container builds.

**Alternatives considered**:

- Manual package edits add version drift and do not prove transitive resolution.
- A package-by-package pip install cannot recreate the complete lock.

## Decision 2: Refresh Ops Platform Packages

**Decision**: Resolve the platform package set with the project interpreter, then pin exact runtime and test packages in pip exports.

**Rationale**: The platform has no existing lock export.
An exact requirements.txt prevents a new install from selecting an incompatible package version.

**Alternatives considered**:

- Keep only lower bounds allows future drift and conflicts with the user request.
- Update pyproject ranges alone does not pin a clean environment.

## Decision 3: Refresh Ops Portal Packages

**Decision**: Refresh package.json and regenerate package-lock.json with npm.

**Rationale**: npm ci requires the manifest and lock to describe the same dependency graph.
The existing CI already checks audit, typecheck, lint, and tests.

**Alternatives considered**:

- Update only package-lock.json can leave package.json declarations stale.
- Skip major updates may leave known current major releases unused.

## Decision 4: Preserve Known Compatibility Constraints

**Decision**: Keep an upper or exact constraint when an existing comment names a Python 3.15 incompatibility.

**Rationale**: A stable application needs a compatibility guard before a package major or incompatible patch is accepted.

**Alternatives considered**:

- Accept every major release may introduce an API or build failure.
- Ignore a compatibility constraint would violate prior repository evidence.

## Decision 5: Coordinate PR 4806

**Decision**: Rebase PR 4806 onto current main, rerun checks, and merge it before the full refresh branch changes root lock files.

**Rationale**: PR 4806 overlaps pyproject.toml, uv.lock, and both requirement exports.
A serial merge avoids conflicting dependency edits.

**Alternatives considered**:

- Branch 4867 before PR 4806 causes a lock conflict.
- Closing PR 4806 would disable an existing update stream and is not necessary.
