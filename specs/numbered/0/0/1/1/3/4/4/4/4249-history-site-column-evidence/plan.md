# Implementation Plan: History Site Column Failure Evidence

**Branch**: `fix/4249-history-site-column-evidence` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/1/3/4/4/4/4249-history-site-column-evidence/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

Issue #4249 reports one failed run of the history test on `main`. The job log holds no assertion text and no traceback. Later runs passed. No root cause is verified. This plan changes no product code and no test logic. It adds a guard for the diagnostics upload that keeps the evidence of the next failure. It also adds one gate-page paragraph and one changelog fragment.

## Technical Context

**Language/Version**: Python. The guard is a pytest module in `tests/guardrails`.

**Primary Dependencies**: pytest, `pytest-playwright==0.10.0`, and `pytest-timeout==2.4.0`, as pinned in `requirements-dev.txt` (lines 333 and 335). The guard file already imports `pytest` and `yaml` (`tests/guardrails/test_e2e_shard_partition.py`, lines 16 and 17).

**Storage**: None. The diagnostics artifact is a CI upload that GitHub keeps.

**Testing**: pytest guard tests. Each test reads `.github/workflows/ci.yml` through `yaml.safe_load`. Mutation cases prove that each rule can fail.

**Target Platform**: The guard runs on Windows 11, macOS, and Linux. The shard job runs on `ubuntu-latest` (`.github/workflows/ci.yml`, line 781).

**Project Type**: CI workflow and guard tests in an existing repository.

**Performance Goals**: The guard reads one workflow file. It makes no network call.

**Constraints**: The five-item rule applies. `tests/guardrails` holds 79 direct entries on `main`, and `tests/e2e/upgrade_portal` holds 68. Neither folder may gain an entry.

**Scale/Scope**: One read-only workflow step, one guard class with one method, two test functions (one with five cases), one gate-page paragraph, and one changelog fragment.

## Constitution Check

*Gate: passes before research. Re-checked after design: passes.*

| Principle or rule | Gate | Evidence in this plan |
|---|---|---|
| I. Five-item rule | Pass with recorded debt | The change adds no direct child to a full folder. The new class has one method. `ShardPartitionAudit` keeps its six methods. Complexity Tracking records the existing debt. |
| II. Class-based architecture | Pass | The new audit is a class with one method. It holds no wrapper function. |
| III. Safety first | Pass | The change adds no input, no destructive action, and no credential. |
| IV. Full deployment pipeline | Pass with tasks | T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover the steps that the agent runs. Steps 10 to 12 need the owner. |
| V. Observability and logging | Pass | New log lines use ASCII. They use the module logger with `%s` values. |
| VI. Inline comments | Pass with task | T002 requires an inline comment on each executable line of the new code. |
| VII. Action logging | Pass with task | T002 requires an `info` line before the workflow read and a `debug` line after it. |
| Mist Cloud transport | Not applicable | The feature makes no Mist Cloud request. |
| Output backends | Not applicable | The feature exports no collected API data. |
| Database keys | Not applicable | The feature changes no database key. |
| Data directory | Pass | The change writes no product output. The browser output folder stays under `test-artifacts/`. |
| Container security | Not applicable | The feature starts no container. |
| File paths | Pass | The guard keeps its existing `pathlib` paths. The change adds no path join. |
| Release notes | Pass | T006 adds one fragment (`.specify/memory/constitution.md`, line 409). |
| Documentation | Pass | T005 updates the gate page in the same change. |
| Testing | Pass | Five mutation cases prove that each audit rule can fail. |
| Security findings | Not applicable | No security tool reports a finding for this change. |
| Fix over suppress | Pass | The change adds no suppression, no retry, and no timeout change. |

For repository structure and generated files:

- The commit subject and the pull request title use the type `test` and the scope `e2e`. The title guard accepts that form.
- The change adds its own record under `specs/numbered/`, and one fragment under `changelog.d/`.
- The plan records the existing folder debt in Complexity Tracking. A separate action owns each remediation.
- Product output stays under `data/`. Test output stays under `test-artifacts/`.

