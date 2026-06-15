# Quickstart: Site Marvis Config Actions Planning-to-Implementation Handoff

## Goal

Implement four site-scoped Marvis config action menu operations from `specs/1001-site-marvis-config-actions/spec.md` with strict safety parity and deterministic export behavior.

## Planned Operation Set

- Site config action count (safe)
- Site config action search (safe, paginated)
- Site config action feedback submission (mutating, strongly validated)
- Site config action delete by action ID (destructive, exact typed confirmation)

## Menu Number Assignments

- **216**: Site Marvis Config Action Count (safe)
- **217**: Site Marvis Config Action Search (safe, paginated)
- **218**: Submit Site Marvis Config Action Feedback (mutating)
- **219**: Delete Site Marvis Config Action by ID (destructive)

## Implementation Sequence

1. Add menu entries and handler dispatch paths for all four operations.
2. Implement shared site-scope prompt collection (`org_id`, `site_id`, optional filters/window) via `safe_input()`.
3. Implement count operation with deterministic export payload and summary output.
4. Implement search operation with pagination traversal and deterministic result export.
5. Implement feedback payload builder + strict validator (required fields, allowlist checks, bounded text).
6. Implement delete workflow with warning banner + exact typed confirmation gate before API call.
7. Register explicit `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries for count/search/feedback/delete result datasets.
8. Route all outputs through existing exporter pipeline (CSV/SQLite/polyglot parity).
9. Add/adjust tests for safe paths, feedback validation rejection/success paths, and destructive guards.
10. Update release docs in `README.md` (menu inventory/count) and `CHANGELOG.md` in same delivery.

## Verification Checklist

### Static quality gates
- `python -m py_compile MistHelper.py`
- `python -m ruff check MistHelper.py`
- `python -m black --check MistHelper.py`

### Test coverage targets
- count/search happy paths with representative filters
- search pagination behavior on multi-page datasets
- feedback validation: missing/invalid fields rejected pre-call
- feedback valid payload: mutating call executed and result summarized
- delete guard: wrong confirmation cancels, exact confirmation permits call path
- unattended test mode: destructive path skipped/guarded with explicit reporting
- CSV + SQLite export compatibility for count/search and operation-result datasets

### Manual behavior checks
- operator can complete safe count/search workflows in under target time for typical dataset
- feedback flow gives clear, actionable validation messages on bad input
- delete flow always warns and never executes without exact typed confirmation
- terminal summaries include site scope, operation status, and row/result counts

## Done Criteria

Feature is ready for `/speckit.tasks` when:
- `plan.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md` are complete,
- all FR/SC requirements map to planned implementation and tests,
- no unresolved clarifications remain in technical context or constitution checks.
