# Specification Quality Checklist: Batch target site snapshot

**Purpose**: Confirm that `spec.md` is complete and testable before the plan and tasks start.
**Created**: 2026-11-26
**Feature**: `spec.md` in the parent folder

## Content Quality

- [x] The spec names the operator impact: one organization read for each preview (User Story 1).
- [x] Each user story has an independent test and acceptance scenarios.
- [x] Module names appear only in FR-011, FR-012, and the plan and contracts, where the constraints need them.
- [x] Each clarification has a recorded answer and a decision reference.

## Requirement Completeness

- [x] Each functional requirement uses MUST and a testable condition (FR-001 to FR-012).
- [x] Each requirement maps to at least one task and one test in `tasks.md`, under "Requirement coverage".
- [x] Success criteria SC-001 to SC-005 name measurable results.
- [x] Edge cases cover an added site, a removed site, an empty organization, a restart, HTTP 429, and concurrent checks.
- [x] Assumptions name their evidence: `wsgi.py` line 4, `routes/pickers.py` line 25, and the page reader lines.
- [x] Out of scope names each excluded area, including issue #4921.
- [x] Each safety statement starts with `Caution:` or `Warning:`. The Caution in the edge cases names the recoverable harm.
- [x] Explained: the live acceptance of page limit 1000 is unverified. Reason: no live Mist call is made in this record (U-1 in `research.md`).
- [x] Explained: the 5000-call threshold is documented for an API token, not for a credential. Reason: the wording differs, and the substance matches (A-6 in `analysis.md`).

## Feature Readiness

- [x] Each user story maps to the tests in T002, T003, and T004.
- [x] The spec contains no unfinished text and no empty section.
- [x] The spec uses one term for each concept: site snapshot, site check, organization read, discovery, and preview.
- [x] The spec does not change the repository. Its only writes are in the draft folder and the metadata folder.

## Notes

- Checked on 2026-11-26 after the self-review of `spec.md`.
- The explained items record residual risk. They do not block the spec.
