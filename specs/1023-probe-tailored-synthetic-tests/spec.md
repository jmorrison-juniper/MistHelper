# Feature Specification: Probe-Tailored Synthetic Tests

**Feature Branch**: `1023-probe-tailored-synthetic-tests`

**Created**: 2026-07-26

**Status**: Draft

**Input**: User description: "Menu 206 (org Zscaler synthetic-probes manager) currently emits `https://<host>` targets for every Zscaler CENR hostname in the catalogue, including VPN initiators (`*-vpn.zscaler.net`). VPN initiators do not answer HTTPS — they answer IKE/IPsec on UDP 500/4500. A real Marvis-mini pcap capture confirms the failure: `chi1-2-vpn.zscaler.net` receives 8× TCP SYN retries on port 443 with zero SYN+ACK response, while `chi1-2.sme.zscaler.net` (the proxy pair) completes TLS cleanly in the same trace. Root cause: (1) `src/utils/zscaler_probe.py` only probes TCP:{80,443,8080} with no UDP path; (2) `src/org/org_synthetic_probes_manager.py::_probe_target` builds the Mist `target` URL strictly from the catalogue's declared `probe.protocol` — never from any live observation."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Correct probe target for VPN endpoints (Priority: P1)

A NOC engineer runs Menu 206 for an org whose Zscaler CENR catalogue includes VPN initiators such as `chi1-2-vpn.zscaler.net`. Today the engineer pushes synthetic-probe configuration to Mist, then discovers in the Marvis mini pcap that every VPN endpoint records 8× TCP SYN retries with zero response — the probe was aimed at TCP/443, a port those hosts never open. The engineer needs the probe manager to observe the real reachable protocol/port and emit a target that matches (e.g. `chi1-2-vpn.zscaler.net:500`), so Marvis-mini pass/fail signal reflects actual VPN reachability rather than a guaranteed failure.

**Why this priority**: This is the presenting bug. Every VPN row in every generated `custom_probes` list is silently useless today; without this fix the operator cannot trust Menu 206 output at all.

**Independent Test**: Given a cached CENR catalogue that contains at least one `*-vpn.zscaler.net` host, when the operator runs Menu 206 to regenerate `custom_probes`, then every VPN endpoint in the generated Mist payload MUST appear as `host:500` (bare host:port form), and every proxy/HTTPS endpoint MUST remain `https://host`. Verification does not require a live Mist push — the intermediate payload is inspectable in-process and via existing telemetry.

**Acceptance Scenarios**:

1. **Given** the CENR cache contains `chi1-2-vpn.zscaler.net` with a recorded UDP/500 observation, **When** Menu 206 builds the synthetic-probes payload, **Then** the `target` for that host MUST be `chi1-2-vpn.zscaler.net:500` (not `https://chi1-2-vpn.zscaler.net`).
2. **Given** the CENR cache contains `chi1-2.sme.zscaler.net` with a recorded HTTPS observation, **When** Menu 206 builds the synthetic-probes payload, **Then** the `target` for that host MUST remain `https://chi1-2.sme.zscaler.net`.
3. **Given** the CENR cache contains a hostname with NO recorded observation, **When** Menu 206 builds the synthetic-probes payload, **Then** the `target` MUST fall back to the catalogue-declared default AND a WARN log entry MUST be emitted naming the host and the reason ("no observation cached").

---

### User Story 2 - UDP reachability testing in the probe layer (Priority: P1)

A NOC engineer or a scheduled cache-refresh job invokes the Zscaler catalogue refresh (TTL-triggered). Today `src/utils/zscaler_probe.py` only exercises TCP:{80,443,8080}; VPN initiators appear "dead" and get flagged for removal or continue to get HTTPS-shaped targets. The engineer needs the probe layer to attempt IKE/IPsec on UDP/500 and UDP/4500 for endpoints where UDP is expected (VPN role hint or hostname pattern) OR where every TCP port came back dead, so the resulting observation record accurately describes which protocol the host actually answers on.

**Why this priority**: Without a UDP capability in the probe layer there is no factual source for the target-tailoring logic in User Story 1. This story delivers the observation; Story 1 consumes it.

