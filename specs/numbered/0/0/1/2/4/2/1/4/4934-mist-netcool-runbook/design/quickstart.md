# Quickstart for feature 4934

This guide runs the checks of the NOC runbook and the read-only smoke test. Run each PowerShell command from the root of the feature worktree. The commands use the Python environment of the worktree, so do not run a bare `python` or `py` command.

## 1. Prerequisites

- The worktree has a `.venv` folder. A new worktree needs the bootstrap of `.github/copilot-instructions.md`, section "Language and environment".
- On the Windows host, set the executable extensions before each command that runs a program:

```powershell
$env:PATHEXT = @(".COM", ".EXE", ".BAT", ".CMD", ".VBS", ".JS", ".WS", ".MSC", ".PS1") -join [System.IO.Path]::PathSeparator
```

- The live run needs a read-only token for one Mist organization. The token stays in an ignored env file. No command accepts a token value.

Warning: a token in a shared file, a log, or a commit can cause unauthorized access to the Mist organization. Keep the env file out of Git and out of shared folders.

## 2. Unit tests

Run the unit tests of the smoke test. The test folder holds the five test modules of the smoke test.

```powershell
.venv\Scripts\python.exe -m pytest tests\unit\scripts\netcool_runbook_smoke -q -p no:cacheprovider
```

The run passes when the summary line reports no failed test and no error. A test that fails in the full run and passes alone changes shared state, so repair that test.

## 3. Document test

The document test runs offline. It needs no token and no network access. It checks each heading, each path, each of the 25 operations, and the privacy scan of the runbook.

```powershell
.venv\Scripts\python.exe -m pytest tests\unit\scripts\netcool_runbook_smoke\test_netcool_runbook_document.py -q -p no:cacheprovider
```

The test prints the number of paths, headings, and lines that it examined. The test fails when it cannot read the runbook or the OpenAPI file. A zero count is not a pass.

## 4. Local gates

Run each gate on the changed files. The paths below cover the smoke test package and its test folder.

| Gate | Command | Expected result |
| --- | --- | --- |
| Lint | `.venv\Scripts\ruff.exe check --no-cache scripts\netcool_runbook_smoke` | `All checks passed` |
| Format | `.venv\Scripts\black.exe --check --diff scripts\netcool_runbook_smoke` | No file needs a change |
| Types | `.venv\Scripts\mypy.exe scripts\netcool_runbook_smoke --config-file pyproject.toml` | `Success` |
| Security | `.venv\Scripts\bandit.exe -c pyproject.toml -r scripts\netcool_runbook_smoke -q` | No finding |
| Complexity | `.venv\Scripts\radon.exe cc scripts\netcool_runbook_smoke -j \| .venv\Scripts\complexity-gate.exe --max 10` | No block above 10 |
| Docstrings | `.venv\Scripts\pydocstyle.exe scripts\netcool_runbook_smoke` | No violation |
| Docstring content | `.venv\Scripts\pydoclint.exe --style=google scripts\netcool_runbook_smoke`, when that file exists. Otherwise report that pydoclint is absent. | No violation |
| Docstring coverage | `.venv\Scripts\interrogate.exe scripts\netcool_runbook_smoke -v --fail-under 90` | Coverage of 90 percent or more, which is the gate floor. The target for the new package is 100 percent. |
| Dead code | `.venv\Scripts\vulture.exe scripts\netcool_runbook_smoke --min-confidence 70` | No finding |
| Test format | `.venv\Scripts\black.exe --check --diff tests\unit\scripts\netcool_runbook_smoke` | No file needs a change |
| Markdown links | `.venv\Scripts\python.exe -m pytest tests\guardrails\test_markdown_links.py -q -p no:cacheprovider` | All tests pass |
| Mermaid | Run the Mermaid lint step of the `ci.yml` job at lines 672 to 684 on the runbook. | No error |
| STE, CI mode | `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 --no-dictionary <file>` | Score of 80 or more |
| STE, full mode | `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 --dictionary "<path to data\ste_dictionary.json>" <file>` | Score of 80 or more |

Replace `<file>` with each Markdown file of the change, for example the runbook path `documentation\noc-runbooks\MIST_NETCOOL_ALARM_INTEGRATION.md`. A score without a dictionary proves sentence structure only. Pass both modes.

For the link gate, stage each Markdown file first with `git add <file>`, then run `markdown-link-check --root . <file>`.

The test quality ratchet has its own procedure. Follow `.github/copilot-instructions.md`, section "Test quality ratchet". Commit the intended tests first, then run the preflight and the gate.

The guardrail suite checks the repository rules. Run it with `.venv\Scripts\python.exe -m pytest tests\guardrails -q`. Compare each failure with the failures of the main branch before you accept it.

## 5. Live smoke test

