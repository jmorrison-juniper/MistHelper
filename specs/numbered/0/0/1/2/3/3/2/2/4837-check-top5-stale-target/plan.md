# Implementation Plan: Top-Five Complexity Target Map

**Branch**: `fix/4837-check-top5-stale-target` | **Date**: 2026-11-26 | **Spec**: `spec.md` in this folder

**Input**: Numeric specification from `specs/numbered/0/0/1/2/3/3/2/2/4837-check-top5-stale-target/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

The utility holds a target map. The map names one file, `MistHelper.py`, for five target functions. Four targets now live in other source files on main. The fix changes the map so that each target names its current file. Three guard tests check the map and the utility result. No runtime module changes.

## Technical Context

**Language/Version**: Python 3.15 or newer (R44).

**Primary Dependencies**: radon 6.0.1 (R22), pytest, and the standard library modules `ast`, `json`, `pathlib`, and `subprocess`. No new dependency.

**Storage**: Not applicable. The utility writes no file during a run.

**Testing**: pytest in `tests/integration/test_top5_compatibility_paths.py`, plus the local gates in `design/quickstart.md`.

**Target Platform**: Windows 11 for local development. CI runs its radon gate on `RADON_PATHS` only (R18, R19).

**Project Type**: A developer utility script with pytest guard tests.

**Performance Goals**: Each radon run stops after 300 seconds. This bound already exists (R02).

**Constraints**: Paths resolve from the working directory. The change keeps the module-level names that existing tests use (R16).

**Scale/Scope**: One script, one test module, one changelog fragment, and one spec record.

## Constitution Check

*Gate: passes before research. Re-checked after design: passes, with existing debt recorded.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule (R37) | Pass, with existing debt | The record adds one child at the last route level. Each level keeps five children or fewer (R32). `main()` holds seven logical blocks and 26 lines. This change does not touch `main()`. |
| II. Class-based architecture (R38) | Fail, existing debt | The utility uses module-level functions. This change edits only the target map. A follow-up issue records the remediation. |
| III. Safety-first | Pass | The utility reads no keyboard input and prints no secret. |
| IV. Full deployment pipeline (R40) | Pass, with steps 10 to 12 not triggered | Steps 1 to 9 run. Container build runs only for product paths (R21). Decision D-10 records the reason. |
| V. ASCII logs | Pass | Output lines and new messages use ASCII characters only. |
| VI. Inline comments | Pass for touched lines | Each changed line of the target map has an inline comment. Each executable line of the new tests has one. Untouched existing lines stay as they are, and the debt is recorded. |
| VII. Action logging | Not applicable to the change, with existing debt | The change adds no production action. The utility has no action logging today. A follow-up issue covers it. |
| File paths (R39) | Pass | Each new map key uses `pathlib.Path`. The one literal key has no separator. |
| Container runtime | Not applicable | The utility runs on the host. No container starts. |
| mistapi | Not applicable | The utility calls no Mist API. |
| Dependencies | Pass | No dependency changes. radon stays at 6.0.1 (R22). |
| Documentation: release notes (R41) | Pass | One changelog fragment is added (D-9). |
| Specification escalation (R34) | Pass | The change touches four paths, so a spec record exists. |
| Multi-agent git workflow | Pass, planned | Issue first. Branch `fix/4837-check-top5-stale-target`. Conventional Commit subject. The pull request body contains `Closes #4837`. |

## Architecture

```text
TARGETS (target map: file path -> target names)
  -> for each file: _run_radon(file)     one radon run per file, 300-second bound
  -> records: file, name, complexity, rank, line
  -> lookup by file suffix and bare name (R46)
  -> target rows -> PASS (exit 0) or FAIL (exit 1)
```

Radon 6.0.1 names each method by its bare name (R25). It keys each file by the path that the utility passes (R23). The lookup therefore needs both the file key and the bare name.

## File-by-File Change Map

| Path | Action | Change |
| - | - | - |
| `scripts/check_top5_complexity.py` | Modify | Replace the single `MistHelper.py` key in `TARGETS` (lines 14 to 22) with four keys. Each key names the current file of its targets. Add an inline comment to each line of the block. |
| `tests/integration/test_top5_compatibility_paths.py` | Modify | Add three guard tests after the two existing tests. Add an inline comment to each executable line. |
| `changelog.d/issue-4837-check-top5-stale-target.md` | Add | One `###` heading and one `Fixed` bullet that names issue #4837. |
| `specs/numbered/0/0/1/2/3/3/2/2/4837-check-top5-stale-target/` | Add | The spec record copied from the draft folder. |

