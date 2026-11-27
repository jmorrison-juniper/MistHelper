# Contract: SDK Login Calls of the Interactive Login

This contract describes the mistapi calls of the interactive login and the SDK console output at the new level. The installed SDK is version 0.64.1 (RC-73). The SDK source is read from the local `.venv` copy, and each row cites its line.

## Identity

- Package: `mistapi`, installed from the pin `mistapi==0.64.1` (RC-45).
- Callers: `LoginOrchestrator._create_api_session` builds the session. `LoginOrchestrator._initial_login` makes the first login call. `LoginOrchestrator._handle_two_factor` makes the 2FA replay call.
- Source of the caller lines: `src/mist/access/auth/interactive/login_orchestrator.py` (remote blob fd475be9467068e6c34a819697c3c46235801047). The constructor call is at line 138, and its arguments are at lines 139 to 143. The console level argument is at line 142.

## Constructor

| Argument | Value | Change |
|----------|-------|--------|
| `email` | Operator email | unchanged |
| `password` | Operator password | unchanged |
| `host` | Selected cloud host | unchanged |
| `console_log_level` | 30 | changed from 20 |
| `show_cli_notif` | False | unchanged |

The constructor calls the shared console level setter on each construction (RC-68). The default level of the constructor is 20 (RC-69). The shared console object serves the whole SDK (RC-71).

## Login calls

| Call | Arguments | SDK path | Result shape |
|------|-----------|----------|--------------|
| First login | None | Sends a POST to `/api/v1/login` (RC-74), then reads `/api/v1/self` (RC-76) | `{"authenticated": bool, "error": text or dictionary}` |
| 2FA replay | `email`, `password`, `two_factor` | Replays the password POST, then posts the code to `/api/v1/login/two_factor`, then reads `/api/v1/self` | `{"authenticated": bool, "error": text or dictionary}` |

The OpenAPI file names the endpoints (RC-59 for `/api/v1/login`, RC-60 for `/api/v1/login/two_factor`, and RC-61 for `/api/v1/self`). The SDK method `login_with_return` is the public method that returns the dictionary (RC-75).

On success the SDK returns `authenticated` true with an empty error. On failure it returns `authenticated` false with the error detail.

## SDK console lines at level 30

| SDK line | Level | Printed at 30 | Remote row |
|----------|-------|---------------|------------|
| `Authentication successful!` | INFO | No | RC-66 |
| `2FA authentication succeeded` | INFO | No | RC-67 |
| `Authentication failed: <detail>` | ERROR | Yes | RC-80 |

The SDK console prints one label and one message for each line (RC-70). The shared console object (RC-71) and the SDK logger `mistapi` (RC-72) are separate outputs. The logger records follow `CONSOLE_LOG_LEVEL`, because the root console handler decides which records reach the terminal (RC-30). This change does not filter the logger records.

## Failure handling

- A proxy or connection failure raises `ConnectionError` inside the SDK. The orchestrator maps the error to a failure line (unchanged).
- A refused password returns `authenticated` false. The orchestrator prints the failure line (unchanged).
- A refused 2FA code returns `authenticated` false with the error `2FA authentication failed`. The orchestrator prints the failure line and prints no 2FA success line.

## Contract tests

| Test | Status | Purpose |
|------|--------|---------|
| `test_two_factor_login_resends_credentials_with_installed_sdk` | unchanged | Proves the 2FA replay uses the installed SDK |
| `test_http_503_login_clears_session_and_reports_server_failure` | unchanged | Proves a server refusal does not succeed |
| `test_returns_session_and_clears_token` | updated | Pins the constructor argument `console_log_level=30` |
| `test_sdk_success_line_stays_off_console` | new | Runs the real SDK with a patched HTTP session and proves no INFO success line and one ERROR line for a refused password |
| `test_accepted_2fa_code_prints_success_line` | new | Proves the 2FA success line appears only after `authenticated` is true |
| `test_refused_2fa_code_prints_no_success_line` | new | Proves the 2FA success line does not appear after a refusal |
