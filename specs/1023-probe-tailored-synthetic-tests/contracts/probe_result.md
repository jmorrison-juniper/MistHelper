# Contract: `ProbeResult` (extended)

**Feature**: 1023-probe-tailored-synthetic-tests
**Module**: `src/utils/zscaler_probe.py`
**Kind**: Internal Python API contract (dataclass + producing function)

## Scope

Documents the extended `ProbeResult` dataclass, the new `_udp_check` helper,
and the `_probe_fqdn` UDP-trigger predicate. All three are internal-only;
callers outside `src/utils/` MUST NOT import them (existing convention).

## `IKE_UDP_PORTS`

```python
IKE_UDP_PORTS: tuple[int, int] = (500, 4500)
```

- Module-level constant. New in this feature.
- MUST be a two-tuple in this exact order (500 first, 4500 second).
- Referenced by `_udp_check` and `_probe_fqdn`.

## `ProbeResult` extension

```python
@dataclass
class ProbeResult:
    # ... existing fields (unchanged) ...
    udp: dict[int, str] = field(default_factory=dict)
```

- Field `udp` is NEW.
- Default is an empty dict (host had no UDP probe run against it).
- Keys are ints in `IKE_UDP_PORTS`.
- Values are one of: `"open"`, `"no_reply"`, or a string of the exact form
  `f"error:{type(exc).__name__}"` where `exc` is an OSError-family instance.

## `_udp_check(host, port, timeout) -> str`

### Signature

```python
def _udp_check(host: str, port: int, timeout: float) -> str: ...
```

### Behaviour Contract

| Input Condition                                       | Return Value               |
|-------------------------------------------------------|----------------------------|
| Any datagram received on the socket before timeout    | `"open"`                   |
| Socket recv times out                                 | `"no_reply"`               |
| Any OSError-family exception during send/recv         | `f"error:{ExcClassName}"`  |

### Post-Conditions

- MUST NOT raise. All OSError-family exceptions are caught and reported via
  the return string.
- MUST call `.settimeout(timeout)` on the socket before any send.
- MUST close the socket in a `finally` clause.
- MUST complete within `timeout + 500 ms` wall-clock (SC-007).
- MUST NOT open a socket other than `socket.SOCK_DGRAM`.

### Packet Shape

- Port 500: 28-byte IKE_SA_INIT header + minimal Notify payload (~36-40
  bytes total). Assembled with `struct.pack(">8s8sBBBBII", ...)`.
- Port 4500: 4-byte non-ESP marker (`b"\x00\x00\x00\x00"`) prefixed to the
  same IKE header + payload.

### Logging

- `logger.info("udp_check: sending IKE_SA_INIT to %s:%d", host, port)`
  before send.
- `logger.debug("udp_check: %s:%d -> %s", host, port, result)` after recv or
  error branch.

## `_probe_fqdn` UDP trigger predicate

### Rule

UDP probing fires for a host when EITHER of:

- **(a) Name match**: hostname contains the literal token `-vpn.`
  (case-insensitive).
- **(b) All-TCP-dead safety net**: every port in `ports_to_scan` returned a
  non-`"open"` status.

### Behaviour

- When (a) OR (b) holds, iterate `IKE_UDP_PORTS` and call `_udp_check` for
  each. Record result into `result.udp[port]`.
- For each port where result is `"open"`, append `f"UDP/{port}"` to
  `result.responding_protocols` (deduplicated).
- When NEITHER (a) NOR (b) holds, `result.udp` remains empty.

### Non-Regression Assertions

- Hosts that answer TCP/443 cleanly and lack `-vpn.` MUST have empty
  `result.udp` and no `UDP/*` tokens in `responding_protocols`.
- ICMP path is UNCHANGED (FR-010). `icmp_ok` retains its current semantics.

## Test Boundaries

- Tests MUST mock `socket.socket` at
  `src.utils.zscaler_probe.socket.socket`.
- Tests MUST NOT instantiate a real `SOCK_DGRAM` socket.
- Tests MUST cover: `"open"`, `"no_reply"`, and `"error:<ExcName>"` return
  branches of `_udp_check`; and the (a)/(b)/(neither) branches of the
  trigger predicate.

## Non-Goals

- Parsing IKE responder replies for SPI/cookie echo validation.
- Rejecting ICMP unreachable relays; any datagram counts as `"open"`.
- Adding GRE or ESP-null probes.
