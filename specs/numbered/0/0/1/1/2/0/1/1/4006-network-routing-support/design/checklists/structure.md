# Structure Checklist: Isolate Network Routing Support Modules

**Purpose**: Check the structure rules that the change must meet.
**Created**: 2026-11-26
**Feature**: `plan.md` section "Architecture" and `tasks.md` T013

## Hierarchy Limits

- [ ] Network root holds five structural children after the change (FR-003). Not met yet: the move occurs in T004. TC-01 measures it.
- [ ] Support package holds three structural children after the change (FR-004). Not met yet: the move occurs in T004. TC-01 measures it.
- [x] Feature root holds five children: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design`.
- [x] Design folder holds five children: `research.md`, `data-model.md`, `quickstart.md`, `contracts`, and `checklists`.
- [x] Contracts folder holds one file: `module-path-map.md`.
- [x] Checklists folder holds three files: `requirements.md`, `structure.md`, and `publication.md`.

## Function Limits for New Code

- [ ] The structure guard has no function over 25 lines (plan Constitution Check). Not met yet: the refresh occurs in T013. The candidate has one 27-line function.
- [x] The structure guard uses at most two parameters for each function.
- [ ] Each line of the structure guard has an inline comment (Principle VI). Not met yet: the refresh occurs in T013.

## Guard Behavior

- [x] The guard checks five network children and three support children (FR-003, FR-004).
- [x] The guard scans active paths and excludes `specs/` (FR-016, FR-013).
- [x] The guard has negative tests for a sixth child and for a missing support root (candidate design).
- [ ] The guard prints examined counts on success (FR-016). Not met yet: the candidate prints counts on failure only. The refresh occurs in T013.
