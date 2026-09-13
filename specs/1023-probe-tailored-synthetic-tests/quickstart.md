# Quickstart: Probe-Tailored Synthetic Tests

**Feature**: 1023-probe-tailored-synthetic-tests
**Purpose**: Runnable validation scenarios that prove the feature works
end-to-end after implementation. Use these to verify each User Story is
observably delivered.

## Prerequisites

- Python 3.13+ venv activated at repository root.
- Working `data/zscaler_cenr_hostnames.json` (either freshly refreshed or a
  captured fixture).
- Working `data/zscaler_client_connector_probes.json`.
- No network access needed for scenarios 1-3 (all mocked). Scenario 4 is a
  manual acceptance run that DOES touch the network.

## Setup

```bash
# From repo root
cd "C:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper"
python -m venv .venv
. .venv/Scripts/activate   # or `source .venv/bin/activate` on POSIX
pip install -e .
```

Confirm the baseline test suite:

```bash
cd src
pytest -q
# Expect: 8719+ passing (baseline), 0 failures.
```

## Scenario 1: UDP probe returns "open" on mocked responder (User Story 2)

**Goal**: Verify `_udp_check` returns `"open"` when a datagram is received.

**Command**:

```bash
pytest tests/unit/utils/test_zscaler_probe.py::test_udp_check_returns_open_on_datagram -v
```

**Expected**: Test passes. Log output includes the mandated action-logging
line `udp_check: sending IKE_SA_INIT to <host>:500` before send and
`udp_check: <host>:500 -> open` after recv.

## Scenario 2: `_probe_fqdn` triggers UDP for `*-vpn.` hosts (User Story 2)

**Goal**: Verify hostname-based trigger predicate branch (a).

**Command**:

```bash
pytest tests/unit/utils/test_zscaler_probe.py::test_probe_fqdn_triggers_udp_for_vpn_hostname -v
```

**Expected**: Test passes. Assertion confirms `result.udp[500] == "open"`
and `"UDP/500"` is in `result.responding_protocols`.

## Scenario 3: `_probe_fqdn` triggers UDP when all TCP dead (User Story 2)

**Goal**: Verify all-TCP-dead safety-net branch (b).

**Command**:

```bash
pytest tests/unit/utils/test_zscaler_probe.py::test_probe_fqdn_triggers_udp_when_all_tcp_dead -v
```

**Expected**: Test passes for a non-`-vpn.` hostname whose every TCP port
returned `"no_reply"`. UDP probes fire; result records outcomes in
`result.udp`.

## Scenario 4: Cache schema v3 write + v2 backward-compat read (User Story 3)

**Goal**: Verify observations persist and v2 caches still load.

**Command**:

```bash
pytest tests/unit/utils/test_zscaler_catalogue.py -k "schema_v3 or v2_compat" -v
```

**Expected**: All tests pass. A v3 round-trip preserves observation fields;
a v2 fixture loads without exception and produces one
`logger.info` line about missing observations.

## Scenario 5: URL builder three-branch priority (User Story 1)

**Goal**: Verify `_probe_target` prefers observations over catalogue
default and emits the WARN on missing observation.

**Command**:

```bash
pytest tests/unit/org/test_org_synthetic_probes_manager.py -k "probe_target" -v
```

**Expected**: All three branches (UDP-family, HTTPS/TCP-443, missing) are
green. `caplog` asserts the WARN string exactly once for Branch 3.

## Scenario 6: Full suite green after implementation

**Goal**: SC-003 gate.

**Command**:

```bash
cd src
pytest -q
```

**Expected**: `>= 8719 + N` passing tests, 0 failures, where `N` is the
count of newly added tests from Scenarios 1-5.

## Scenario 7 (manual): End-to-end Menu 206 dry run against a real org

**Goal**: SC-001 and SC-008 gates. Requires operator env with Mist token.

**Command sketch**:

1. Activate venv, cd to `src/`.
2. Delete or timestamp-invalidate `data/zscaler_cenr_hostnames.json` so
   `ensure_fresh` triggers a real refresh.
3. Launch MistHelper and choose Menu **206** on a small test org.
4. Inspect the generated `custom_probes` payload before it is PUT to Mist
   (existing dry-run/preview path in menu).

**Expected**:

- Zero `custom_probes[i].target` values match `^https://.*-vpn\.`.
- At least one VPN endpoint appears as `<host>:500` (or `:4500`).
- Every HTTPS-observed host retains `https://<host>` shape.
- `data/zscaler_cenr_hostnames.json` now shows
  `"schema_version": 3` and populated `observed_protocol` / `observed_port`
  / `last_probed` fields for every host that responded.

## References

- Contracts:
  - [`contracts/probe_result.md`](./contracts/probe_result.md)
  - [`contracts/cenr_cache_schema_v3.md`](./contracts/cenr_cache_schema_v3.md)
  - [`contracts/probe_target_url_builder.md`](./contracts/probe_target_url_builder.md)
- Data model: [`data-model.md`](./data-model.md)
- Research: [`research.md`](./research.md)
- Plan: [`plan.md`](./plan.md)
- Spec: [`spec.md`](./spec.md)
