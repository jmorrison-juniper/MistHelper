---

description: "Task list for feature 1024-vpn-icmp-reachability"
---

# Tasks: VPN Synthetic Probes Use Mist Reachability (ICMP)

**Input**: Design documents from `/specs/1024-vpn-icmp-reachability/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md,
contracts/probe_type_dispatch.md, contracts/vpn_probe_target_shape.md,
contracts/vpn_ike_health_jsonl.md

**Tests**: Tests-first per Principle IV. Every behavioural change lands
as a failing test first, then the implementation that turns it green.

**Organization**: Tasks are grouped by user story. US1 (P1) and US2 (P1)
share the same edit surface but are kept in distinct phases so US2's
byte-stability guard is a first-class deliverable. US3 (P3) is a
distinct trailing block that can be skipped without breaking US1/US2.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Every task carries an explicit file path

## Path Conventions

Single-project CLI layout (per `plan.md`):

- Source: `src/org/`, `src/utils/`
- Tests: `tests/unit/org/`, `tests/unit/utils/`
- Fixtures: `tests/unit/org/fixtures/`
- Telemetry (US3 only, runtime-created): `data/vpn_ike_health.jsonl`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Ensure fixture scaffolding is in place before test-first work
begins. No new dependencies (stdlib only per FR-011).

- [X] T001 [P] Create fixtures directory `tests/unit/org/fixtures/` (if not
  present) and add a placeholder `.gitkeep` so subsequent parallel fixture
  authoring tasks (T012, T013) do not race on mkdir. No content changes to
  existing files.
- [X] T002 [P] Verify no new dependency is required: read
  `pyproject.toml` and confirm `[project].dependencies` and
  `[project.optional-dependencies].dev` are unchanged after this feature
  scope. If any is proposed later, halt and revisit FR-011.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: None. This feature edits two existing modules already
introduced by feature 1023 and adds tests to existing test files. No
schema, no framework, no auth. Skip straight to US1.

**Checkpoint**: Foundation is already in place from feature 1023.
User-story phases may begin immediately after Phase 1.

---

## Phase 3: User Story 1 - Truthful VPN Health Signal in Marvis Minis (Priority: P1) MVP

**Goal**: VPN-classified targets emit as `type: reachability` with a
bare-hostname target instead of `type: application` with `host:500`.

**Independent Test**: Run
`pytest tests/unit/org/test_org_synthetic_probes_manager.py::TestProbeTargetVpn -v`
and `TestProbeTypeDispatch -v`. All new VPN-branch assertions pass. No
row in the emitted bundle for a VPN-classified host contains `:500`,
`:4500`, `http://`, or `https://` (see quickstart Scenarios A, B, C, G).

### Tests for User Story 1 (test-first, MUST FAIL before implementation)

- [ ] T003 [P] [US1] Author `TestProbeTypeDispatch` test class in
  `tests/unit/org/test_org_synthetic_probes_manager.py` covering the 8
  dispatch cases from `contracts/probe_type_dispatch.md` (Scenario G):
  `https://example.com` -> `application`; `http://example.com` ->
  `application`; `example.com:443` -> `application`; `example.com:8080`
  -> `application`; `example.com:500` -> `application` (pre-1024 leakage
  guard); `example.com` -> `reachability`;
  `gateway.zscalerthree.net` -> `reachability`; and shape-wins-over-
  `role_type` (role_type=`application` + bare hostname target still
  returns `reachability`). Tests target
  `src.org.org_synthetic_probes_manager._probe_type_for_target`. MUST NOT
  touch the network.
- [ ] T004 [P] [US1] Author
  `TestProbeTargetVpn::test_cenr_bag_vpn_emits_bare_hostname` in
  `tests/unit/org/test_org_synthetic_probes_manager.py` (Scenario A,
  spec Acceptance 1): fixture CENR document with
  `vpn_hostnames = ["gateway.zscalerthree.net"]`, no observed traffic.
  Assert `_probe_target(fqdn, role, cenr_source) == "gateway.zscalerthree.net"`
  and no `:`, no `http` prefix in the returned string.
