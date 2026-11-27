# Quickstart: History Site Column Failure Evidence

Use these commands to reproduce the failure evidence and to verify the change. Run the GitHub commands with read access only.

## 1. Select the GitHub account for each gh command

Run these two lines before each gh command. They set the account. Do not print the token value.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

## 2. Reproduce the failure from the CI log

Read the job log of the failed run. The failed line is log line 1252.

```powershell
gh run view 38860502112 -R jmorrison-juniper/MistHelper --job 116842182317 --log | Select-String -SimpleMatch -Pattern "test_the_history_of_one_site_shows_no_site_column"
```

Expected: one line that contains `FAILED [  6%]` at 06:25:04.

Check the failed-step view. It prints nothing, because the test step ended as canceled.

```powershell
gh run view 38860502112 -R jmorrison-juniper/MistHelper --log-failed
```

Expected: no output.

Check the log for assertion text. Each command prints nothing.

```powershell
gh run view 38860502112 -R jmorrison-juniper/MistHelper --job 116842182317 --log | Select-String -SimpleMatch -Pattern "AssertionError"
gh run view 38860502112 -R jmorrison-juniper/MistHelper --job 116842182317 --log | Select-String -SimpleMatch -Pattern "Traceback"
```

## 3. Confirm the diagnostics step on main

Read the workflow from `main`. Decode the content and search for the condition.

```powershell
$content = gh api "repos/jmorrison-juniper/MistHelper/contents/.github/workflows/ci.yml?ref=main" --jq .content
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String(($content -replace '\s', ''))) -split "`n" | Select-String -SimpleMatch -Pattern "failure() || cancelled()"
```

Expected: one line, numbered 939 in the decoded file.

## 4. Run the guard tests

Run the full guard file after the edit in T002 to T004.

```powershell
python -m pytest tests/guardrails/test_e2e_shard_partition.py -v
```

Expected: every test passes. The new test function passes. Each mutation case passes, because each case expects an assertion.

Run the mutation cases alone.

```powershell
python -m pytest tests/guardrails/test_e2e_shard_partition.py -k missing_diagnostic -v
```

Expected: three cases pass, named `condition`, `trace`, and `log`.

## 5. Run the failing test locally (optional)

This command needs the Chromium browser. Install it first, as the CI shard does.

```powershell
python -m playwright install --with-deps chromium
python -m pytest "tests/e2e/upgrade_portal/test_history_site_column_journey.py::test_the_history_of_one_site_shows_no_site_column" -v --base-url=http://127.0.0.1:8056 --timeout=180 --screenshot only-on-failure --tracing retain-on-failure --output=test-artifacts/issue-4249-browser
```

Expected: `1 passed`. If the test fails, the folder `test-artifacts/issue-4249-browser` holds a failure screenshot and a trace for that test.

## 6. Read the next failed run

List the recent failed runs of the CI workflow. Copy the databaseId of the run that you need.

```powershell
gh run list -R jmorrison-juniper/MistHelper --workflow ci.yml --status failure --limit 5 --json databaseId,headBranch,displayTitle,createdAt
```

Download the diagnostics artifact of the upgrade-portal shard with `gh run download`. Give the databaseId from the list output as the first argument. Add the options `--name e2e-diagnostics-upgrade-portal`, `--dir test-artifacts/ci-diagnostics`, and `-R jmorrison-juniper/MistHelper`. The folder `test-artifacts` is git ignored.

Then read the artifact in this order:

1. Open the failure screenshot in the folder of the failed test.
2. Open the trace file with the Playwright trace viewer.
3. Search the shard log for the test name and for `FAILED`.

Caution: a canceled shard log can lack the traceback text. The trace and the failure screenshot still show the failure.

## 7. Check the record text

Run the STE command in `tasks.md`, task T-LOCAL-GATES, command 9. Each file must score 80 or above.
