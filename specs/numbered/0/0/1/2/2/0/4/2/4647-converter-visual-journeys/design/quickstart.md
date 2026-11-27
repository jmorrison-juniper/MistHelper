# Quickstart: Add independently authored converter visual journeys

Use this guide to reproduce the current gap and to verify the change after implementation. Run each command from the repository root in PowerShell.

## Prerequisites

- Issues #4636, #4641, and #4642 are merged into `main`. Scenarios 4 to 8 need the implementation (`spec.md`, AS-001).
- The Python environment is installed from `requirements-dev.txt` (RC-58, RC-59).
- Chromium is installed. The bootstrap downloads it (RC-61). If it is absent, use Scenario 3.

## Scenario 1: Confirm the current gap

Search the current presentation for the new controls. Before implementation, no match appears.

```powershell
Select-String -LiteralPath src\interfaces\portals\cisco_config_converter\presentation\converter.html -Pattern 'cisco-confirm|cisco-cancel|cisco-reset'
```

Expected result: no output. The current page has no typed confirmation or cancel control (RC-11).

## Scenario 2: Confirm the test layout before any edit

```powershell
python -m pytest tests/guardrails/test_e2e_package_structure.py
```

Expected result: the tests pass. The E2E root holds five entries (RC-47). The web portal folder holds 32 direct children (RC-48).

## Scenario 3: Install Chromium when it is absent

```powershell
python -m playwright install chromium
```

Expected result: Playwright reports that Chromium is installed.

## Scenario 4: Run the converter journeys with failure evidence

```powershell
python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k CiscoConverterJourneys -v --tracing retain-on-failure --screenshot only-on-failure --output=test-artifacts/issue-4647-browser
```

Expected result: 20 test cases pass. The options match the CI command (RC-52, RC-77). Failed cases keep a trace and a screenshot under `test-artifacts/issue-4647-browser`.

## Scenario 5: Run the theme and viewport matrix

```powershell
python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k shipped_theme_at_viewport -v
```

Expected result: eight cases pass. Each case covers one shipped theme at the phone or the desktop viewport (RC-34, RC-40).

## Scenario 6: Confirm the storage rule and the export gate

```powershell
python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k "structured_review_and_typed_export or typed_word" -v
```

Expected result: the tests pass. The storage assertion lists `misthelper-theme` as the only browser key (RC-27, RC-32).

## Scenario 7: Confirm the production host serves no converter route

```powershell
python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k no_converter_route -v
```

Expected result: the test passes. The production app returns 404 for `/cisco-config-converter/` (RC-30).

## Scenario 8: Inspect the failure evidence

Run this command only after a failed run.

```powershell
Get-ChildItem -LiteralPath test-artifacts\issue-4647-browser -Recurse
```

Expected result: one trace file and one screenshot for each failed test (SC-008).

Caution: remove the evidence folder only by its exact name. The folder is generated and can be made again by a new run.

```powershell
Remove-Item -LiteralPath test-artifacts\issue-4647-browser -Recurse
```

## Scenario 9: Run the local gates for the changed files

```powershell
python -m ruff check .
python -m black --check .
python -m pytest tests/e2e/web_portal/test_portal_smoke.py
```

Expected results: `All checks passed`, `No file needs a change`, and a pytest summary with no failure (RC-91, RC-92, RC-93).

## Scenario 10: Run the test quality gate before the push

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Expected result: the output reports `gate: 0 new findings vs baseline` (RC-95).

## Scenario 11: Watch the remote checks

```powershell
gh pr checks --watch
```

Expected result: the `E2E smoke tests` check and each required check pass on the latest commit. The command reads the pull request of the current branch.
