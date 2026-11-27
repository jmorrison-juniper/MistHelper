# Quickstart: Report a Mist transport fault as an unavailable Mist API

Use these steps to reproduce the defect, to verify the repair, and to run the gates. Use fake values only. Do not use a production credential.

## Prerequisites

1. Create a worktree from `origin/main` on the branch `fix/4748-mist-token-timeout-unavailable` (task T001).
2. Use the project virtual environment. Run each command from `mist-ops-platform/`.
3. Keep test evidence in the git-ignored folder `test-artifacts/`, if a run needs an output file.

## Scenario 1: Red run before the change

Run the new tests on the untouched code. Each behavior test must fail.

```text
python -m pytest tests/unit/api/test_auth.py -q -k "read_timeout or connection_error or http_429 or malformed or environment or contract"
```

Expected before the change:

- The tests for read timeout, connection error, HTTP 429, malformed token, environment isolation, and log redaction fail.
- The SDK contract tests `test_sdk_read_timeout_drops_token_contract` and `test_sdk_rejected_token_raises_value_error_contract` pass. They document the SDK and pass before and after the change.

The autouse guard in `test_auth.py` blocks any unmocked network call. A red run therefore cannot reach the live Mist cloud.

## Scenario 2: Issue reproduction, offline

The issue reproduction uses mocked HTTP. Each step maps to one test.

1. Make the privilege lookup request raise `requests.exceptions.ReadTimeout`. Call `AuthService().validate_token` with a fake token. Expect `MistApiUnavailableError`. Test: `test_fetch_self_read_timeout_reports_unavailable`.
2. Make the privilege lookup request return HTTP 401. Call the same method. Expect empty privileges. Test: `test_fetch_self_returns_empty_privileges_on_401`.
3. Make the privilege lookup request return HTTP 200 with an identity object. Expect the identity and its privileges. Test: `test_fetch_self_identity_object_returns_privileges`.

Build each mocked response with a prepared request. The SDK reads `resp.request.headers` before it checks the status (`mistapi\__api_request.py` L217 and L219). A response without a request raises before the status check and skips the failure branch.

```text
requests.Response with status_code, reason, url, and _content set
response.request equals requests.Request with method GET and the same url, prepared
```

## Scenario 3: Environment isolation

Set fake process environment values with `monkeypatch`. Use these names and fake values only.

```text
monkeypatch.setenv("MIST_APITOKEN", "fake-environment-token")
monkeypatch.setenv("MIST_HOST", "api.eu.mist.com")
```

Call `AuthService().validate_token` with the fake supplied token `fake-supplied-token`. Expect:

- One request to `https://api.mist.com/api/v1/self`.
- The Authorization header equals `Token fake-supplied-token`.
- No request carries `fake-environment-token`.

Test: `test_validation_session_sends_only_supplied_token_to_self_endpoint`.

## Scenario 4: Green run after the change

```text
python -m pytest tests/unit/api/test_auth.py tests/unit/api/test_session_security.py tests/unit/api/test_health.py -q
python -m pytest tests/unit/mist/test_list_status.py tests/unit/mist/test_consumer_registry_usage.py -q
```

Expected: every test passes. The count of new and updated tests is 20.

## Scenario 5: Ops platform gates

```text
pytest --cov=src --cov-fail-under=56 --timeout=120
ruff check . --select F,B,E9 --ignore F401,B008,B905 --output-format=concise
```

Expected: at least 390 tests are collected, coverage is at least 56 percent, and Ruff reports no finding.

## Scenario 6: Root gates for changed files

Run these commands from the repository root. Give each changed Python file on its own command line.

```text
python -m py_compile mist-ops-platform/src/shared/services/auth.py
python -m py_compile mist-ops-platform/src/shared/mist/endpoints.py
python -m py_compile mist-ops-platform/src/shared/mist/types.py
bandit -c pyproject.toml -r mist-ops-platform/src -q
ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4748-mist-token-timeout-unavailable.md
```

Expected: each compile command has no output. Bandit reports no finding. The STE linter scores 80 or above.
