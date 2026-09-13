# Implementation Plan: VPN Synthetic Probes Use Mist Reachability (ICMP)

**Branch**: `1024-vpn-icmp-reachability` | **Date**: 2026-07-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/1024-vpn-icmp-reachability/spec.md`

## Summary

Pivot the VPN branches of the menu 206 synthetic-tests emitter from a fake
L4 probe (`host:500` emitted as an `application`-type row) to a truthful
Mist Marvis Minis **`reachability`** probe (bare-hostname ICMP target). The
row-emission callsite must dispatch probe type from the final target
shape, so the classification rule is central and testable:

- Target with URL scheme (`http://` / `https://`)  -> `type: application`
- Target with an explicit `:port` suffix (no scheme) -> `type: application`
- Bare hostname (no scheme, no port)              -> `type: reachability`

VPN classification is unchanged (CENR `vpn_hostnames` bag, observed UDP
telemetry, `-vpn.` catalogue-default pattern via `_is_vpn_host`). Only the
per-VPN target *shape* changes, from `host:500` to `host`. Non-VPN rows
(HTTPS/TCP-443 and non-443 TCP) are byte-identical to today's output for
the same input snapshot (INV-1).

Optional in-scope P3 follow-up (US3): promote the truthful IKEv2
`IKE_SA_INIT` probe results from `src/utils/zscaler_probe.py::
run_full_validation()` from log-only to append-only JSONL telemetry under
`data/vpn_ike_health.jsonl`.

Feature 1023 delivered the three-branch dispatch that first stopped
emitting fake HTTPS URLs for UDP-observed hosts. Feature 1024 takes the
next honest step: when Mist cannot speak the actual protocol (IKEv2), do
not emit an L4 target it will silently fail — emit a reachability target
Mist can succeed at.

## Technical Context

**Language/Version**: Python 3.13+ (`pyproject.toml` requires `>=3.13`;
matches project constitution binding minimum).

**Primary Dependencies**: Standard library only (`logging`, `pathlib`,
`json`, `datetime`; `socket` and `struct` already imported by
`zscaler_probe.py` for US3). No new third-party package (FR-011).

**Storage**: Local append-only JSONL under `data/` for US3
(`data/vpn_ike_health.jsonl`), matching the existing `TelemetryEmitter`
pattern used elsewhere in the codebase. No schema migration; new file
only.

**Testing**: `pytest` with `pytest-mock` and `caplog`. New tests co-locate
under `tests/unit/org/test_org_synthetic_probes_manager.py` (row-emission
+ dispatch) and `tests/unit/utils/test_zscaler_probe.py` (JSONL append,
US3).

**Target Platform**: Cross-platform Python CLI. Behavior identical on
macOS, Linux, and Windows; JSONL append uses `pathlib` and UTF-8 explicit
encoding.

**Project Type**: Single-project CLI (`MistHelper.py` menu-driven).
Applies existing `src/` and `tests/` layout.

**Performance Goals**: Row emission is O(rows) and unchanged. JSONL append
in US3 is one bounded write per VPN host per 8h refresh cycle — negligible
compared to the existing CENR probe cost.

**Constraints**:

- INV-1 byte stability for every non-VPN row against a fixed input
  snapshot (SC-003).
- Zero new dependencies (FR-011).
- JSONL append must not abort `run_full_validation()` on I/O failure
  (FR-010).
- Existing pytests under
  `tests/unit/org/test_org_synthetic_probes_manager.py` must continue to
  pass after their VPN-row assertions are updated to the new bare-hostname
  shape (FR-008, SC-004).

