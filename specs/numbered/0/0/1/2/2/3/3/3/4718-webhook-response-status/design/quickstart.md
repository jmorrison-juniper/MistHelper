# Quickstart: Webhook response status

Run every command from the repository root. Set the repository path once in the shell.

```powershell
$repo = "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper"
Set-Location -LiteralPath $repo
```

Use the existing `.venv`. Create a missing environment with `python scripts/bootstrap_worktree.py`, as `documentation/development-setup.md` describes (R51).

## 1. Read the pre-fix exporter

The pre-fix blob is `dff2b4d6a`, from the index line of the PR #4852 diff.

```powershell
git -C $repo show dff2b4d6a
```

The pre-fix reader defaults a missing status to 200. The list call has no status check.

## 2. Reproduce the defect on the pre-fix source

1. Find the pre-fix commit of the merge.

```powershell
git -C $repo rev-parse b1307510^1
```

2. Create a worktree for that commit beside the main checkout. Use a path outside `/tmp`.

```powershell
git -C $repo worktree add ..\MistHelper-4718-prefix b1307510^1
```

3. Enter the worktree and create its environment.

```powershell
Set-Location -LiteralPath ..\MistHelper-4718-prefix
python scripts/bootstrap_worktree.py
```

4. Run the rejection tests. On the pre-fix source, the rejected-status tests fail.

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/export/test_org_webhook_deliveries_exporter.py -q -k "rejected_status or absent_status"
```

5. Remove the worktree after the check. Run this command from `$repo`.

```powershell
git -C $repo worktree remove ..\MistHelper-4718-prefix
```

## 3. Verify the repair offline

Run each command in the main checkout. Each command uses synthetic native responses and no network.

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/export/test_org_webhook_deliveries_exporter.py -q
.venv\Scripts\python.exe -m pytest tests/unit/export/test_issue_3188_webhook_id_selection.py -q
.venv\Scripts\python.exe -m pytest tests/integration/export/test_org_webhook_native_refusals.py -q
.venv\Scripts\python.exe -m pytest tests/guardrails/test_changelog_fragment_policy.py -q
.venv\Scripts\python.exe -m pytest tests/e2e/web_portal/test_issue_3188_webhook_control.py -q
```

Expected result for each command: a passed summary and zero failures. The browser module reports a skip when Playwright is absent.

## 4. Run the local gates for the changed files

These commands come from the local gates table in `.github/copilot-instructions.md` (R35). The paths come from the CI variables in `.github/workflows/ci.yml` (R40 to R43).

```powershell
.venv\Scripts\python.exe -m py_compile MistHelper.py
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m black --check .
.venv\Scripts\python.exe -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
.venv\Scripts\python.exe -m pylint src/ --fail-under=9.5
.venv\Scripts\python.exe -m vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
.venv\Scripts\python.exe -m pydocstyle src/ wsgi.py web_portal
.venv\Scripts\python.exe -m interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
.venv\Scripts\python.exe -m bandit -c pyproject.toml -r src/operations/exporting -q
radon cc src/operations/exporting/export -j | complexity-gate --max 10
symbol-diff --base origin/main src/operations/exporting/export/org_webhook_deliveries_exporter.py
```

Expected results follow the table. The compile step prints no output. Ruff prints `All checks passed`. Black reports that no file needs a change. Mypy prints `Success`. The symbol check prints `no module-level name changed` and exits with code 0.

## 5. Run the test-quality ratchet

Fetch the base branch first. Run the commands in order, and stop at the first failure.

```powershell
git fetch --no-tags origin "+refs/heads/main:refs/remotes/origin/main"
.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/main" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected result: the analyzer prints `gate: 0 new findings vs baseline`.

## 6. Check for other callers of the changed helper

```powershell
git -C $repo grep -n _response_status_code -- src tests MistHelper.py
```

Expected result: each hit is a definition or a call in `org_webhook_deliveries_exporter.py`. A hit in another module names a separate helper, which the repair leaves unchanged.

## 7. Check for suppression comments

```powershell
git -C $repo grep -n -E "nosec|noqa|type: ignore" -- src/operations/exporting/export/org_webhook_deliveries_exporter.py tests/unit/export/test_org_webhook_deliveries_exporter.py
```

Expected result: no hit that the repair adds. The repair must not add a suppression.
