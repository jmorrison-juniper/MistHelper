# Contract: VPN `_probe_target` Emits Bare Hostname

**Feature**: 1024-vpn-icmp-reachability
**Module**: `src/org/org_synthetic_probes_manager.py`
**Kind**: Internal Python API contract (VPN branches of a private function)

## Scope

Documents the shape of the value returned by `_probe_target()` when the
target FQDN is VPN-classified. Complements
`specs/1023-probe-tailored-synthetic-tests/contracts/probe_target_url_builder.md`
(the three-branch dispatch for the *non-VPN* half of the function). This
contract narrows the VPN half: pre-1024 returned `f"{fqdn}:500"` for VPN
hosts; post-1024 returns the bare `fqdn`.

## Signature (unchanged)

```python
def _probe_target(fqdn: str, role: str, cenr_source: dict[str, Any]) -> str: ...
```

## Preconditions

- Same as feature 1023: `cenr_source` is the loaded, v3-shaped CENR
  document.
- The caller has *already* determined the classification via
  `_is_vpn_host(fqdn, cenr_source)` OR is calling `_probe_target()`
  unconditionally and expects the function to internally re-classify.

## VPN Branch — Decision

If any of the three VPN conditions applies to `fqdn`:

1. `fqdn` is a member of any `vpn_hostnames` bag in `cenr_source`
   (top-level or `by_city[*]`), OR
2. `fqdn`'s v3 entry has `observed_protocol` starting with `"UDP"`, OR
3. `_is_vpn_host(fqdn, cenr_source)` returns `True` (catalogue-default
   `-vpn.` pattern fallback),

then:

```python
return fqdn
```

The return value is:

- The bare FQDN string, exactly as passed in (case preserved).
- No scheme prefix.
- No `:port` suffix.
- No trailing whitespace or path.

## Non-VPN Branches — Unchanged

For non-VPN targets, the three-branch dispatch from feature 1023 is
preserved verbatim:

- **Branch 1** (UDP-family or non-HTTP TCP observation): returns
  `f"{fqdn}:{observed_port}"` — bare `host:port`, no scheme.
- **Branch 2** (HTTPS/TCP-443 observation): returns `f"https://{fqdn}"`.
- **Branch 3** (no observation fallback): builds from
  `cenr_source["probe_default"]`; if the default is HTTPS/443, elides
  the port to `https://{fqdn}`.

The VPN check runs **before** these branches. If the target is
VPN-classified, none of the three non-VPN branches execute.

## Ordering Contract

```text
_probe_target(fqdn, role, cenr_source):
    if is_vpn(fqdn, cenr_source):
        # 1024: emit bare hostname (was ":500" pre-1024)
        return fqdn
    # else: feature 1023 three-branch dispatch (unchanged)
    return _non_vpn_probe_target(fqdn, role, cenr_source)
```

The VPN pre-check MUST run first so a host that is both in a
`vpn_hostnames` bag AND observed on TCP/443 (Zscaler admin console) is
emitted as VPN — the bag wins (spec Edge Cases).

## Post-Conditions

- Return value is a non-empty string with no whitespace.
- For VPN hosts: return contains no `":"` character, no `"http"` prefix.
- For non-VPN hosts: return contract unchanged from feature 1023.
- Function remains deterministic and free of side effects on
  `cenr_source`.

## Logging

- On VPN branch: `logger.info("probe_target(vpn): %s -> bare (reachability)", fqdn)`
  once per emit. This satisfies Principle VII (Action Logging) for the
  new VPN behavior.
- Non-VPN branches: log lines unchanged from feature 1023.

## Invariants Enforced

- **INV-3** (from `data-model.md`): no VPN row target contains `:500`,
  `:4500`, `https://`, or `http://`. The bare-hostname return here
  guarantees this by construction.
- **INV-1** (byte stability for non-VPN): the non-VPN branches are
  literally the same code path — no risk of drift.

## Interaction With Row Callsite

The row-emission callsite calls `_probe_target()` to fill
`custom_probes[i].target`, then immediately calls
`_probe_type_for_target(target)` (see `probe_type_dispatch.md`) to fill
`custom_probes[i].type`. Because VPN targets are bare hostnames,
`_probe_type_for_target` returns `"reachability"` for them, satisfying
FR-002 and FR-005 in one composed step.

## Test Boundaries

Tests live in
`tests/unit/org/test_org_synthetic_probes_manager.py::TestProbeTargetVpn`
and MUST cover:

- CENR bag member -> bare `fqdn` (no `:500`, no scheme).
- UDP-observed host (not in bag) -> bare `fqdn`.
- `-vpn.` pattern host with no observation and no bag entry -> bare `fqdn`.
- Bag member ALSO observed on TCP/443 -> bare `fqdn` (bag wins).
- Non-VPN TCP/443 host -> unchanged `https://{fqdn}` (byte-stability
  guard).
- Non-VPN non-443 TCP host -> unchanged `{fqdn}:{port}`.
- Logger emits the INFO line once per VPN target (assert via `caplog`).
- MUST NOT touch the network.

## Non-Goals

- The classifier `_is_vpn_host` is not modified. Its own tests remain
  the source of truth for classification correctness.
- No change to which hosts are emitted, only to the target shape for
  those already classified as VPN.
- No change to the non-VPN three-branch dispatch documented in feature
  1023's `probe_target_url_builder.md`.
