# Research: VPN Synthetic Probes Use Mist Reachability (ICMP)

**Feature**: 1024-vpn-icmp-reachability
**Phase**: 0 (Outline & Research)
**Date**: 2026-07-26

## Purpose

Feature 1024 is a targeted follow-up to feature 1023
(`probe-tailored-synthetic-tests`). No NEEDS CLARIFICATION items remain
in the spec. This document records the decisions, rationale, and
alternatives considered so future readers can trust the shape of the
implementation without re-deriving it from spec + code.

## Decision 1: VPN target shape = bare hostname (not `host:500`)

**Decision**: For every VPN-classified target, the emitted row's target
field is the bare hostname — no scheme, no `:port` suffix.

**Rationale**: Mist Marvis Minis supports exactly two probe types:
`application` (HTTP GET / TLS handshake) and `reachability` (ICMP ping).
Zscaler VPN edges answer IKEv2 on UDP/500 and UDP/4500 only. There is no
Mist probe type that speaks IKEv2. Emitting `host:500` under the pre-1024
code (or `https://host` under the pre-1023 code) produces a permanently
failing probe: the target port is dark to any HTTP or TCP-connect probe.
The only truthful signal Mist can produce for a VPN edge today is ICMP
reachability, and that requires a bare hostname target with
`type: reachability`.

**Alternatives considered**:

- **Emit `host:500` and rely on Mist adding an IKE prober someday.** Rejected: hope
  is not a strategy. Every emitted `host:500` today is a false alarm.
- **Emit no row at all for VPN endpoints.** Rejected: an unreachable VPN
  edge is exactly the kind of failure operators want to detect. Zero
  probe means zero signal; ICMP probe means partial signal (IP-layer
  reachability), which is strictly better.
- **Emit both `reachability` and `application` rows for VPN endpoints.**
  Rejected: the `application` row is guaranteed to fail and adds the
  exact noise this feature is removing. INV-1 is best preserved by a
  single-row-per-VPN-endpoint model.

## Decision 2: Probe type dispatched from final target shape

**Decision**: The classifier `_probe_type_for_target(target, role_type)`
inspects the target string and returns:

- `application` if `target` starts with `http://` or `https://`
- `application` if `target` contains an explicit `:port` suffix (no scheme)
- `reachability` if `target` is a bare hostname (no scheme, no `:port`)

The `role_type` parameter is retained for backward-compat but is now
dominated by the shape check.

**Rationale**: The shape of the target is the ground truth for what Mist
will actually do. A `https://` prefix triggers a TLS/HTTP probe; a bare
`host:port` triggers a TCP-connect probe; a bare hostname triggers
ICMP. Deriving the type from the shape (rather than from an upstream
classification that must be threaded through call chains) collapses the
decision into one testable location and eliminates a class of bugs where
target and type could disagree.

**Alternatives considered**:

- **Thread the probe type through every call frame from
  `_probe_target()` down to the row builder.** Rejected: three separate
  emit callsites (`_build_probe_set`, `_build_region_probes`,
  `_merge_probes`) already exist, and passing a second parallel value is
  the exact source of the current bug (target and type diverged in
  `_merge_probes`). One-shape-one-type is the smaller invariant.
- **Move the dispatch inline to each callsite.** Rejected: duplication
  invites drift. The shared helper is 8 lines; the tests for it are the
  single-source-of-truth for the rule.

## Decision 3: Reuse existing `_is_vpn_host` classifier

**Decision**: VPN classification input is unchanged from today
(`_is_vpn_host` + CENR bag lookup + `_udp_check` observation).

**Rationale**: The classification is already correct and covered by
existing tests. The bug this feature fixes is in the target-shape
emission, not in the classifier. Widening scope to also touch the
classifier would risk regressing VPN identification and violate INV-1
for tests that already pin the classification decision.

**Alternatives considered**: n/a — scope-limiting decision.

