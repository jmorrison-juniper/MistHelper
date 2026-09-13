# Contract: Probe-Type Dispatch By Target Shape

**Feature**: 1024-vpn-icmp-reachability
**Module**: `src/org/org_synthetic_probes_manager.py`
**Kind**: Internal Python API contract (private function)

## Scope

Documents the target-shape -> probe-type classifier that all row-emission
callsites (`_build_probe_set`, `_build_region_probes`, `_merge_probes`)
call to decide whether an emitted row carries `type: application` or
`type: reachability`.

## Signature

```python
def _probe_type_for_target(target: str, role_type: str | None = None) -> str: ...
```

- `target`: The final, already-built target string that will be written
  into the `custom_probes[i].target` field of the emitted payload.
- `role_type`: Legacy hint from upstream classification (e.g. `"application"`
  supplied by role metadata). Retained for backwards compat only and
  dominated by the shape check below.

## Return

Exactly one of the two literal strings:

- `"application"`
- `"reachability"`

## Decision Rule

```text
if target starts with "http://" or "https://":
    return "application"
if target contains ":" after any ".":
    # A ":port" suffix is present (no scheme, since the first branch
    # already caught schemed targets).
    return "application"
return "reachability"
```

### Detection details

- **Scheme detection**: case-sensitive prefix match on `"http://"` and
  `"https://"`. Targets emitted by this codebase are always lowercase;
  no normalization required.
- **Port detection**: look for a `":"` character after the last `"."`
  in `target`. This avoids false positives on IPv6-literal targets
  (unsupported by Mist Marvis Minis today; if support arrives, revisit).
  A bare `host` has no `:`; a `host:port` has exactly one `:` after the
  last `.`.
- **`role_type` is not consulted for the decision.** It is kept in the
  signature so existing callers continue to compile. Removal is a
  follow-up cleanup, not part of this feature.

## Invariants Enforced

- **INV-2** (shape=type, from `data-model.md`): every emitted row's
  `type` matches the shape of its `target`.
- **INV-3** (VPN never L4): coupled with the VPN-target contract
  (`vpn_probe_target_shape.md`), VPN rows always have bare-hostname
  targets and therefore always return `reachability` here.

## Post-Conditions

- Return is one of the two literal strings above.
- Return is deterministic: for the same `target`, always returns the same
  value.
- Function is pure — no I/O, no logging beyond `logger.debug` for trace
  visibility.

## Logging

- `logger.debug("probe_type: target=%s -> %s", target, decision)` after
  the return decision. No WARN or INFO from this function; the emitting
  callsite handles higher-severity logging per Principle VII.

## Test Boundaries

Tests live in
`tests/unit/org/test_org_synthetic_probes_manager.py::TestProbeTypeDispatch`
and MUST cover:

- `https://example.com` -> `"application"`
- `http://example.com` -> `"application"`
- `example.com:443` -> `"application"` (bare host:port, non-standard shape)
- `example.com:8080` -> `"application"`
- `example.com:500` -> `"application"` (guards against pre-1024 shape leakage)
- `example.com` -> `"reachability"`
- `gateway.zscalerthree.net` -> `"reachability"` (the primary US1 case)
- `role_type` parameter set to `"application"` with a bare hostname
  target -> still `"reachability"` (shape wins)
- MUST NOT touch the network.

## Non-Goals

- The function does not validate FQDN syntax.
- The function does not deduplicate or reorder rows.
- IPv6-literal targets are out of scope; assumed unsupported by Mist
  reachability probes at this time.