Run the smoke test against the Mist organization. The command reads the token and the organization identifier from the env file. Replace the placeholder with the path of an ignored file.

```powershell
.venv\Scripts\python.exe -m scripts.netcool_runbook_smoke --env-file "<path to an ignored .env file>"
```

The env file must be outside the repository, or it must be the file `.env` in the repository root. Git ignores that file.

The env file names `MIST_API_TOKEN` or `MIST_APITOKEN` for the token. It names `MIST_ORG_ID`, `org_id`, or `ORG_ID` for the organization. It can name `MIST_HOST` for the regional host, and the default host is `api.mist.com`.

Caution: the mistapi SDK can sleep for the full `Retry-After` value after an HTTP 429 response. When the header is absent or not an integer, the SDK sleeps 5, 10, or 20 seconds. Each run also uses part of the hourly request limit of the token. A run can slow other jobs that use the same token.

The client waits at most `--call-timeout` seconds (default 30) for each SDK call. A longer wait gives a `Timeout` error. The second `Timeout` in one run stops the run with exit code 3.

A typical run takes 1 to 3 minutes. The worst case is about 33 minutes at the default budget and the default call timeout. The full rules are in `contracts/smoke-cli.md`, section 6.

Use this command to run the smoke test with the default options. The request budget is 60 requests, and each paged query stops at 3 pages.

```powershell
.venv\Scripts\python.exe -m scripts.netcool_runbook_smoke --env-file "<path to an ignored .env file>" --max-requests 60 --max-pages 3
```

The option `--call-timeout` sets the wait for each SDK call. The default is 30 seconds.

Do not raise the request budget without owner approval. The rate-limit stop applies after a final HTTP 429 response. It also applies after the second Timeout in one run. It applies when `request_limit` minus `requests` is fewer than two times the request budget. The rate-limit stop protects the token from a run that uses too many requests in one hour.

## 6. Read the summary

The console prints one line for each check. Each line has the check identifier, the status, the title, and the detail. The summary line and the outcome line print on every run, including a run that stops before SMK-01. The console then prints these lines.

- The summary line, with the counts of checks examined, passed, warnings, information lines, failed checks, skipped checks, and requests sent.
- The outcome, with the outcome class and the exit code.
- The path of the evidence record, or `Evidence: not written` when the run writes no record.

The final verification run, with the runbook, must show no SKIP for SMK-02. It must show no SKIP for any Appendix B name check.

The statuses have these meanings:

| Status | Meaning | Action |
| --- | --- | --- |
| `PASS` | The check confirmed its fact. | None. |
| `WARN` | The check confirmed its fact with a limit or a risk. Zero records and a page ceiling give WARN. | Read the detail, and decide with the NOC lead. |
| `INFO` | The check recorded an observation. | None. |
| `FAIL` | The proof of the check failed. | Follow the troubleshooting section of the runbook. |
| `SKIP` | The check, or one part of it, did not run. | Read the cause in the detail. |

The exit codes have these meanings.

| Exit code | Outcome class | Action |
| --- | --- | --- |
| 0 | `Pass` | None. The run is complete. |
| 1 | `Check failure` | Read each `FAIL` line. |
| 2 | `Configuration error` | Correct the token, the organization identifier, the host, or the file path. Use a token that grants the organization when SMK-03 gives FAIL. |
| 3 | `Rate-limit stop` | For an HTTP 429 response or low hourly usage, wait for the reset. The `seconds` value of `/api/v1/self/usage` gives the wait time. For two timeouts, check the network path and the proxy. |
| 4 | `Budget stop` | Read which checks did not run. Do not raise the budget without approval. |
| 5 | `Unsafe paging stop` | Report the stop to the Mist administrator and the integration engineer. |
| 6 | `Internal error` | Read the logged traceback and each printed cause. Report the traceback to the tool owner. |

The full rules are in `contracts/smoke-cli.md`.

## 7. Read the evidence

The evidence record is a JSON file under `test-artifacts/netcool-runbook-smoke/`. The record holds no token and no identifier. Print the main keys with this command.

```powershell
Get-Content -Raw "<path of the evidence record>" | ConvertFrom-Json | Select-Object outcome_class, exit_code, request_count, request_budget, sdk_retry_possible
```

The record also holds the status of each check, the catalog names, and the answers to the live questions. The schema and the redaction rules are in `contracts/evidence.md`.

## 8. Remove old evidence

Each run writes a new file. Review the files before you remove them. The command below lists the files whose last write was more than seven days ago.

```powershell
Get-ChildItem -Path "test-artifacts\netcool-runbook-smoke" -Filter "*.json" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | Select-Object FullName
```

Remove each file by its full path after the review. Add `-WhatIf` to the command first, to see the result without a change.

```powershell
Remove-Item -Path "<full path of a file to remove>" -WhatIf
```
