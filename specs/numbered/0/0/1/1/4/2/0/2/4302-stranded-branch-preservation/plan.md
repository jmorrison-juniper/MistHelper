# Implementation Plan: Stranded Branch Preservation

**Branch**: `docs/4302-stranded-branch-preservation` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification from `/specs/numbered/0/0/1/1/4/2/0/2/4302-stranded-branch-preservation/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Issue #4302 tracks branches that hold commits above `main` and have no PR. The issue lists 48 rows. Report #4911 lists 505 rows. This record verifies every row on GitHub. It defines the gates that must pass before a branch publishes. It changes no branch ref.

## Technical Context

**Language/Version**: Markdown for the record. Python 3.15 only for the two existing guard tests.

**Primary Dependencies**: GitHub CLI (`gh`) for reads and for gated writes. Git for read-only evidence. `ste-linter` and `markdown-link-check`, run with pre-commit.

**Storage**: GitHub for remote refs, PRs, and issues. The local `.git` directory, read-only.

**Testing**: The two guard tests, the STE gate, and the link check. The commands are in `design/quickstart.md`.

**Target Platform**: github.com. Windows 11 for local runs.

**Project Type**: Repository record. No product code changes.

**Performance Goals**: None. Obey the GitHub rate limit. Wait 60 seconds after HTTP 403 or 429, then retry up to three times.

**Constraints**: The repository checkout is read-only for this agent. The repository is public.

**Scale/Scope**: 505 report rows. 598 remote head refs, including `main`. 48 annotated rows. 93 remote checks. 11 record files.

## Constitution Check

Each rule has a result and a reason.

- **I. Five-Item Rule**: PASS. Directory `0/0/1/1` keeps five children and gains none. Directory `0/0/1/1/4` keeps three children and gains one. The new levels `2`, `0`, and `2` each hold one child. The record folder holds five children. See RC-19 to RC-21.
- **II. Class-Based Architecture**: PASS. The change adds no code and no wrapper.
- **III. Safety-First**: PASS. The change adds no input handling. Each publication needs owner authorization and a scan (FR-005).
- **IV. Full Deployment Pipeline**: PASS. The record PR runs the local gates, the CI checks, and a squash merge (T-LOCAL-GATES, T-REMOTE-CI, T-MERGE). No product file changes, so `container-build.yml` does not run.
- **V. Observability and Logging**: PASS. The change adds no code, so the rule does not apply.
- **VI. Inline Comments**: PASS. The change adds no code, so the rule does not apply.
- **VII. Action Logging**: PASS. The change adds no code, so the rule does not apply.
- **Technology and Compatibility**: PASS. The change adds no Mist REST call, no SDK call, and no container work.
- **Development Workflow**: PASS. The record reads `AGENTS.md`, the repository instructions, and the constitution before the change.
- **Release Notes**: PASS. One fragment is added (D-13).
- **Multi-Agent Git Workflow**: PASS. The branch starts from `main`. The labels include a type, a scope, and a status (D-15).
- **SpecKit Escalation**: PASS. The change touches more than three files, so the spec is required.

Existing violations touched: none.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/4/2/0/2/4302-stranded-branch-preservation/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      branch-disposition-table.md
    checklists/
      requirements.md
      publication.md
```

## File Change Map