- [ ] T005 [P] [US1] Author
  `TestProbeTargetVpn::test_udp_observed_emits_bare_hostname` in
  `tests/unit/org/test_org_synthetic_probes_manager.py` (Scenario B, spec
  Acceptance 2): fixture with `edge-vpn.example.com` present only via
  observed UDP/500 telemetry, not in any `vpn_hostnames` bag. Assert
  `_probe_target` returns bare `"edge-vpn.example.com"` and the emitted
  bundle contains no `application`-type row for the same host.
- [ ] T006 [P] [US1] Author
  `TestProbeTargetVpn::test_vpn_pattern_only_emits_bare_hostname` in
  `tests/unit/org/test_org_synthetic_probes_manager.py` (Scenario C, spec
  Acceptance 3): fixture with `fra4-vpn.zscalerthree.net` — no CENR bag
  entry, no observation, matches `_is_vpn_host` catalogue-default
  `-vpn.` pattern. Assert `_probe_target` returns bare
  `"fra4-vpn.zscalerthree.net"` and `_probe_type_for_target` returns
  `reachability`.
- [ ] T007 [P] [US1] Author
  `TestProbeTargetVpn::test_bag_wins_over_tcp443_observation` in
  `tests/unit/org/test_org_synthetic_probes_manager.py` (spec Edge Case
  "VPN hostname also observed on TCP/443"): fixture with the host in
  `vpn_hostnames` bag AND observed on TCP/443. Assert `_probe_target`
  returns bare FQDN (bag wins), not `https://...`.
- [ ] T008 [P] [US1] Author
  `TestProbeTargetVpn::test_vpn_emit_logs_info_once` in
  `tests/unit/org/test_org_synthetic_probes_manager.py` using pytest
  `caplog` at `INFO`. Assert one line matching
  `probe_target(vpn): <fqdn> -> bare (reachability)` per VPN emit
  (satisfies Principle VII / `vpn_probe_target_shape.md` §Logging).
- [ ] T009 [US1] Update the existing test
  `test_no_https_vpn_targets_in_generated_payload` (line ~1803) and any
  other existing pytests in
  `tests/unit/org/test_org_synthetic_probes_manager.py` that assert the
  pre-1024 VPN target shape (`host:500`) so they assert the new bare-
  hostname + `type: reachability` shape. Do NOT weaken assertions;
  strengthen or replace them. Runs sequentially after T003-T008 because
  it edits the same file those tasks touched.

### Implementation for User Story 1

- [ ] T010 [US1] Tighten `_probe_type_for_target` at
  `src/org/org_synthetic_probes_manager.py` line ~163 to shape-based
  dispatch per `contracts/probe_type_dispatch.md` §Decision Rule:
  (1) if `target` starts with `http://` or `https://` return
  `"application"`; (2) if a `":"` appears after the last `"."` in
  `target` return `"application"`; (3) else return `"reachability"`.
  Preserve the `role_type` parameter in the signature for backwards
  compat but do not consult it. Add `logger.debug("probe_type: target=%s -> %s", target, decision)`
  before return. Update the docstring's "Why" section to explain
  shape-wins-over-role-type and INV-2. Verify T003 (dispatch tests) now
  passes.
- [ ] T011 [US1] Modify the VPN pre-check branch in `_probe_target` at
  `src/org/org_synthetic_probes_manager.py` line ~337 (the
  `if _is_vpn_host(fqdn, cenr_source):` block) per
  `contracts/vpn_probe_target_shape.md`: return the bare `fqdn` (drop
  the `:500` suffix that pre-1024 code produced). Emit
  `logger.info("probe_target(vpn): %s -> bare (reachability)", fqdn)`
  once inside the branch. Do NOT touch the non-VPN branches below it
  (INV-1). Update the function docstring's "Why" section to explain
  Mist has no IKEv2 probe type, so ICMP reachability is the only
  truthful signal. Verify T004-T008 now pass.
- [ ] T012 [US1] Audit the three row-emission callsites that call
  `_probe_type_for_target(target, role.get("type"))` at
  `src/org/org_synthetic_probes_manager.py` lines ~793, ~879, ~1196
  (`_build_probe_set`, `_build_region_probes`, `_merge_probes`). Confirm
  each callsite (a) builds `target` via `_probe_target(...)` first and
  (b) derives `type` via `_probe_type_for_target(target, ...)` with no
  per-callsite override of `type`. If any callsite still hard-codes
  `type: application` for VPN paths, remove that override — the
  shape-based dispatcher is now the single source of truth (INV-2).

