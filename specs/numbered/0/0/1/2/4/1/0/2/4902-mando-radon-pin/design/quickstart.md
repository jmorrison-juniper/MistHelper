# Quickstart: Reproduce and Verify the mando 0.8.2 Failure

**Scope**: Issue #4902, pull request #4888, workflow run 45064243269, and job 137336719038.

**Rule**: Set the two GitHub variables before each `gh` command. The commands in section 1 and section 2 are read only.

## 1. Reproduce the failure from the CI log

Run these lines in PowerShell. The first two lines set the GitHub variables.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh run view 45064243269 -R jmorrison-juniper/MistHelper --job 137336719038 --log-failed
```

Expected: The output contains the three conflict lines at log lines 561, 565, and 574.

- `ERROR: Cannot install -r requirements-dev.txt (line 365) and mando==0.8.2 because these package versions have conflicting dependencies.`
- `radon 6.0.1 depends on mando<0.8 and >=0.6`
- `ERROR: ResolutionImpossible`

Filter the same output with this command. It prints only the conflict lines.

```powershell
gh run view 45064243269 -R jmorrison-juniper/MistHelper --job 137336719038 --log-failed | Select-String -Pattern 'ERROR: Cannot install|radon 6.0.1 depends|ResolutionImpossible'
```

Find the failing step with this command. The expected result is `Run pip install -r requirements-dev.txt`.

```powershell
gh run view 45064243269 -R jmorrison-juniper/MistHelper --json jobs --jq '.jobs[] | select(.databaseId==137336719038) | .steps[] | select(.conclusion=="failure") | .name'
```

## 2. Confirm the state of main

Read the blob SHA of `requirements-dev.txt` on main. The expected SHA is `9a528bfe03a10f7bc903f5768ef26de765bbff43`.

```powershell
gh api "repos/jmorrison-juniper/MistHelper/contents/requirements-dev.txt?ref=main" --jq ".sha"
```

Confirm that no folder starts with `4902-`. The expected result is an empty line.

```powershell
gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" --jq '.tree[] | select(.path | test("(^|/)4902-")) | .path'
```

## 3. Run the local gates after the change

Run each command from the worktree root. Stop at the first failed command.

| Gate | Command | Expected result |
| - | - | - |
| Lint | `python -m ruff check .` | `All checks passed` |
| Format | `python -m black --check .` | No file needs a change |
| Test target 1 and 2 | `python -m pytest tests/guardrails/test_pr_title_workflow.py` | All tests pass |
| Test target 3 | `python -m pytest tests/guardrails/test_changelog_fragment_policy.py` | All tests pass |
| Test target 4 | `python -m pytest tests/guardrails/test_dependency_export.py` | All tests pass |
| Test target 5 | `python -m pytest tests/guardrails/test_dependency_lock_file.py` | All tests pass |
| Symbols | `symbol-diff --base origin/main tests/guardrails/test_pr_title_workflow.py` | `no module-level name changed`, exit code 0 |
| Unchanged dependency files | `git diff --name-only origin/main -- requirements-dev.txt requirements.txt uv.lock pyproject.toml` | No output |
| STE | `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/4/1/0/2/4902-mando-radon-pin/spec.md specs/numbered/0/0/1/2/4/1/0/2/4902-mando-radon-pin/plan.md specs/numbered/0/0/1/2/4/1/0/2/4902-mando-radon-pin/tasks.md specs/numbered/0/0/1/2/4/1/0/2/4902-mando-radon-pin/analysis.md specs/numbered/0/0/1/2/4/1/0/2/4902-mando-radon-pin/design/research.md specs/numbered/0/0/1/2/4/1/0/2/4902-mando-radon-pin/design/data-model.md specs/numbered/0/0/1/2/4/1/0/2/4902-mando-radon-pin/design/quickstart.md specs/numbered/0/0/1/2/4/1/0/2/4902-mando-radon-pin/design/checklists/requirements.md changelog.d/issue-4902-mando-radon-pin.md` | Each file scores 80 or above |

Not applicable, with the reason for each gate:

- Compile: The change does not edit `MistHelper.py`.
- Types: The Types gate reads the source paths in `.github/workflows/ci.yml` line 93 (research R44). The change adds no source file.
- Dead code, docstrings, complexity, Bandit, Pylint, and coverage: The change adds no source module.
- Dependency audit: The change edits no dependency file.
- Menu reference, safe sweep, ops portal, and ops platform: The change edits no menu, portal, or platform file.

## 4. Run the test quality check before the push

Run this check after the local commit, from the worktree root. It mirrors the analyzer command in `.github/workflows/ci.yml` line 632 (research R16).

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main
```

Expected: The gate reports zero new findings against the baseline.

## 5. Optional proof of the pin failure

This step is optional, and it did not run for this record (research U-4). It uses a scratch worktree, not the main checkout.

1. Create a scratch worktree from the new branch.
2. In the scratch worktree, change the pin in `requirements-dev.txt` to `mando==0.8.2`.
3. Run `python -m pytest tests/guardrails/test_pr_title_workflow.py -k pinned_mando`.
4. Expect a failure that names `mando 0.8.2 conflicts with radon 6.0.1`.
5. Remove the scratch worktree.

## 6. Check the remote state after the push

Watch the required checks on the pull request.

```powershell
gh pr checks <number> -R jmorrison-juniper/MistHelper --watch
```

Expected: Every required check reports success.

Read the pull request title and body.

```powershell
gh pr view <number> -R jmorrison-juniper/MistHelper --json title,body
```

Expected: The title is the commit subject, and the body contains `Closes #4902`.

After the merge, read the state of pull request #4888.

```powershell
gh pr view 4888 -R jmorrison-juniper/MistHelper --json state,closedAt
```

Expected: The state is `CLOSED`.