**Scale/Scope**: One code path in `_probe_target()` (VPN branches), one
callsite-shared classifier (`_probe_type_for_target`), one optional JSONL
appender in `zscaler_probe.py`. Estimated blast radius: ~40 LOC in
`org_synthetic_probes_manager.py` (VPN-target return + tightened
dispatch), ~30 LOC in `zscaler_probe.py` (US3 append helper + call
integration), ~15 new/updated assertions in tests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against `.specify/memory/constitution.md` v1.4.0 (seven Core
Principles).

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Docstring Coverage & Style | PASS | All new/modified functions carry Google-style docstrings with a "Why" section. `interrogate` >=90% gate holds; `pydoclint --style=google` passes. |
| II. Class Extraction When Idiomatic | PASS (justified variance, carried from 1023) | The shared dispatch helper `_probe_type_for_target` and the VPN-target computation remain **plain module functions** — they are stateless, single-purpose, and idiomatic Python. Wrapping them in a class would add ceremony without state or polymorphism. See Complexity Tracking below. |
| III. Standard-Library Preference | PASS | Zero new dependencies. `logging`, `pathlib`, `json`, `datetime`, `socket`, `struct` already present. |
| IV. Test-First for Behavioural Change | PASS | Phase 1 emits contracts + quickstart validation scenarios; failing tests will be authored before impl (see `quickstart.md`). |
| V. Byte-Stable Emission (INV-1) | PASS | Non-VPN row output pinned by test (FR-007, SC-003). Diff-of-bundles fixture in tests will assert byte identity. |
| VI. Inline Comments For Non-Obvious Blocks | PASS | The three-branch classifier and the JSONL failure-swallow path carry explicit `#` comments explaining the constraint (Mist cannot speak IKEv2; graceful-degrade required by FR-010). |
| VII. Action Logging (non-negotiable) | PASS | `logger.info(...)` records every VPN row emitted with target and probe type; `logger.warning(...)` records JSONL append failures per FR-010. |

**Gate result**: PASS (one justified variance under Principle II,
identical to the variance already accepted in feature 1023's plan).

## Project Structure

### Documentation (this feature)

```text
specs/1024-vpn-icmp-reachability/
|-- plan.md                              # This file
|-- spec.md                              # Feature spec (input)
|-- research.md                          # Phase 0 output
|-- data-model.md                        # Phase 1 output
|-- quickstart.md                        # Phase 1 output
|-- contracts/                           # Phase 1 output
|   |-- probe_type_dispatch.md           # Target-shape -> type dispatch rule
|   |-- vpn_probe_target_shape.md        # VPN branches emit bare hostname
|   `-- vpn_ike_health_jsonl.md          # US3 JSONL schema (optional)
`-- tasks.md                             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/
|-- org/
|   `-- org_synthetic_probes_manager.py  # MODIFIED: VPN branches of
|                                        # _probe_target() -> bare hostname;
|                                        # _probe_type_for_target() tightened
|                                        # to shape-based dispatch
`-- utils/
    `-- zscaler_probe.py                 # MODIFIED (US3 only): JSONL append
                                         # in run_full_validation()

tests/
`-- unit/
    |-- org/
    |   `-- test_org_synthetic_probes_manager.py  # UPDATED: VPN rows now
    |                                             # assert bare hostname +
    |                                             # type: reachability;
    |                                             # non-VPN byte-stability test
    `-- utils/
        `-- test_zscaler_probe.py                 # NEW tests for US3
                                                  # JSONL append

data/
`-- vpn_ike_health.jsonl                          # NEW (US3 only, runtime-created)
```

**Structure Decision**: Existing single-project CLI layout under `src/`
and `tests/` is preserved. All edits are targeted to the two modules
already established by feature 1023 and their unit-test peers. No new
top-level directories or packages.

## Complexity Tracking

> Justifies one variance carried over from feature 1023.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Plain module functions (`_probe_type_for_target`, `_probe_target` VPN branches) instead of a `ProbeTargetClassifier` class per Principle II | These helpers are stateless single-purpose computations that fit the local pipeline call-site idiomatically. Extracting a class adds construction ceremony, an implicit `self` bag, and a new import surface for every emit callsite (`_build_probe_set`, `_build_region_probes`, `_merge_probes`) with no behavior gain. | A class was rejected because there is no shared state, no polymorphic dispatch, and no lifecycle to manage. The functions are already at the right granularity — small, pure, testable — and Principle II explicitly permits plain functions "when idiomatic." Wrapping them would violate the spirit of the principle to satisfy its letter. |
