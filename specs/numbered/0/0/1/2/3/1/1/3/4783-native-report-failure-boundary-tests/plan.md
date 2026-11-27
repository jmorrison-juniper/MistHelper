# Implementation Plan: Native Report Failure-Boundary Tests

**Branch**: `fix/4783-native-report-failure-boundary-tests` (proposed). Cut it from main only, after decision D-2 is recorded.

**Date**: 2026-11-26

**Spec**: `spec.md` in this folder. Route: `specs\numbered\0\0\1\2\3\1\1\3\4783-native-report-failure-boundary-tests`.

**Input**: Numeric specification from `specs/numbered/0/0/1/2/3/1/1/3/`. The route is the base-5 digits of 4783, padded to eight levels (research R14).

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Supporting files stay under `design/`.

## Summary

The chain adds three hardware test modules that the test-quality gate rejects. Two boundary tests stay invisible to the detector, because they call a class staticmethod. This plan turns the report helper into a module-level source-driving helper. It also enters the empty-body case at the product byte boundary. The baseline, the settings file, and all product code stay unchanged.

## Technical Context

- **Language and version**: Python 3.15 or newer, as `.github/copilot-instructions.md` requires.
- **Primary dependencies**: pytest 9.2.0 and misthelper-devtools pinned at `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` (research R11).
- **Storage**: None. The tests write only under the pytest `tmp_path` folder.
- **Testing**: pytest, the pinned `test-quality-analyzer`, and `symbol-diff`.
- **Target platform**: Windows 11 for local runs. Linux runs the CI jobs (`ci.yml` sets `ubuntu-latest`).
- **Project type**: Python command-line tool and web portal.
- **Performance goals**: The unit shard took 1179.3 seconds on 2026-09-17, as `copilot-instructions.md` records.
- **Constraints**: No product change. No baseline or settings change. ASCII log text only.
- **Scale**: Three hardware test modules, one helper, and seven planned pytest cases.

## Constitution Check

Each rule has a result and a reason. The rules are in `.specify/memory/constitution.md` version 1.9.0.

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule, directories | Fail, recorded | The chain makes `tests/unit/websocket_streams/web/hardware/` hold six children (research R15). This change adds no child. The debt is recorded in this plan and in `analysis.md`. FR-016 tracks the fix. |
| I. Five-item rule, functions | Pass | `create_report_run` has four parameters and fewer than 25 lines. T-LOCAL-GATES re-checks the line count. |
| II. Class-based architecture | Pass | The helper is not a wrapper. It builds fixture state and calls source. Precedent: `make_batch_service` is a module-level helper on main (research R27). |
| III. Safety-first input | Pass | No `input()` call is added. Tests write only under `tmp_path`. No secret is used. |
| IV. Full deployment pipeline | Pass with exception | Steps 10 to 12 do not run. `container-build.yml` runs only for product files (research R46). The pull request body records this exception. |
| V. Observability | Pass | Every new log message is ASCII. |
| VI. Inline comments | Pass | FR-013 requires an inline comment on each changed line. |
| VII. Action logging | Pass | The helper logs before and after the publication action (decision D-6). Repository tests carry no other logging. |
| Mist Cloud transport | Not applicable | No mistapi call or WebSocket transport is added. |
| Container and ports | Not applicable | No compose, port, or container change. |
| Data directory | Pass | Test evidence uses `tmp_path`, not `data/`. |
| Documentation | Pass | No behavior changes, so no README update. The changelog fragment is added (FR-015). |
| Release notes | Pass | One fragment is added under `changelog.d/`. |
| Specification | Pass | The change touches three or more files, so this spec is required. |
| Branch and stacking | Pass with dependency | The branch starts from main only. It waits for D-2 and task T001 (FR-014). |

## Architecture

The detector reads three inputs for each test module (research R32 to R36):

1. **Risk.** Imports from repository source decide whether the module is in scope.
2. **Coverage source.** Only source-driving tests become coverage evidence. A test is source-driving when it calls an imported source name or a module-level helper that calls source.
3. **Markers.** Literal text in the coverage source decides each failure mode. The empty-body marker is `b""`, and the malformed-JSON marker is `JSONDecodeError` (research R37, R38).

The two report boundary tests call `ReportRun.create`, a class staticmethod. The detector does not bridge that call, so the markers in those tests do not count (research R35). The fix has two parts:

- Replace the class with a module-level helper, so the test calls a source-driving name.
- Put a real `b""` into the empty-body test, at the decoder boundary (FR-002).

The helper keeps the existing signature shape. Its body moves the identity and ledger setup into `_synthetic_identity`, so the helper stays within 25 lines.

## File-by-File Change Map

