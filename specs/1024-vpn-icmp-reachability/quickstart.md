# Quickstart: VPN Synthetic Probes Use Mist Reachability (ICMP)

**Feature**: 1024-vpn-icmp-reachability
**Phase**: 1 (Design output — validation guide)
**Date**: 2026-07-26

This is a runnable validation guide. It documents the scenarios that
prove the feature works end-to-end. Implementation details live in
`plan.md`, contracts, and (eventually) `tasks.md` — this file focuses on
"how do I confirm the change is right?"

## Prerequisites

- Repository at branch `1024-vpn-icmp-reachability`.
- Python 3.13+ available on `PATH`.
- Existing dev deps installed (`pip install -e ".[dev]"` or the
  equivalent used in CI). No new deps required by this feature.
- Fixture CENR snapshot(s) available under `tests/unit/utils/fixtures/`
  (already used by feature 1023 tests).

## Scenario A — US1 Acceptance 1: CENR bag VPN emits `reachability` bare hostname

**Setup**: Fixture CENR document with `vpn_hostnames`
containing `gateway.zscalerthree.net`. No observed traffic for the host.

**Run**:

```bash
cd tests
pytest unit/org/test_org_synthetic_probes_manager.py::TestProbeTargetVpn::test_cenr_bag_vpn_emits_bare_hostname -v
```

**Expected outcome**:

- Test passes.
- Emitted row for `gateway.zscalerthree.net` has `type == "reachability"`.
- Target field is exactly `"gateway.zscalerthree.net"` (no scheme, no
  `:500`, no `:4500`, no path).

Corresponds to spec Acceptance Scenario 1.

## Scenario B — US1 Acceptance 2: UDP-observed host emits `reachability`

**Setup**: Fixture with `edge-vpn.example.com` present only via observed
UDP/500 telemetry (not in any `vpn_hostnames` bag).

**Run**:

```bash
pytest unit/org/test_org_synthetic_probes_manager.py::TestProbeTargetVpn::test_udp_observed_emits_bare_hostname -v
```

**Expected outcome**:

- Emitted row for `edge-vpn.example.com` has `type == "reachability"`.
- Target is bare hostname `edge-vpn.example.com`.
- No `application`-type row exists for the same host in the emitted
  bundle.

Corresponds to spec Acceptance Scenario 2.

## Scenario C — US1 Acceptance 3: `-vpn.` pattern host emits `reachability`

**Setup**: Fixture with `fra4-vpn.zscalerthree.net` — no observed
traffic, no CENR bag entry. Matches `_is_vpn_host` catalogue-default
`-vpn.` pattern only.

**Run**:

```bash
pytest unit/org/test_org_synthetic_probes_manager.py::TestProbeTargetVpn::test_vpn_pattern_only_emits_bare_hostname -v
```

**Expected outcome**:

- Row for `fra4-vpn.zscalerthree.net` has `type == "reachability"` and
  bare-hostname target.

Corresponds to spec Acceptance Scenario 3.

## Scenario D — US1 Acceptance 4 + US2: Non-VPN TCP/443 unchanged

**Setup**: Fixture with a non-VPN host `example.com` observed on TCP/443.

**Run**:

```bash
pytest unit/org/test_org_synthetic_probes_manager.py::TestProbeTargetVpn::test_non_vpn_https_unchanged -v
```

**Expected outcome**:

- Row has `type == "application"`, target `"https://example.com"`.
- Byte-identical to the pre-1024 output for the same input (INV-1).

Corresponds to spec Acceptance Scenarios 4 and US2/1.

## Scenario E — US1 Acceptance 5 + US2: Non-VPN non-443 TCP unchanged

**Setup**: Non-VPN host `example.com` observed on TCP/8080.

**Run**:

```bash
pytest unit/org/test_org_synthetic_probes_manager.py::TestProbeTargetVpn::test_non_vpn_tcp_non443_unchanged -v
```

**Expected outcome**:

- Row has `type == "application"`, target `"example.com:8080"`.

Corresponds to spec Acceptance Scenario 5 and US2/2.

## Scenario F — INV-1 byte-stability regression guard

**Setup**: Full fixture bundle with a mix of VPN and non-VPN hosts.

**Run**:

```bash
pytest unit/org/test_org_synthetic_probes_manager.py::TestInv1ByteStability -v
```

**Expected outcome**:

- Test loads the expected smoke bundle from
  `tests/unit/org/fixtures/expected_smoke_bundle.json` (or an
  in-line-declared expected value).
- Filters both baseline and current output to non-VPN rows.
- `diff` is empty.

Corresponds to SC-003.

## Scenario G — Probe-type dispatch by shape

**Setup**: Direct unit tests on `_probe_type_for_target`.

**Run**:

```bash
pytest unit/org/test_org_synthetic_probes_manager.py::TestProbeTypeDispatch -v
```

**Expected outcome**:

- `https://example.com` -> `"application"`.
- `example.com:443` -> `"application"`.
- `example.com:8080` -> `"application"`.
- `example.com:500` -> `"application"` (defensive: catches pre-1024
  shape leakage if it ever recurs).
- `example.com` -> `"reachability"`.
- `role_type="application"` with target `example.com` -> `"reachability"`
  (shape wins).

Corresponds to FR-005 and contract `probe_type_dispatch.md`.

## Scenario H — US3 (optional in-scope): JSONL IKE health append

**Setup**: Monkeypatch `_icmp_ping` and `_udp_check` in
`src/utils/zscaler_probe.py`. Point the JSONL path at `tmp_path`.

**Run**:

```bash
pytest unit/utils/test_zscaler_probe.py::TestVpnIkeHealthJsonl -v
```

**Expected outcome**:

- One JSONL line appended per VPN host per invocation (SC-005).
- Second invocation appends a second line without truncating the first
  (US3 Acceptance Scenario 3).
- `PermissionError` during `.open("a")` results in one `WARN` log line
  and no exception propagation (FR-010).
- Field order in the emitted line is exactly
  `ts, hostname, icmp_ok, ike_500_ok, ike_4500_ok`.

Corresponds to US3 Acceptance Scenarios 1, 2, 3 and FR-009 / FR-010.

## Scenario I — End-to-end smoke via menu 206

**Setup**: Run against a fixture org that exercises all three
classifications.

**Run** (manual smoke; not a pytest):

```bash
python MistHelper.py --menu 206 --fixture tests/unit/org/fixtures/smoke_org.json --dry-run
```

**Expected outcome**:

- `custom_probes` in the printed dry-run payload contains at least one
  `type: reachability` row with a bare-hostname target.
- No row targets any VPN host with `:500`, `:4500`, `http://`, or
  `https://<vpn-host>`.
- Non-VPN rows visually match pre-1024 output for the same fixture.

Corresponds to SC-001, SC-002, SC-003, and the qualitative goal of SC-006.

## Full pytest sweep

Before marking implementation complete:

```bash
cd tests
pytest unit/ -v
```

All tests must pass, including feature 1023's tests (which are unchanged)
and the updated feature 1024 tests.

## Ruff / Black / mypy / interrogate / pydoclint

Existing gates from `pyproject.toml` and CI:

```bash
ruff check src/ tests/
black --check src/ tests/
mypy src/
interrogate -c pyproject.toml src/
pydoclint --style=google src/
```

All must pass. This feature does not relax any gate.

## References

- Spec: `specs/1024-vpn-icmp-reachability/spec.md`
- Plan: `plan.md`
- Contracts: `contracts/probe_type_dispatch.md`,
  `contracts/vpn_probe_target_shape.md`,
  `contracts/vpn_ike_health_jsonl.md`
- Data model: `data-model.md`
