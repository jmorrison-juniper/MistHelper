# Contract: Shared Test Fixtures

**Feature**: 1017-remove-coverage-omits
**Refs**: #878
**Applies to**: PR-3 through PR-8c
**Success criteria**: SC-003 (`fail_under=90`), SC-006 (no ad-hoc mocks). Frozen omit set is defined by SC-001 (6 non-source entries) — see contracts/coverage_assertion.md §3.

**Validation rule**: Every fixture listed below MUST be `@pytest.fixture`-decorated in the exact file path shown, MUST use function scope unless explicitly noted, and MUST match the return-type contract in this document. A test that imports a fixture from an unlisted path violates SC-006 (no ad-hoc mocks).

## §1 `mock_mistapi_session`

**Location**: `tests/conftest.py` (repo-wide) — introduced PR-3.
**Scope**: `function`.
**Returns**: `MagicMock(spec=mistapi.APISession)`.

**Contract**:
- Bound to the real `mistapi.APISession` symbol via `spec=` so attribute typos raise `AttributeError`.
- No default return values on `.mist_get`, `.mist_post`, `.mist_put`, `.mist_delete` — each test configures its own responses.
- MUST NOT be `autospec=True` (too slow for the ~200-test target); the `spec=` narrow form is sufficient.
- Consumers: PR-3 (api/analytics), PR-4a/b (org exporters), PR-5a/b (site exporters + reports), PR-6 (state-changing managers), PR-7 (SSH/TUI).

**Reference shape**:
```python
@pytest.fixture
def mock_mistapi_session():
    return MagicMock(spec=mistapi.APISession)
```

## §2 `mock_config`

**Location**: `tests/conftest.py` — introduced PR-3.
**Scope**: `function`.
**Returns**: `dict[str, Any]` mirroring the `.env` config schema loaded by `src/utils/environment_utils.py`.

**Contract**:
- Populated with placeholder credentials (`MIST_ORG_ID="00000000-0000-0000-0000-000000000000"`, `MIST_HOST="api.mist.com"`, `MIST_TOKEN="fake-token"`).
- Tests that mutate the dict must do so on a copy (`mock_config.copy()`) — the fixture returns a fresh dict per test.
- Consumers: same as `mock_mistapi_session`.

## §3 `mock_mistapi_paginated_response`

**Location**: `tests/unit/api/conftest.py` — introduced PR-3.
**Scope**: `function`.
**Returns**: factory callable `(pages: list[list[dict]]) -> MagicMock` that produces a mistapi paginated iterator mock.

**Contract**:
- Each `pages[i]` element becomes one call to `mistapi.get_next(...)`.
- Final call returns `None` to terminate the pagination loop.
- Consumers: PR-3 (api_data_fetcher, api_core_fetch_utils), PR-4a/b, PR-5a/b (exporters that page through devices/sites).

## §4 Golden-file writers: `golden_json_writer`, `golden_csv_writer`

**Location**: `tests/unit/export/conftest.py` — introduced PR-4a.
**Scope**: `function`.
**Returns**: callable `(payload, expected_filename) -> Path`.

**Contract**:
- Writes payload to `tmp_path / expected_filename`, then re-reads and returns parsed contents for assertion against a golden fixture file under `tests/unit/export/goldens/`.
- JSON writer uses `indent=2, sort_keys=True` for deterministic diffs.
- CSV writer preserves column order from the exporter under test — column-order regression is a hard failure.
- Consumers: PR-4a, PR-4b, PR-5a, PR-5b (all exporter tests).

## §5 `mock_paramiko_ssh_client`

**Location**: `tests/unit/ssh/conftest.py` — introduced PR-7.
**Scope**: `function`.
**Returns**: `MagicMock(spec=paramiko.SSHClient)` with `.invoke_shell()` returning `MagicMock(spec=paramiko.Channel)`.

**Contract**:
- `.connect()`, `.close()`, `.set_missing_host_key_policy()` are no-ops but recorded in `mock_calls` for assertion.
- Channel `.recv(n)` returns bytes controlled per-test via `.side_effect`.
- Consumers: PR-7 (`cli_shell_manager.py`).

## §6 `mock_sshkeyboard_listen`

**Location**: `tests/unit/ui/conftest.py` — extends existing conftest, introduced PR-7.
**Scope**: `function`.
**Returns**: `MagicMock` bound to `sshkeyboard.listen_keyboard` via `monkeypatch.setattr`.

**Contract**:
- Default behavior: immediately calls the registered `on_press` handler with a configurable keypress sequence, then returns.
- Consumers: PR-7 (`tui.py`).

## §7 `mock_websocket_transport`

**Location**: `tests/unit/websocket/conftest.py` — introduced PR-8a.
**Scope**: `function`.
**Returns**: `MagicMock(spec=websocket.WebSocketApp)` — sync `websocket-client`, NOT `websockets` (async).

**Contract**:
- `.run_forever()` MUST exit after ≤ 2 mocked message iterations (drive by `.side_effect` on `.send`).
- Callback registration (`on_message`, `on_error`, `on_close`) invoked synchronously by test setup, not by a real thread.
- Threading is NOT mocked — tests use `threading.Event.set()` to signal shutdown paths.
- Consumers: PR-8a (toplevel), PR-8b (diagnostics), PR-8c (polling).

## Fixture-migration invariants

- No fixture may be redefined in a nested conftest. Redefinition indicates spec drift and MUST be caught in PR review.
- A fixture introduced in a later PR MUST NOT be back-imported into an earlier PR — enforce with `pytest --collect-only` in CI.
- New fixtures added outside this contract require a spec amendment and a `Refs #878` sub-issue.