| Path | Action | Change |
| - | - | - |
| `tests/unit/websocket_streams/web/hardware/test_report.py` | Modify | Replace `class ReportRun` (line 37 at the chain tip) with `_synthetic_identity` and `create_report_run`. Add `import logging` and `_LOGGER`. Add `HardwareXmlSupport` to the preset import. Rewrite the empty-body test (line 83) to pass `b""` through the decoder. Keep the malformed-JSON precondition (line 96) and rename its call. |
| `tests/unit/websocket_streams/web/hardware/test_normalization.py` | Modify | Restore `test_empty_body_cannot_become_zero_module_inventory` to `normalize("", native_format)` and remove the marker-only `b""` decode (line 83). Add `test_empty_raw_reply_is_refused_at_byte_boundary`. Add `HardwareXmlPreset` and `HardwareXmlSupport` to the preset import (lines 14 to 16). Keep the cause assertion (line 92). |
| `tests/unit/websocket_streams/web/hardware/test_contracts.py` | Modify | Rename the import (line 24) and the call (line 120) to `create_report_run`. Keep `assert manager.started is True` (line 59). |
| `tests/unit/websocket_streams/web/hardware/test_cli.py` | Modify | Rename the import (line 25) and the call (line 177) to `create_report_run`. |
| `changelog.d/issue-4783-native-report-failure-boundary-tests.md` | Add | One `### Fixed` heading and one bullet that names #4783. |
| `specs/numbered/0/0/1/2/3/1/1/3/4783-native-report-failure-boundary-tests/` | Add | Copy this record into the repository at the route in T-PR. |

The change renames 17 occurrences in `test_report.py`, two in `test_contracts.py`, and two in `test_cli.py` (research R16 and the chain grep).

Unchanged paths: everything under `src/`, `MistHelper.py`, `.github/test-quality-baseline.json`, `.github/test-quality-config.toml`, `.github/workflows/ci.yml`, `requirements.txt`, `requirements-dev.txt`, `documentation/`, and `README.md`.

## Planned Test Cases

The changed or new cases are seven pytest cases. Each one has a requirement.

| Case | Requirement |
| - | - |
| `test_normalization.py::test_empty_raw_reply_is_refused_at_byte_boundary[xml]` and `[json]` | FR-001, FR-002 |
| `test_normalization.py::test_empty_body_cannot_become_zero_module_inventory[xml]` and `[json]` | FR-001, FR-002 |
| `test_report.py::test_empty_body_refuses_native_publication_and_report[xml]` and `[json]` | FR-001, FR-002, FR-005, FR-006 |
| `test_report.py::test_malformed_json_refuses_report_and_preserves_native` | FR-004, FR-006 |

The malformed-JSON normalizer case keeps its chain-tip form and does not change in this plan. It still meets FR-003.

## Contracts

The `design/contracts/` folder is omitted. This change alters no menu, CLI, output column, or API shape. The helper signature is internal to the test modules.

## Dependencies

- No new package and no version change.
- The pinned analyzer and `symbol-diff` are pinned in `requirements-dev.txt` line 197.
- The chain must already exist on GitHub (T001).

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| The chain is not on GitHub, so no branch can start. | T001 checks GitHub first. Decision D-2 names the owner action. |
| The rebase onto main conflicts. Main is 73 commits ahead of the chain base `ac046837b2bef943f0edbcd3298456265d7014fe`. | Rebase in a worktree. Resolve each file. Rerun T-LOCAL-GATES after the rebase. |
| The gate still reports a finding after the change. | Read the finding. Fix the test, not the baseline. Escalate to the devtools follow-up if the cause is the analyzer. |
| A new helper triggers a new rule. | T-LOCAL-GATES runs the full gate on the changed scope. |
| `symbol-diff` exits 1 for the rename. | Record the output in the pull request. CI has no symbol job. `documentation/quality-gates.md` lines 3 to 9 list every CI job. |
| Reviewers reject the helper as analyzer-driven. | FR-002 and FR-006 require a real boundary. The assertions stay the same. D-1 records the reason. |
| A partial feature reaches main. | Decision D-2 is human. The default stays off. |
| Principle IV steps 10 to 12 do not run. | The pull request body records the exception (research R46). |

## Rollback Steps

1. If main fails after the squash merge, open a revert pull request. Do not force-push.
2. If a rename breaks an import, restore `class ReportRun` from commit `07cf3eec5` on a new branch from main.
3. Do not delete the chain commits until the pull request merges.

Warning: deleting local chain commits `58ab484ba` or `07cf3eec5` removes the only copy of these tests.

## Project Structure

```text
specs/numbered/0/0/1/2/3/1/1/3/4783-native-report-failure-boundary-tests/
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
      analyzer-gate.md
```

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| Six children in `tests/unit/websocket_streams/web/hardware/` | The chain creates the folder. This change edits its files and adds no child. | Moving files now would widen the scope to a second concern. FR-016 tracks the move. |
| Module-level helper in a test module | The detector bridges only module-level helpers (research R35). | A class staticmethod stays invisible to the detector. Duplicated setup in two tests adds about 20 lines of copy. |