**Independent Test**: Given a `_udp_check` implementation and a mocked UDP responder, when `_probe_fqdn` runs against a hostname flagged as VPN, then the returned `ProbeResult` MUST include `udp[500]` (or `udp[4500]`) set to `"open"` and MUST list `UDP/500` (or `UDP/4500`) in `responding_protocols`. Testable in unit tests without any real network access.

**Acceptance Scenarios**:

1. **Given** a hostname containing `-vpn.` (or with a role hint indicating VPN), **When** `_probe_fqdn` runs against a mocked UDP responder on port 500, **Then** the result's `udp` dict MUST contain `500: "open"` and `responding_protocols` MUST include `"UDP/500"`.
2. **Given** a hostname where all three TCP checks return no response, **When** `_probe_fqdn` runs, **Then** UDP/500 and UDP/4500 MUST be attempted as a fallback and any successful UDP result MUST be recorded.
3. **Given** a mocked UDP socket that never replies within the timeout, **When** `_udp_check` runs, **Then** it MUST return `"no_reply"` (not raise, not hang past the configured timeout).
4. **Given** a mocked UDP socket that raises OSError, **When** `_udp_check` runs, **Then** it MUST return the string `"error:<ExceptionClassName>"` and MUST NOT propagate the exception.

---

### User Story 3 - Persisted observations for downstream reuse (Priority: P2)

An operator refreshes the Zscaler catalogue cache (via TTL expiration or explicit refresh). Today the JSON cache files under `data/` record only the declared catalogue metadata; observed reachability is discarded after each run. The operator needs the last-known observed protocol and port persisted per host/role so that (a) subsequent Menu 206 runs can tailor targets without re-probing, (b) operators can inspect the cache directly to answer "which VPN endpoints did we observe last time?", and (c) older cache files remain readable (backward compatibility) so a fleet mid-rollout does not break.

**Why this priority**: Persisting observation removes the need to re-probe every Menu 206 invocation and gives operators an inspectable record. It is P2 because a strictly in-memory implementation would still satisfy Story 1 for a single session — but would silently regress on the next fresh start.

**Independent Test**: Given a mocked probe that returns `UDP/500` for a VPN host, when the catalogue refresh runs and writes `data/zscaler_cenr_hostnames.json`, then re-reading the file MUST yield an entry whose observation fields expose `UDP/500` in a documented shape. An older-shape cache file MUST still load without exception.

**Acceptance Scenarios**:

1. **Given** the catalogue refresh has just completed with observations for host `H`, **When** the JSON cache file for CENR hostnames is read back, **Then** the entry for `H` MUST expose `observed_protocol` and `observed_port` (or the equivalent schema-v2 shape) reflecting the last probe result.
2. **Given** a `data/zscaler_client_connector_probes.json` from an older build (no observation fields), **When** the loader reads it, **Then** the loader MUST succeed without exception and MUST treat missing observations as "no observation cached" (falling back to catalogue defaults with a WARN, per Story 1).
3. **Given** a cache file with an observation older than the TTL, **When** the refresh runs, **Then** the observation MUST be replaced with a fresh probe result and the file re-written.

---

### Edge Cases

