# Implementation Plan: RADIUS API Failure Test Assertion

**Branch**: `fix/4798-radius-api-failure-test-assertion` (fallback route only) | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric specification from `/specs/numbered/0/0/1/2/3/1/4/3/4798-radius-api-failure-test-assertion/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Add one assertion to the target test. The assertion reads the failure line that the production error branch prints. The change touches one test module only. The baseline and the production code stay unchanged. The assertion commit `843be63` already exists in PR #4208. That commit lacks the inline comments that the constitution requires. A follow-up commit on the same PR adds them.

## Technical Context

**Language/Version**: Python 3.15.2. The issue environment names this version.

**Primary Dependencies**: mistapi 0.64.1 is installed in `.venv`. `pyproject.toml` line 29 pins `mistapi>=0.64.1,<0.65` (research RC-38). `requirements-dev.txt` line 197 pins misthelper-devtools to commit `2239e7bd` (research RC-22).

**Storage**: Not applicable. The change writes no data.

**Testing**: pytest in `.venv`. The gates are ruff, black, bandit, symbol-diff, and test-quality-analyzer.

**Target Platform**: The issue reproduced on Linux or macOS. This record uses Windows 11 commands in PowerShell. On macOS or Linux, use the same commands with `.venv/bin/` in place of `.venv\Scripts\`.

**Project Type**: CLI tool with a pytest suite.

**Performance Goals**: Not applicable. The change edits one unit test.

**Constraints**: The baseline stays unchanged (FR-005). The line limit is 120 columns (`pyproject.toml` lines 202 and 559, research RC-39 and RC-40). Only one open pull request may change the test module (`AGENTS.md` line 245, research RC-44).

**Scale/Scope**: One test method in one module. The change adds one assertion line and three comment-only edits.

## Constitution Check

*GATE: Must pass before implementation. Re-check after the follow-up commit.*

| Rule | Result | Reason |
| - | - | - |
| Five-Item Rule (Principle I) | Pass | The change adds no directory child. The changed method has three parameters. Its body has one `with` block. |
| Class-Based Architecture (Principle II) | Pass | The change edits an existing test method in its class. It adds no wrapper function. |
| Safety-First (Principle III) | Pass | The change adds no input, no destructive operation, and no secret. |
| Full Deployment Pipeline (Principle IV) | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover each step. No task pushes to `main`. |
| Observability and Logging (Principle V) | Pass | The assertion text is ASCII. The change adds no log line. |
| Inline Comments (Principle VI) | Fail at PR head, Pass after T001 | The PR head lacks comments on lines 707, 710, and 712 (research RC-06, analysis A-9). The follow-up commit adds them. |
| Action Logging (Principle VII) | Pass | `AGENTS.md` line 107 defines an action as an external request, file output, database operation, data transform, or operator question (research RC-47). The mocked call in the target test is none of these. Decision D-5 records the reasoning. |
| Mist Cloud: mistapi only (Technology constraints) | Pass | The change sends no request. The test mocks `updateSiteWlan`. Production code calls the mistapi method (research RC-10). |
| Mist Cloud: owned WebSocket transport | Not applicable | The feature adds no transport. |
| File paths (Technology constraints) | Pass | The change adds no path code. |
| Test containers (Technology constraints) | Not applicable | No container starts for this change. The quickstart starts none. |
| Zscaler and container security | Not applicable | The change has no image, registry, or push step. |
| Security findings | Pass | The change adds no suppression comment. Scenario 5 of the quickstart runs bandit on the test module. |
| Documentation | Pass | The change alters no documented behavior. |
| Release notes | Pass | The change adds no user-visible behavior. The repository adds a fragment only for user-visible changes (research RC-36). |
| Issue first | Pass | Issue #4798 is open. It carries the `bug`, `tests`, and `in-progress` labels. |
| Branch name | Fail on existing PR, accepted | PR #4208 uses `jmorrison-juniper-4200-migrate-mistwanperformance`. `AGENTS.md` line 194 requires the type and issue form (research RC-45). Analysis item A-4 records the deviation. |
| PR body closure | Deviation, accepted by owner | PR #4208 says `Refs #4798`. `AGENTS.md` line 224 asks for `Closes`. The owner keeps issue #4798 open until merge (research RC-46, analysis A-3). |
| One open PR per file | Pass | Seven PRs are open. Only PR #4208 changes the test module (research section 2). |
| Specification escalation | Pass | The change touches one file and the cause is known. A specification is not required. The orchestrator requested this record. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/3/1/4/3/4798-radius-api-failure-test-assertion/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      operator-failure-message.md
    checklists/
      requirements.md
```

### Source Code (repository root)

```text
tests/
  unit/
    refactors/
      test_wlanradius_timer_manager_paths.py   (modify: target test, main lines 694-698)
