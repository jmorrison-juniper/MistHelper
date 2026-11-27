# Contract: Interactive login request timeout

**Scope**: The Python interfaces and the operator-visible messages of the interactive login request timeout. The contract changes no menu, no command flag, and no output file.

## 1. Constructor

`LoginOrchestrator(state, safe_input, detect_msp_privileges, request_timeout_seconds)`

- `request_timeout_seconds` is a whole number of seconds. It holds the value of `API_REQUEST_TIMEOUT`.
- The interactive initializer passes `_MH.API_REQUEST_TIMEOUT` (RC-14, RC-15).
- The argument is required. A caller that omits it fails at construction.

## 2. Method: `_apply_request_timeout(apisession)`

The method accepts one SDK session object. The object must expose `_new_session` and `_session`.

The method runs these steps in order:

1. Raise `ValueError` when `request_timeout_seconds` is zero or less. The message is `API_REQUEST_TIMEOUT must be a positive number of seconds`.
2. Log an info line before any change.
3. Raise `RuntimeError` when the object has no `_new_session` attribute. The message is `The Mist API SDK session has no transport factory for the request timeout`.
4. Replace `_new_session` on the object. The replacement calls the original factory, mounts one timeout adapter for `https://` and one for `http://`, and returns the transport.
5. Mount one timeout adapter for each scheme on the current `_session` transport.
6. Log a debug line after the change. The line contains no password, token, or session value.

After the method returns, each transport that the SDK builds carries the timeout adapter. The current transport carries it too.

## 3. Adapter: `RequestTimeoutAdapter`

The adapter extends `requests.adapters.HTTPAdapter` (RC-66). Its `send` method takes `request` and keyword arguments.

- When `timeout` is missing or `None`, the adapter sets `timeout` to `request_timeout_seconds`.
- When the caller sets `timeout`, the adapter keeps that value.
- The adapter creates no retry. Its `max_retries.total` value is 0.
- The adapter changes no URL and no header.

## 4. SDK hook (mistapi 0.64.1, pinned)

| Item | Source | Evidence |
| - | - | - |
| Transport factory `_new_session(self)` | `.venv\Lib\site-packages\mistapi\__api_session.py` line 193 | RC-54 |
| `_process_login` calls `self._new_session()` | same file, line 730 | RC-55 |
| `login_with_return` calls `self._new_session()` | same file, line 841 | RC-56 |
| Login URI `/api/v1/login` | same file, line 738 | RC-57, RC-41 |
| Two-factor URI `/api/v1/login/two_factor` | same file, line 1096 | RC-58, RC-42 |
| Current self URI `/api/v1/self` | same file, line 853, read through `mist_get` (`__api_request.py` line 260) | RC-88, RC-89, RC-43 |

The pin test `test_login_paths_call_the_transport_hook` fails when an SDK release removes the hook or a login path stops calling it.

## 5. Operator-visible messages

| Condition | Console line | Log line | Source |
| - | - | - | - |
| Zero or negative request timeout | `  X Authentication error: API_REQUEST_TIMEOUT must be a positive number of seconds` | `Interactive login value error: API_REQUEST_TIMEOUT must be a positive number of seconds` | `_handle_value_error`, `login_orchestrator.py` lines 258 to 267 |
| No transport factory | `  X Login failed: The Mist API SDK session has no transport factory for the request timeout` | `Interactive login failed: The Mist API SDK session has no transport factory for the request timeout` | `_handle_generic_error`, `login_orchestrator.py` lines 269 to 277 |
| Read timeout on a login request | `  X Authentication failed: Exception occurred during authentication` | SDK error log with the traceback | `_process_login`, `.venv\Lib\site-packages\mistapi\__api_session.py` lines 713 to 777, then `_report_auth_failure`, `login_orchestrator.py` lines 212 to 224 |
| Connect timeout on a login request | `  X Connection failed: <connection error text>` | `Interactive login connection error: <connection error text>` | `_process_login` raises `ConnectionError` (`__api_session.py` lines 713 to 777), then `_handle_connection_error`, `login_orchestrator.py` lines 251 to 256 |

Each console line starts with two spaces and the marker `X`, as the existing messages do. The file-level rows RC-04 and RC-54 hold the blob SHA of each cited file.

## 6. Non-goals

- The token path and `MistSessionConfigurator.configure_once` keep their behavior (RC-12).
- The contract adds no retry for any login request.
- The contract adds no new command flag and no new output column.
