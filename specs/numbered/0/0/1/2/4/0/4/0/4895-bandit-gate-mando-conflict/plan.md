# Implementation Plan: Bandit Gate Dependency Conflict

**Branch**: `4895-bandit-gate-mando-conflict` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification from `/specs/numbered/0/0/1/2/4/0/4/0/4895-bandit-gate-mando-conflict/spec.md`. The route comes from `.specify/scripts/powershell/spec-route.ps1`, lines 4 to 17.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, and checklists under `design/`. This feature omits `design/contracts/`, because no interface contract applies.

## Summary

The Bandit gate stops in the install step before Bandit runs. PR #4888 pins `mando==0.8.2`, but radon 6.0.1 requires `mando` below 0.8. The fix keeps `mando` at 0.7.1 on `main`, adds a Dependabot ignore for `mando` major and minor updates, and proves the rule with guard tests. PR #4888 closes after the fix merges.

## Technical Context

**Language/Version**: Python 3.15 for CI (`.github/workflows/ci.yml` line 77).

**Primary Dependencies**: pip, uv (lock export), radon 6.0.1, and mando 0.7.1. Radon 6.0.1 declares `mando (<0.8,>=0.6)`. The parity guard already imports packaging at line 13.

**Storage**: Not applicable. The change stores no data.

**Testing**: pytest guard tests under `tests/guardrails`, Ruff, Black, and the test quality analyzer.

**Target Platform**: GitHub Actions `ubuntu-latest` (`.github/workflows/ci.yml` line 415).

**Project Type**: CI policy and guard test change.

**Performance Goals**: The Bandit job keeps its five-minute timeout (`.github/workflows/ci.yml` line 416).

**Constraints**: The Bandit configuration stays unchanged. Each new executable line carries an inline comment.

**Scale/Scope**: Three existing files change. One pull request closes. The bot closes 15 gate issues. One run holds 28 failed jobs.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule | Pass | No new direct child is added. Base-5 route digits give at most five children at each level. Existing debt: `tests/guardrails` holds 77 files (grandfathered, constitution lines 42 to 43). A separate remediation action owns that debt. |
| II. Class-based architecture | Pass | The check logic lives in class `RadonPinBoundary`. The test functions call the class and wrap nothing. |
| III. Safety-first | Pass | No input handling changes. No destructive operation runs. |
| IV. Full deployment pipeline | Pass with recorded deviation | Steps 1 to 9 map to tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. Step 10 records a run that does not start, because the push paths in `container-build.yml` lines 6 to 19 exclude both changed files. Steps 11 and 12 do not apply, because no image changes. |
| V. Observability and logging | Pass | New log text uses ASCII only. |
| VI. Inline comments | Pass | Each new executable line carries an inline comment. The YAML ignore block carries a comment that gives the cause. |
| VII. Action logging | Pass | New helper code logs an info line before each file read and a debug line after it. |
| Technology: Python, uv, requirements | Pass | `requirements.txt` and `uv.lock` stay unchanged. |
| Technology: Podman and test containers | Not applicable | No container starts. |
| Technology: Mist API and mistapi | Not applicable | The change makes no Mist call. |
| Security findings: fix over suppress | Pass | No suppression is added. The Bandit configuration stays unchanged. |
| Documentation | Pass | The rationale lives in one place, the comment in `.github/dependabot.yml`. No changelog fragment is added, because no user sees the change. |
| Specifications | Pass | The record exists before any code. The conflict stops 26 jobs. |
| Multi-agent Git and labels | Pass | Labels `bug` and `ci` cover type and scope. `in-progress` covers status. No open pull request touches the three target files. |
| Compliance review | Pass | Complexity Tracking lists only grandfathered debt. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/0/4/0/4895-bandit-gate-mando-conflict/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    checklists/
      requirements.md