**Checkpoint**: US1 is functional. Menu 206 emits `type: reachability` +
bare hostname for every VPN-classified target. All new US1 tests pass;
existing pre-1024 VPN-shape tests have been rewritten (T009). SC-001 and
SC-002 are testable at this point.

---

## Phase 4: User Story 2 - Byte-Identical Non-VPN Behavior (Priority: P1)

**Goal**: Non-VPN rows (HTTPS/TCP-443, non-443 TCP, no-observation
fallback) are byte-identical to the pre-1024 output for the same input
snapshot. INV-1 preserved.

**Independent Test**: Run
`pytest tests/unit/org/test_org_synthetic_probes_manager.py::TestInv1ByteStability -v`
and the Scenario D + E targeted tests. Non-VPN row diff between
pre-1024 baseline and post-1024 output is empty.

### Tests for User Story 2 (test-first)

- [ ] T013 [P] [US2] Create fixture
  `tests/unit/org/fixtures/smoke_org.json` — a minimal CENR-shaped
  input containing (a) at least one CENR-bag VPN host, (b) at least one
  UDP-observed VPN host, (c) at least one `-vpn.` pattern host with no
  observation, (d) at least one non-VPN TCP/443 host, (e) at least one
  non-VPN non-443 TCP host. Used by both US2 INV-1 test and the
  quickstart Scenario I smoke.
- [ ] T014 [P] [US2] Create fixture
  `tests/unit/org/fixtures/expected_smoke_bundle.json` — the
  hand-authored expected bundle for the mixed VPN+non-VPN smoke fixture,
  covering (i) VPN rows in the post-1024 shape (bare hostname,
  `type: reachability`) and (ii) all non-VPN rows in their current
  shape. This is the authoritative INV-1 baseline for future diffs.
- [ ] T015 [P] [US2] Author
  `TestProbeTargetVpn::test_non_vpn_https_unchanged` in
  `tests/unit/org/test_org_synthetic_probes_manager.py` (Scenario D,
  spec US2 Acceptance 1): fixture non-VPN host observed on TCP/443.
  Assert row has `type == "application"` and `target == "https://<host>"`.
- [ ] T016 [P] [US2] Author
  `TestProbeTargetVpn::test_non_vpn_tcp_non443_unchanged` in
  `tests/unit/org/test_org_synthetic_probes_manager.py` (Scenario E,
  spec US2 Acceptance 2): fixture non-VPN host observed on TCP/8080.
  Assert row has `type == "application"` and `target == "<host>:8080"`.
- [ ] T017 [P] [US2] Author `TestInv1ByteStability` test class in
  `tests/unit/org/test_org_synthetic_probes_manager.py` (Scenario F):
  load `tests/unit/org/fixtures/smoke_org.json`, run the bundle
  emission through the public entrypoint used by menu 206, load
  `tests/unit/org/fixtures/expected_smoke_bundle.json`, filter both
  to non-VPN rows (rows whose target starts with `http` or contains
  `:port` after the last `.`), assert the two filtered lists are
  byte-identical (`json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)`).

### Implementation for User Story 2