- **Host resolves but is completely silent** (no TCP, no UDP): probe records all ports as `no_reply`; Menu 206 falls back to catalogue default and emits WARN. The host MUST NOT be silently dropped.
- **Host answers on BOTH TCP/443 and UDP/500** (unusual but possible for hybrid endpoints): observation MUST prefer the role-appropriate protocol (VPN role -> UDP; proxy role -> HTTPS). Both signals SHOULD still appear in `responding_protocols` for diagnostic purposes.
- **Malformed cache file** (invalid JSON, truncated write): loader MUST log an error and behave as if no cache exists (trigger a fresh refresh), never crash the menu.
- **Cache schema mismatch** (e.g. new field type in v2 that v1 loader doesn't know): backward-compatible loader MUST ignore unknown fields; forward-compatible loader (older MistHelper reading a newer file) is out of scope for this feature.
- **Concurrent refresh** (two menu invocations racing to rewrite the same JSON): out of scope for this feature; existing catalogue file-write behaviour is unchanged.
- **DNS resolution failure**: existing behaviour is preserved — `_probe_fqdn` records a resolution failure and no observation is written. Menu 206 emits WARN and falls back to catalogue default.
- **UDP reply from an unrelated source** (e.g. ICMP port-unreachable from an intermediate hop): `_udp_check` treats any datagram received on the socket as `"open"`; refining this to validate IKE cookie echo is out of scope for this feature (documented in Assumptions).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The probe layer MUST provide a UDP reachability check that sends a well-formed IKE_SA_INIT cookie payload on UDP/500 and UDP/4500 and returns one of `"open"` (any datagram received), `"no_reply"` (timeout elapsed with no datagram), or `"error:<ExceptionClassName>"` (OSError family).
- **FR-002**: The UDP check MUST honour a caller-supplied timeout and MUST NOT block past that timeout under any condition (including DNS failure, socket errors, or router black-holing).
- **FR-003**: The probe layer's per-FQDN result MUST expose UDP outcomes in a machine-readable field (`udp: dict[int, str]`) alongside the existing TCP results, and MUST append protocol tokens (`"UDP/500"`, `"UDP/4500"`) to `responding_protocols` for any UDP port that returned `"open"`.
- **FR-004**: The probe layer MUST run UDP probes for a host when EITHER (a) the hostname matches the VPN pattern (contains `-vpn.` or a role hint that says VPN), OR (b) all TCP ports for that host returned no response (fallback safety net).
- **FR-005**: The Zscaler catalogue refresh MUST persist the latest observed protocol and port for each catalogued host/role into the JSON cache files under `data/` so that subsequent runs can consume them without re-probing.
- **FR-006**: The cache-file schema MUST remain backward-compatible: a cache file written by an older MistHelper (no observation fields) MUST load without exception and be treated as "no observation cached". If a schema version bump is required, the loader MUST detect and handle both versions.
- **FR-007**: The synthetic-probes manager's target-URL construction MUST prefer the cached observation over the catalogue default: HTTPS/TCP-443 observations produce `https://<host>`, non-HTTP observations (UDP/500, UDP/4500, any non-HTTP TCP port) produce bare `<host>:<port>`, and any host with no observation MUST fall back to the catalogue-declared default AND emit a WARN log entry naming the host and reason.
- **FR-008**: The Mist API surface used by Menu 206 MUST NOT change — the same `updateOrgSettings` PUT is used, and only the string value of individual `target` fields inside `custom_probes` may change shape.
- **FR-009**: ZCC roles that already have working HTTPS probes MUST NOT be altered — a host currently reachable and correctly targeted as `https://<host>` MUST continue to receive that exact target string.
- **FR-010**: The ping/ICMP path MUST NOT be modified by this feature.
- **FR-011**: GRE probing MUST NOT be added by this feature — only IKE (UDP 500/4500) is in scope for the pcap failure mode.
- **FR-012**: All new/modified Python code MUST have Google-style docstrings with a `Why:` section, per project DOCS.md policy.
- **FR-013**: Every comment written for new/modified code MUST satisfy the 5-W's rule (Who / What / When / Where / Why). Historical or backstory comments MUST NOT be introduced.
- **FR-014**: Unit tests for the new probe paths MUST NOT touch the real network — socket and subprocess interactions MUST be mocked via `unittest.mock`.
- **FR-015**: Action logging (constitution Principle VII) MUST be applied to any function touched by this feature: `logging.info(...)` before each meaningful action and `logging.debug(...)` after with a result summary. Secrets MUST NOT be logged (constitution Principle V).
- **FR-016**: Inline comments (constitution Principle VI) MUST be added to every changed or adjacent line explaining what and why.
- **FR-017**: The stdlib-only constraint MUST be respected — no new runtime dependency may be introduced to satisfy this feature (`socket` is sufficient for UDP; `struct` is available for IKE payload assembly).

### Key Entities *(include if feature involves data)*

- **ProbeResult**: Represents the outcome of a single probe run against one FQDN. Existing attributes describe TCP port outcomes and derived `responding_protocols`. This feature adds a `udp: dict[int, str]` mapping (port -> `"open"` | `"no_reply"` | `"error:<ExcName>"`) and extends `responding_protocols` with UDP tokens where applicable.
- **CENRHostEntry** (row inside `data/zscaler_cenr_hostnames.json`): Represents one catalogued Zscaler CENR hostname. Currently a flat string per role bucket; this feature promotes it to a small object (or attaches optional sibling fields) so an observation (observed protocol + observed port + observed_at timestamp) can persist alongside the catalogue-declared defaults.
- **ZCCProbeEntry** (row inside `data/zscaler_client_connector_probes.json`): Represents one Zscaler Client Connector critical probe target, keyed by role. Same observation-persistence extension as CENRHostEntry.
- **SyntheticProbeTarget** (transient — the string value emitted into a Mist `custom_probes[i].target` field): Represents the URL/host:port form Mist will actually test. Three shapes: `https://<host>` (HTTP observation), `<host>:<port>` (non-HTTP observation), or catalogue-declared fallback (no observation, with WARN).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For any org whose CENR catalogue contains at least one `*-vpn.zscaler.net` host, the generated `custom_probes` payload contains ZERO `https://*-vpn.*` target strings after this feature ships. (Before: 100% of VPN rows were mis-shaped as HTTPS.)
- **SC-002**: For the same org, at least one VPN endpoint reports `UDP/500` (or `UDP/4500`) as a responding protocol in the observation cache after a fresh refresh. Verifiable by inspecting the JSON cache under `data/`.
- **SC-003**: The full pytest suite MUST remain green with no regressions — baseline is 8719+ passing tests today; the post-change count MUST be `>= baseline + new tests added`.
- **SC-004**: Unit tests exercise all three `_udp_check` return branches (`"open"`, `"no_reply"`, `"error:..."`), the VPN-flagged and TCP-dead fallback paths in `_probe_fqdn`, and all three `_probe_target` branches (HTTPS observation, non-HTTP observation, missing observation + WARN). 100% branch coverage on the new probe target logic.
- **SC-005**: No new runtime dependency appears in `pyproject.toml` or `requirements.txt` as a result of this feature.
- **SC-006**: A cache file written by an older MistHelper build loads without exception in the new build (backward compatibility). Verifiable by a unit test that loads a captured v1 fixture.
- **SC-007**: `_udp_check` completes within `timeout + <500 ms` overhead in every branch (including error and no-reply). No unit test involving UDP blocks longer than 2 seconds.
- **SC-008**: A manual end-to-end run of `run_full_validation` against a real CENR cache confirms at least one VPN endpoint reports `UDP/500` responding, matching the Marvis-mini pcap ground truth.

## Assumptions

- The Mist API's `custom_probes[i].target` field accepts a bare `host:port` string (no `scheme://` prefix) for non-HTTP checks. This has been confirmed by the operator based on prior manual testing; this spec is written on that assumption.
- A single UDP datagram received on the probe socket is sufficient evidence of "open" for our purposes. Validating IKE cookie echo semantics (i.e. distinguishing a real IKE responder from an intermediate ICMP-unreachable reply) is out of scope; the pcap ground truth is that VPN initiators do reply.
- IKE_SA_INIT cookie payload construction can be done from stdlib `struct` alone — no cryptographic material is exchanged, only header framing sufficient for the responder to recognise "this looks like IKE" and reply.
- The TTL-based cache refresh in `src/utils/zscaler_catalogue.py` is the correct integration point for probing and persisting observations. No new refresh trigger is required.
- The two JSON cache files (`data/zscaler_cenr_hostnames.json` and `data/zscaler_client_connector_probes.json`) are the sole persistence surface for observations. No database schema change is required.
- The existing WARN-level logger (`logging.warning(...)`) reaches the same operator-visible sink as other Menu 206 warnings. No new log routing is introduced.
- "Backward compatibility" for the cache file schema means: a cache file WITHOUT observation fields loads cleanly on the new build. Forward compatibility (older MistHelper reading a newer file) is NOT required — mixed-version fleets are not supported in this codebase.
- Concurrent refresh contention is not addressed by this feature; the existing single-writer assumption on the JSON cache is preserved.
- The unit-test discipline (`unittest.mock` for all socket/subprocess interactions) is enforceable purely at the test-code level — no production-side hook is required.
