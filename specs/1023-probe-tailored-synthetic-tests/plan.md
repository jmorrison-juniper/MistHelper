# Implementation Plan: Probe-Tailored Synthetic Tests

**Branch**: `1023-probe-tailored-synthetic-tests` | **Date**: 2026-07-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/1023-probe-tailored-synthetic-tests/spec.md`

## Summary

Menu 206 (org Zscaler synthetic-probes manager) currently emits `https://<host>`
targets for every catalogued Zscaler CENR hostname, including VPN initiators
(`*-vpn.zscaler.net`) that only answer IKE on UDP 500/4500. Real Marvis-mini
pcap traces confirm those VPN rows record 8x TCP SYN retries with zero reply,
while sibling proxy hosts (`*.sme.zscaler.net`) complete TLS cleanly.

This plan delivers three cooperating changes, all stdlib-only:

1. **`src/utils/zscaler_probe.py`** gains a `_udp_check()` primitive that sends a
   well-formed IKE_SA_INIT header (stdlib `struct`, no crypto) on UDP/500 and
   UDP/4500. `ProbeResult` grows a `udp: dict[int, str]` field and
   `_probe_fqdn()` triggers UDP probing when the FQDN matches `*-vpn.` **or**
   every TCP port came back non-open.
2. **`src/utils/zscaler_catalogue.py`** bumps the CENR cache schema to v3 so
   each hostname persists its last-observed protocol/port. A small adapter
   keeps v2 (flat-string) caches readable; the TTL refresh now calls
   `run_full_validation()` and writes observations back to disk.
3. **`src/org/org_synthetic_probes_manager.py::_probe_target()`** prefers the
   persisted observation over the catalogue default. UDP-family observation ->
   bare `host:port`; HTTPS/TCP-443 -> `https://host`; no observation -> current
   catalogue default plus a `logger.warning` naming the host.

No new runtime dependencies. All new tests mock `socket.socket`,
`subprocess.run`, and `getaddrinfo`; unit-test suite baseline is 8719+ passing
tests and must stay green plus grow by the newly added cases.

## Technical Context

**Language/Version**: Python 3.13+ (per constitution binding minimum and
`pyproject.toml` `py313` target).

**Primary Dependencies**: stdlib only. `socket` (existing), `struct` (new use
for IKE_SA_INIT header assembly), `logging`, `dataclasses`, `pathlib`, `json`,
`concurrent.futures` are already in scope. `mistapi>=0.63.1` is already a
transitive dependency of Menu 206 and is unchanged by this feature.

**Storage**: Local append-only JSON files under `data/`:
- `data/zscaler_cenr_hostnames.json` (schema bumps v2 -> v3)
- `data/zscaler_client_connector_probes.json` (unchanged file location;
  observation fields attached at the role/fqdn level per the same v3 pattern).

No database schema change. No remote persistence added.

**Testing**: `pytest` with `unittest.mock`. All new tests live in:
- `tests/unit/utils/test_zscaler_probe.py` (extended)
- `tests/unit/utils/test_zscaler_catalogue.py` (extended)
- `tests/unit/org/test_org_synthetic_probes_manager.py` (extended for the URL
  builder branches)

100% branch coverage is required on the new decision points (`_udp_check`
return states, `_probe_fqdn` UDP-trigger predicate, `_probe_target` three-way
priority) per SC-004.

**Target Platform**: Windows 11 + venv for local dev; Linux Podman container in
production. No platform-specific UDP behaviour is introduced (stdlib
`socket.SOCK_DGRAM` on both).

**Project Type**: Single project (existing MistHelper layout under `src/` and
`tests/`).

**Performance Goals**: `_udp_check` completes within `timeout + <500 ms`
overhead in every branch (SC-007). No unit test blocks longer than 2 seconds.
`run_full_validation()` is still full-fleet (~1000 endpoints) but only fires
on TTL refresh (>=8h cadence).

**Constraints**:
- Stdlib-only (FR-017); no new package in `pyproject.toml` or
  `requirements.txt`.
- Backward compatibility (FR-006): v2 flat-string caches load without
  exception and are treated as "no observation cached".
- Mist API surface unchanged (FR-008): still `updateOrgSettings` PUT; only the
  string value inside `custom_probes[i].target` changes shape.
- Constitution Principle VI (inline comments) and VII (action logging)
  are non-negotiable quality gates on every changed line.

**Scale/Scope**: ~30 ZCC catalogue entries + ~990 CENR ZEN hostnames. Roughly
10-20% of CENR entries are VPN initiators; those are the exact rows this
feature repairs. Three source files touched; three test files extended.

## Constitution Check

Evaluating against MistHelper constitution v1.4.0 (all seven Core Principles):

