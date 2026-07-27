# Phase 0 Research: Probe-Tailored Synthetic Tests

**Feature**: 1023-probe-tailored-synthetic-tests
**Date**: 2026-07-26
**Purpose**: Resolve every NEEDS CLARIFICATION and lock design decisions before
Phase 1 artifacts are generated.

## R-001: IKE_SA_INIT packet shape (stdlib-only, no crypto)

**Decision**: Send a fixed 28-byte IKEv2 header immediately followed by a
minimal Notify payload. Total frame ~36-40 bytes. Assembled via
`struct.pack(">8s8sBBBBII", ...)` from stdlib. No crypto material.

**Rationale**:
- RFC 7296 IKEv2 responders that receive a syntactically well-formed
  IKE_SA_INIT are required to reply (with either an IKE_SA_INIT response or a
  Notify carrying `INVALID_SYNTAX`, `COOKIE_REQUIRED`, or similar). Either
  reply counts as `"open"` for our purposes.
- Zscaler VPN initiators observed in the operator's pcap replied to a similar
  probe within ~50 ms, confirming the responder is not filtering unknown
  cookie/SPI values.
- A raw NAT-T (UDP/4500) datagram starts with a 4-byte non-ESP marker
  (`0x00000000`) followed by the same IKE header; the same helper handles
  both by prepending the marker when `port == 4500`.
- Using `struct` alone (already in stdlib) satisfies FR-017 (no new dep).

**Alternatives considered**:
- **Send an empty datagram**: rejected. Well-behaved responders drop
  malformed IKE packets silently, and firewalls may too. The pcap shows
  Zscaler responders ignore truly empty payloads.
- **Send an ESP-null probe**: rejected. Requires SPI negotiation state and
  crypto material, violating FR-017.
- **Use `scapy` for IKE assembly**: rejected. Introduces a heavy runtime
  dependency; FR-017 forbids new deps.

## R-002: "Open" definition for UDP

**Decision**: A datagram of ANY length received from the peer address
(regardless of port match, IKE cookie echo, or protocol correctness) is
sufficient evidence of `"open"`. Timeout -> `"no_reply"`. OSError family ->
`"error:<ExceptionClassName>"`.

**Rationale**:
- Firewalls between MistHelper and the Zscaler responder may terminate
  ICMP-unreachable at the transit layer, so the presence of *any* datagram
  back to the source socket is the loudest signal we can get without
  parsing IKE semantics.
- The spec explicitly documents this in Assumption paragraph and Edge Cases:
  refining "open" to validate IKE cookie echo is out of scope for this
  feature.
- Symmetry with `_tcp_check` (which treats a successful handshake as `open`
  without inspecting payload) is preserved.

**Alternatives considered**:
- **Parse the IKE reply header and require SPI match**: rejected as
  out-of-scope. Would double the code and add a maintenance burden with no
  operational benefit for the specific pcap failure mode we are fixing.
- **Require the reply to come from the same UDP port we probed**: rejected.
  Some responders answer from a different ephemeral port when NAT-T is
  active. Any datagram to our socket is treated as open.

## R-003: CENR cache schema shape (per-hostname object vs sidecar map)

**Decision**: Promote each hostname from a bare string to an object of the
shape `{"host": "<fqdn>", "observed_protocol": "<UDP|HTTPS|TCP|...>",
"observed_port": <int>, "last_probed": "<ISO8601-UTC>"}`. Bump
`schema_version` from 2 to 3. Old v2 (flat strings) are read via an adapter
that maps `"<fqdn>"` -> `{"host": "<fqdn>"}` (no observation fields).

**Rationale**:
- Locality: the observation lives next to the host it describes, so a human
  reading the JSON can answer "which VPN endpoints did we observe last time?"
  by scanning `vpn_hostnames` alone. This directly satisfies User Story 3's
  operator-inspectability requirement.
- Backward compatibility is trivial: the adapter runs unconditionally at
  load time; missing fields -> treated as "no observation cached" and a
  single INFO log is emitted per load (FR-006).
- Symmetry: the same shape works for `proxy_hostnames` and `vpn_hostnames`
  in the CENR file and for `roles[].fqdns` in the ZCC probes file. One
  adapter, one writer, one accessor.
- `by_city[<city>].proxy_hostnames` / `by_city[<city>].vpn_hostnames` inside
  the CENR file follow the same promotion rule (bare string -> object) so
  the merged document has a single consistent hostname representation.

