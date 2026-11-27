# Implementation Plan: Dash module isolation for map callback tests

**Branch**: `4731-dash-module-isolation` | **Date**: 2026-11-26 | **Spec**: spec.md

**Input**: Numeric specification at `specs/numbered/0/0/1/2/2/4/1/1/4731-dash-module-isolation/spec.md`.

Keep spec.md, plan.md, and tasks.md at the feature root. Place research, data model, quickstart, and checklists under design/. The contracts folder is omitted. The change adds no menu, CLI, output, or API shape.

## Summary

Four callback test files install a Dash stub at import time. Their fixtures save the stub, not the Dash entry that existed before collection. The stub remains after collection and breaks later imports of Dash.

Each slice removes the import-time install. Each slice rewrites its autouse fixture to record and restore the exact prior entry. Two slices also replace weak non-None assertions named in the issue. No source file changes. Each slice becomes one pull request, and publication stays serial.

## Technical Context

**Language/Version**: Python, from the project virtual environment in `.venv`.

**Primary Dependencies**: dash (installed in `.venv`, research row R27) and pytest. The local gates use ruff, black, test-quality-analyzer, symbol-diff, and bandit (research row R33).

**Storage**: Not applicable. The change does not touch data.

**Testing**: pytest for the `tests/maps` package. Lint, format, symbol, and test-quality gates run locally before each publication (quickstart QS-08 to QS-12).

**Target Platform**: Windows development host. CI runs `tests/maps` in the root-and-contracts shard (research row R30).

**Project Type**: Test-only change inside the existing `tests/maps` package.

**Performance Goals**: Not applicable. The change adds no subprocess and no network call.

**Constraints**: No source change. No baseline change. No new module-level name (symbol gate, research row R29). No new child in any folder or module (constitution Principle I, research row R39).

**Scale/Scope**: Four test files. Each file changes one fixture body and its module-level install. Two files also change one or two assertions.

## Constitution Check

*Gate result: Pass for each rule except Principle IV steps 10 to 12, which carry a documented exception (U-1).*

| Rule | Result | Reason |
| - | - | - |
| Principle I, five-item rule (R39) | Pass | The change adds no child to any folder or module. Each fixture stays within five blocks and 25 lines. Existing test modules hold more than five top-level names. Complexity Tracking records this as grandfathered debt. |
| Principle I, managed roots and base-5 route (R40) | Pass | ROUTE `specs\numbered\0\0\1\2\2\4\1\1` equals the eight-digit base-5 value of 4731 (122411, padded with zeros). The record folder is the only child of the route leaf. |
| Principle II, class-based architecture (R60) | Pass | The fixtures stay as existing test functions. The change adds no wrapper function. |
| Principle III, safety-first (R61) | Pass | The change adds no input, no secret, and no external call. The stub replaces no network client. |
| Principle IV, full deployment pipeline (R41) | Fail, documented exception | Steps 1 to 9 apply to each slice. Steps 10 to 12 do not run. The container build ignores changes under `tests/` (research row R32). Decision D-10 and unresolved item U-1 record this. |
| Principle V, ASCII logging (R62) | Pass | Log messages use ASCII text and `%s` arguments (FR-014). |
| Principle VI, inline comments (R42) | Pass | Each changed line carries an inline comment (FR-015). |
| Principle VII, action logging (R43) | Pass with scope reading | The fixture changes interpreter state. The fixture logs before and after each change (FR-014). Test assertions do not perform an action, so they get no logs (D-9). Wave E1 lacks logs. See finding F-05 in analysis.md. |
| Technology and compatibility (R63) | Pass | No Mist API call changes. The change adds no container, no path string, and no data directory write. |
| Development workflow, syntax check (R64) | Pass | `python -m py_compile MistHelper.py` runs before each commit (quickstart QS-10). |
| Security findings (R65) | Pass | No security finding is suppressed. Bandit runs on `tests/maps` (quickstart QS-14). |
| Release notes (R44) | Pass | Each pull request adds one changelog fragment (FR-022). D-8 resolves the difference from the copilot rule (R49). |
| Complexity-driven SpecKit escalation (R66) | Pass | The work touches four files, so a specification is required. This record is that specification. |
| Multi-agent git and labels (R50, R67) | Pass | Each branch starts from main and uses the prefix `fix/4731-`. Each pull request carries the `bug` and `tests` labels. The issue keeps `in-progress`. |
| Governance (R45) | Pass | This plan follows the constitution where the copilot rule differs (D-8). |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/4/1/1/4731-dash-module-isolation/
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
      isolation.md
      publication.md
```

### Source Code (repository root)

| Slice | File | Action | Scope of the change |
| - | - | - | - |
| S1, wave A | `tests/maps/test_viewer_callbacks_wave_a.py` | Modify | Remove the module install at lines 40 to 44. Rewrite the fixture at lines 49 to 60. Yield the stub. Replace the checks at lines 134 and 181. Add the `_dash_stub` argument to the test at line 169. |
| S2, wave B/C | `tests/maps/test_viewer_callbacks_wave_b_c.py` | Modify | Remove the module install at line 48. Rewrite the fixture at lines 53 to 68. |
| S3, wave D | `tests/maps/test_viewer_callbacks_wave_d.py` | Modify | Remove the module install at line 46. Rewrite the fixture at lines 51 to 63. |
| S4, wave E2 | `tests/maps/test_viewer_callbacks_wave_e2.py` | Modify | Remove the module install at line 45. Rewrite the fixture at lines 50 to 62. Replace the checks at lines 174 and 178 inside the test at line 171. |
| Merged | `tests/maps/test_viewer_callbacks_wave_e1.py` | None | Merged through PR #4735. No change (FR-029). |
| Each PR | One file in `changelog.d/`, named `pr-` followed by the pull request number | Add | One fragment with one `### Fixed` heading and one bullet that names issue #4731. |

