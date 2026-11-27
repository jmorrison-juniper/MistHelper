# Quickstart: RADIUS API Failure Test Assertion

These steps reproduce the gate failure, verify the fix, and run the local gates. The commands use PowerShell on Windows 11. Use the same commands on macOS or Linux with `.venv/bin/` in place of `.venv\Scripts\` and forward slashes in paths.

Define the tool path in each PowerShell session. A new session does not keep variables.

```powershell
$REPO = "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper"
$VENV = "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\.venv\Scripts"
$BASE_REF = "main"
```

## Prerequisites

- The `.venv` in `$REPO` is built from `requirements-dev.txt`. A new worktree has no `.venv`, so the commands use the `$VENV` path from the main checkout.
- The commits `1f4843c20c43832ca6a85a7a26d31e4b2a5c9693` and `843be63bc837513b4442dae69da9f0db922e0ed1` exist in `origin`. Research RC-06 and RC-09 hold their blob SHAs.
- Run `git fetch --no-tags origin "+refs/heads/main:refs/remotes/origin/main"` before any check that compares with `origin/main`.

## Scenario 1: Reproduce the gate failure on the fixture repair

Expected result: the gate prints one new finding at line 707 and exits 1.

```powershell
git worktree add ..\MistHelper-4798-repro 1f4843c20c43832ca6a85a7a26d31e4b2a5c9693
cd ..\MistHelper-4798-repro
& "$VENV\test-quality-analyzer.exe" --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/$BASE_REF" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected lines:

```text
gate_new: weak_zero_assertions tests/unit/refactors/test_wlanradius_timer_manager_paths.py:707 Test function 'test_an_api_failure_is_contained' contains no assertions.
gate: 1 new findings vs baseline
```

## Scenario 2: Verify the assertion commit

Expected result: the gate prints zero new findings and exits 0.

```powershell
cd $REPO
git worktree add ..\MistHelper-4798-head 843be63bc837513b4442dae69da9f0db922e0ed1
cd ..\MistHelper-4798-head
& "$VENV\test-quality-analyzer.exe" --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/$BASE_REF" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected line: `gate: 0 new findings vs baseline`.

## Scenario 3: Add the inline comments (follow-up commit)

Run this scenario only after the orchestrator authorizes a push to the PR branch. Do not force-push.

1. Open the test module in the PR worktree. Apply the header, the `with` line comment, and the assertion comment from `plan.md`, section "File-by-File Change Map". Keep the existing `# WHY:` comments.
2. Run TC-001 from Scenario 4.
3. Check that no other file changed:

```powershell
git status --short
```

Expected output: exactly one line, ` M tests/unit/refactors/test_wlanradius_timer_manager_paths.py`.

4. Commit with the Conventional Commits subject and the trailer:

```powershell
@'
test(tests): add WHY comments to the contained RADIUS failure test

Refs #4798

Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>
'@ | git commit -F -
```

5. Run the scoped gate from Scenario 2 on the new commit. Expected line: `gate: 0 new findings vs baseline`.
6. Push to the PR branch as a fast-forward:

```powershell
git push origin HEAD:jmorrison-juniper-4200-migrate-mistwanperformance
```

## Scenario 4: Prove that the target test can fail

Run each mutation in the `MistHelper-4798-head` worktree only. Revert each mutation before the next one.

Target node:

```powershell
& "$VENV\python.exe" -m pytest -q tests\unit\refactors\test_wlanradius_timer_manager_paths.py::TestApplyChangesDispatch::test_an_api_failure_is_contained
```

- TC-001: Run the target node on the unchanged branch. Expected: 1 passed.
- TC-002: Replace the print call on line 733 of `src\foundation\support\refactors\wlanradius_timer_manager.py` with `pass`. Run the target node. Expected: 1 failed with an assertion error. Revert with `git checkout -- src/foundation/support/refactors/wlanradius_timer_manager.py`.
- TC-003: Change the text `Error applying changes` on line 733 to `Error applying change`. Run the target node. Expected: 1 failed with an assertion error. Revert the same way.

After each revert, run `git status --short`. Expected output: no line for `src`.

## Scenario 5: Run the local gates

Run each command from the branch worktree. Expected results are in the comments after each command.

```powershell
& "$VENV\python.exe" -m py_compile MistHelper.py
& "$VENV\python.exe" -m ruff check .
& "$VENV\python.exe" -m black --check .
& "$VENV\python.exe" -m pytest -q tests\unit\refactors\test_wlanradius_timer_manager_paths.py
& "$VENV\python.exe" -m bandit -c pyproject.toml -q tests\unit\refactors\test_wlanradius_timer_manager_paths.py
& "$VENV\symbol-diff.exe" --base origin/main tests\unit\refactors\test_wlanradius_timer_manager_paths.py
& "$VENV\python.exe" -B -m pytest -p no:cacheprovider -s -q tests\guardrails\local_test_quality_loop\test_guidance.py::TestLiveGuides
```

Expected results:

- Compile: no output (research RC-56).
- Lint: `All checks passed` (research RC-57).
- Format: no file needs a change (research RC-58).
- Tests: all tests pass (research RC-59).
- Security lint: no output (research RC-60).
- Symbols: `no module-level name changed`, exit code 0 (research RC-61).
- Guard preflight: all tests in `TestLiveGuides` pass. The preflight reads the four required inputs.

Gates that do not apply:

- Full tests: CI runs the shards. The unit shard takes 1179.3 seconds (research RC-35).
- Coverage, complexity, pylint, and dependency audit: these scan product code or dependencies. This change edits neither.
- Dead code, docstrings, and type checking: the CI paths exclude `tests` (research RC-26 to RC-29).
- Menu reference and safe sweep: this change edits no menu.
- STE: this change edits no Markdown file in the list of the STE row.
- Operations portal and operations platform: this change edits neither package.

## Scenario 6: Run the test-quality gates

Scoped gate, the required form before push:

```powershell
& "$VENV\test-quality-analyzer.exe" --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/$BASE_REF" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Full-suite check, the push and manual CI form:

```powershell
& "$VENV\test-quality-analyzer.exe" --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Expected line for both: `gate: 0 new findings vs baseline`. If the full-suite count is not zero, stop and report the findings. Do not edit the baseline.

Baseline check:

```powershell
git diff --quiet origin/main -- .github/test-quality-baseline.json
```

Expected result: exit code 0.

## Scenario 7: Check the remote run

Read-only check of the PR checks. Use `gh` for reads only.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh pr checks 4208 -R jmorrison-juniper/MistHelper
```

Expected result: `Test quality ratchet (gate)` reports `pass` on the newest head commit.

## Scenario 8: Remove the worktrees

Run this scenario after all runs finish and all mutations revert.

```powershell
cd $REPO
git worktree remove ..\MistHelper-4798-repro
git worktree remove ..\MistHelper-4798-head
```

No container starts in this quickstart. No port publishes. No container cleanup applies.