**Alternatives considered**:
- **Sidecar observation map** (`{"observations": {"chi1-2-vpn.zscaler.net":
  {"protocol": "UDP", "port": 500, "at": "..."}}}` at the top of the file):
  rejected. Introduces a second lookup layer; operators inspecting a specific
  hostname would need to cross-reference two locations. Object-per-host is
  strictly simpler on the read path.
- **Flat parallel arrays** (`vpn_hostnames_observed_protocols[]` aligned by
  index with `vpn_hostnames[]`): rejected. Index alignment is a
  maintenance hazard and breaks the human-readable JSON layout.
- **Keep v2 shape, add a separate `data/zscaler_observations.jsonl`**:
  rejected. A separate persistence surface complicates atomic-write and
  concurrent-refresh reasoning without any benefit; the operator ergonomics
  requirement (User Story 3, "inspect the cache directly") tips the
  decision to co-located per-host objects.

## R-004: Trigger predicate for UDP probing inside `_probe_fqdn`

**Decision**: Run UDP probes on UDP/500 and UDP/4500 when EITHER (a) the
hostname's second-level label contains the literal token `-vpn.` (case-
insensitive), OR (b) every TCP port in `ports_to_scan` returned a non-`open`
status (`no_reply`, `closed`, or `error:...`).

**Rationale**:
- The pcap failure mode is precisely captured by (a): `chi1-2-vpn.zscaler.net`
  matches `-vpn.` and never responds on TCP; the current probe layer silently
  reports it as dead.
- (b) is a safety net: any host that is completely silent on TCP is worth
  one round of UDP checks. This catches unclassified endpoints (e.g. a new
  ZEN role that terminates only on UDP) at the cost of two extra datagrams
  per silent host - cheap in the aggregate.
- Combining the two into a single boolean predicate keeps `_probe_fqdn`'s
  logical-block count under the Principle I ceiling of 5.
- The catalogue's `role` metadata can also carry a VPN hint (e.g. a future
  `probe.family = "ike"` field), but the spec deliberately keeps the trigger
  purely hostname-driven for this feature to avoid a v3-only role schema
  change beyond what R-003 already introduces.

**Alternatives considered**:
- **Always probe UDP for every host**: rejected. Doubles the probe traffic
  for the entire ~1000-endpoint validation sweep with no signal gain on
  hosts that already answer TCP cleanly.
- **Never probe UDP on TCP-live hosts**: rejected. Hybrid endpoints that
  answer both TCP/443 and UDP/500 would lose the UDP signal; edge-case
  guidance in the spec says the diagnostic value of `responding_protocols`
  including both is worth the extra check. Note: the trigger is `-vpn.` OR
  `all-TCP-dead`; hybrid endpoints will still hit branch (a) if their
  hostname matches.

## R-005: Persistence write path (where to plumb observations back into disk)

**Decision**: `zscaler_catalogue.ensure_fresh()` already calls
`run_full_validation()` on refresh. Extend that call site to walk the
resulting `list[ProbeResult]`, index the results by FQDN, and mutate the
in-memory `fresh` dict (both `proxy_hostnames`/`vpn_hostnames` and the
`by_city[*].{proxy,vpn}_hostnames` mirror sets) to carry observation fields
before the atomic write.

**Rationale**:
- `ensure_fresh` is already the single choke point (line 398). No new call
  path is introduced.
- The mutation happens after `attach_city_metadata` and before the atomic
  write, so the persisted document is self-consistent (all four hostname
  bags see the same observations).
- The ZCC probes file (`data/zscaler_client_connector_probes.json`) gets the
  same treatment: its `roles[].fqdns` entries are also promoted to objects
  during the same write. The catalogue module owns the write.

**Alternatives considered**:
- **Write observations from `_probe_target` on read**: rejected. Coupling a
  URL-builder to a disk write creates a hidden side effect at menu-render
  time and violates the read-only-under-menu ideal.
- **Write observations from `zscaler_probe.run_full_validation`**: rejected.
  The probe module intentionally has no I/O responsibility; that separation
  keeps the probe unit-testable in pure-mock mode.

## R-006: URL-builder priority order in `_probe_target`

**Decision**: Three-branch priority:
1. If `observed_protocol` is a UDP-family token (`UDP`, `UDP/500`, `UDP/4500`,
   or any non-HTTP/TCP-443 shape), return `f"{fqdn}:{observed_port}"` (bare
   host:port, no scheme prefix).
2. Else if `observed_protocol` is `HTTPS` or `TCP/443`, return
   `f"https://{fqdn}"` (default port elided per existing convention).
3. Else (no observation), fall back to the current catalogue-driven behavior
   AND emit `logger.warning("no observation for %s, using catalogue default
   %s", fqdn, target)`.

