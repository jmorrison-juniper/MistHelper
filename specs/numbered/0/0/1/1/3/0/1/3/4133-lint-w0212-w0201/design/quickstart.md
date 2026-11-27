# Quickstart: Lint repair for W0212 and W0201 findings

Run these commands from the worktree root. Create the `.venv` with the bootstrap script in `documentation/development-setup.md`. Then activate it with `.venv\Scripts\Activate.ps1`. The later commands assume the activated environment, except where they name `.venv\Scripts\python.exe`.

## 1. Reproduce the findings (before the change)

```powershell
.venv\Scripts\python.exe -B -m pylint --persistent=n --disable=all --enable=W0212,W0201 --output-format=json MistHelper.py tests\unit\test_menu_entry_metadata.py
```

Expected before the change: two JSON messages with message-id `W0212`. Both sit in `tests\unit\test_menu_entry_metadata.py`, at lines 84 and 93. The check reports no message for `MistHelper.py`.

Expected after the change: the output is `[]`.

## 2. Run the test module

```powershell
.venv\Scripts\python.exe -m pytest tests\unit\test_menu_entry_metadata.py
```

Expected: 35 passed. The count holds 3 non-parametrized tests, 29 boundary cases, 2 invalid-selection cases, and 1 empty-selection case.

## 3. Run the changelog guard

```powershell
.venv\Scripts\python.exe -m pytest tests\guardrails\test_changelog_fragment_policy.py
```

Expected: the guard passes with the new fragment `changelog.d\issue-4133-lint-w0212-w0201.md`.

## 4. Run the local gates for the changed files

```powershell
.venv\Scripts\python.exe -m py_compile tests\unit\test_menu_entry_metadata.py
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m black --check .
.venv\Scripts\python.exe -m bandit -c pyproject.toml -r tests\unit\test_menu_entry_metadata.py -q
```

Expected:

- `py_compile` prints no output.
- `ruff check .` prints `All checks passed`.
- `black --check .` reports that no file needs a change.
- `bandit` reports no finding.

## 5. Check the complexity limit

```powershell
radon cc tests\unit\test_menu_entry_metadata.py -j | complexity-gate --max 10
```

Expected: no block above cyclomatic complexity 10.

## 6. Check the symbols

```powershell
symbol-diff --base origin/main tests/unit/test_menu_entry_metadata.py
```

Expected: `no module-level name changed`, with exit code 0.

## 7. Run the test-quality preflight and gate

Run the preflight first:

```powershell
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -s -q tests\guardrails\local_test_quality_loop\test_guidance.py::TestLiveGuides
```

Expected: the preflight passes. A failed preflight stops the gate.

Then run the gate. Fetch the base branch first, as `.github/copilot-instructions.md` describes in its Test quality ratchet section:

```powershell
git fetch --no-tags origin "+refs/heads/main:refs/remotes/origin/main"
```

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected: the line `gate: 0 new findings vs baseline` appears. Any other count stops the task. Do not edit `.github/test-quality-baseline.json`.

## 8. Check the STE rules for the record Markdown

After the record folder is copied into the worktree, run the STE linter on each Markdown file of the record:

```powershell
ste-linter --config .ste-linter.toml --min-score 80 specs\numbered\0\0\1\1\3\0\1\3\4133-lint-w0212-w0201\spec.md specs\numbered\0\0\1\1\3\0\1\3\4133-lint-w0212-w0201\plan.md specs\numbered\0\0\1\1\3\0\1\3\4133-lint-w0212-w0201\tasks.md specs\numbered\0\0\1\1\3\0\1\3\4133-lint-w0212-w0201\analysis.md
```

Expected: each file scores 80 or above. Run the same command on each file under `design\`.

## 9. Read the remote evidence again (read only)

Set the host and the token before each `gh` call. The token comes from the account variable named `COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper`. Do not print its value.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh api repos/jmorrison-juniper/MistHelper/git/ref/heads/main --jq .object.sha
```

Expected: the current `main` commit SHA. At the time of this record, the SHA is f03c6c9b36d612a48d7b9652998c2fd87dd777ca.

Confirm the blob of the test file with the same two lines, then this read:

```powershell
gh api repos/jmorrison-juniper/MistHelper/git/blobs/d9b4d79ebb6f303e54ad52add9c741e87eb01e32 --jq .sha
```

Expected: the blob SHA echoes the request value. This read confirms that the blob exists.

## 10. Cleanup

Delete the scratch folder of the research run in `META_DIR` after the record is final. The folder holds decoded copies of the repository files. It holds no secret.
