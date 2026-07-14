# Contract: Mocking Conventions

**Feature**: 1017-remove-coverage-omits
**Refs**: #878
**Applies to**: PR-1 through PR-8c (all new unit tests)
**Success criteria**: SC-006 (no bare mocks), SC-007 (zero live network calls), SC-003 (`fail_under=90` after this convention holds). Frozen retained omit set is authoritative under SC-001 (6 non-source entries) — see contracts/coverage_assertion.md §3.

**Validation rule**: Every mock of an external dependency (mistapi, paramiko, websocket-client, python-arango, redis, sshkeyboard) MUST be constructed via `MagicMock(spec=<real class>)` or `monkeypatch.setattr(<import path>, <fake>)`. Bare `Mock()` or `MagicMock()` without `spec=` is a hard rejection in code review (attribute typos escape detection and cause false-positive coverage).

## §1 mistapi — sync HTTP session

**Real class**: `mistapi.APISession`.

```python
from unittest.mock import MagicMock
import mistapi

session = MagicMock(spec=mistapi.APISession)
session.mist_get.return_value = {"result": [{"id": "abc"}]}
```

**Rules**:
- Never mock `mistapi.get_next` at module level — mock the paginator via the `mock_mistapi_paginated_response` fixture (contracts/shared_fixtures.md §3).
- HTTP verbs (`mist_get`/`mist_post`/`mist_put`/`mist_delete`) return dicts, not `requests.Response` — mistapi already unwraps the JSON body.
- The `SC-007` invariant (zero live network calls) is enforced by `podman run --network=none` in CI. A test that hits the network under mocks-only mode indicates missing coverage of the mistapi call site.

## §2 paramiko — SSH transport

**Real class**: `paramiko.SSHClient`, `paramiko.Channel`.

```python
from unittest.mock import MagicMock
import paramiko

client = MagicMock(spec=paramiko.SSHClient)
channel = MagicMock(spec=paramiko.Channel)
client.invoke_shell.return_value = channel
channel.recv.side_effect = [b"prompt> ", b"output\n", b""]  # empty = EOF
```

**Rules**:
- Never let a real `paramiko.SSHClient()` instance be constructed in a unit test — patch at the import site (`src.ssh.cli_shell_manager.SSHClient`) not the module (`paramiko.SSHClient`).
- `set_missing_host_key_policy` MUST be exercised by every SSH test (host-key discipline).
- Real connections belong under `@pytest.mark.integration` — excluded from default CI (SC-007).

## §3 websocket-client — sync WebSocketApp + threading

**Real class**: `websocket.WebSocketApp`. Project uses the **synchronous** `websocket-client` package, NOT the async `websockets` package.

```python
from unittest.mock import MagicMock
import websocket

app = MagicMock(spec=websocket.WebSocketApp)
```

**Rules**:
- `run_forever()` MUST be configured to exit after ≤ 2 iterations. Real callbacks accept `(ws, message)` positional args — validate signatures with `spec=`.
- Threading is real in tests — do not mock `threading.Thread`. Use `threading.Event().set()` to trigger shutdown paths.
- Injected utility deps (config, logger, safe_input) MUST be passed via constructor and mocked by the caller. Global patching of `safe_input` is acceptable only inside interactive-prompt tests.

## §4 python-arango — DB session

**Real class**: `arango.database.StandardDatabase`.

```python
from unittest.mock import MagicMock
import arango.database

db = MagicMock(spec=arango.database.StandardDatabase)
db.collection.return_value.insert.return_value = {"_key": "abc"}
```

**Rules**:
- Never construct a real `ArangoClient` in unit tests.
- `database_schema_utils.py` is a pure string builder — NO DB fixture required (verified in research.md §2).
- Integration-only DB tests live under `tests/integration/db/` and require live ArangoDB reachable — excluded from default CI.

## §5 redis — cache / timeseries

**Real class**: `redis.Redis` (sync client used by the project).

```python
from unittest.mock import MagicMock
import redis

client = MagicMock(spec=redis.Redis)
client.get.return_value = None
client.set.return_value = True
```

**Alternative**: `fakeredis.FakeStrictRedis()` for tests that need round-trip fidelity on hash/list operations. Do NOT mix `MagicMock` and `fakeredis` in the same test — pick one per test.

## §6 sshkeyboard — TUI key listener

**Real callable**: `sshkeyboard.listen_keyboard`.

```python
def fake_listen(on_press=None, **kwargs):
    on_press("q")  # simulate quit keypress and return
monkeypatch.setattr("sshkeyboard.listen_keyboard", fake_listen)
```

**Rules**:
- The real listener blocks forever — tests MUST replace it, never call it.
- Use the `mock_sshkeyboard_listen` fixture from `tests/unit/ui/conftest.py` (contracts/shared_fixtures.md §6) rather than inline patching.

## §7 stdin / interactive prompts (`safe_input`)

```python
monkeypatch.setattr("src.ui.prompt_utils.safe_input", lambda *_, **__: "UPGRADE")
```

**Rules**:
- Patch at the **import site** where `safe_input` is called (e.g., `src.firmware.firmware_manager.safe_input`), not the definition site — otherwise the patch is invisible to the module under test.
- Every state-changing manager (PR-6) MUST test BOTH accept AND reject responses. Constitution Principle III non-negotiable.

## §8 Filesystem

```python
def test_writer(tmp_path):
    output = tmp_path / "out.csv"
    writer(output)
    assert output.read_text().startswith("col1,col2")
```

**Rules**:
- Use pytest's `tmp_path` fixture — never write to the repo working tree or system temp directly.
- For golden-file comparisons, use the `golden_json_writer` / `golden_csv_writer` fixtures (contracts/shared_fixtures.md §4).

## §9 Rejection criteria (grep-checkable in PR review)

```bash
# Reject: bare Mock without spec=
grep -rn "= MagicMock()" tests/unit/ && exit 1
grep -rn "= Mock()" tests/unit/ && exit 1

# Reject: real network calls
grep -rn "requests\.get\|requests\.post" tests/unit/ && exit 1
grep -rn "paramiko\.SSHClient()" tests/unit/ && exit 1

# Reject: patching the wrong site
grep -rn 'monkeypatch\.setattr("mistapi\.' tests/unit/ && exit 1
```

Any hit above is a hard PR rejection.
