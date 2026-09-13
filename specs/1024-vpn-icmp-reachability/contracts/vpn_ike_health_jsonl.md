# Contract: VPN IKE Health JSONL Telemetry (US3, optional in-scope)

**Feature**: 1024-vpn-icmp-reachability
**Module**: `src/utils/zscaler_probe.py`
**Kind**: Append-only file schema + write-side contract
**Applicability**: US3 only. If US3 is deferred, this contract does not
apply and no file is created.

## Scope

Documents the append-only JSONL file
`data/vpn_ike_health.jsonl` written by
`src/utils/zscaler_probe.py::run_full_validation()` — one line per VPN
host per invocation.

## File Path

`data/vpn_ike_health.jsonl` (relative to repository root).

- Encoding: UTF-8, explicit.
- Newline: `\n` (LF), explicit — not platform-default.
- Mode: append (`"a"`).
- Created on first write; never truncated.

## Line Schema (single-line JSON, no trailing whitespace)

```jsonc
{
  "ts": "2026-07-26T18:03:12Z",
  "hostname": "gateway.zscalerthree.net",
  "icmp_ok": true,
  "ike_500_ok": false,
  "ike_4500_ok": false
}
```

### Field-by-field

| Field | Type | Required | Semantics |
|-------|------|----------|-----------|
| `ts` | string | yes | ISO-8601 UTC, second precision, trailing `Z`. Produced by `datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")`. |
| `hostname` | string | yes | FQDN of the VPN host under probe. Lowercase preserved as passed. |
| `icmp_ok` | bool | yes | `True` if `_icmp_ping()` returned success for this host in this run. |
| `ike_500_ok` | bool | yes | `True` if `_udp_check(host, 500)` observed a valid IKEv2 response. |
| `ike_4500_ok` | bool | yes | `True` if `_udp_check(host, 4500)` observed a valid IKEv2 response (with non-ESP marker). |

### Field ordering

Deterministic key ordering is required for grep/diff-friendly telemetry:

```python
json.dumps(record, sort_keys=False, separators=(",", ":"))
```

with the record built as a `dict` in the exact order: `ts`, `hostname`,
`icmp_ok`, `ike_500_ok`, `ike_4500_ok`. Python 3.7+ preserves insertion
order; `sort_keys=False` keeps that. `separators` avoids extra spaces.

## Write-Side Contract

### Signature (new helper, private)

```python
def _append_ike_health_record(
    hostname: str,
    icmp_ok: bool,
    ike_500_ok: bool,
    ike_4500_ok: bool,
    *,
    path: pathlib.Path = pathlib.Path("data") / "vpn_ike_health.jsonl",
) -> None: ...
```

- `path` is injectable for tests (they will pass a `tmp_path`).
- No return value.
- Called once per VPN host per `run_full_validation()` invocation, after
  both `_icmp_ping()` and `_udp_check(500/4500)` have completed.

### Failure handling (FR-010)

```python
try:
    with path.open("a", encoding="utf-8", newline="") as fp:
        fp.write(json.dumps(record, separators=(",", ":")) + "\n")
except OSError as exc:
    logger.warning(
        "vpn_ike_health.jsonl append failed for %s: %s", hostname, exc
    )
    return
```

Exact behavior:

- Any `OSError` subclass (permission denied, disk full, file-not-found
  on parent dir, etc.) is caught.
- One `logger.warning` line per failed append.
- Function returns normally. `run_full_validation()` continues processing
  remaining hosts.
- No re-raise. No retry.

### Invariants

- **One line per host per run** (SC-005). If N VPN hosts are processed,
  exactly N lines are appended (or fewer if some appends fail, but
  never more).
- **Append-only** (SC-005 / spec Acceptance 3.3). The file is never
  truncated; prior records are preserved across runs.
- **Row order within a single run** matches the host-iteration order of
  `run_full_validation()` (which is deterministic per its own contract).
  Order across runs is chronological by append time.

## Test Boundaries

Tests live in
`tests/unit/utils/test_zscaler_probe.py::TestVpnIkeHealthJsonl` and MUST
cover:

- Happy path: mock `_icmp_ping` and `_udp_check`, call
  `run_full_validation` (or the helper directly) with a fixture host,
  assert one line in `tmp_path / "vpn_ike_health.jsonl"` with the
  expected schema and values.
- Append across two invocations: two `run_full_validation` runs with the
  same fixture produce two lines total, prior line preserved.
- Reachable-but-IKE-dead: `icmp_ok=True`, `ike_500_ok=False`,
  `ike_4500_ok=False` -> one line with those exact values (US3 Acceptance
  Scenario 1).
- IKE-healthy: `icmp_ok=True`, `ike_500_ok=True` -> one line
  (Acceptance Scenario 2).
- Failure swallow: monkeypatch `path.open` to raise `PermissionError`,
  assert `run_full_validation` still completes and a WARN log line is
  emitted (FR-010).
- Field ordering: read back the JSON line, assert the four keys appear
  in `ts, hostname, icmp_ok, ike_500_ok, ike_4500_ok` order.
- MUST NOT touch the network. MUST NOT write outside `tmp_path`.

## Non-Goals

- No reader implementation in this feature. A future report may consume
  the file; that consumer is out of scope.
- No rotation, no compaction, no size limit. The file grows unbounded;
  ops can `mv` or truncate manually. If growth becomes a problem, a
  later feature can add rotation without breaking this contract (append
  semantics are stable).
- No schema version field. If future fields are added, they will be
  additive and downstream readers must be tolerant of unknown fields.
- Latency fields (`ike_500_latency_ms`, `ike_4500_latency_ms`) are noted
  as a possible future extension but are NOT emitted in this feature.
