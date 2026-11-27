# Quickstart: Converter Privacy and Shared Portal Integration

Use these steps to reproduce the baseline and run each verification. Run each command from the repository root, unless a step names another folder. The steps use read-only Git and GitHub reads. The test and linter steps write only to caches and test output.

This draft ran none of these commands. The expected results describe the planned outcome.

## 1. Set the GitHub read account

Set the host and copy the token from the account variable. Never print the token value.

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## 2. Confirm the handover state

```powershell
gh pr view 4208 -R jmorrison-juniper/MistHelper --json state,headRefName --jq '[.state, .headRefName] | @tsv'
```

Expected result: `OPEN` while PR #4208 owns the shared files. Phase B waits for `CLOSED` or `MERGED`, and for the handover checklist to read `recorded`.

## 3. Confirm that the shared files lack the converter

```powershell
git grep -n "cisco" -- web_portal/app.py web_portal/templates/base.html
```

Expected result before task T009: no output. The command is read-only.

## 4. Confirm the route baseline

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py
```

Expected result: all existing tests pass. This command checks the offline journey that the cross-cutting tests reuse.

## 5. Run the offline cross-cutting suite (Phase A)

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/test_parity.py
```

Expected result: all 28 cases pass. Pytest prints the count. The suite opens no network socket.

## 6. Confirm the nested package limits

```powershell
python -m pytest tests/guardrails/test_nested_package_structure.py
```

Expected result: the test passes and reports its examined count.

## 7. Confirm the changelog fragment policy

```powershell
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
```

Expected result: the test passes after T-PR adds the fragment.

## 8. Run the real-portal browser module (Phase B)

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/test_portal_browser.py
```

Expected result: all four tests pass. A failed browser test writes a screenshot under `test-artifacts/cisco-portal/`. If Chromium is missing, run the bootstrap command in `.github/copilot-instructions.md`, section "Language and environment".

## 9. Run the regression suites (Phase B)

```powershell
python -m pytest tests/e2e/web_portal/test_portal_smoke.py
python -m pytest tests/integration/web_portal
```

Expected result: both commands pass. Record each pass count in `analysis.md` before and after the integration.

## 10. Check the style of the record

Run this command from the record folder:

```powershell
ste-linter --config .ste-linter.toml --min-score 80 spec.md plan.md tasks.md analysis.md design/research.md design/data-model.md design/quickstart.md
```

Expected result: each file scores 80 or above.

## 11. Read the remote tree

```powershell
gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" --jq '.tree[] | [.path, .sha] | @tsv'
```

Expected result: each path in `design/research.md` appears with its blob or tree SHA. A path that is absent does not appear.
