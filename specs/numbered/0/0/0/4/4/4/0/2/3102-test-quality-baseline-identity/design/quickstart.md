# Quickstart: Reproduce and verify issue 3102

This quickstart gives the exact steps for reproducing the drift defect and for verifying the fix. Run each step in a worktree of MistHelper. Do not run these steps in a checkout that another agent uses.

## Prerequisites

1. Create a worktree from `origin/main` for the branch `fix/3102-test-quality-baseline-identity`.

```text
git worktree add ..\MistHelper-3102 -b fix/3102-test-quality-baseline-identity origin/main
```

2. Enter the worktree. Create the environment with the bootstrap command in section "Language and environment" of `.github/copilot-instructions.md` (lines 18-49).

```text
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

## Step 1: Confirm the gate passes before the edit

Run the full-suite gate. Expect exit code 0, a `gate_scope` line with non-zero counts, and `gate: 0 new findings vs baseline`.

```text
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

## Step 2: Choose a live finding

1. Open `test_quality_analyzer_output\report.json`. The analyzer writes it into this folder (R-50).
2. Select one finding with a `file_path` under `tests/` and a `line_number` greater than 1.
3. Record the file path and the line number.

Caution: do not choose an entry from the issue body. Those rows do not match the baseline on main (R-21, R-23).

## Step 3: Reproduce the defect on the current pin

1. Insert one blank line above the selected flagged line.
2. Run the gate from Step 1.
3. Expect exit code 1. Expect a `gate_new:` line for each finding at or below the inserted line in that file.
4. Remove the blank line.

## Step 4: Verify the fix on the new pin

4. Repeat Step 3 after the pin and the migration are in place. Expect exit code 0, `gate: 0 new findings vs baseline`, and `gate_removed: 0`.

## Step 5: Verify that a real change fails

1. In the same test function, add one line of the form `assert <name> is not None`. Use a name that exists in that function.
2. Run the gate from Step 1. Expect exit code 1, one `gate_new:` line, and `gate: 1 new findings vs baseline`.
3. Remove the added line.

## Step 6: Verify removal and prune

1. Delete one flagged assert statement that the report lists for a matched test.
2. Run the gate from Step 1. Expect exit code 0 and `gate_removed: 1`.
3. Run the prune command. Expect `prune: dropped 1 baseline occurrence(s)`.

```text
test-quality-analyzer --prune-baseline --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

4. Restore the test file. Restore the baseline file in this worktree.

```text
git checkout -- .github/test-quality-baseline.json
```

Warning: the restore command discards uncommitted changes to the baseline file in this worktree. Run it only in the MistHelper-3102 worktree.

## Step 7: Migrate the baseline

1. Confirm that Step 1 passes on the branch.
2. Run the write command with the new pin.

```text
test-quality-analyzer --write-baseline --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

3. Record the insertion and deletion counts of the baseline file.

```text
git diff --numstat -- .github/test-quality-baseline.json
```

4. Compare the new entries with the entries on main. Run these lines in PowerShell. They use memory only.

```text
$old = (git show origin/main:.github/test-quality-baseline.json | Out-String) | ConvertFrom-Json
$new = (Get-Content -LiteralPath .github\test-quality-baseline.json -Raw) | ConvertFrom-Json
$oldSet = $old | ForEach-Object { '{0}|{1}|{2}|{3}|{4}' -f $_.category, $_.rule_id, $_.file_path, $_.line_number, $_.explanation }
$newSet = $new | ForEach-Object { '{0}|{1}|{2}|{3}|{4}' -f $_.category, $_.rule_id, $_.file_path, $_.line_number, $_.explanation }
"retained_entries=$(@($newSet).Count) old_entries=$(@($oldSet).Count)"
"new_not_in_old=$(@($newSet | Where-Object { $oldSet -notcontains $_ }).Count)"
"dropped=$(@($oldSet | Where-Object { $newSet -notcontains $_ }).Count)"
```

5. Expect `new_not_in_old=0`. Each retained entry matches one entry on main by category, rule, file, line, and explanation.
6. Record each dropped entry in the pull request body. Record the total.

Caution: the migration removes entries from the baseline file. Git restores them if the pull request closes unmerged.

## Step 8: Run the verification commands

Run each command separately. Stop at the first failed command.

```text
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
python -m pytest tests/guardrails/local_test_quality_loop/test_scope.py
python -m ruff check .
python -m black --check .
ste-linter --config .ste-linter.toml --min-score 80 .github/copilot-instructions.md documentation/quality-gates.md
```

Expected results:

- The preflight test passes.
- The full-suite gate prints `gate: 0 new findings vs baseline`.
- The changed-scope gate exits 0 for a pull request with changed test files.
- The scope test file passes, including the four new cases.
- Ruff prints `All checks passed`.
- Black prints that no file needs a change.
- STE scores each file at 80 or above.

## Upstream verification

Run these commands in a checkout of misthelper-devtools at the release commit.

```text
python -m pytest tests/tools/test_quality_analyzer/test_baseline_differ.py
python -m pytest tests/tools/test_quality_analyzer/test_gate_decision.py
python -m pytest tests/tools/test_quality_analyzer/test_cli.py
python -m pytest tests/tools/test_quality_analyzer/test_types.py
```
