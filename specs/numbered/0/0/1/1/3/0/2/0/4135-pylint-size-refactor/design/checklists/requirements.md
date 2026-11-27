# Specification Quality Checklist: Function and module size for Pylint limits

**Purpose**: Confirm the spec, plan, and tasks for issue 4135 meet the quality bar before the implementation starts.
**Created**: 2026-11-26
**Feature**: `spec.md`, `plan.md`, `tasks.md` in the feature root

## Content Quality

- [x] CHK001 Each user story states a value to a maintainer or an operator. Explained: Stories 1 and 2 serve the Pylint gate and operator behavior. Stories 3 and 4 serve the Juniper writer and the documents.
- [x] CHK002 Each user story is independently testable. Each story names its test command or its reading step.
- [x] CHK003 Each story has a priority. Stories 1 and 2 are P1. Stories 3 and 4 are P2.
- [x] CHK004 Implementation detail appears only where the refactor needs exact paths. Explained: A move record must name exact repository paths, so the plan and tasks name them.
- [x] CHK005 The spec uses plain language for each requirement. Each requirement uses the MUST form with one action.

## Requirement Completeness

- [x] CHK006 Each functional requirement FR-001 to FR-018 is testable by a command, a test, or a reading step named in `tasks.md`.
- [x] CHK007 Each success criterion SC-001 to SC-006 names a measurement or a command.
- [x] CHK008 Edge cases appear in the spec, and each edge case names a mitigation task.
- [x] CHK009 Out-of-scope items appear in the spec and in `plan.md`, with the remediation task named.
- [x] CHK010 Assumptions appear in the spec.
- [x] CHK011 The clarifications section records a recorded answer for each question.
- [x] CHK012 The Mist Cloud section states why it does not apply. Explained: The change moves code and adds no request.
- [x] CHK013 The record holds no unresolved marker text. Explained: A scan finds no open marker words, no ellipsis, and no empty section.

## Feature Readiness

- [x] CHK014 Each functional requirement maps to at least one task. The map appears in `analysis.md`.
- [x] CHK015 Each requirement maps to at least one test or gate. The map appears in `analysis.md`. FR-016 maps to a reviewer check, because no automated check exists for inline comments.
- [x] CHK016 Each task names exact repository paths and one verification command from the local gates table. Explained: The final tasks name the pull request check, because the table has no command for that step.
- [x] CHK017 The plan states the constitution check for each rule. Each recorded violation appears in the complexity table.
- [x] CHK018 The remote claims carry the blob SHA and the decoded line number for each code claim. The count of 62 rows matches across `research.md`, `STATUS.json`, and `summary.md`.
- [x] CHK019 The contracts folder is omitted, and `plan.md` says so.
- [x] CHK020 The data model names each entity, its natural key, and its state transitions.

## Notes

- Items CHK006 and CHK015 rely on the reviewer check for FR-016. No automated check covers inline comments.
- Item CHK013 is checked by a scan of the drafts for the forbidden marker words. The validator in the META folder runs the scan.
- The stricter child count that includes `__init__.py` is recorded in `analysis.md`. The nested-package guard is the operative count.
