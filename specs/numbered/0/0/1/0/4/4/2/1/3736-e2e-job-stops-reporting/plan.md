# Implementation Plan: E2E stall diagnostics

**Branch**: `fix/3736-e2e-stall-diagnostics` (planned) | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification from `specs/numbered/0/0/1/0/4/4/2/1/3736-e2e-job-stops-reporting/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root.
Place research, data model, quickstart, contracts, and checklists under `design/`.
Keep five children or fewer at every new directory level.

## Summary

The E2E browser suite stopped reporting results in four observed runs. Each stall ended at the same test. The current shards have no observed stall. The root cause is unknown.

This plan adds evidence capture and does not change behavior. The E2E harness writes a stack dump of all threads when an item runs for 100 seconds. The phase trail records the start and end of each item. The shard diagnostics upload includes both files. The cancel message names both possible causes. No timeout, selection, or assertion changes.

## Technical Context

**Language/Version**: Python 3.15 or newer. Source: `.github/copilot-instructions.md`, section "Language and environment".

**Primary Dependencies**: pytest 9.2.0 and pytest-timeout 2.4.0 (pinned). Standard library `faulthandler`. Sources: RC-28, RC-41, RC-46.

**Storage**: Diagnostic files under `test-artifacts/`, which Git ignores. Source: RC-35.

**Testing**: pytest guard tests in `tests/guardrails/`. The guards read the workflow and run a synthetic project in a subprocess.

**Target Platform**: GitHub Actions `ubuntu-latest`. Local runs on Windows 11 must also work, because the repository requires Windows compatibility.

**Project Type**: Test harness and CI workflow. No product code.

**Performance Goals**: No change to the per-test budget (120 seconds) or the job limits (20, 5, and 30 minutes).

**Constraints**: ASCII output only. No new dependency. No change to product files. No suppression comment.

**Scale/Scope**: About 980 E2E items in one process in the single-job era, and three shards with 201 to 453 items each in the current era.

## Constitution Check

The constitution (`.specify/memory/constitution.md`, version 1.9.0) and the repository rules were read in full. Each row names one rule and gives a result.

| Rule | Result | Reason |
| - | - | - |
| Principle I, five-item rule | Pass | No new directory is created. The new tests extend existing files. `tests/guardrails/e2e_timeout_budget/` holds five children today and gets no new file. |
| Principle I, existing folder debt | Pass with a tracked action | `changelog.d/` holds 335 children today (research section 6 and RC-36). The one fragment is the unique record that Principle I permits. Task T012 tracks a separate remediation issue. |
| Principle I, function limits | Pass by design | Each new function takes at most five parameters and has at most 25 lines. T-LOCAL-GATES runs `radon` and `pylint`. |
| Principle II, class-based design | Pass | The new code is a class. The new hooks are methods of a registered plugin object (D-10). The existing module-level hooks predate this record. |
| Principle III, safety-first | Pass | The change reads no user input. It runs no destructive operation. It validates the threshold variable before use. |
| Principle IV, deployment pipeline, steps 1 to 9 | Pass | T-LOCAL-GATES, the commit, the rebase, the push, the pull request, T-REMOTE-CI, and T-MERGE cover steps 1 to 9. |
| Principle IV, steps 10 to 12 | Pass with a stated reading | Steps 10 to 12 wait for `container-build.yml`. That workflow runs on a push that changes a product file, or on manual dispatch (`.github/copilot-instructions.md`, section "Containers and ports"). FR-010 forbids product file changes, so the build does not run. The orchestrator must confirm this reading (analysis UR-4). |
| Principle V, observability | Pass | Both files stay ASCII. `json.dumps` escapes non-ASCII text by default. Faulthandler output is ASCII (RC-48). Log lines describe actions without secrets. |
| Principle VI, inline comments | Pass by requirement | Each new executable line carries an inline comment. The reviewer checks this in T-PR. |
| Principle VII, action logging | Pass by requirement | Each action logs before and after execution. A file error logs the full context. |
| Technology, Mist Cloud and mistapi | Not applicable | The change sends no Mist Cloud request. |
| Technology, Podman and test containers | Not applicable | The change starts no container. |
| Technology, file paths | Pass | The new code builds paths with `pathlib.Path`. |
| Technology, data directory | Pass | Diagnostics go to `test-artifacts/`. Git ignores that folder (RC-35). |
| Testing, guards | Pass | New tests extend existing guard modules. The synthetic project uses the real conftest hooks. |
| Security findings | Pass | The change adds no suppression comment. |
| Documentation | Pass | `documentation/quality-gates.md` is updated (D-9). A changelog fragment is added (FR-011). No README change is needed, because no user-visible operation changes. |
| SpecKit escalation | Pass | The change touches more than two files, so this specification is required. |
| Multi-agent Git | Pass | The issue exists and carries `in-progress`. The branch name follows `<type>/<issue>-<slug>`. The commit subject is Conventional. T001 checks for overlapping pull requests before the branch. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/0/4/4/2/1/3736-e2e-job-stops-reporting/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      e2e-diagnostic-files.md
    checklists/
      requirements.md
      ci-workflow.md
```

