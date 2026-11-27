# Quickstart: Radon Job Mando Pin Conflict

## Prerequisites

- The `gh` command is available.
- The account variable `COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper` is set. Do not print its value.
- Run the read commands from any folder. Run the local gates in the fix worktree only.

## Scenario 1: Reproduce the failure (read-only)

Each `gh` command needs the host and the token first. Set both in the same session.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh issue view 4898 -R jmorrison-juniper/MistHelper --json number,title,state,labels
gh pr view 4888 -R jmorrison-juniper/MistHelper --json headRefOid,files,state,statusCheckRollup
gh run view 45064243269 -R jmorrison-juniper/MistHelper --job 137336719006
gh run view 45064243269 -R jmorrison-juniper/MistHelper --job 137336719006 --log-failed
```

Expected results:

- The issue is OPEN with the labels bug, ci, and quality-gate.
- PR #4888 changes `requirements-dev.txt`, and its head is `e86098cdc2b189d217805b3b4060ef609cbc37af`.
- The job view marks `Run pip install -r requirements-dev.txt` with X. It marks `Check cyclomatic complexity` with a dash, which means skipped.
- The log holds `ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2`.
- The log holds `radon 6.0.1 depends on mando<0.8 and >=0.6`.

## Scenario 2: Confirm that main passes (read-only)

```powershell
gh run view 45774119357 -R jmorrison-juniper/MistHelper --json jobs
gh api "repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=main" --jq .sha
```

Expected results:

- The job `Radon (complexity)` has the conclusion success. Its steps include `Check cyclomatic complexity` with success.
- The second command prints `9a528bfe03a10f7bc903f5768ef26de765bbff43`.

## Scenario 3: Verify the local gates in the fix worktree

Run each command in the fix worktree. Each command has one expected result.

```powershell
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
python -m pytest tests/guardrails/test_dependency_lock_file.py
```

Expected results:

- The compile command prints nothing.
- Ruff prints `All checks passed`.
- Black reports that no file needs a change.
- Pytest reports eight passing tests. Four tests are new, and four tests already existed.

Run the test quality ratchet from `.github/copilot-instructions.md`, in this order.

```powershell
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Expected results: the preflight passes. The analyzer prints `gate: 0 new findings vs baseline`.

Run the symbol gate and the security lint on the changed test module.

```powershell
symbol-diff --base origin/main tests/guardrails/test_dependency_lock_file.py
bandit -c pyproject.toml -r tests/guardrails/test_dependency_lock_file.py -q
```

Expected results: the symbol gate prints `no module-level name changed` and exits with code 0. Bandit prints no finding.

Run the STE gate on the changelog fragment.

```powershell
ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4898-radon-mando-conflict.md
```

Expected result: the score is 80 or above.

The gates below do not apply to this change, so this record does not run them. The reason follows each name.

- Complexity: `RADON_PATHS` does not include `tests/guardrails`, and no source file changes.
- Dependency audit: no requirement file changes (FR-010).
- Coverage, Code quality, Dead code, Docstrings, Types: their paths in `ci.yml` exclude the guard tests.
- Menu reference, Safe sweep, Ops portal, Ops platform: no menu, portal, or npm file changes.
- Full tests: CI runs the two `pytest-chunks` shards (T-REMOTE-CI).

## Scenario 4: Mutation checks (guard proof, then restore)

Run these checks in the fix worktree. Restore each file before you commit.

1. Change line 179 of `requirements-dev.txt` from `mando==0.7.1` to `mando==0.8.2`. Run the next command. The test `test_pinned_mando_satisfies_the_radon_requirement` fails.
2. Restore line 179 to `mando==0.7.1`.
3. Remove the `ignore` block from the pip entry of `.github/dependabot.yml`. Run the next command. The test `test_dependabot_ignores_the_mando_release_that_radon_rejects` fails.
4. Restore the `ignore` block.

```powershell
python -m pytest tests/guardrails/test_dependency_lock_file.py -k "radon or mando"
```

Expected results: the command fails in each mutation and passes after each restore. Run `git diff --name-only` and confirm that `requirements-dev.txt` is absent from the list.

## Scenario 5: Acceptance checks after the fix PR

Set `FIX_PR` to the number of the fix PR before you run these commands.

```powershell
gh pr view $env:FIX_PR -R jmorrison-juniper/MistHelper --json title,headRefName,body,labels
gh pr view $env:FIX_PR -R jmorrison-juniper/MistHelper --json statusCheckRollup
git diff --name-only origin/main HEAD
git diff --quiet origin/main -- requirements-dev.txt requirements.txt pyproject.toml uv.lock .github/workflows/ci.yml
```

Expected results:

- V-02: the title starts with `fix(ci):`. The head is `fix/4898-radon-mando-conflict`. The body contains `Closes #4898`. The labels include bug, ci, and tests.
- V-03: the status for `Radon (complexity)` is SUCCESS.
- V-04: the changed list holds `.github/dependabot.yml`, `tests/guardrails/test_dependency_lock_file.py`, `changelog.d/issue-4898-radon-mando-conflict.md`, and the record folder files.
- V-04 and V-05: the last command exits with code 0. It confirms that no requirement, lock, or workflow file changed.

After the merge, check the closed PR.

```powershell
gh pr view 4888 -R jmorrison-juniper/MistHelper --json state,mergedAt
```

Expected result: the state is CLOSED, and `mergedAt` is null (V-01).