- [ ] T018 [US2] Run the US2 test suite (T015, T016, T017) against the
  US1 implementation from T010-T012. Non-VPN rows should already be
  byte-stable because T010 only tightens dispatch and T011 only touches
  the VPN branch. If any drift is observed, isolate it (likely a
  callsite in T012's audit that had a stale `type` override), fix in
  the same file, and re-run until the diff in T017 is empty. Do NOT
  modify baseline `expected_smoke_bundle.json` to hide drift — treat
  any diff as a regression.

**Checkpoint**: US1 + US2 both green. Menu 206 emits truthful VPN
signal AND preserves byte-stable non-VPN output. This is the MVP.
Feature can ship here; US3 is optional trailing.

---

## Phase 5: User Story 3 - VPN IKE Health JSONL Telemetry (Priority: P3, optional in-scope)

> **Skippable**: US3 is P3 per spec. If scope pressure arises, skip
> Phase 5 entirely and ship US1+US2. Nothing in Phase 5 modifies files
> touched by US1/US2. All Phase 5 file edits are additive.

**Goal**: `run_full_validation()` in `src/utils/zscaler_probe.py`
appends one JSONL line per VPN host per invocation to
`data/vpn_ike_health.jsonl`, so a future report can distinguish
reachable-but-IKE-dead edges from fully-healthy ones.

**Independent Test**: Run
`pytest tests/unit/utils/test_zscaler_probe.py::TestVpnIkeHealthJsonl -v`.
All six US3 tests pass. `run_full_validation` remains stable on
`PermissionError` from the JSONL write path (FR-010).

### Tests for User Story 3 (test-first)

- [ ] T019 [P] [US3] Author
  `TestVpnIkeHealthJsonl::test_happy_path_writes_one_line` in
  `tests/unit/utils/test_zscaler_probe.py` (contract §Test Boundaries,
  quickstart Scenario H): monkeypatch `_icmp_ping` and `_udp_check`,
  call `_append_ike_health_record(hostname="gateway.zscalerthree.net", icmp_ok=True, ike_500_ok=False, ike_4500_ok=False, path=tmp_path / "vpn_ike_health.jsonl")`
  once, assert file exists with exactly one line, `json.loads` yields
  the five expected keys with expected values, `ts` is ISO-8601 UTC
  matching `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z`.
- [ ] T020 [P] [US3] Author
  `TestVpnIkeHealthJsonl::test_append_across_two_runs` in
  `tests/unit/utils/test_zscaler_probe.py` (spec US3 Acceptance 3):
  call `_append_ike_health_record` twice with the same host, assert
  file has exactly two lines and prior line preserved (no truncation).
- [ ] T021 [P] [US3] Author
  `TestVpnIkeHealthJsonl::test_reachable_but_ike_dead` in
  `tests/unit/utils/test_zscaler_probe.py` (spec US3 Acceptance 1):
  call `_append_ike_health_record` with `icmp_ok=True, ike_500_ok=False, ike_4500_ok=False`.
  Assert emitted line has those exact three bools.
- [ ] T022 [P] [US3] Author
  `TestVpnIkeHealthJsonl::test_ike_500_healthy` in
  `tests/unit/utils/test_zscaler_probe.py` (spec US3 Acceptance 2):
  call with `icmp_ok=True, ike_500_ok=True`. Assert emitted record has
  `ike_500_ok: true`.
- [ ] T023 [P] [US3] Author
  `TestVpnIkeHealthJsonl::test_permission_error_swallowed_with_warn`
  in `tests/unit/utils/test_zscaler_probe.py` (FR-010): monkeypatch
  `pathlib.Path.open` on the target path to raise `PermissionError`
  (or use a `path` argument pointing at an unwritable location). Call
  `_append_ike_health_record`. Assert (a) function returns without
  raising, (b) exactly one `WARNING`-level log line is emitted via
  `caplog` containing the hostname and error, (c) file is not created.
- [ ] T024 [P] [US3] Author
  `TestVpnIkeHealthJsonl::test_field_ordering` in
  `tests/unit/utils/test_zscaler_probe.py` (contract §Field ordering):
  parse the raw line (not `json.loads`, which drops ordering) and
  assert the four keys appear in the order
  `ts, hostname, icmp_ok, ike_500_ok, ike_4500_ok`.
- [ ] T025 [P] [US3] Author
  `TestVpnIkeHealthJsonl::test_run_full_validation_appends_once_per_host`
  in `tests/unit/utils/test_zscaler_probe.py` (integration, SC-005):
  monkeypatch the network primitives, invoke `run_full_validation()`
  with a fixture list of N VPN hosts pointing the JSONL path at
  `tmp_path`, assert exactly N lines are appended.

### Implementation for User Story 3

- [ ] T026 [US3] Add private helper `_append_ike_health_record` to
  `src/utils/zscaler_probe.py` per `contracts/vpn_ike_health_jsonl.md`
  §Write-Side Contract. Signature:
  `_append_ike_health_record(hostname: str, icmp_ok: bool, ike_500_ok: bool, ike_4500_ok: bool, *, path: pathlib.Path = pathlib.Path("data") / "vpn_ike_health.jsonl") -> None`.
  Build record as ordered `dict` with keys `ts`, `hostname`, `icmp_ok`,
  `ike_500_ok`, `ike_4500_ok`. Timestamp:
  `datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")`. Serialize:
  `json.dumps(record, separators=(",", ":"))`. Write:
  `path.open("a", encoding="utf-8", newline="")` + `\n`. Wrap in
  `try/except OSError as exc: logger.warning("vpn_ike_health.jsonl append failed for %s: %s", hostname, exc); return`.
  Docstring MUST include Google-style Args/Returns and a "Why" section
  citing FR-009, FR-010, and the append-only invariant. Verify T019-T024
  now pass.
- [ ] T027 [US3] Wire the append call into
  `src/utils/zscaler_probe.py::run_full_validation()` at line ~646.
  After both `_udp_check(host, 500, ...)` and `_udp_check(host, 4500, ...)`
  return for a given VPN host, before moving to the next host, call
  `_append_ike_health_record(hostname=host, icmp_ok=..., ike_500_ok=bool(udp_500_result), ike_4500_ok=bool(udp_4500_result))`.
  Truthiness rule per contract §Field-by-field: `_udp_check` returns
  a truthy string on IKE success, empty/falsy on failure. Do not
  otherwise alter `run_full_validation()` behavior (FR-011 scope
  limit; Decision 6). Verify T025 now passes.
- [ ] T028 [US3] Add module-level `from datetime import UTC, datetime`,
  `import json`, `import pathlib` imports to
  `src/utils/zscaler_probe.py` if not already present. `logging`,
  `socket`, `struct` should already be imported. Keep stdlib-only per
  FR-011.

**Checkpoint**: US3 green. `data/vpn_ike_health.jsonl` accumulates one
line per VPN host per `run_full_validation()` cycle. Failure to write
is logged at WARNING and does not destabilize the CENR refresh.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Gate checks and manual smoke to catch anything the unit
tests missed. Non-blocking for MVP (US1+US2), but MUST run before merge.

- [ ] T029 [P] Run `ruff check src/ tests/`. Fix any lint findings
  introduced by T010, T011, T026, T027. Do not silence rules; fix the
  underlying code.
- [ ] T030 [P] Run `black --check src/ tests/`. If it fails, run
  `black src/ tests/` and commit the formatting fix in a separate
  commit so the code-change diff stays reviewable.
- [ ] T031 [P] Run `mypy src/`. Address any type findings in the
  modified functions in `src/org/org_synthetic_probes_manager.py` and
  `src/utils/zscaler_probe.py`. No new `# type: ignore` unless
  justified by a comment.
- [ ] T032 [P] Run `interrogate -c pyproject.toml src/` and confirm
  docstring coverage remains >=90% (per Principle I). New functions
  from T010, T011, T026 MUST have Google-style docstrings with a "Why"
  section.
- [ ] T033 [P] Run `pydoclint --style=google src/`. Fix any doc-style
  regressions in the docstrings authored in T010, T011, T026.
- [ ] T034 Run the full pytest sweep: `cd tests && pytest unit/ -v`.
  All tests must pass including feature 1023 tests (which are
  unchanged) and the new US1/US2/US3 tests.
- [ ] T035 Execute quickstart Scenario I as a manual smoke:
  `python MistHelper.py --menu 206 --fixture tests/unit/org/fixtures/smoke_org.json --dry-run`
  (or the equivalent dry-run invocation used by the repo). Confirm the
  printed `custom_probes` list has (a) at least one
  `type: reachability` row with a bare-hostname target for every VPN
  host in the fixture and (b) no row targets any VPN host with `:500`,
  `:4500`, `http://`, or `https://<vpn-host>`.
- [ ] T036 Confirm no menu-entry change was introduced (this feature
  edits `_probe_target` / `_probe_type_for_target` internals only). No
  update to `src/utils/operation_registry.py` is required. Record in
  the PR description that OperationRegistry is unchanged.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. Start immediately.
- **Foundational (Phase 2)**: None; skip.
- **US1 (Phase 3)**: Depends on Phase 1 (fixtures dir exists).
- **US2 (Phase 4)**: Depends on Phase 3 (US1 implementation exists so
  its non-VPN paths can be diffed against the baseline). Fixture
  authoring tasks (T013, T014) can start in parallel with US1
  implementation.
- **US3 (Phase 5)**: Independent of US2. Can be scheduled in parallel
  with US2, or deferred entirely without breaking US1/US2. Edits a
  different module (`src/utils/zscaler_probe.py`) and a different test
  file (`tests/unit/utils/test_zscaler_probe.py`).
- **Polish (Phase 6)**: Depends on all included user stories being
  code-complete.

### User Story Dependencies

- **US1 (P1)**: No dependencies on other stories.
- **US2 (P1)**: Depends on US1 implementation for the diff to be
  meaningful. Fixture authoring is independent.
- **US3 (P3, optional)**: No dependencies on US1 or US2. Safe to skip.

### Within Each User Story

- Tests MUST be authored and MUST FAIL before implementation (Principle IV).
- `_probe_type_for_target` (T010) can be tightened before `_probe_target`
  (T011) because the dispatcher does not read the VPN return shape.
- The three-callsite audit (T012) runs after T010 + T011.
- The JSONL helper (T026) must exist before wiring it into
  `run_full_validation` (T027).

### Parallel Opportunities

- All Phase 1 tasks (T001, T002) run in parallel.
- All US1 tests (T003-T008) run in parallel — different test classes /
  different test methods, one file (pytest handles file-level test
  parallelism cleanly).
- US1 implementation (T010, T011) is two edits in one file; run
  sequentially to avoid merge friction.
- All US2 fixture-authoring tasks (T013, T014) and test tasks (T015,
  T016, T017) run in parallel.
- All US3 tests (T019-T025) run in parallel.
- All Polish gate checks (T029-T033) run in parallel; T034-T036 run
  sequentially.
- US2 fixture authoring (T013, T014) can start in parallel with US1
  implementation once the shape decisions in `_probe_target` are
  locked (i.e. after T011 begins).

---

## Parallel Example: User Story 1 Tests

```bash
# Author all US1 tests in parallel (all in the same file — use
# separate PRs/branches or scoped test classes to avoid text-level
# merge conflicts; pytest itself does not care):
pytest tests/unit/org/test_org_synthetic_probes_manager.py::TestProbeTypeDispatch -v
pytest tests/unit/org/test_org_synthetic_probes_manager.py::TestProbeTargetVpn::test_cenr_bag_vpn_emits_bare_hostname -v
pytest tests/unit/org/test_org_synthetic_probes_manager.py::TestProbeTargetVpn::test_udp_observed_emits_bare_hostname -v
pytest tests/unit/org/test_org_synthetic_probes_manager.py::TestProbeTargetVpn::test_vpn_pattern_only_emits_bare_hostname -v
```

## Parallel Example: User Story 3 Tests

```bash
pytest tests/unit/utils/test_zscaler_probe.py::TestVpnIkeHealthJsonl -v
```

---

## Implementation Strategy

### MVP First (US1 + US2 — both P1)

1. Complete Phase 1 (setup).
2. Complete Phase 3 (US1) — VPN reachability shape.
3. Complete Phase 4 (US2) — non-VPN byte-stability guard.
4. STOP and VALIDATE with Scenario I (T035).
5. Ship. This is the MVP.

### Optional Extension (US3)

6. Complete Phase 5 (US3) — JSONL IKE health telemetry.
7. Run Phase 6 (Polish) gates.
8. Ship, or defer US3 to a follow-up feature if scope pressure arises.

### Parallel Team Strategy

- Dev A: US1 tests + implementation (T003-T012).
- Dev B: US2 fixture authoring + tests + diff-guard (T013-T018),
  waiting for Dev A's T011 to unblock T018.
- Dev C (optional): US3 in parallel — different module, different test
  file, zero merge conflict with Dev A or B.

---

## Notes

- Every task carries an explicit file path.
- `[P]` marks tasks in different files (or non-overlapping regions of
  the same file) with no dependency on incomplete work.
- Tests-first per Principle IV: T003-T009 authored before T010-T012;
  T013-T017 before T018; T019-T025 before T026-T028.
- Failure to preserve INV-1 (US2 diff empty) is a hard stop. Do not
  edit the baseline to make the diff pass.
- Standard-library only (FR-011). If a task is tempted to add a
  dependency, halt and re-check.
- Every merge point is a natural commit boundary — commit after each
  task or logical group.
- The 8 dispatch cases in T003 are the authoritative source of truth
  for `_probe_type_for_target`; if a case moves, update the contract
  first, then the test, then the code.
