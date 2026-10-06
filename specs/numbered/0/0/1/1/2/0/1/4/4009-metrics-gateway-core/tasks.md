---

description: "Implementation tasks for the metrics gateway core package"
---

# Tasks: Metrics Gateway Core Package

**Input**: Routed design documents from `specs/numbered/0/0/1/1/2/0/1/4/4009-metrics-gateway-core/`

## Phase 1: Package Move

- [X] T001 Move `cache.py`, `catalog.py`, `collector.py`, and `samples.py` with `git mv`.
- [X] T002 Add `core/__init__.py` and preserve the root package exports.
- [X] T003 Update all active canonical imports and logger assertions.

## Phase 2: Guard and Reference Updates

- [X] T004 Map the four old module paths in the public symbol guard.
- [X] T005 Assert five gateway children and four core children.
- [X] T006 Update MIB generator modules, contracts, active MIB references, documentation, and generated menu pages.

## Phase 3: Validation

- [ ] T007 Run focused metrics gateway and MIB tests.
- [ ] T008 Run structure, symbol, compile, lint, format, type, security, complexity, docstring, changelog, Markdown-link, menu, and post-commit test-quality checks.
- [ ] T009 Commit locally with `Closes #4009` and the Copilot co-author trailer.

## Scope Rules

- Do not edit `MistHelper.py`.
- Do not edit historical specifications.
- Do not add compatibility wrappers or aliases.
- Do not push, open a pull request, change issue state, run workflows, add auto-merge, or merge.