src/
  foundation/
    support/
      refactors/
        wlanradius_timer_manager.py            (read only, no change)
.github/
  test-quality-baseline.json                   (read only, no change)
  test-quality-config.toml                     (read only, no change)
```

**Structure Decision**: One test module changes. The record uses the numeric route. The route for issue 4798 is base-5 digits `0\0\1\2\3\1\4\3`. The digits come from `4798 = 1x5^5 + 2x5^4 + 3x5^3 + 1x5^2 + 4x5^1 + 3x5^0`. The routine is in `.specify/scripts/powershell/spec-route.ps1` (research RC-48 and RC-49).

## File-by-File Change Map

| Path | Action | Change |
| - | - | - |
| `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` | Modify | Split the target header from one line into three lines. Add the `capsys: Any` parameter. Add one assertion. Add an inline `# WHY:` comment to the header closing line, the `with` line, and the assertion line. |
| `specs/numbered/0/0/1/2/3/1/4/3/4798-radius-api-failure-test-assertion/` | Add | This record. |

Target method after the change. The header uses the black split form that the file already uses for long signatures.

```python
    def test_an_api_failure_is_contained(
        self, manager: WLANRadiusTimerManager, capsys: Any
    ) -> None:  # WHY: capsys reads the failure line that the operator sees.
        """A raised error must not crash the menu after the confirmation."""
        manager.selected_wlan = {"id": "w1", "_inheritance_level": "site"}  # WHY: set the scope.
        with patch.object(manager, "_update_site_wlan", side_effect=OSError("no route")):  # WHY: fail the write.
            manager._apply_changes()  # WHY: the call must swallow the error.
        assert "Error applying changes: no route" in capsys.readouterr().out  # WHY: the operator must see the failure.
```

## Dependencies

- No new package. The module already imports `Any`, `patch`, and `WLANRadiusTimerManager`.
- Tools in `.venv\Scripts`: `python.exe`, `pytest.exe`, `ruff.exe`, `black.exe`, `bandit.exe`, `test-quality-analyzer.exe`, `symbol-diff.exe`, and `ste-linter.exe`. Their presence is verified (research section 4). Their versions are unverified (research section 7).

## Test Plan

| ID | Check | Method | Covers |
| - | - | - | - |
| TC-001 | The target test passes | pytest node run | FR-001, FR-002 |
| TC-002 | The target test fails when the print line is removed | Mutation in a worktree, then revert | FR-003, SC-003 |
| TC-003 | The target test fails when the printed text changes | Mutation in a worktree, then revert | FR-003, SC-003 |
| TC-004 | The module tests pass | pytest module run | FR-008, SC-002 |
| TC-005 | The scoped test-quality gate reports zero new findings | Required form with `--changed-from` | FR-004, SC-001 |
| TC-006 | The full-suite test-quality gate reports zero new findings | Full-suite form without `--changed-from` | FR-004 |
| TC-007 | The baseline content matches `main` | `git diff --quiet origin/main -- .github/test-quality-baseline.json` | FR-005 |
| TC-008 | The commit changes one file | `symbol-diff` and `git show --name-only` | FR-006, SC-004 |
| TC-009 | Lint and format pass | `ruff check .` and `black --check .` | FR-007, FR-008 |
| TC-010 | One open PR changes the module | `gh pr list` file check | FR-009 |
| TC-011 | Record counts match | Count check against the Metrics section of `analysis.md` | FR-010 |

## Risks and Mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| R-1: PR #4208 is a draft and its merge state is DIRTY (analysis A-2) | The merge waits | The owner converts the PR and resolves conflicts. T-MERGE stays open until then. |
| R-2: The PR head lacks inline comments (analysis A-9) | Constitution failure and review block | The follow-up commit in T001 adds the comments. T-REMOTE-CI reruns the checks. |
| R-3: A line shift occurs above the target test without the assertion (analysis A-1) | A new finding returns | Keep the assertion. Keep module changes in one PR. Follow-up issue for the analyzer key. |
| R-4: The production failure text changes | The target test fails | This is intended. Change the contract file and the test in one commit. |
| R-5: The full-suite check reports new findings in another module | The gate fails for that module | Stop and report. Do not change the baseline. |
| R-6: PR #4208 closes without merge | The fix needs a new route | Open the fallback PR only after #4208 closes. Never keep two open PRs for the module. |

Warning: a force push can delete commits that no other copy holds. Do not force-push the PR branch.

## Rollback Steps

1. Before merge, run `git revert` on the follow-up commit and on the assertion commit. Push the reverts to the PR branch. Do not force-push.
2. After merge, run `git revert` on the squash commit that the merge created on `main`. The gate then returns to the `main` state, which reports zero new findings.
3. Run `git worktree remove` for each worktree that the quickstart creates.

## Complexity Tracking

No constitution violation needs justification. The Constitution Check table lists the two failing rows and their fixes.
