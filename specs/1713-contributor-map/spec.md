# Feature Specification: Contributor map for `MistHelper.py`

**Feature Branch**: `docs/1713-contributor-map`

**Created**: 2026-09-13

**Status**: Draft

**Input**: GitHub issue #1713 asks for a contributor orientation map for `MistHelper.py`.

## Problem

A new contributor can read the user guide and the agent guide.
Neither guide tells that contributor where each concern belongs in `MistHelper.py`.
The file changes often during the current refactor work.
A map that uses line numbers will become wrong quickly.

## Acceptance Criteria

1. Create `documentation/CONTRIBUTING-MistHelper.md`.
2. Link the document from `README.md`.
3. Link the document from `.github/copilot-instructions.md`.
4. Explain the purpose of `MistHelper.py`.
5. Explain what `MistHelper.py` must not contain.
6. Map the major regions by stable symbol name only.
7. State that contributors must not cite line numbers for `MistHelper.py`.
8. Point readers to `src\` as the home for product logic.
9. Link menu-operation rules to `.github/copilot-instructions.md`.
10. List the local validation loop.
11. State the hot-file rule for `MistHelper.py`.
12. Add one release-note fragment for issue #1713.
13. Pass the diagram and document link gate.
14. Score 80 or better with the STE linter.

## Out of Scope

This change does not edit `MistHelper.py`.
This change does not add code or tests.
This change does not change `CHANGELOG.md`.

## Verification

Run the diagram and link gate.
Run the STE linter on the new document.
Run the requested local quality gates before the commit.
