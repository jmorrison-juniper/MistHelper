# Quickstart: reproduce the evidence and verify the change

Run section A only during this specification phase. It uses read-only GitHub calls.
Run section B only during the implementation phase. The specification phase runs no gate.

## A. Reproduce the evidence (read-only)

Set the GitHub host and the token variable before each `gh` command. Never print the token value.

1. Set the host.
   `$env:GH_HOST='github.com'`
2. Set the token from the account variable.
   `$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper`
3. Read the steps of the failing job. The call is a GET request.
   `gh api repos/jmorrison-juniper/MistHelper/actions/jobs/111057821335 --jq '.steps[] | [.name, .conclusion, .started_at, .completed_at] | @tsv'`
   Expected: `Run E2E smoke tests` is `cancelled` from 22:38:02Z to 22:51:56Z.
4. Read the check-run annotations of the failing job.
   `gh api repos/jmorrison-juniper/MistHelper/check-runs/111057821335/annotations --jq '.[] | [.annotation_level, .message] | @tsv'`
   Expected: the message `The job has exceeded the maximum execution time of 15m0s`.
5. Read the log with escape sequences allowed. Strip the escape sequences in memory. Do not write the log to a file.
   `gh api repos/jmorrison-juniper/MistHelper/actions/jobs/111057821335/logs --allow-escape-sequences`
6. Count the outcome lines. Use this pattern after the timestamp: `(tests/\S.*?) +(PASSED|FAILED|SKIPPED|ERROR|XFAIL|XPASS)`.
   Expected: 442 distinct IDs, 391 PASSED, and 51 SKIPPED. The last PASSED line is at 22:44:48.678Z.
7. Search the same log for pytest-timeout report text. Use the case-sensitive pattern `Timeout \(>`.
   Expected: no match.
8. Repeat steps 5 to 7 for the stall-class jobs 116833147946, 116842182317, and 116850242205.
   Expected: the last PASSED line is `test_progress_region_shows_every_section_of_the_status_body`, and the silence before the cancel is 104 to 188 seconds.

## B. Verify the change (implementation phase)

Run each command from the repository root. Record each result in the pull request body.

1. `python -m py_compile tests/e2e/conftest.py`
2. `python -m ruff check tests/e2e/conftest.py tests/guardrails`
3. `python -m black --check tests/e2e/conftest.py tests/guardrails`
4. `python -m mypy $MYPY_PATHS --config-file pyproject.toml`, with `MYPY_PATHS` read from `.github/workflows/ci.yml`
5. `python -m pytest tests/guardrails/e2e_timeout_budget/test_timeout_budget.py -q`
6. `python -m pytest tests/guardrails/test_e2e_shard_partition.py tests/guardrails/test_ci_runtime_budgets.py tests/guardrails/e2e_timeout_budget/test_browser_installation.py -q`
7. `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`
8. `ste-linter --config .ste-linter.toml --min-score 80 documentation/quality-gates.md`
9. `git diff --name-only origin/main` and confirm that no listed path starts with `src/`, `web_portal/`, or `container/`, and that `Containerfile` and `compose.yml` are absent.

## C. Read a stall after a local run

1. Open the trail file in `test-artifacts/e2e-phase-trail.jsonl`.
2. Find the last line with `"phase": "protocol_start"`. Its `node_id` names the item that was open.
3. If no later line has `"phase": "protocol_end"` for that `node_id`, the item stalled or was interrupted.
4. Open `test-artifacts/e2e-stack-dumps.txt`. Find the line that begins with `Timeout (`. Read the frames of the main thread first.