### Source Code (repository root)

The implementation touches the files in the change map below. No other file changes.

## Architecture

The flow for each E2E item runs in this order.

1. The session starts. The E2E plugin object opens `test-artifacts/e2e-stack-dumps.txt` once and keeps the file open.
2. For each item, the protocol hook appends a `protocol_start` record to the phase trail.
3. The hook arms the watch. The watch runs `faulthandler.dump_traceback_later` with the threshold (100 seconds by default) and the open file.
4. The hook yields. Pytest runs the logstart, setup, call, teardown, and logfinish steps. The existing logreport hook appends one record for each phase.
5. The hook cancels the watch and appends a `protocol_end` record.
6. If an item runs longer than the threshold, the watchdog thread writes the stacks of all threads to the dump file. The main thread does not participate.
7. In CI, the shard diagnostics step uploads the log, the trail, and the dump file when the shard fails or is cancelled.

The per-test budget and the teardown budget keep their current behavior. The watch does not replace or cancel the pytest-timeout timer.

## File-by-File Change Map

| Path | Action | Purpose | Tasks |
| - | - | - | - |
| `tests/e2e/conftest.py` | Modify | Add the `StackDumpWatch` class, the plugin registration, the boundary records in `PhaseTrailWriter`, and the protocol hook. Keep `E2E_TIMEOUT_SECONDS = 120` unchanged. | T003, T004 |
| `.github/workflows/ci.yml` | Modify | Add `test-artifacts/e2e-stack-dumps.txt` to the shard diagnostics paths. Reword the cancel message at lines 948 to 952. | T005, T006 |
| `tests/guardrails/test_e2e_shard_partition.py` | Modify | Add three workflow contract tests for the diagnostics path, the upload condition, and the cancel message. | T007 |
| `tests/guardrails/e2e_timeout_budget/test_timeout_budget.py` | Modify | Add four behavior tests for the watch and the boundary records. | T008 |
| `documentation/quality-gates.md` | Modify | Add the shard rows, the job limits, the effective per-test budget, and the diagnostics artifact. | T009 |
| `changelog.d/issue-3736-e2e-stall-diagnostics.md` | Add | Add the release note for one `Changed` entry. | T010 |
| `specs/numbered/0/0/1/0/4/4/2/1/3736-e2e-job-stops-reporting/` | Add | Add this specification record. The record ships in the same pull request. | T-PR |

No file is deleted.

## Dependencies

No dependency is added. The change uses the standard library `faulthandler` module and the existing pins for pytest and pytest-timeout.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| A slow but healthy item writes dump text. | The dump goes to a file only. The item outcome does not change. The threshold stays above the observed normal shard item durations. |
| The phase trail grows by two lines for each item. | The growth is about 1,200 lines for each shard. The trail stays in the artifact only. |
| The diagnostic file cannot open. | The session stops before the first item, and the error names the path (contract, failure behavior). |
| Another module installs a `faulthandler` watch and replaces this one. | Research shows no other `faulthandler` use in the searched paths (section 7). The guard tests fail if a later change adds one in the E2E harness. |
| The shard `ci.yml` edit conflicts with the planned WAN upload of #4208. | T001 checks the open pull requests. The branch rebases on `main` before the push. |
| The stall recurs before the dump proves the cause. | The watch records the stacks at 100 seconds. The stalled item appears in the trail. A repair follows the evidence, and D-5 keeps the signal method until then. |
| The cancel message still conflates two causes. | The reworded message names both causes. The guard test fails if either cause is removed. |

## Rollback Steps

1. Create a revert branch from `main`. Do not force-push and do not run `git reset --hard`.
2. Revert the squash commit of the pull request. The revert removes the watch, the boundary records, the diagnostics path, the cancel message, the documentation rows, and the changelog fragment.
3. Confirm that `.github/workflows/ci.yml` again has the diagnostics paths at lines 943 to 946 and the original cancel message at line 952.
4. Confirm that `tests/e2e/conftest.py` again has no `StackDumpWatch` class.
5. Delete the local `test-artifacts/e2e-stack-dumps.txt` file on each runner. The file is ignored by Git, and the runner discards it.

## Contracts

The contract folder holds one file, `design/contracts/e2e-diagnostic-files.md`. It defines the trail record fields, the dump format, the invariants, and the failure behavior.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| `changelog.d/` has 335 children. | The repository requires one fragment for each change (Principle I permits it). | The debt predates this change. Consolidation is a separate action (T012). |