For a feature that uses Mist Cloud: not applicable (see the table above).

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/3/4/4/4/4249-history-site-column-evidence/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      diagnostics-artifact.md
    checklists/
      requirements.md
```

### Source Code (repository root)

```text
tests/guardrails/test_e2e_shard_partition.py
documentation/quality-gates.md
changelog.d/issue-4249-history-site-column-evidence.md
```

Files that stay unchanged, verified on `main`:

```text
.github/workflows/ci.yml
tests/e2e/upgrade_portal/test_history_site_column_journey.py
src/interfaces/portals/upgrade_portal/app/routes/review.py
src/interfaces/portals/upgrade_portal/app/assets/templates/review/history.html
tests/e2e/upgrade_portal/conftest.py
tests/e2e/upgrade_portal/screenshot.py
```

**Structure Decision**: The guard stays in the existing shard guard file. `tests/guardrails` already holds 79 direct entries, so a new file there breaks the five-item rule. The new audit has its own class, because `ShardPartitionAudit` already holds six methods.

## File-by-File Change Map

| Path | Action | Change |
|---|---|---|
| `tests/guardrails/test_e2e_shard_partition.py` | Modify | Add one sentence to the module docstring. Add class `EvidenceUploadAudit` with method `check_upload`. Add test `test_the_diagnostics_upload_keeps_the_evidence_after_a_failure_or_cancel` and test `test_a_missing_diagnostic_fails`. |
| `documentation/quality-gates.md` | Modify | Name the diagnostics artifact in the `playwright` row (line 68). Add one paragraph after the warning at line 86. |
| `changelog.d/issue-4249-history-site-column-evidence.md` | Add | One `###` heading and one `Changed` bullet that names issue 4249. |
| `specs/numbered/0/0/1/1/3/4/4/4/4249-history-site-column-evidence/` | Add | The record from the draft folder. |

## Dependencies

No new dependency. The guard file already imports `pytest` and `yaml`.

## Complexity Tracking

Existing debt that the change touches or avoids. None of this debt is new.

| Item | Kind | Why it stays | Remediation |
|---|---|---|---|
| `tests/guardrails` holds 79 direct entries | Grandfathered | The change adds no entry there. | A separate action owns the folder. |
| `tests/e2e/upgrade_portal` holds 68 direct entries | Grandfathered | The change adds no entry there. | A separate action owns the folder. |
| `ShardPartitionAudit` holds six methods | Grandfathered | The change adds a class, not a method. | A separate action splits the class. |
| The guard module holds more top-level names than the limit | Grandfathered | The change adds three top-level names. | A separate action splits the module. |

New design that needs a reason.

| Item | Why it is needed | Simpler alternative rejected because |
|---|---|---|
| Class `EvidenceUploadAudit` | The audit needs one method. | A method on `ShardPartitionAudit` adds to a class that is already over the limit. |
| Two test functions in the existing file, one with five cases | Each removed rule needs a negative case. | A new file in `tests/guardrails` breaks the five-item rule. |

## Risks and Mitigations

- **A workflow edit renames the diagnostics step**: The audit finds the step by name and requires exactly one. A rename fails the guard with a clear message.
- **The root cause stays unknown**: The follow-up issue keeps the cause open. Each push still runs the required check.
- **Caution: a canceled shard can lose the traceback text**: The failure screenshot and the trace remain. The gate page states this limit (FR-007).
- **The diagnostics artifact grows**: Pytest keeps files for failed tests only. The artifact grows with the number of failed tests.

## Rollback

1. Open a pull request that reverts the squash commit on `main`. Do not push to `main` directly.
2. The revert removes the guard, the gate-page paragraph, and the fragment.
3. The workflow and the product code stay unchanged, so no runtime change follows.
4. The change touches no data, no container, and no secret.

## Deployment Notes

None. The change alters CI guard tests and documentation only.