## Design

### Current state on main

- Waves A, B/C, D, and E2 each assign `sys.modules['dash']` at import time (research rows R02, R06, R08, R10).
- Each autouse fixture saves `sys.modules.get('dash')` at the start of the test. At that point the saved value is the import-time stub (research rows R03, R07, R09, R11).
- Restoring that saved value leaves the stub in place. A None entry also restores as absent, because the fixture tests `original is None`.
- Wave E1 merged a scoped helper that restores the entry after import (research rows R14 to R16). Its design differs from the four slices. See D-14.

### Target state for each slice

The target design uses the fixture only. The module no longer installs a stub at import time. Research shows that the launcher package does not import dash at module load (research rows R23, R24, R25, R26). The fixture installs the stub during each test and restores the exact prior entry afterward.

1. Remove the module-level assignment to `sys.modules['dash']` and its comment lines.
2. Keep `_build_dash_stub` and the launcher import unchanged.
3. Replace the fixture body with the target shown below.
4. Keep every other test function unchanged, except the assertion edits named in FR-007, FR-008, and FR-010.

Target fixture for wave A. Waves B/C, D, and E2 use the same body. Their fixtures already yield the stub, so only the body changes. Wave A changes the return type and the yield.

```python
@pytest.fixture(autouse=True)
def _dash_stub() -> Iterator[types.ModuleType]:
    """Per-test: install a fresh stub, then restore the exact prior dash entry."""
    import logging  # Local import adds no module-level name, which keeps the symbol gate clean
    dash_was_present = "dash" in sys.modules  # Tell an absent entry apart from a loaded or None entry
    original_dash = sys.modules.get("dash")  # Keep the loaded module object or the None entry
    logging.info("Installing a fresh dash test stub for one test")  # Log before the sys.modules change
    stub = _build_dash_stub()  # Build a fresh stub for this test only
    sys.modules["dash"] = stub  # Install the stub for the test body
    logging.debug("Installed the dash test stub")  # Log the result of the install
    try:
        yield stub  # Run the test with the stub active
    finally:
        logging.info("Restoring the dash entry that existed before this test")  # Log before the restore
        if dash_was_present:  # A loaded module or a None entry existed before the test
            sys.modules["dash"] = original_dash  # Restore the exact prior value, including None
        else:  # Dash was absent before the test
            sys.modules.pop("dash", None)  # Remove the stub and keep Dash absent
        logging.debug("Restored the dash entry, previously present: %s", dash_was_present)  # Log the result
```

### Assertion edits

- Wave A line 134 currently reads `assert record.bound_func is not None`. Replace it with an assertion that the bound value is a function or a bound method. Keep the line within 120 characters.
- Wave A line 181 currently reads `assert captured["html"] is not None`. Replace it with an identity check against `_dash_stub.html`. The test at line 169 then takes `_dash_stub` as an argument.
- Wave E2 lines 174 and 178 currently check that serializer and figure builder are not None. The test creates a named serializer and a named figure builder. It passes both into `_make_state`, and it asserts identity for each.

## Complexity Tracking

| Violation | Status | Why needed | Simpler alternative rejected because |
| - | - | - | - |
| Test modules hold more than five top-level names | Grandfathered | Existing structure of the callback test suite. The change adds no name. | Splitting the modules changes files outside the owner reservations. |
| Wave E1 fixture lacks action logging | Grandfathered | The slice merged in PR #4735. | Editing wave E1 breaks the owner reservation and the merged state. |
| Fixture body repeated in four files | New design, justified | Each file has one owner. A shared helper needs another file and serial merges. | A shared conftest touches an unreserved file. A helper module adds a module-level import, which the symbol gate rejects. |
| Principle IV steps 10 to 12 do not run | Documented exception | The container build ignores changes under `tests/` (research row R32). | A manual container build runs no new code for a test-only change. |

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| The test-quality baseline keys findings by line number (research row R28) | A moved finding counts as new, and the gate fails | Fix both wave A findings and both wave E2 findings, so no baseline finding remains in those files. Run quickstart QS-11 before publication. |
| Real dash loads during collection (unverified item U-1) | Later tests import the real Dash package | This result is correct. The stub no longer leaks. Quickstart QS-15 records the result. |
| Other `tests/maps` files change behavior under real dash (unverified item U-2) | A test fails in the directory run | Run `python -m pytest tests/maps` (QS-13) before publication. Investigate each failure before publication. |
| The symbol gate rejects the function-local import (unverified item U-4) | The local gate fails | The design adds no module-level name. Quickstart QS-12 confirms the result. |
| A held candidate commit reaches a branch | Duplicate regression cases and new module-level names reach main | Do not rebase, amend, or push a held candidate commit (FR-027). Decision D-2 explains why the candidates are not reused. |
| The owner hold delays the work | Publication slips | Finish and verify all four slices locally first. Publish each slice when the owner releases the hold. |
| A future test file repeats the leak | The defect returns | Recommend a follow-up guard issue after the final slice merges. See D-3. |

## Rollback Steps

1. Before a merge, close the unmerged pull request and keep its branch. Record the preservation proof in the closing comment.
2. After a merge, create a new branch from main. Restore the previous fixture with a new commit. Open a new pull request with `Refs #4731`.
3. Caution: A failed rebase leaves conflict markers in the file. Abort the rebase before you retry.
4. Warning: Do not force-push a branch that another agent shares. Other agents lose the commits that they built on.