| Path | Action | Purpose |
| - | - | - |
| `specs/numbered/0/0/1/1/4/2/0/2/4302-stranded-branch-preservation/spec.md` | Add | Scope, requirements, and success criteria |
| `specs/numbered/0/0/1/1/4/2/0/2/4302-stranded-branch-preservation/plan.md` | Add | Constitution check, file map, and risks |
| `specs/numbered/0/0/1/1/4/2/0/2/4302-stranded-branch-preservation/tasks.md` | Add | Ordered tasks with gates |
| `specs/numbered/0/0/1/1/4/2/0/2/4302-stranded-branch-preservation/analysis.md` | Add | Consistency review and findings |
| `specs/numbered/0/0/1/1/4/2/0/2/4302-stranded-branch-preservation/design/research.md` | Add | Decisions, remote checks, and unverified items |
| `specs/numbered/0/0/1/1/4/2/0/2/4302-stranded-branch-preservation/design/data-model.md` | Add | Entities, keys, and states |
| `specs/numbered/0/0/1/1/4/2/0/2/4302-stranded-branch-preservation/design/quickstart.md` | Add | Commands and tests |
| `specs/numbered/0/0/1/1/4/2/0/2/4302-stranded-branch-preservation/design/contracts/branch-disposition-table.md` | Add | Format of the status comment on #4302 |
| `specs/numbered/0/0/1/1/4/2/0/2/4302-stranded-branch-preservation/design/checklists/requirements.md` | Add | Spec quality checklist |
| `specs/numbered/0/0/1/1/4/2/0/2/4302-stranded-branch-preservation/design/checklists/publication.md` | Add | Checklist for each publication batch |
| `changelog.d/issue-4302-stranded-branch-preservation.md` | Add | Release-note fragment |

No file is modified or deleted. No other repository path changes.

## Changelog Fragment

The fragment follows the shape of the existing fragments on `main`. Its content is:

```markdown
### Added
- Stranded branch preservation record, with verified report scope and owner gates, for issue #4302.
```

## Branch Evidence Summary

- Annotated rows: 48. Present: 47. Absent: 1 (`fix/3417-snmp-base-oid`, kept by merged PR #4318).
- Report #4911 rows: 505. PR-kept: 248. Unkept: 257.
- Unkept annotated rows: 47. They form holds H1, H2, and H3, and batches B1, B2, and B3.
- Unkept new rows: 210. They form group N.
- High-impact paths on unkept heads include `upgrade_portal/app/routes/org_upgrade.py` below the retired `src` root on `fix/3222-confirm-details` and `src/interfaces/portals/upgrade_portal/upgrade/driver.py` on `jmorrison-juniper-fix-2863-identifier-defaults-batch-1`. Both sit on the destructive upgrade path.

## Dependencies

- GitHub CLI, authenticated as the owner account. Used for reads and for gated writes.
- Git, used read-only. No checkout and no fetch.
- Pre-commit hooks `ste-linter` and `markdown-link-check`, pinned in `.pre-commit-config.yaml`.
- The two guard tests `tests/guardrails/test_spec_route_contract.py` and `tests/guardrails/test_process_folder_structure.py`.
- The shared report workflow `reusable-stranded-branch-report.yml`, read only, at `79a5e45970e876f1656d69520d9635cea1aa25ef`.

## Risks and Mitigations

- Warning: a published head stays readable after its PR closes. Mitigation: owner authorization and a scan before each PR (FR-005).
- Warning: deleting a branch with no PR destroys its only copy. Mitigation: no deletion in this issue (FR-008).
- Caution: a draft PR can be closed and reopened. Publication uses draft PRs for that reason.
- Risk: a head moves after its scan. Mitigation: TST-06 and TST-17 run again when the PR opens.
- Risk: a scan finds a secret. Mitigation: the batch stops, and the owner handles it under the credential policy.
- Risk: the report keeps listing PR-kept rows. Mitigation: D-4 and D-11. Published rows leave the report, because their PR uses the branch name.
- Risk: the public PR list grows with each batch. Mitigation: D-3 limits each step to an owner-selected batch.
- Risk: the record PR closes #4302 too early. Mitigation: the `Refs` form (D-10).

## Rollback Steps

1. For the record PR, open a revert PR. Do not force-push `main`.
2. For a draft PR, close it without merge. The head stays readable.
3. For exposed content, close the PR, notify the owner, and rotate any exposed credential. Warning: exposed content stays readable by commit SHA after closure.

## Complexity Tracking

None. No constitution rule is violated.
