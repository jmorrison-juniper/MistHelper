# Feature Specification: VPN Synthetic Probes Use Mist Reachability (ICMP)

**Feature Branch**: `1024-vpn-icmp-reachability`

**Created**: 2026-07-26

**Status**: Draft

**Input**: User description: "VPN synthetic probes use Mist `reachability` (ICMP), not fake HTTP application probes. Split synthetic-probe emission by target classification: VPN hosts emit as bare hostname with `type: reachability`; non-VPN observed HTTPS or TCP/443 keep `https://host` with `type: application`; non-VPN observed non-443 TCP keep `host:port` with `type: application`. The row builder inspects target shape and picks the probe type. Optional in-scope follow-up: promote `run_full_validation()` VPN IKE probe results from log-only to JSONL telemetry under `data/`."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Truthful VPN Health Signal in Marvis Minis (Priority: P1)

An operator running menu 206 (`org_synthetic_probes_manager`) pushes a synthetic-tests bundle to Mist. The bundle includes Zscaler VPN edge FQDNs discovered from CENR `vpn_hostnames` bags, from observed UDP telemetry, or from the `-vpn.` hostname pattern. The bundle emits those endpoints as bare hostnames tagged `type: reachability` so Mist Marvis Minis performs an ICMP ping — a check the endpoints can actually answer. Healthy VPN edges show as healthy in Marvis; unreachable edges surface as real alerts.

**Why this priority**: Today every VPN endpoint in the emitted bundle is a permanently-failing `application` probe (Mist speaks no IKEv2; TCP/500 to a Zscaler VPN edge is never answered). Every alert on those probes is noise. That noise is worse than no monitoring — operators learn to ignore synthetic-test failures, so real failures on non-VPN probes also get ignored. Restoring truthful signal is the reason the feature exists.

**Independent Test**: Run menu 206 against a fixture org that contains at least one CENR `vpn_hostnames` entry. Inspect the emitted synthetic-tests payload. Every VPN entry must appear as a row with `type: reachability` and a bare-hostname target (no scheme, no port). No VPN entry may appear as a row with `type: application` or a target containing `:500`, `https://`, or `http://`.

**Acceptance Scenarios**:

1. **Given** a CENR record whose `vpn_hostnames` bag contains `gateway.zscalerthree.net`, **When** menu 206 emits its synthetic-tests bundle, **Then** the bundle contains a row with `type: reachability` and `hostname: gateway.zscalerthree.net` and does not contain any row targeting `gateway.zscalerthree.net:500` or `https://gateway.zscalerthree.net`.
2. **Given** an observed telemetry record for host `edge-vpn.example.com` seen on UDP/500 only, **When** menu 206 emits its bundle, **Then** the bundle contains a `type: reachability` row for `edge-vpn.example.com` and no `application` row for the same host.
3. **Given** a host matching the `-vpn.` hostname pattern (`fra4-vpn.zscalerthree.net`) with no observed traffic and no CENR entry, **When** menu 206 emits its bundle, **Then** the row is `type: reachability` with a bare-hostname target.
4. **Given** a non-VPN host observed on TCP/443, **When** menu 206 emits its bundle, **Then** the row for that host is unchanged from today: `type: application`, target `https://<host>`.
5. **Given** a non-VPN host observed on TCP/8080, **When** menu 206 emits its bundle, **Then** the row for that host is unchanged from today: `type: application`, target `<host>:8080`.

---

### User Story 2 - Byte-Identical Non-VPN Behavior (Priority: P1)

An operator diffing today's emitted bundle against tomorrow's bundle (after this change ships) sees changes only in rows tied to VPN endpoints. Every non-VPN row — HTTPS on TCP/443, other TCP ports, application probes — is byte-identical to the pre-change output for the same input CENR/telemetry data.

**Why this priority**: The synthetic-probes pipeline has an existing invariant (INV-1, run-to-run byte stability) that operators depend on to distinguish "input data changed" from "code changed" when reviewing menu 206 diffs. Silently drifting non-VPN row shape as a side effect of the VPN fix would violate that trust and hide real regressions. This is P1 because it is a hard constraint on the fix, not an enhancement.

**Independent Test**: Capture the emitted bundle for a representative org on the current branch. Apply the fix. Regenerate the bundle for the same org against the same input snapshot. Diff the two bundles. Every non-VPN row (identified by target lacking a `vpn_hostnames` match, `-vpn.` pattern, or UDP observation) must be byte-identical between the two bundles.

**Acceptance Scenarios**:

1. **Given** an input snapshot with 100 non-VPN observed TCP/443 hosts, **When** the bundle is emitted before and after the change, **Then** the 100 non-VPN rows are byte-identical.
2. **Given** an input snapshot with non-VPN hosts observed on mixed non-443 TCP ports, **When** the bundle is emitted before and after the change, **Then** those rows keep the `host:port` shape and `type: application` unchanged.

---

