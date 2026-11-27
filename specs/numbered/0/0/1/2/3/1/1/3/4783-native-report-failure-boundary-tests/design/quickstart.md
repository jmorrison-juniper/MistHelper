# Quickstart: Native Report Failure-Boundary Tests

This guide gives the exact steps and commands for issue #4783. Run each command from the repository root in a worktree on the branch that carries the chain. Use the repository Python 3.15 environment, which `documentation/development-setup.md` line 40 describes.

## Prerequisites

1. Confirm that the `gh` account is `jmorrison-juniper` before each GitHub command. Issue #1893 in `copilot-instructions.md` records the wrong-account risk.
2. Confirm that GitHub holds the chain. Run the command in Scenario 1.
3. Confirm that decision D-2 is recorded by the human owner.

## Scenario 1: Confirm the Chain on GitHub (T001)

Run this command. The result must print the full commit SHA.

```powershell
gh api repos/jmorrison-juniper/MistHelper/commits/07cf3eec5eafbc131091fb5debf9f20036f293d9 --jq .sha
```

If the command returns HTTP 422, stop. Do not create a branch. Record the result in `tasks.md` T001.

## Scenario 2: Reproduce the Two Findings on the Chain Tip (Before the Fix)

Run the changed-scope analyzer on the chain tip. The output must name two findings for `test_report.py`. The count line must read `gate: 2 new findings vs baseline`.

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Save the `gate_scope` line and the `gate_new` lines for the pull request body.

## Scenario 3: Apply the Change (T002 to T008)

1. Replace `class ReportRun` in `tests/unit/websocket_streams/web/hardware/test_report.py` with `_synthetic_identity` and `create_report_run`.
2. Add `import logging` and `_LOGGER` to `test_report.py`.
3. Add `HardwareXmlSupport` to the preset import in `test_report.py`.
4. Rewrite the empty-body test in `test_report.py` to pass `b""` to `HardwareXmlSupport.Decoder.decode_output`.
5. Restore `test_empty_body_cannot_become_zero_module_inventory` in `test_normalization.py` to `normalize("", native_format)`.
6. Add `test_empty_raw_reply_is_refused_at_byte_boundary` in `test_normalization.py`.
7. Add `HardwareXmlPreset` and `HardwareXmlSupport` to the preset import in `test_normalization.py`.
8. Rename the call in `test_report.py` and the import and call in `test_contracts.py` and `test_cli.py`.
9. Add the changelog fragment `changelog.d/issue-4783-native-report-failure-boundary-tests.md`.

Confirm that no reference remains:

```powershell
git grep -n ReportRun -- tests/unit/websocket_streams/web/hardware
```

The command must print no line.

## Scenario 4: Run the Gates in This Order (T-LOCAL-GATES)

Run each command. Stop at the first failed analyzer command, and record the output.

1. Preflight guard:

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

2. Compile check, with no output expected:

```powershell
python -m py_compile MistHelper.py
```

3. Lint, with `All checks passed` expected:

```powershell
python -m ruff check .
```

4. Format check, with no file that needs a change:

```powershell
python -m black --check .
```

5. Changed test modules:

```powershell
python -m pytest tests/unit/websocket_streams/web/hardware/test_normalization.py tests/unit/websocket_streams/web/hardware/test_report.py tests/unit/websocket_streams/web/hardware/test_contracts.py tests/unit/websocket_streams/web/hardware/test_cli.py
```

6. Security lint on the hardware folder, with no finding expected:

```powershell
bandit -c pyproject.toml -r tests/unit/websocket_streams/web/hardware -q
```

7. Coverage, which must reach 80 percent or above:

```powershell
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
```

8. Full unit shards. Each command prints one summary line:

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

9. Test-quality gate, changed scope, after the local commit:

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected: `gate: 0 new findings vs baseline`.

10. Test-quality gate, full suite:

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Expected: `gate: 0 new findings vs baseline`.

11. Symbol check, once for each changed file:

```powershell
symbol-diff --base origin/main tests/unit/websocket_streams/web/hardware/test_report.py
```

Expected: the intended lost name `ReportRun` and the added name `create_report_run`, with exit code 1 when the base holds the file. A line that begins with `cannot read` means the base file is absent, and the result is not evidence.

12. Protected paths:

```powershell
git diff --quiet origin/main -- .github/test-quality-baseline.json .github/test-quality-config.toml
```

Expected: exit code 0.

13. Source path check for the last commit on the branch, which is the fix commit:

```powershell
git diff --name-only HEAD^ HEAD -- src
```

Expected: no output.

## Scenario 5: Expected Results at a Glance

| Check | Expected result |
| - | - |
| Chain on GitHub | SHA printed |
| Changed-scope analyzer before the fix | `gate: 2 new findings vs baseline` |
| Changed-scope analyzer after the fix | `gate: 0 new findings vs baseline` |
| Full-suite analyzer after the fix | `gate: 0 new findings vs baseline` |
| Baseline and settings blobs | Unchanged, exit 0 |
| `src/` in the fix commit | No path |
| Symbol check on a base that holds the file | `ReportRun` lost, `create_report_run` added, exit 1 |
| Symbol check on an absent base | `cannot read` line, no delta |

## Scenario 6: Open the Pull Request (T-PR)

Open the pull request only after Scenario 4 passes and decision D-2 is recorded. The title is `feat(websocket): add optional transceiver master report`. The body must contain:

- `Closes #4783`.
- `Refs #4773`.
- The result of each gate from Scenario 4.
- The output of the symbol check from Scenario 4, step 11.
- The Principle IV exception. Steps 10 to 12 do not run, because `container-build.yml` runs only for product files.
- The two follow-up items: the analyzer blind spot and the six-child test folder.

Do not add the `auto-merge` label until T-REMOTE-CI passes and the orchestrator authorizes the merge.
