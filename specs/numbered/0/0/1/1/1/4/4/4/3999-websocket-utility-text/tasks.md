---

description: "Implementation tasks for the WebSocket utility text catalog move"

---

# Tasks: WebSocket Utility Text Catalog

**Input**: Routed design documents from `specs/numbered/0/0/1/1/1/4/4/4/3999-websocket-utility-text/`

**Prerequisites**: `spec.md`, `plan.md`

## Phase 1: Move and update imports

- [X] T001 Move `utility_text.py` into `catalog/utilities` with `git mv`.
- [X] T002 Update the four active imports to the canonical utilities path.
- [X] T003 Add the exact old-to-new module mapping to the public symbol preservation guard.

## Phase 2: Preserve the package contract

- [X] T004 Confirm the old module path has no wrapper, alias, or fallback import.
- [X] T005 Confirm `catalog` and `catalog/utilities` each have no more than five structural children.
- [X] T006 Run the focused utility text tests and the public symbol preservation guard.

## Phase 3: Record and validate

- [X] T007 Add the issue-specific changelog fragment.
- [X] T008 Run compile, Ruff, Black, Mypy, Bandit, complexity, applicable docstring, changelog, and Markdown-link checks.
- [ ] T009 Commit the verified bounded change locally with the required co-author trailer.
- [ ] T010 Run the required post-commit test-quality procedure and report its result.

## Scope Boundary

Do not edit historical specifications 3574, 3889, or 3890. Do not edit shared registries, generated references, or unrelated source modules.
