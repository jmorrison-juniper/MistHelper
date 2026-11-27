# Implementation Plan: WLAN fixture host teardown

**Branch**: `fix/4492-wlan-fixture-host-teardown` | **Date**: 2026-11-26 | **Spec**: `specs\numbered\0\0\1\2\0\4\3\2\4492-wlan-fixture-host-teardown\spec.md`

**Input**: Numeric specification. The route comes from `.specify\scripts\powershell\spec-route.ps1` (R-51, R-52) and the rule that numbered records use the eight-level base-5 route (R-61).

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, and checklists under `design\`. This record omits the `contracts\` folder (see Contracts).

## Summary

Restore the resolver host in the `fake_mh` fixture. Add one `info` log line and one `debug` log line. Shift seven WLAN baseline line numbers by four. Change no production code.

## Technical Context

- **Language/Version**: The interpreter in the repository `.venv`. This record does not measure its version.
- **Primary Dependencies**: pytest 9.2.0 (`.venv\Lib\site-packages\_pytest`, R-37). mistapi 0.64.1, used through mocks only (R-39). misthelper-devtools 0.6.4, which supplies the analyzer (R-24).
- **Storage**: Not applicable. The change writes no product output.
- **Testing**: pytest with the `fake_mh` fixture and the autouse fixtures in the root conftest (R-14).
- **Target Platform**: Windows 11 for local runs. Ubuntu 24.04 for CI runners (job log, R-42).
- **Project Type**: Command-line tool with a pytest suite.
- **Performance Goals**: The CI root-units run took 1080.82 seconds on the PR branch (R-41).
- **Constraints**: Baseline keys include line numbers (R-24). Ruff and Black use a 120-character line length (R-35, R-36).
- **Scale/Scope**: Two modified files and one record folder.

## Constitution Check

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule (R-63) | Pass | The deepest existing parent, `specs\numbered\0\0\1\2`, holds five children. The route reuses child `2` (R-49). Each route directory keeps five children or fewer. |
| II. Class-Based Architecture (no wrappers) | Pass | The change adds no function and no class. |
| III. Safety-First | Pass | The change adds no input handling and no destructive operation. |
| IV. Full Deployment Pipeline | Pass | Steps 1 to 9 map to T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. Steps 10 to 12 run after the merge (T-MERGE). |
| V. Observability and Logging | Pass | Both new log messages use ASCII text. |
| VI. Inline Comments (R-64) | Pass | Each changed executable line carries an inline comment (FR-005). |
| VII. Action Logging (R-65) | Pass | One `info` line precedes the bind. One `debug` line follows the restore (D-3). |
| Technology: mistapi only | Pass | The change makes no REST call. |
| Technology: test containers | Not applicable | The local gates run on the host `.venv` (R-57). No container starts. |
| Technology: file paths | Not applicable | The change adds no path code. |
| Data directory and secrets | Pass | The change writes no output file and no secret. |
| AGENTS rule on leaking tests (R-53) | Pass | The leaking fixture receives the repair. No other test changes (D-7). |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/0/4/3/2/4492-wlan-fixture-host-teardown/
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
      verification.md
```

### Source Code (repository root)

```text
tests/unit/refactors/test_wlanradius_timer_manager_paths.py   modify: fixture lines 44-46 become lines 44-50
.github/test-quality-baseline.json                            modify: seven line_number values
```

**Structure Decision**: Edit one fixture in one test file. Update seven integers in the baseline file. Add the record folder. No other path changes.

## File-by-File Change Map

| Path | Action | Change |
| - | - | - |
| `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` | Modify | Replace lines 44 to 46 with the block in Implementation Outline. The net change is +4 lines. Lines 37 to 43 and line 47 onward keep their content. |
| `.github/test-quality-baseline.json` | Modify | Change seven `line_number` values: 351 to 355, 694 to 698, 729 to 733, 737 to 741, 807 to 811, 817 to 821, and 841 to 845. |
| `specs\numbered\0\0\1\2\0\4\3\2\4492-wlan-fixture-host-teardown\` | Add | The record folder described in Project Structure. |

## Implementation Outline

1. Keep lines 37 to 43 unchanged.
2. Replace lines 44 to 46 with this block. The block occupies lines 44 to 50 after the edit.

```python
    logging.info("Binding the fake MistHelper host for one test")  # Log before the bind so a leak is traceable.
    with (  # Enter both patches together, so teardown restores each value.
        patch.dict(sys.modules, {"MistHelper": fake}),  # WHY: the proxy imports by name.
        patch.object(_MH, "_root_module", fake),  # WHY: restore the previous resolver host at teardown.
    ):
        yield fake  # WHY: the test body runs with the fake in place.
    logging.debug("Restored the previous resolver host after the test")  # Log after the restore.
```

3. Remove the original `_MH.bind_root_module(fake)` line. Its replacement is the `patch.object` line.
4. Shift the seven baseline values listed in the change map.
5. Run the gates in `design\quickstart.md`. Commit, push, open the pull request, and watch CI.

Caution: do not commit the mutation proof in quickstart Scenario 4. Restore the line before the commit.

## Dependencies

- No new runtime or development dependency.
- The gates use `pytest`, `ruff`, `black`, `symbol-diff`, `test-quality-analyzer`, and `pytest-chunks` from the repository environment.

## Architecture

```text
Session start
  conftest.py preloads MistHelper.py as sys.modules["MistHelper"]   (R-12, R-14)
  MistHelper.py calls MainEntrypoint.bind_host_module(module)       (R-12, R-13)
  resolver _root_module = real MistHelper module                     (R-04, R-13)

Each WLAN test that uses fake_mh
  setup     patch.dict sets sys.modules["MistHelper"] to the fake host
            patch.object sets the resolver _root_module to the fake host
  body      resolver.root_module() returns the fake host
  teardown  patch.object restores the real module, then patch.dict restores sys.modules
```

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| Black changes the line count of the new block. | Re-measure the delta and update the seven baseline values to the measured delta (U-8). |
| A baseline value misses its shift. | Run the test-quality gate and expect zero new findings (SC-003). |
| Another failing test has a second cause. | Run both shard orders (T005, T006). File a new issue for any residual failure (D-7). |
| The restore line regresses in a later edit. | The mutation proof (T004) shows that the named tests fail without it. |
| The new log lines change test output. | The new lines only log. They do not change any assertion. |
| Reviewers use the stale issue path. | The PR body names the main path and the absent issue path (R-02). |

## Rollback Steps

1. Restore lines 44 to 46 of the fixture to the original three lines: the `with patch.dict` line, the `bind_root_module` line, and the `yield` line.
2. Restore the seven baseline values to 351, 694, 729, 737, 807, 817, and 841.
3. Revert the record commit if the record must leave the branch.
4. Rerun the test-quality gate and the three-node sequence.

## Contracts

Not applicable: no interface contract applies. The change alters test setup only. The record omits the `design\contracts\` folder.

## Complexity Tracking

Not applicable: the Constitution Check has no violation that needs justification.