### User Story 3 - VPN IKE Telemetry Distinguishes Reachable-But-Dead Edges (Priority: P3)

An operator wants to distinguish a VPN edge that is IP-reachable but IKE-dead (ICMP responds, but IKEv2 `IKE_SA_INIT` gets no reply on UDP/500 or UDP/4500) from a VPN edge that is fully healthy. The truthful IKE check already runs during the 8h CENR refresh in `src/utils/zscaler_probe.py::run_full_validation()` — its results are currently log-only. This story promotes those results to append-only JSONL telemetry under `data/` (e.g. `data/vpn_ike_health.jsonl`) so a future report can surface the "reachable but IKE-dead" class.

**Why this priority**: Optional in-scope follow-up per feature description. Adds diagnostic depth. Not required for the primary fix (US1) to deliver value. Reasonable to defer to a follow-up feature if scope pressure arises, but cheap enough to include here.

**Independent Test**: Run `run_full_validation()` against a synthetic input containing at least one VPN edge that responds to ICMP but not to IKEv2 `IKE_SA_INIT`. Confirm one JSONL record is appended to `data/vpn_ike_health.jsonl` capturing the hostname, timestamp, ICMP result, UDP/500 IKE result, and UDP/4500 IKE result.

**Acceptance Scenarios**:

1. **Given** a VPN edge that answers ICMP but not IKEv2 on UDP/500 or UDP/4500, **When** `run_full_validation()` completes for that host, **Then** one line is appended to `data/vpn_ike_health.jsonl` with `ike_500_ok: false`, `ike_4500_ok: false`, and hostname/timestamp fields populated.
2. **Given** a VPN edge that answers IKEv2 on UDP/500 with a valid `IKE_SA_INIT` response, **When** `run_full_validation()` completes for that host, **Then** the JSONL record for that host has `ike_500_ok: true`.
3. **Given** the JSONL file already exists from a prior run, **When** a new `run_full_validation()` cycle completes, **Then** the file is appended to (not truncated) and prior records are preserved.

---

### Edge Cases

- **VPN hostname also observed on TCP/443**: A host is both in a CENR `vpn_hostnames` bag and observed serving TCP/443 traffic. The VPN classification wins — the row is `type: reachability` with a bare hostname. Rationale: the `vpn_hostnames` bag is authoritative for VPN identity; TCP/443 observation on a VPN edge is likely admin console traffic, not the VPN service.
- **Host in `vpn_hostnames` bag but with `-vpn.` NOT in name**: The bag membership alone qualifies as VPN. No pattern check required.
- **Host with `-vpn.` in name but not in any `vpn_hostnames` bag and no UDP observation**: Still qualifies as VPN (the `_is_vpn_host` catalogue-default branch). Row is `type: reachability`.
- **Non-VPN host observed only on UDP**: Out of scope for this feature. Existing behavior applies (whatever the current code does for that shape today — do not regress it).
- **IPv6-only VPN host**: Bare hostname emission is protocol-agnostic; Mist reachability probes resolve DNS server-side. No special-case handling required beyond the same bare-hostname shape.
- **Empty `vpn_hostnames` bag on a CENR record**: No rows emitted for that record's VPN slot; other slots emit normally.
- **JSONL telemetry file (US3) is unwritable** (permission denied, disk full): The IKE probe still completes and still logs its result as today; the JSONL append failure is logged as a warning but must not abort `run_full_validation()` or destabilize the CENR refresh.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The synthetic-tests row builder MUST classify each target as VPN or non-VPN before choosing the probe type. A target is classified VPN if any of the following are true: (a) the hostname is a member of a CENR `vpn_hostnames` bag, (b) the hostname was observed on a UDP transport in telemetry, (c) the hostname matches the `-vpn.` pattern used by `_is_vpn_host`.
- **FR-002**: For every VPN-classified target, the emitted row MUST have `type: reachability` and a target field containing the bare hostname only — no URL scheme (`http://`, `https://`), no port suffix (`:500`, `:4500`), no path.
- **FR-003**: For every non-VPN target observed on HTTPS or TCP/443, the emitted row MUST retain the current behavior: `type: application` and target `https://<host>`.
- **FR-004**: For every non-VPN target observed on non-443 TCP, the emitted row MUST retain the current behavior: `type: application` and target `<host>:<port>`.
- **FR-005**: The row-emission callsite MUST dispatch the probe type from the target shape: a target with a URL scheme or explicit `:port` suffix maps to `application`; a bare hostname (no scheme, no port) maps to `reachability`.
- **FR-006**: No emitted row may target a VPN host with a URL of the form `https://<host>-vpn.<domain>`, `http://<host>`, or `<host>:500`. These synthetic-probe shapes are prohibited outputs.
- **FR-007**: The row-shape and probe-type choice for every non-VPN target MUST be byte-identical to the current implementation for the same input snapshot (INV-1 preservation).
- **FR-008**: All existing pytests under `tests/unit/org/test_org_synthetic_probes_manager.py` MUST continue to pass. New pytests MUST cover: (a) VPN row emits `type: reachability` for each of the three VPN classification paths (CENR bag, UDP observation, `-vpn.` pattern), (b) VPN row target is bare hostname, (c) non-VPN TCP/443 row is unchanged, (d) non-VPN non-443 TCP row is unchanged, (e) probe-type dispatch from target shape.
- **FR-009** *(optional, US3 only)*: If US3 is included in this feature, `src/utils/zscaler_probe.py::run_full_validation()` MUST append one JSONL record per VPN host per run to `data/vpn_ike_health.jsonl`. Each record MUST contain at minimum: hostname, ISO-8601 timestamp, ICMP reachability result (bool), UDP/500 `IKE_SA_INIT` result (bool), UDP/4500 `IKE_SA_INIT` result (bool).
- **FR-010** *(optional, US3 only)*: The JSONL append MUST NOT abort or destabilize `run_full_validation()` on failure (permission denied, disk full, path missing). The failure MUST be logged at WARNING level and the function MUST continue.
- **FR-011**: The feature MUST NOT introduce any new third-party dependency. Standard library only, matching the existing pattern in `src/utils/zscaler_probe.py` (`socket`, `struct`).