## Decision 4: JSONL telemetry under `data/` (US3, optional in-scope)

**Decision**: If US3 is included, `run_full_validation()` appends one
JSONL record per VPN host per invocation to `data/vpn_ike_health.jsonl`.
Fields: `hostname`, `ts` (ISO-8601 UTC), `icmp_ok` (bool),
`ike_500_ok` (bool), `ike_4500_ok` (bool). Optional field:
`ike_500_latency_ms` and `ike_4500_latency_ms` if the existing
`_udp_check()` returns them.

**Rationale**: JSONL is the existing telemetry-emission pattern in this
codebase (see other `data/*.jsonl` under the repo). Append-only preserves
history. Standard-library `json.dumps` + `pathlib.Path.open("a", encoding="utf-8")`
is enough; no new deps. Wrapping the write in a `try/except OSError` with
a `logger.warning` fulfils FR-010.

**Alternatives considered**:

- **Write to SQLite.** Rejected: FR-011 forbids new deps; SQLite from
  stdlib is available but adds schema management and file-locking
  concerns for a pure append workload. JSONL wins on simplicity.
- **Log-line-with-structured-fields only.** Rejected: US3 explicitly asks
  to promote log-only to structured telemetry so a downstream report can
  differentiate reachable-but-IKE-dead edges. Log parsing is the wrong
  layer.
- **Emit inside a new `TelemetryEmitter` instance.** Considered — the
  existing `TelemetryEmitter` in the codebase already handles this shape,
  but importing it into `zscaler_probe.py` creates a new module
  dependency for a 10-line helper. Direct stdlib write is smaller and
  keeps `zscaler_probe.py` self-contained.

## Decision 5: Byte-stable non-VPN output (INV-1) enforced by test

**Decision**: A regression test captures the emitted bundle for a
fixture org containing a mix of VPN and non-VPN endpoints against the
pre-1024 baseline, filters to non-VPN rows, and diffs against the
post-1024 output for the same input. Any drift fails the test.

**Rationale**: INV-1 is a hard constraint on this fix (SC-003, FR-007).
A dedicated test is the only way to catch accidental drift in the merge
paths or the dispatch. Test lives in
`tests/unit/org/test_org_synthetic_probes_manager.py` under an
`INV1` marker or naming prefix so it is grep-visible.

**Alternatives considered**:

- **Rely on the existing broad test coverage.** Rejected: existing tests
  assert individual rows; none diff whole bundles. A dedicated bundle
  test is needed to catch cross-row ordering / whitespace regressions.

## Decision 6: No new `run_full_validation()` behavior beyond append

**Decision**: US3 changes only where the existing IKE probe results are
persisted (log-line -> log-line + JSONL append). The probe wire format,
the timeout defaults, and the `_udp_check` semantics are unchanged.

**Rationale**: The IKE probe is already correct per RFC 3948 §2.2 (bare
IKEv2 on UDP/500, non-ESP marker on UDP/4500). Scope-creep into the
prober risks regressing a working component.

**Alternatives considered**: n/a — scope-limiting decision.

## Open items (none blocking)

- **Choice of ISO-8601 field name (`ts` vs `timestamp` vs `time`)**:
  Resolved: `ts` chosen to match existing convention across contract,
  data-model, and task fixtures. No further check required at
  implementation time.

## References

- Spec: `specs/1024-vpn-icmp-reachability/spec.md`
- Precursor: `specs/1023-probe-tailored-synthetic-tests/plan.md`,
  `specs/1023-probe-tailored-synthetic-tests/contracts/probe_target_url_builder.md`
- Constitution: `.specify/memory/constitution.md` (v1.4.0)
- Code: `src/org/org_synthetic_probes_manager.py::_probe_target`,
  `::_probe_type_for_target`, `::_is_vpn_host`;
  `src/utils/zscaler_probe.py::run_full_validation`, `::_udp_check`