Not changed: `MistHelper.py`, `src/`, `.github/workflows/`, `requirements-dev.txt`, `documentation/`, and `README.md`.

Documentation: no page names the utility. A local search of `documentation/`, `README.md`, and `.github/` found no reference. Research.md lists the search scope.

Proposed target map block:

```python
TARGETS = {
    "MistHelper.py": [  # Entry point that owns the bootstrap check
        "early_dependency_check",  # Public entry point in MistHelper.py
    ],
    str(Path("src", "operations", "execution", "capture", "packet_capture.py")): [  # Packet capture manager methods
        "_execute_site_capture_loop",  # Method of PacketCaptureManager
        "start_org_packet_capture",  # Method of PacketCaptureManager
    ],
    str(Path("src", "operations", "exporting", "export", "org_alarm_event_exporter.py")): [  # Static method holder
        "device_events_52w",  # Static method of OrgAlarmEventExporter
    ],
    str(Path("src", "mist", "resources", "gateway", "gateway_export_utils.py")): [  # Static method holder
        "with_wan_overrides",  # Static method of GatewayExportUtils
    ],
}
```

New guard tests:

- `test_top5_target_files_define_each_target` parses each mapped file with `ast`. It asserts that each target name is a defined function. Its message names the file and each missing target. Covers FR-001 and FR-004.
- `test_top5_check_runs_to_a_result_on_current_sources` changes to the repository root and runs `main()` with real radon. It asserts a return value of 0 or 1. Covers FR-002.
- `test_top5_check_returns_zero_and_one_for_pass_and_fail` replaces `_run_radon` with a stub. The stub gives CC 1 to every target, then CC 11 to one target. It asserts return values 0 and 1. Covers FR-003.

## Dependencies

- Runtime: none added. radon 6.0.1 is already pinned (R22).
- Test: pytest. The module already imports `MistHelper` (R14), so the new tests add no import cost.
- Process: the local gates in `design/quickstart.md` and the CI checks in task T-REMOTE-CI.

## Risks and Mitigations

- Risk: a target has CC above 10, so the utility prints FAIL. Likelihood is low, because the CI radon gate passed on main (R18 to R20). Mitigation: record the actual result, open a follow-up issue, and keep the limit.
- Risk: radon keys a file differently on Windows. Mitigation: `pathlib.Path` builds each key. Task T004 and the real-run guard test check the result on Windows.
- Risk: a future move breaks the map again. Mitigation: the first guard test fails in pytest before merge.
- Risk: four radon runs take longer than one. Mitigation: each run keeps the 300-second bound. Task T004 records the run time.
- Risk: the test-quality analyzer flags a new test. Mitigation: run the ratchet before the push. Fix each new finding. Do not edit the baseline to hide a finding.
- Risk: reviewers expect a `pr-<number>.md` fragment name. Mitigation: D-8 explains the name in the pull request body.

## Rollback Steps

1. Open a revert pull request that restores the previous single-key `TARGETS` block.
2. Remove the three guard tests from `tests/integration/test_top5_compatibility_paths.py`.
3. Remove `changelog.d/issue-4837-check-top5-stale-target.md`.
4. Remove the spec record folder if the revert also drops the record.
5. Run the local gates in `design/quickstart.md` on the revert branch.

Caution: the reverted utility raises the missing-target error again. Use the rollback only when the fix causes a new failure.

## Complexity Tracking

Existing violations that this change does not touch. Each row names its follow-up remediation.

| Violation | Why it stays | Simpler alternative rejected because | Remediation |
| - | - | - | - |
| `main()` holds seven logical blocks and 26 lines (R26 rules, Principle I) | The defect sits in the map, not in `main()`. | Splitting `main()` widens the diff and changes review scope. | Follow-up issue to split `main()`. |
| `main()` estimated CC 13 (R26 rules, U-2) | The CI radon gate excludes this file (R18). | Refactoring for CC needs its own issue. | Follow-up issue, with the local complexity output as evidence. |
| Module-level functions instead of a class (Principle II, R38) | Converting to a class renames names that the timeout test uses (R16). | A class conversion is a refactor, not a fix. | Follow-up issue to move the utility into a class. |
| No action logging (Principle VII, R36) | Logging changes the output contract documented in `design/contracts/top5-cli.md`. | Adding logs without review changes operator-visible output. | Follow-up issue with a logging design. |
| Existing lines in `main()` and `_run_radon` lack inline comments (Principle VI, R35) | The touched block is the map only. | Commenting untouched code widens the diff. | Follow-up issue with the class conversion. |
