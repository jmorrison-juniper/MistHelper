# Contract: `_probe_target` URL Builder

**Feature**: 1023-probe-tailored-synthetic-tests
**Module**: `src/org/org_synthetic_probes_manager.py`
**Kind**: Internal Python API contract (private function)

## Scope

Documents the three-branch observation-first priority order for the URL
builder emitted into `custom_probes[i].target` in the Mist
`updateOrgSettings` PUT.

## Signature (unchanged)

```python
def _probe_target(fqdn: str, role: str, cenr_source: dict[str, Any]) -> str: ...
```

- Callers and signature are unchanged; only the body's decision tree is
  modified.

## Precondition

- `cenr_source` is the loaded CENR document (post v2->v3 adapter). Host
  entries are v3-shaped objects: `{"host": str, "observed_protocol": str |
  None, "observed_port": int | None, "last_probed": str | None}`.

## Decision Tree (three-branch priority)

The function looks up the v3 entry for `fqdn` inside `cenr_source` (across
`proxy_hostnames`, `vpn_hostnames`, or role-specific ZCC bags depending on
`role`). It then applies:

### Branch 1: UDP-family or non-HTTP TCP observation

**Trigger**: `observed_protocol` starts with `"UDP"` OR equals `"TCP/<n>"`
where `n != 443`.

**Return**: `f"{fqdn}:{observed_port}"` (bare `host:port`, no scheme).

**Example**: `chi1-2-vpn.zscaler.net:500`

### Branch 2: HTTPS/TCP-443 observation

**Trigger**: `observed_protocol` is `"HTTPS"` or `"TCP/443"`.

**Return**: `f"https://{fqdn}"` (default 443 elided).

**Example**: `https://chi1-2.sme.zscaler.net`

### Branch 3: No observation (fallback)

**Trigger**: `observed_protocol` is `None`, missing, or an unrecognised
token.

**Return**: Existing catalogue-default behaviour, i.e. build from
`cenr_source["probe_default"]["protocol"]` and `["port"]`. If the default
scheme is `https` and port is 443, elide the port to match Branch 2's
convention.

**Side effect**: EXACTLY ONE `logger.warning(...)` call of the form:

```
no observation for %s, using catalogue default %s
```

with `%s` args being `fqdn` and the final target string.

## Post-Conditions

- Return value is a non-empty string with no whitespace.
- HTTPS return never contains an explicit `:443` (elided).
- Bare `host:port` return never contains a scheme prefix.
- Return is deterministic given the same `fqdn` + `cenr_source` state
  (idempotent).

## Logging

- Branch 1 and Branch 2: `logger.debug("probe_target: %s -> %s (obs=%s)",
  fqdn, target, observed_protocol)` after the return decision.
- Branch 3: the mandatory `logger.warning` above, then the same
  `logger.debug` line for consistency.

## Invariants Enforced

- **INV-1** (from `data-model.md`): every HTTPS observation -> `https://`.
- **INV-2**: every UDP observation -> bare `host:port`, never `https://`.
- **FR-009**: hosts already reachable on HTTPS retain their exact previous
  target string.

## Test Boundaries

Tests live in `tests/unit/org/test_org_synthetic_probes_manager.py` and:

- MUST cover Branch 1 with `observed_protocol` values `"UDP"`, `"UDP/500"`,
  `"UDP/4500"`, and `"TCP/8080"`.
- MUST cover Branch 2 with both `"HTTPS"` and `"TCP/443"`.
- MUST cover Branch 3 with `observed_protocol` values `None`, missing key,
  and unknown token like `"WEIRD/9999"`.
- MUST assert the WARN log content in Branch 3 via `caplog`.
- MUST NOT touch the network.

## Non-Goals

- The function does not persist anything; it is a pure computation on the
  in-memory `cenr_source`.
- The function does not mutate `cenr_source`.
- ZCC probe target selection for roles other than CENR ones follows the
  same three-branch dispatch (identical shape via the shared entry object).