```

The folder `design/contracts/` is omitted. No menu, CLI, output column, or API contract applies to a dependency policy.

### Source Code (repository root)

```text
.github/dependabot.yml
tests/guardrails/test_dependency_declaration_parity.py
tests/guardrails/test_pr_title_workflow.py
```

**Structure Decision**: Edit three existing files. Add no file under `tests/guardrails`, because that folder already holds 77 files.

## File-by-File Change Map

| Path | Action | Requirement | Change |
| - | - | - | - |
| `.github/dependabot.yml` | Modify | FR-004 | Add an `ignore` block to the pip stream, lines 3 to 11. |
| `tests/guardrails/test_dependency_declaration_parity.py` | Modify | FR-002, FR-003, FR-007 | Add class `RadonPinBoundary`, one synthetic test, and one real-file test. |
| `tests/guardrails/test_pr_title_workflow.py` | Modify | FR-005 | Add the same ignore entry to the pip stream of `POLICY_SNAPSHOTS["dependabot"]`, lines 23 to 30. |
| `specs/numbered/0/0/1/2/4/0/4/0/4895-bandit-gate-mando-conflict/` | Add | SC-005 | Add the record files from this draft. |
| `requirements-dev.txt` | No change | FR-001 | `main` already pins `mando==0.7.1` at line 179. |
| `uv.lock` | No change | FR-001 | The lock already pins `mando` 0.7.1 at line 1301. |
| `.github/workflows/ci.yml` | No change | FR-008 | Every gate command stays unchanged. |
| `pyproject.toml` | No change | FR-008 | The Bandit configuration stays unchanged. |

## Design

### Regression guard (FR-002, FR-003, FR-007)

Class `RadonPinBoundary` lives in `tests/guardrails/test_dependency_declaration_parity.py`. It has two static methods.

- `pinned_version` returns the exact version of one `name==version` line.
- `defects` returns one message for each requirement that the pinned version violates.

Two module-level test functions use the class.

- `test_radon_boundary_rejects_mando_0_8_2` passes synthetic text. It proves that the boundary can fail.
- `test_pinned_mando_satisfies_installed_radon` reads `requirements-dev.txt` and the installed radon metadata. It fails on the PR #4888 head content.

### Dependabot policy (FR-004, FR-005)

The pip stream gains one ignore entry. The npm stream already uses the same entry shape at `.github/dependabot.yml` lines 45 to 81.

```yaml
    ignore:
      # radon 6.0.1 requires mando below 0.8. A higher mando pin stops pip with ResolutionImpossible.
      # Both update types cover 0.x releases, whichever type Dependabot assigns.
      # Remove this entry in the pull request that raises radon to a release that accepts mando 0.8.
      - dependency-name: "mando"
        update-types: ["version-update:semver-major", "version-update:semver-minor"]
```

The snapshot in `tests/guardrails/test_pr_title_workflow.py` receives the same entry. The complete-policy assertion at line 295 then passes.

### Gates and scope (FR-006, FR-008, FR-009)

No gate command changes. Bandit excludes `tests` at `pyproject.toml` line 503, so Bandit does not scan the new guard code.

## Dependencies

- No package is added. The guard uses `importlib.metadata` from the standard library and `packaging`, which the parity guard already imports.
- The guard reads the installed radon 6.0.1 metadata. The CI install step provides it.
- PR #4888 closes only after the fix merges.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| Dependabot raises another `mando` bump before the fix merges. | Merge the fix first. The ignore applies to later runs. |
| radon publishes a release that accepts `mando` 0.8. The ignore then blocks that upgrade. | The ignore comment names its removal condition. The maintainer removes it in the radon upgrade pull request. |
| The real-file case passes on a machine that lacks radon. | The test reads installed metadata and never skips. A missing distribution fails with its name. |
| The 15 gate issues stay open after PR #4888 closes. | The bot closes them after a `main` run. T-MERGE waits for that run and records the result. |
| Bandit reports a real defect later. | The gate stays strict. The team fixes the finding or opens a new issue. No suppression is added. |

## Rollback

1. Revert the fix merge commit with `git revert` on `main`.
2. Reopen PR #4888 in the GitHub interface if the owner wants the Dependabot bump.
3. Keep the branch `dependabot/pip/mando-0.8.2` until the closing comment of PR #4888 exists.

Warning: deleting the branch `dependabot/pip/mando-0.8.2` removes the remote branch that holds the bump. Keep the branch until the closing comment exists.

Caution: closing PR #4888 removes it from the default open list. Reopening the pull request restores the entry.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| `tests/guardrails` holds 77 files and 3 folders (existing debt). | The guard cases belong with the existing dependency guards. | A new file adds a direct child to a noncompliant parent (constitution lines 42 to 43). |
