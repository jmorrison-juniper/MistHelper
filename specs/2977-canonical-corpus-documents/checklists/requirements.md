# Specification Quality Checklist: Canonical Corpus Documents

**Purpose**: Validate specification completeness and quality before bounded local planning.
**Created**: 2026-10-01
**Feature**: [Canonical Corpus Documents](../spec.md)

**Note**: This checklist validates the specification only.
Checked items do not prove implementation, historical acceptance, or permission for protected merge work.

## Content Quality

- [x] CHK001 The specification adds no implementation design beyond the user's required compatibility and safety constraints.
- [x] CHK002 The specification focuses on storage savings, safe resume, source evidence, and operator needs.
- [x] CHK003 The specification uses plain language and defines the required content terms.
- [x] CHK004 All mandatory sections of the current specification template are complete.

## Requirement Completeness

- [x] CHK005 No unresolved scope-clarification marker remains.
- [x] CHK006 Requirements state testable pass or fail conditions.
- [x] CHK007 Success criteria use measurable counts, bytes, percentages, and bounded work.
- [x] CHK008 Success criteria describe observable outcomes without selecting implementation technology.
- [x] CHK009 Each user story defines independent proof and acceptance scenarios.
- [x] CHK010 Edge cases cover content collisions, invalid files, interrupted writes, failed persistence, migration, and placement.
- [x] CHK011 The scope separates file-only specification, later code prevention, historical acceptance, and protected merge acceptance.
- [x] CHK012 Existing dependencies, compatibility constraints, assumptions, and reserved paths are explicit.

## Feature Readiness

- [x] CHK013 Functional requirements define clear acceptance conditions for the required behavior.
- [x] CHK014 User scenarios cover acquisition, aliases, restart, manifests, placement, and migration.
- [x] CHK015 Required local proof covers every measurable outcome in the specification.
- [x] CHK016 The specification selects no new language, framework, parser, dependency, storage layout, or implementation algorithm.

## Notes

### Validation Record

- Validation iteration 2 passes all 16 specification quality items.
  The review covers FR-001 through FR-032 and SC-001 through SC-008.
- Iteration 1 found two overbroad acceptance statements under CHK006 and CHK013.
  FR-027 previously required each path consumer and "its dry-run behavior."
  The runner has no required dry run, so the revised requirement names only the two existing dry-run tools.
  SC-004 previously required "Every successful record" to refer to a complete payload.
  The revised criterion preserves valid records without a payload and their nullable file fields.
  User Story 1 also now distinguishes an unknown resolved URL from a new root that selects an already known URL.
- CHK001 and CHK016 distinguish required compatibility constraints from a proposed implementation design.
  The user requires SHA256, existing call boundaries, exact identity metadata, a 1 MiB read ceiling, and reserved paths.
  The specification records those constraints without selecting a new design.
- FR-002 states: "This reuse saves physical writes and storage bytes, not the first transfer for an unknown URL."
  SC-001 and SC-007 require measured fetch and write counts.
- FR-009 requires size, device, inode, `mtime_ns`, `ctime_ns`, and the expected digest.
  FR-010 and FR-028 require same-size corruption detection with restored modification time.
- FR-022 through FR-025 define the complete legacy compatibility and migration acceptance contract.
  Later design must document each actual new field, cache relation, version rule, backup rule, and recovery rule.
- FR-026 through FR-030 require actual-flow red/green proof, measured work, zero required skips, and changed-method coverage of at least 80 percent.
  No software test or coverage result is claimed by this checklist.
- SC-004, SC-006, and SC-008 connect retained metadata, valid move references, and migration preservation to operator-visible outcomes.
- No scope question blocks bounded local planning.
  A later planning request must name `specs/2977-canonical-corpus-documents/` explicitly.
  Shared feature selection remains unchanged.

### Unresolved Acceptance

- The actual-flow red regression and green implementation proof remain unperformed.
- Actual manifest, alias, restart, invalid-file, interruption, permission, stat, hash, and store proof remain unperformed.
- Measured file, byte, write, fetch, walk, and hash work remains unproved.
- Changed-method coverage of at least 80 percent remains unproved.
- New schema/cache design, verified migration, backup recovery, and older-reader/writer compatibility evidence remain pending.
- Historical Windows files remain absent and unauthorized.
  The reported 2,974 source PDFs, 2,623 distinct documents, 351 redundant files, and 1.32 GB remain unverified.
  Issue 2977 remains open.
- Normal branch and companion context hooks remain unresolved because their writes exceed the file-only scope.
  The optional commit hook does not run.
  This checklist does not claim full completion of the normal hooked stage.
- Protected merge acceptance requires the parent's full verified main-SHA grant.
  The initial main revision is not that grant.
  No fetch, commit, push, pull request, merge, or deployment is authorized here.

### Readiness

The specification is ready for a separately authorized bounded `/speckit.plan` stage.
Its quality pass does not authorize implementation or remote work.
If a scope decision changes, update the specification before `/speckit.clarify` or `/speckit.plan`.