| Principle | Compliance | Notes |
|-----------|------------|-------|
| I. Five-Item Rule | PASS | `_udp_check` fits <=25 lines / <=5 blocks. `_probe_target` gains a 3-branch dispatch (still <=5). No new function exceeds 5 parameters. |
| II. Class-Based Architecture | PASS with justification | Existing module-level free functions in `zscaler_probe.py` are the established idiom for this file (a stdlib-probe primitives library, not a stateful service). No wrapper functions added; new helpers (`_udp_check`, adapter) are peer primitives that live alongside `_tcp_check`. See Complexity Tracking. |
| III. Safety-First | PASS | New code paths add no `input()` calls. UDP socket timeouts are enforced via `settimeout`. OSError family is caught explicitly and returned as `"error:<ExceptionClassName>"`. No secrets touched or logged. |
| IV. Full Deployment Pipeline | DEFERRED to `/speckit.implement` | Plan does not commit or push; implementation phase runs syntax-validate + commit + push + CI + container pull + restart + verify. |
| V. Observability & Logging | PASS | New logs are ASCII-only; use `%s` formatting; `logger.info` before each meaningful action, `logger.debug` after with result summary; `logger.warning` on missing observation per FR-007. No secrets logged. |
| VI. Inline Comments (NON-NEGOTIABLE) | PASS | Every changed and adjacent line will carry an inline `#` comment explaining what and why. Enforced during implementation; validated in review. |
| VII. Action Logging (NON-NEGOTIABLE) | PASS | Every meaningful action (UDP send, socket close, observation write, target build) is wrapped with `logging.info(...)` before and `logging.debug(...)` after per Principle VII sample pattern. |

**Result**: PASS. One justified variance (Principle II, plain-function
extraction) documented in the Complexity Tracking table below.

## Project Structure

### Documentation (this feature)

```text
specs/1023-probe-tailored-synthetic-tests/
|-- plan.md              # This file (/speckit.plan output)
|-- research.md          # Phase 0 output (/speckit.plan output)
|-- data-model.md        # Phase 1 output (/speckit.plan output)
|-- quickstart.md        # Phase 1 output (/speckit.plan output)
|-- contracts/           # Phase 1 output (/speckit.plan output)
|   |-- probe_result.md
|   |-- cenr_cache_schema_v3.md
|   \-- probe_target_url_builder.md
|-- checklists/          # (pre-existing)
|-- spec.md              # (input)
\-- tasks.md             # Phase 2 output (/speckit.tasks - NOT created here)
```

### Source Code (repository root)

```text
src/
|-- utils/
|   |-- zscaler_probe.py         # MODIFIED: add IKE_UDP_PORTS, _udp_check,
|   |                            #           extend ProbeResult.udp, extend
|   |                            #           _probe_fqdn trigger logic.
|   \-- zscaler_catalogue.py     # MODIFIED: schema_version 2 -> 3, persist
|                                #           observations, v2 adapter,
|                                #           run_full_validation feedback.
\-- org/
    \-- org_synthetic_probes_manager.py  # MODIFIED: _probe_target consults
                                         #           observation first;
                                         #           logger.warning on miss.

tests/
\-- unit/
    |-- utils/
    |   |-- test_zscaler_probe.py       # EXTENDED: UDP branches + trigger
    |   \-- test_zscaler_catalogue.py   # EXTENDED: v3 write + v2-read adapter
    \-- org/
        \-- test_org_synthetic_probes_manager.py  # EXTENDED: 3-branch
                                                  #           target builder.

data/
|-- zscaler_cenr_hostnames.json          # WRITTEN on refresh (schema_version=3)
\-- zscaler_client_connector_probes.json # WRITTEN on refresh (obs fields
                                         #           added under roles[].fqdns)
```

**Structure Decision**: Single-project layout as established. All three
source files already exist and are extended in-place; no new modules are
created. Test files are extended, not replaced. No changes outside `src/` and
`tests/` beyond the specs directory and the persisted JSON caches under
`data/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Plain-function extractions in `zscaler_probe.py` (Principle II calls for classes) | `zscaler_probe.py` is a stdlib-probe primitives library. Every existing primitive (`_tcp_check`, `_do_http`, `_tls_peer`, `_icmp_ping`, `_resolve`) is a plain module-level function. Introducing a `UdpProbe` class purely for `_udp_check` would break the symmetry of the file and force every caller (already-existing `_probe_fqdn`) into inconsistent invocation patterns for peer primitives. | Wrapping `_udp_check` inside a class (e.g. `UdpReachabilityChecker.check(host, port, timeout)`) satisfies Principle II's letter but not its intent: the class would carry no state, exist for one method, and force call sites to instantiate-per-call. That is precisely the "wrapper function" anti-pattern Principle II forbids. Symmetry with existing peers (`_tcp_check`) is the primary constraint. |