### Key Entities *(include if feature involves data)*

- **Synthetic-test row**: A single entry in the payload emitted to Mist by menu 206. Attributes referenced by this feature: `type` (either `application` or `reachability`) and the target field (URL for `application`, bare hostname for `reachability`).
- **VPN classification input**: Per-host metadata consulted during row emission. Attributes: CENR `vpn_hostnames` bag membership, observed transport (TCP/UDP) and port from telemetry, hostname pattern match against `-vpn.`.
- **VPN IKE health record** *(US3 only)*: One JSONL line in `data/vpn_ike_health.jsonl`. Attributes: hostname, timestamp, ICMP reachability, UDP/500 IKE result, UDP/4500 IKE result.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of VPN-classified hosts in the emitted synthetic-tests bundle carry `type: reachability` (measured by grep/count over a representative fixture bundle: count of rows where the target is a bare hostname matching a VPN classifier equals count of rows where type is `reachability`).
- **SC-002**: 0% of emitted rows target a VPN host with a fake URL or a `:500` suffix (grep over the emitted bundle for `:500`, `https://*-vpn.*`, and `http://*-vpn.*` returns zero matches on any VPN-classified host).
- **SC-003**: For a fixed input snapshot, the count of non-VPN rows and their byte-level content is unchanged between the pre-fix bundle and the post-fix bundle (INV-1 byte stability, verifiable by `diff` of the two bundles filtered to non-VPN rows).
- **SC-004**: Every existing pytest in `tests/unit/org/test_org_synthetic_probes_manager.py` passes, and the new reachability-emission tests add at least one assertion for each of the five FR-008 coverage points.
- **SC-005** *(US3 only)*: For every VPN host processed by one `run_full_validation()` run, exactly one JSONL record is appended to `data/vpn_ike_health.jsonl` (measured by line-count delta equal to the number of VPN hosts processed).
- **SC-006**: Once this fix is deployed, operators no longer see synthetic-test alerts on healthy Zscaler VPN edges (measured qualitatively: the pre-fix "permanent failure" baseline drops to zero on a live org with known-healthy VPN edges).

## Assumptions

- Menu 206 (`src/org/org_synthetic_probes_manager.py`) is the only emission path that produces synthetic-test rows for VPN endpoints. No other module emits parallel rows for the same hosts.
- Mist accepts `type: reachability` rows with a bare hostname (no port, no scheme) and interprets them as ICMP-ping targets. This is the documented Marvis Minis probe surface (two probe types: `application`, `reachability`).
- The CENR `vpn_hostnames` bag is authoritative for VPN identity: if a host is in the bag, it is a VPN endpoint even if it also happens to serve TCP/443 for admin traffic.
- The `_is_vpn_host` catalogue-default branch (`-vpn.` hostname pattern) is a stable fallback and its match criteria will not change under this feature.
- The existing `_udp_check()` in `src/utils/zscaler_probe.py` correctly sends IKEv2 `IKE_SA_INIT` per RFC 3948 §2.2 (bare on UDP/500, with non-ESP marker on UDP/4500). No changes to the IKE-probe wire format are required by this feature.
- The `data/` directory is writable by the process running `run_full_validation()`. If it is not, US3's JSONL append fails gracefully per FR-010.
- INV-1 (run-to-run byte stability for non-VPN rows) is measured against a fixed input snapshot, not against varying live CENR data — the invariant is about code determinism, not upstream data drift.
- No IPv6-only behavior differences are anticipated; Mist resolves DNS server-side for reachability targets, and bare-hostname emission is address-family-agnostic.
- Standard-library-only constraint applies: no new packages added to `pyproject.toml`.
