# Data Model: VPN Synthetic Probes Use Mist Reachability (ICMP)

**Feature**: 1024-vpn-icmp-reachability
**Phase**: 1 (Design)
**Date**: 2026-07-26

Feature 1024 does not introduce new persistent schemas at the Mist API
boundary — it changes the *shape* of an existing emitted row for one
subset of targets. US3 introduces one new append-only JSONL file. Both
are documented below.

## 1. Synthetic-test row (emitted to Mist)

A single entry in the `custom_probes` list within the payload emitted by
menu 206 (`updateOrgSettings`).

### Shape (unchanged fields elided)

```jsonc
{
  "type": "application" | "reachability",   // dispatched by target shape
  "target": "<per-classification>",         // see below
  "name": "<probe name, unchanged>",
  // other fields (aggressiveness for critical probes, etc.) unchanged
}
```

### Target-field contract by classification

| Classification | Example input | `type` | `target` shape | Example output |
|----------------|---------------|--------|----------------|----------------|
| VPN (any source: CENR `vpn_hostnames` bag, UDP observation, or `-vpn.` pattern) | `gateway.zscalerthree.net` in `vpn_hostnames` bag | `reachability` | bare hostname (no scheme, no port) | `gateway.zscalerthree.net` |
| Non-VPN, observed HTTPS/TCP-443 | `example.com` observed on TCP/443 | `application` | `https://<host>` (elided :443) | `https://example.com` |
| Non-VPN, observed non-443 TCP | `example.com:8080` observed on TCP/8080 | `application` | `<host>:<port>` (bare, no scheme) | `example.com:8080` |
| Non-VPN, no observation (fallback) | catalogue default HTTPS/443 | `application` | `https://<host>` | `https://example.com` |

### Invariants

- **INV-1** (byte stability, feature 1023): For a fixed input snapshot,
  every non-VPN row is byte-identical before and after this feature.
  Enforced by test (SC-003, FR-007).
- **INV-2** (shape=type): The row's `type` is derived from the shape of
  its `target`. No row may have `type: application` with a bare hostname,
  and no row may have `type: reachability` with a scheme or port.
- **INV-3** (VPN never L4): No row for a VPN-classified host may contain
  `:500`, `:4500`, `https://`, or `http://`.

## 2. VPN classification input (in-memory)

Per-host metadata consulted by `_is_vpn_host()` and the row builder. No
persistence changes; documented here so the contract with the classifier
is explicit.

### Shape

```python
class VpnClassificationInput:
    """Per-host input used by _is_vpn_host + emit callsites."""

    fqdn: str
    cenr_bag_membership: bool          # host is in a CENR vpn_hostnames bag
    observed_transport: str | None     # e.g. "UDP", "UDP/500", "TCP/443", None
    observed_port: int | None
    hostname_matches_vpn_pattern: bool # matches _is_vpn_host's "-vpn." rule
```

### Derived classification rule

```text
is_vpn(input) := input.cenr_bag_membership
              OR input.observed_transport.startswith("UDP")
              OR input.hostname_matches_vpn_pattern
```

Precedence (from spec Edge Cases): the CENR bag wins over TCP/443
observation on the same host — a bag member is VPN even if TCP/443 is
also seen (Zscaler admin-console traffic).

## 3. VPN IKE health record (US3 only, optional in-scope)

One line per VPN host per `run_full_validation()` invocation, appended
to `data/vpn_ike_health.jsonl`.

### Shape

```jsonc
{
  "ts": "2026-07-26T18:03:12Z",           // ISO-8601 UTC, second precision
  "hostname": "gateway.zscalerthree.net",
  "icmp_ok": true,
  "ike_500_ok": false,
  "ike_4500_ok": false
}
```

### Field contract

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `ts` | string (ISO-8601 UTC) | yes | `datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")` |
| `hostname` | string | yes | The FQDN under probe |
| `icmp_ok` | bool | yes | `ProbeResult.icmp_ok` from `_icmp_ping()` |
| `ike_500_ok` | bool | yes | Truthy `ProbeResult.udp[500]` slot from `_udp_check(500)` |
| `ike_4500_ok` | bool | yes | Truthy `ProbeResult.udp[4500]` slot from `_udp_check(4500)` |

### Semantics

- One line per VPN host per run. If `run_full_validation()` processes N
  VPN hosts in one 8h refresh cycle, exactly N lines are appended
  (SC-005).
- File is created on first write; not truncated on subsequent runs.
- Line format: single-line JSON followed by `\n`. UTF-8 encoding
  explicitly declared on file open.
- On write failure (permission, disk full, path missing), the failure
  is logged at WARNING and `run_full_validation()` continues (FR-010).

### Storage location

- Path: `data/vpn_ike_health.jsonl` relative to the repository root.
- Directory `data/` is assumed to exist (already used by
  `TelemetryEmitter`). If it does not, the write raises `FileNotFoundError`
  which is caught by the FR-010 handler.

### Consumers (out of scope for this feature)

A future report (not this feature) will read the JSONL and surface
reachable-but-IKE-dead edges. This feature only writes.

## References

- Spec: `specs/1024-vpn-icmp-reachability/spec.md` §Key Entities, §FR-009, §FR-010
- Research: `research.md` §Decision 4
- Contracts: `contracts/vpn_probe_target_shape.md`, `contracts/probe_type_dispatch.md`,
  `contracts/vpn_ike_health_jsonl.md`