**Rationale**:
- Priority (1) directly implements SC-001 (zero `https://*-vpn.*` targets
  after ship).
- Priority (2) preserves FR-009 (working HTTPS probes MUST NOT be altered).
- Priority (3) surfaces the gap so operators can inspect and refresh; also
  matches Acceptance Scenario 3 in User Story 1.
- The Mist `target` field accepts bare `host:port` for non-HTTP checks
  (Assumption in spec; confirmed by operator).

**Alternatives considered**:
- **Prefer catalogue over observation**: rejected. Would leave the pcap bug
  unfixed; the whole point of the feature is to trust live signal over
  static config.
- **Suppress the WARN for no-observation hosts** (silent fallback):
  rejected. The operator explicitly needs the log entry (User Story 1
  Acceptance Scenario 3) so a stale cache is visible in the console during
  Menu 206 runs.

## R-007: Backward-compat load path for v2 caches

**Decision**: The loader detects `schema_version` in the top-level dict. When
missing OR `< 3`, the loader wraps every bare string in
`proxy_hostnames`/`vpn_hostnames` (and the mirror bags inside `by_city`) into
`{"host": "<fqdn>"}` (no observation fields). One `logger.info(
  "zscaler_catalogue: loaded v%d cache (%d entries); observations absent",
  detected_version, count)` fires per load. The in-memory shape after
adaptation is identical to a freshly-written v3 file, so downstream code has
one code path.

**Rationale**:
- FR-006 explicitly requires backward compatibility.
- The adapter is one function (~10 lines) executed once per load; overhead
  is negligible.
- Forward compatibility (older MistHelper reading a v3 file) is explicitly
  out of scope per the spec's Assumption paragraph.

**Alternatives considered**:
- **Emit a WARN instead of INFO for v2 loads**: rejected. v2 caches are a
  legitimate transient state during rollout; WARN would create noise.
- **Force an immediate refresh on v2 detection**: rejected. `is_stale()`
  already handles the TTL gate; forcing a refresh here would break the
  offline/failed-fetch degradation path.

## R-008: Testing shape (mocking boundaries)

**Decision**: All new tests mock at these boundaries:
- `socket.socket` (both TCP and UDP paths) via
  `unittest.mock.patch("src.utils.zscaler_probe.socket.socket")`.
- `subprocess.run` (for `_icmp_ping`) via
  `unittest.mock.patch("src.utils.zscaler_probe.subprocess.run")`.
- `socket.getaddrinfo` via
  `unittest.mock.patch("src.utils.zscaler_probe.socket.gethostbyname")` (the
  existing resolve path).
- No `pytest-network-mock` or similar new dependencies.

**Rationale**:
- FR-014 forbids real network I/O in unit tests.
- FR-017 forbids new dependencies. `unittest.mock` is stdlib.
- Existing tests in `tests/unit/utils/test_zscaler_probe.py` already use
  this pattern; consistency reduces reviewer cognitive load.

**Alternatives considered**:
- **`respx` / `pytest-httpserver` / similar**: rejected. New deps.
- **Integration tests against a live UDP listener** (loopback): rejected.
  Flaky on CI runners that block UDP; violates FR-014's "no network in unit
  tests" spirit.

## R-009: Coverage strategy for new decision points

**Decision**: Target 100% branch coverage on:
- `_udp_check`: three return branches (`"open"`, `"no_reply"`,
  `"error:..."`).
- `_probe_fqdn` UDP trigger predicate: (a) hostname matches `-vpn.`; (b)
  all TCP ports non-open; (c) neither -> no UDP probe.
- `_probe_target`: (i) UDP-family observation; (ii) HTTPS/TCP-443
  observation; (iii) no observation with WARN.
- CENR loader v2 adapter: (I) v3 file; (II) v2 file with strings; (III)
  malformed file (error path already covered elsewhere).

**Rationale**: SC-004 explicitly names these branches. Direct 1:1 test cases
are cheaper to write and read than parameterized fixtures for this small a
matrix.

## R-010: No-network guarantee for UDP tests

**Decision**: All UDP unit tests instantiate a `MagicMock()` for the socket
and assert against `.sendto` / `.recvfrom` call arguments; no real
`socket.socket(AF_INET, SOCK_DGRAM)` is ever created. A guard test asserts
`socket.socket` is not called with `SOCK_DGRAM` outside the mock scope.

**Rationale**: Enforces FR-014 mechanically instead of by convention. Also
proves SC-007 (no test blocks longer than 2s) trivially since no real socket
timeout is possible.
