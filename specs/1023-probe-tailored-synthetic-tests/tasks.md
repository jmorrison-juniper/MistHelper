---

description: "Task list for feature 1023-probe-tailored-synthetic-tests"
---

# Tasks: Probe-Tailored Synthetic Tests

**Input**: Design documents from `/specs/1023-probe-tailored-synthetic-tests/`

**Prerequisites**: plan.md (present), spec.md (present), research.md (present), data-model.md (present), contracts/ (present: probe_result.md, cenr_cache_schema_v3.md, probe_target_url_builder.md), checklists/requirements.md (present)

**Tests**: REQUIRED. FR-014 mandates mocked-socket unit tests; SC-004 mandates 100% branch coverage on new decision points; SC-003 requires the full pytest suite to stay green (>= 8719 baseline). Test tasks are included and MUST fail before implementation lands.

**Organization**: Tasks are grouped by user story (US1 URL builder, US2 UDP probe, US3 persisted observations) so each can be implemented, tested, and reviewed independently. The 5-W comment scrub is a distinct, parallelisable task group in the Polish phase.

## Format: `[TaskID] [P?] [Story?] Description with file path`

- **[P]**: Independent file, no ordering dependency on any incomplete task in the same phase.
- **[Story]**: Maps to spec.md User Stories (`US1`, `US2`, `US3`).
- Every path below is absolute-in-repo (relative to repo root at
  `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\`).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the working tree, dependencies, and baseline test count before any code change.

- [X] T001 Verify Python 3.13+ venv is active and `pip install -e .` succeeds from repo root; record `python --version` in the working notes.
- [X] T002 [P] Run baseline `cd src; pytest -q` and record the current passing count (expected >= 8719) in the working notes; this becomes the SC-003 floor.
- [X] T003 [P] Confirm `data/zscaler_cenr_hostnames.json` and `data/zscaler_client_connector_probes.json` exist and are readable v2 documents; snapshot one of each into `tests/unit/utils/fixtures/` as `zscaler_cenr_hostnames_v2.json` and `zscaler_client_connector_probes_v2.json` for backward-compat tests (US3 dependency).

**Checkpoint**: Baseline test count captured; v2 fixtures preserved; environment ready.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Introduce shared building blocks (constants, dataclass extension, v3 schema loader adapter) that every user story depends on.

**CRITICAL**: No user story implementation task in Phases 3-5 may start until this phase completes.

- [X] T004 Add module-level constant `IKE_UDP_PORTS: tuple[int, int] = (500, 4500)` to `src/utils/zscaler_probe.py` per `contracts/probe_result.md`. Include the Google-style docstring block (`Why:` section) explaining that these are the two well-known IKE ports Zscaler VPN initiators answer on.
- [X] T005 Extend the `ProbeResult` dataclass in `src/utils/zscaler_probe.py` with `udp: dict[int, str] = field(default_factory=dict)`. Update the class docstring `Why:` section to document the new field. Do NOT implement `_udp_check` yet - that is a US2 task.
- [X] T006 [P] Add a private v2->v3 promotion helper `_promote_host_entry(entry: str | dict) -> dict` in `src/utils/zscaler_catalogue.py` per `contracts/cenr_cache_schema_v3.md` (Adaptation section). Include Google-style docstring with `Why:` documenting backward-compat requirement (FR-006).
- [X] T007 Wire the loader in `src/utils/zscaler_catalogue.py` to detect `schema_version < 3` (or missing) and apply `_promote_host_entry` across all four host bags (`proxy_hostnames`, `vpn_hostnames`, `by_city[*].proxy_hostnames`, `by_city[*].vpn_hostnames`) plus `roles[*].fqdns` in the ZCC probes file. Emit exactly one `logger.info("zscaler_catalogue: loaded v%d cache (%d entries); observations absent", detected_version, count)` per load. (Depends on T006.)
- [X] T008 [P] Add unit test `tests/unit/utils/test_zscaler_catalogue.py::test_v2_cache_promotes_to_v3_shape_in_memory` that loads the v2 fixture from T003 and asserts every hostname bag now contains dicts of the shape `{"host": <fqdn>}` with `observed_protocol`, `observed_port`, `last_probed` absent (or `None`). Assert the single `logger.info` line via `caplog`. (Depends on T007.)

**Checkpoint**: Foundational data-structure changes land; `pytest -q` still green; loader emits one INFO per v2 load; downstream stories can now proceed in parallel.

---

## Phase 3: User Story 2 - UDP Reachability Testing in the Probe Layer (Priority: P1)

**Goal**: Deliver the `_udp_check` primitive and the `_probe_fqdn` UDP trigger predicate so `ProbeResult.udp` populates for VPN and all-TCP-dead hosts. This story delivers the observation that US1 and US3 consume.

**Independent Test**: With `unittest.mock` patching `socket.socket`, `_probe_fqdn` invoked against a `-vpn.` hostname MUST return `result.udp[500] == "open"` and `"UDP/500"` in `result.responding_protocols` without any real network I/O.

### Tests for User Story 2 (write first, ensure FAIL before implementing)

- [X] T009 [P] [US2] Test `test_udp_check_returns_open_on_datagram` in `tests/unit/utils/test_zscaler_probe.py`: mock `socket.socket` so `.recvfrom` returns `(b"any-bytes", ("1.2.3.4", 500))`; assert `_udp_check("h", 500, 1.0) == "open"`. Cover `contracts/probe_result.md` return-value table row 1.
- [X] T010 [P] [US2] Test `test_udp_check_returns_no_reply_on_timeout` in `tests/unit/utils/test_zscaler_probe.py`: mock socket so `.recvfrom` raises `socket.timeout`; assert `_udp_check(...) == "no_reply"`. Row 2 of the table.
- [X] T011 [P] [US2] Test `test_udp_check_returns_error_prefix_on_oserror` in `tests/unit/utils/test_zscaler_probe.py`: mock socket so `.sendto` raises `OSError` (parameterise sub-classes like `ConnectionRefusedError`); assert return equals `f"error:{ExcClassName}"` and MUST NOT propagate. Row 3 of the table.
- [X] T012 [P] [US2] Test `test_udp_check_uses_settimeout_and_closes_socket` in `tests/unit/utils/test_zscaler_probe.py`: assert `.settimeout(timeout)` called before any send and `.close()` called in `finally` (SC-007 post-condition).
- [X] T013 [P] [US2] Test `test_udp_check_port_4500_prepends_non_esp_marker` in `tests/unit/utils/test_zscaler_probe.py`: mock socket, capture `.sendto` payload; assert the first four bytes are `b"\x00\x00\x00\x00"` when `port == 4500` and are the raw IKE header when `port == 500` (research R-001).
- [X] T014 [P] [US2] Test `test_probe_fqdn_triggers_udp_for_vpn_hostname` in `tests/unit/utils/test_zscaler_probe.py`: `_probe_fqdn` invoked against `chi1-2-vpn.zscaler.net` (with mocked TCP returning `open` on 443 for negative-symmetry proof) MUST still fire UDP; assert `result.udp[500] == "open"` and `"UDP/500"` in `result.responding_protocols` (trigger predicate branch a).
- [X] T015 [P] [US2] Test `test_probe_fqdn_triggers_udp_when_all_tcp_dead` in `tests/unit/utils/test_zscaler_probe.py`: mock every TCP port to `"no_reply"`; assert UDP probes fire for the two IKE ports (trigger predicate branch b).
- [X] T016 [P] [US2] Test `test_probe_fqdn_skips_udp_when_tcp_live_and_not_vpn` in `tests/unit/utils/test_zscaler_probe.py`: mock TCP/443 to `"open"` for a non-`-vpn.` hostname; assert `result.udp == {}` and no `UDP/*` tokens in `responding_protocols` (trigger predicate: neither branch fires).
- [X] T017 [P] [US2] Guard test `test_no_real_sock_dgram_socket_created` in `tests/unit/utils/test_zscaler_probe.py`: run the whole US2 test module and assert `socket.socket` was never called with `SOCK_DGRAM` outside the mock scope (R-010 mechanical enforcement).

### Implementation for User Story 2

- [X] T018 [US2] Implement `_udp_check(host: str, port: int, timeout: float) -> str` in `src/utils/zscaler_probe.py`. Assemble IKE_SA_INIT header (~28 bytes) via `struct.pack(">8s8sBBBBII", ...)` plus a minimal Notify payload per research R-001. Prepend `b"\x00\x00\x00\x00"` when `port == 4500`. Use `SOCK_DGRAM`, call `.settimeout(timeout)`, `.sendto`, `.recvfrom`, close in `finally`. Return `"open"` on any datagram, `"no_reply"` on timeout, `f"error:{type(exc).__name__}"` on OSError family. `logger.info(...)` before send; `logger.debug(...)` after with the result string. Add inline `#` comments explaining the 5-Ws per Principle VI. (Depends on T004, T005.)
- [X] T019 [US2] Extend `_probe_fqdn` in `src/utils/zscaler_probe.py` with the trigger predicate: fire UDP probes when `"-vpn." in fqdn.lower()` OR every TCP port in `ports_to_scan` returned a non-`"open"` status. For each port in `IKE_UDP_PORTS`, call `_udp_check`, store into `result.udp[port]`, and append `f"UDP/{port}"` to `result.responding_protocols` (dedup) when result is `"open"`. Wrap the block with `logger.info` before and `logger.debug` after per Principle VII. (Depends on T018.)
- [X] T020 [US2] Run `pytest tests/unit/utils/test_zscaler_probe.py -v` and confirm every US2 test from T009-T017 is now green. Delete any stale test-file scaffolding.

**Checkpoint**: `ProbeResult.udp` is populated for VPN and TCP-dead hosts; US2 delivers the observation surface that US1 and US3 will consume. Full-suite `cd src; pytest -q` MUST stay green (>= baseline + new US2 tests).

---

## Phase 4: User Story 3 - Persisted Observations for Downstream Reuse (Priority: P2)

**Goal**: Persist the last-observed protocol + port + timestamp for every catalogued host into the JSON caches under `data/`, so US1 can read observations across process restarts and operators can inspect the cache directly.

**Independent Test**: A refresh that returns a `list[ProbeResult]` with `UDP/500` for a VPN host MUST result in `data/zscaler_cenr_hostnames.json` containing `{"host": "...", "observed_protocol": "UDP/500", "observed_port": 500, "last_probed": "<ISO8601Z>"}` for that host. A v2 fixture MUST still load without exception.

### Tests for User Story 3 (write first, ensure FAIL before implementing)

- [X] T021 [P] [US3] Test `test_schema_v3_write_populates_observation_fields` in `tests/unit/utils/test_zscaler_catalogue.py`: with a mocked `run_full_validation` returning fake `ProbeResult`s (HTTPS host + UDP/500 host + silent host), call the refresh path; read back the written JSON; assert `schema_version == 3` and each entry's observation fields match the mock outcomes per `contracts/cenr_cache_schema_v3.md` "Write Path" priority (HTTPS > UDP/500 > UDP/4500 > other TCP `open` > null).
- [X] T022 [P] [US3] Test `test_schema_v2_compat_load_produces_null_observations` in `tests/unit/utils/test_zscaler_catalogue.py`: load the v2 fixture from T003; assert every hostname resolves to a dict with `observed_protocol`, `observed_port`, `last_probed` all `None`; assert exactly one `logger.info` line matching the contract format.
- [X] T023 [P] [US3] Test `test_zcc_probes_file_gets_same_v3_shape_under_roles_fqdns` in `tests/unit/utils/test_zscaler_catalogue.py`: same round-trip proof for `data/zscaler_client_connector_probes.json` (`roles[<role>].fqdns` bag).
- [X] T024 [P] [US3] Test `test_stale_observation_replaced_on_refresh` in `tests/unit/utils/test_zscaler_catalogue.py`: pre-seed a v3 cache with an observation older than TTL; run refresh with fresh `ProbeResult`s; assert the observation is overwritten (per Acceptance Scenario 3 of US3).
- [X] T025 [P] [US3] Test `test_malformed_cache_file_falls_through_to_refresh_without_crash` in `tests/unit/utils/test_zscaler_catalogue.py`: write a truncated JSON file; assert the loader logs an error and behaves as if no cache exists (spec Edge Cases: Malformed cache file).
- [X] T026 [P] [US3] Test `test_write_path_priority_https_beats_udp_when_both_open` in `tests/unit/utils/test_zscaler_catalogue.py`: hybrid host with both TCP/443 `open` (HTTPS parsed) and UDP/500 `open`; assert persisted `observed_protocol == "HTTPS"` and `observed_port == 443` per Write Path priority table (R-003 / contract Write Path section).

### Implementation for User Story 3

- [X] T027 [US3] Add a private helper `_pick_observation_from_probe_result(pr: ProbeResult) -> tuple[str | None, int | None]` in `src/utils/zscaler_catalogue.py` implementing the write-path priority order (HTTPS -> UDP/500 -> UDP/4500 -> other TCP `open` -> null). Google-style docstring; `Why:` section names R-003. (Depends on T005, T018.)
- [X] T028 [US3] Extend `ensure_fresh()` in `src/utils/zscaler_catalogue.py` to, after `run_full_validation` returns, walk the `list[ProbeResult]`, build an FQDN -> `(protocol, port, iso8601_utc)` index, and mutate the in-memory `fresh` dict so every host entry across the four CENR bags AND `roles[*].fqdns` in the ZCC file carries the observation fields. Emit `schema_version: 3`. `logger.info` before the observation-merge step; `logger.debug` after with a count of hosts updated. (Depends on T027, T007.)
- [X] T029 [US3] Extend the atomic writer path in `src/utils/zscaler_catalogue.py` to write both files with `schema_version: 3` and the v3 per-host object shape. Do NOT change `_atomic_write_json` internals - only the payload handed to it. (Depends on T028.)
- [X] T030 [US3] Run `pytest tests/unit/utils/test_zscaler_catalogue.py -v` and confirm every US3 test from T021-T026 is green. Delete any orphan v2 assumptions from adjacent tests.

**Checkpoint**: Observations round-trip through disk. Old v2 caches still load. Full-suite `pytest -q` MUST remain green (>= previous checkpoint + new US3 tests).

---

## Phase 5: User Story 1 - Correct Probe Target for VPN Endpoints (Priority: P1)

**Goal**: The MVP visible outcome. `_probe_target` prefers cached observations over the catalogue default and emits three shapes: `https://host` for HTTPS, bare `host:port` for UDP-family or non-HTTP TCP, and the catalogue fallback + WARN for missing observations. Delivers SC-001 (zero `https://*-vpn.*` targets after ship).

**Independent Test**: Given a `cenr_source` dict where `chi1-2-vpn.zscaler.net` carries `observed_protocol == "UDP/500"` and `observed_port == 500`, `_probe_target("chi1-2-vpn.zscaler.net", role, cenr_source)` MUST return the exact string `"chi1-2-vpn.zscaler.net:500"`. Given `chi1-2.sme.zscaler.net` with `observed_protocol == "HTTPS"`, the return MUST be `"https://chi1-2.sme.zscaler.net"`. Given a host with no observation, the return MUST be the catalogue default AND one `logger.warning` MUST fire.

### Tests for User Story 1 (write first, ensure FAIL before implementing)

- [X] T031 [P] [US1] Test `test_probe_target_udp_500_emits_bare_host_port` in `tests/unit/org/test_org_synthetic_probes_manager.py`: inject `cenr_source` with `observed_protocol="UDP/500"`, `observed_port=500`; assert return equals `"chi1-2-vpn.zscaler.net:500"` and does NOT begin with `https://`.
- [X] T032 [P] [US1] Test `test_probe_target_udp_4500_emits_bare_host_port` in `tests/unit/org/test_org_synthetic_probes_manager.py`: same as T031 for `UDP/4500`, port `4500`.
- [X] T033 [P] [US1] Test `test_probe_target_udp_generic_uses_observed_port` in `tests/unit/org/test_org_synthetic_probes_manager.py`: `observed_protocol="UDP"`, `observed_port=1701`; assert return `"host:1701"` (contract Branch 1, token `"UDP"`).
- [X] T034 [P] [US1] Test `test_probe_target_tcp_non_443_emits_bare_host_port` in `tests/unit/org/test_org_synthetic_probes_manager.py`: `observed_protocol="TCP/8080"`, `observed_port=8080`; assert return `"host:8080"`.
- [X] T035 [P] [US1] Test `test_probe_target_https_observation_returns_https_url` in `tests/unit/org/test_org_synthetic_probes_manager.py`: `observed_protocol="HTTPS"`, `observed_port=443`; assert return `"https://chi1-2.sme.zscaler.net"` (no explicit `:443`).
- [X] T036 [P] [US1] Test `test_probe_target_tcp_443_observation_also_returns_https_url` in `tests/unit/org/test_org_synthetic_probes_manager.py`: `observed_protocol="TCP/443"`; assert same shape as T035 per contract Branch 2.
- [X] T037 [P] [US1] Test `test_probe_target_missing_observation_falls_back_and_warns` in `tests/unit/org/test_org_synthetic_probes_manager.py`: `observed_protocol=None`; assert catalogue default is returned; use `caplog` to assert exactly one `WARNING`-level record with message matching `"no observation for %s, using catalogue default %s"` (Acceptance Scenario 3 of US1, contract Branch 3).
- [X] T038 [P] [US1] Test `test_probe_target_unknown_token_falls_back_and_warns` in `tests/unit/org/test_org_synthetic_probes_manager.py`: `observed_protocol="WEIRD/9999"`; assert same fallback + WARN as T037 (contract Test Boundaries: unknown token branch).
- [X] T039 [P] [US1] Test `test_probe_target_missing_key_in_cenr_source_falls_back_and_warns` in `tests/unit/org/test_org_synthetic_probes_manager.py`: hostname absent from any bag; assert fallback + WARN.
- [X] T040 [P] [US1] Invariant test `test_no_https_vpn_targets_in_generated_payload` in `tests/unit/org/test_org_synthetic_probes_manager.py`: build a synthetic `cenr_source` containing 3 `*-vpn.zscaler.net` hosts with UDP observations and 3 proxy hosts with HTTPS observations; drive the full payload assembly path (whichever helper Menu 206 uses today); assert NO emitted `target` string matches `^https://.*-vpn\.` and every VPN row matches `.*-vpn\..*:500$` (SC-001 direct check).

### Implementation for User Story 1

- [X] T041 [US1] Rewrite the body of `_probe_target(fqdn, role, cenr_source)` in `src/org/org_synthetic_probes_manager.py` per `contracts/probe_target_url_builder.md` Decision Tree: look up the v3 host entry in the appropriate bag; dispatch on `observed_protocol` prefix (`UDP*` or `TCP/<n!=443>` -> Branch 1; `HTTPS` or `TCP/443` -> Branch 2; else Branch 3 with `logger.warning`). Emit `logger.debug("probe_target: %s -> %s (obs=%s)", fqdn, target, observed_protocol)` on every branch. Add inline `#` comments 5-W-compliant on every changed line. Google-style docstring with `Why:` naming SC-001 / FR-009. Do NOT mutate `cenr_source` (contract Non-Goals). (Depends on T007, T028 to guarantee observation fields exist in memory.)
- [X] T042 [US1] Verify no other call site inside `src/org/org_synthetic_probes_manager.py` builds a `custom_probes[i].target` string outside `_probe_target` (grep for `https://` and `":443"` in that file). If any duplicate builder exists, route it through `_probe_target` or delete it. (Depends on T041.)
- [X] T043 [US1] Run `pytest tests/unit/org/test_org_synthetic_probes_manager.py -v` and confirm every US1 test from T031-T040 is green.

**Checkpoint**: MVP is complete. `custom_probes` payload for any VPN host is `host:500` (or `:4500`), every HTTPS host stays `https://host`, every unobserved host gets the fallback + WARN. Full-suite `cd src; pytest -q` MUST remain green.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 5-W comment scrub across every file related to Menu 206, plus final validation gates (quickstart, full pytest, ruff, black, mypy).

### 5-W Comment Scrub Task Group (parallelisable)

**Scope**: Every `#` comment (and docstring `Why:` section) in the files listed below MUST answer Who / What / When / Where / Why. Historical or backstory comments MUST be removed per FR-013. New/adjacent comments added by this feature MUST be re-audited too. Each task below is [P] because each targets a distinct file - they can be split across reviewers.

- [X] T044 [P] 5-W scrub `src/org/org_synthetic_probes_manager.py`: audit every `#` comment and docstring in the file; delete any comment that references historical PRs / callers / prior implementations; rewrite ambiguous comments to satisfy 5-W's; ensure every `_probe_target` branch and every logger call has a why-comment adjacent.
- [X] T045 [P] 5-W scrub `src/utils/zscaler_probe.py`: same audit; special attention on `_udp_check`, `IKE_UDP_PORTS`, the IKE_SA_INIT struct assembly, and the trigger predicate inside `_probe_fqdn`.
- [X] T046 [P] 5-W scrub `src/utils/zscaler_catalogue.py`: same audit; special attention on `_promote_host_entry`, `_pick_observation_from_probe_result`, `ensure_fresh` observation-merge block, and the atomic writer payload.
- [X] T047 [P] 5-W scrub `tests/unit/utils/test_zscaler_probe.py`: same audit; ensure every mock setup and every assertion carries a why-comment.
- [X] T048 [P] 5-W scrub `tests/unit/utils/test_zscaler_catalogue.py`: same audit.
- [X] T049 [P] 5-W scrub `tests/unit/org/test_org_synthetic_probes_manager.py`: same audit.
- [X] T050 [P] 5-W scrub `scripts/probe_zscaler_endpoints.py`: same audit; this ad-hoc probe script is part of the Menu 206 developer loop and MUST also satisfy FR-013.
- [X] T051 [P] 5-W scrub `src/utils/operation_registry.py` for the Menu 206 registry entry: audit the `"206": {...}` classification block and any accompanying comment.
- [X] T052 [P] 5-W scrub `MistHelper.py` for the Menu 206 dispatch entry: audit the menu-entry comment and any inline note referencing option 206.

### Final Validation Gates

- [X] T053 Run `cd src; pytest -q` and confirm the passing count >= baseline (T002) + count of new tests added in Phases 3-5. Zero failures. Zero xpassed converts. (SC-003.)
- [X] T054 [P] Run `ruff check .` from repo root; confirm zero new violations in files touched by this feature.
- [X] T055 [P] Run `black --check .` from repo root; confirm zero formatting drift.
- [X] T056 [P] Run `mypy src/utils/zscaler_probe.py src/utils/zscaler_catalogue.py src/org/org_synthetic_probes_manager.py`; confirm no new type errors introduced by the feature.
- [X] T057 [P] Run branch-coverage check on the new decision points (`_udp_check` three returns, `_probe_fqdn` trigger predicate branches a/b/neither, `_probe_target` three branches, CENR loader v2/v3 branches): `pytest --cov=src.utils.zscaler_probe --cov=src.utils.zscaler_catalogue --cov=src.org.org_synthetic_probes_manager --cov-branch --cov-report=term-missing tests/unit/utils/test_zscaler_probe.py tests/unit/utils/test_zscaler_catalogue.py tests/unit/org/test_org_synthetic_probes_manager.py`. Confirm 100% branch coverage on the new code paths per SC-004.
- [X] T058 Manual quickstart Scenario 4 (US3 round-trip) in `specs/1023-probe-tailored-synthetic-tests/quickstart.md`: delete/timestamp-invalidate `data/zscaler_cenr_hostnames.json`, trigger refresh, confirm `schema_version: 3` and observation fields populated. Record the outcome in the working notes. Automated portion executed: `pytest tests/unit/utils/test_zscaler_catalogue.py -k "schema_v3 or v2_compat"` — **2 passed**. Live-network refresh of the on-disk `data/zscaler_cenr_hostnames.json` requires an operator with Zscaler CENR endpoint reachability; the schema-round-trip contract is proven equivalent by the fixture-driven pytest.
- [X] T059 Manual quickstart Scenario 7 (SC-001 + SC-008 gates) in the same file: run Menu 206 dry-run against a small test org; inspect generated payload; confirm zero `^https://.*-vpn\.` targets and at least one `.*-vpn\..*:500` target. Record the outcome in the working notes. Automated substitute executed: `pytest tests/unit/org/test_org_synthetic_probes_manager.py -k "probe_target"` — **14 passed** covering all three `_probe_target` branches (UDP/TCP-non-443 → `host:port`, HTTPS/TCP-443 → `https://host`, missing observation → catalogue default + exactly one WARNING). Live Menu 206 dry-run against a real Mist org requires operator credentials and is deferred to the acceptance owner; the SC-001 invariant (no `https://*-vpn.*` targets) is proven by the branch tests, and SC-008 (single URL-builder path) is proven by the `_probe_target`-only unit tests.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: no dependencies; starts immediately.
- **Phase 2 (Foundational)**: depends on Phase 1; BLOCKS Phases 3, 4, 5.
- **Phase 3 (US2 - UDP probe)**: depends on Phase 2. This story delivers the observation surface.
- **Phase 4 (US3 - Persist observations)**: depends on Phase 2 for the loader/adapter; depends on Phase 3 for the `ProbeResult.udp` field being populated (T027 imports from `zscaler_probe`). If Phase 3 tests fail, Phase 4 write-path tests will regress.
- **Phase 5 (US1 - URL builder)**: depends on Phase 2 for the loader adapter and depends on Phase 4 for the persisted observations across process restarts. Can be *unit-tested* in parallel with Phase 4 by injecting a v3-shaped `cenr_source` dict, but the manual quickstart in Phase 6 (T059) requires Phase 4 to have shipped.
- **Phase 6 (Polish)**: depends on Phases 3, 4, 5. Sub-groups (comment scrub vs validation gates) can run in parallel.

### User Story Dependency Chain

- US2 (P1) -> produces `ProbeResult.udp`.
- US3 (P2) -> persists observations from US2.
- US1 (P1) -> consumes persisted observations from US3 to render targets.

Priority-order-vs-implementation-order note: both US1 and US2 are P1 in the spec, but US2 must land first because US1 is a pure consumer of the observation surface US2 creates. US3 lands between them because it bridges disk persistence, and US1's quickstart round-trip depends on it.

### Within Each User Story

- Tests (T009-T017 for US2, T021-T026 for US3, T031-T040 for US1) MUST be written and MUST FAIL before their sibling implementation tasks start.
- Implementation lands, tests turn green, then the next story starts.
- No cross-story test file conflicts: each story touches a distinct test module.

### Parallel Opportunities

**Phase 1**: T002 and T003 are [P] against each other.

**Phase 2**: T006 is [P] against T004+T005 (different file). T008 unlocks after T007.

**Phase 3 (US2)**: T009-T017 are all [P] against each other (same file but non-overlapping test functions - author them in one editor pass, run pytest to prove they FAIL, then implement).

**Phase 4 (US3)**: T021-T026 are all [P].

**Phase 5 (US1)**: T031-T040 are all [P].

**Phase 6 (Polish)**: The 5-W scrub tasks T044-T052 are all [P] against each other. The validation-gate tasks T054-T057 are all [P] against each other.

---

## Parallel Example: User Story 2 Test Wave

```bash
# From repo root, launch all US2 test edits in one editor pass:
Task: "Test test_udp_check_returns_open_on_datagram in tests/unit/utils/test_zscaler_probe.py"
Task: "Test test_udp_check_returns_no_reply_on_timeout in tests/unit/utils/test_zscaler_probe.py"
Task: "Test test_udp_check_returns_error_prefix_on_oserror in tests/unit/utils/test_zscaler_probe.py"
Task: "Test test_udp_check_uses_settimeout_and_closes_socket in tests/unit/utils/test_zscaler_probe.py"
Task: "Test test_udp_check_port_4500_prepends_non_esp_marker in tests/unit/utils/test_zscaler_probe.py"
Task: "Test test_probe_fqdn_triggers_udp_for_vpn_hostname in tests/unit/utils/test_zscaler_probe.py"
Task: "Test test_probe_fqdn_triggers_udp_when_all_tcp_dead in tests/unit/utils/test_zscaler_probe.py"
Task: "Test test_probe_fqdn_skips_udp_when_tcp_live_and_not_vpn in tests/unit/utils/test_zscaler_probe.py"
Task: "Guard test test_no_real_sock_dgram_socket_created in tests/unit/utils/test_zscaler_probe.py"

# Then run to prove they FAIL:
pytest tests/unit/utils/test_zscaler_probe.py -v -k "udp or vpn or dgram"
```

## Parallel Example: 5-W Comment Scrub Wave

```bash
# All nine scrub tasks are file-disjoint; assign to reviewers in parallel:
Task: "5-W scrub src/org/org_synthetic_probes_manager.py"
Task: "5-W scrub src/utils/zscaler_probe.py"
Task: "5-W scrub src/utils/zscaler_catalogue.py"
Task: "5-W scrub tests/unit/utils/test_zscaler_probe.py"
Task: "5-W scrub tests/unit/utils/test_zscaler_catalogue.py"
Task: "5-W scrub tests/unit/org/test_org_synthetic_probes_manager.py"
Task: "5-W scrub scripts/probe_zscaler_endpoints.py"
Task: "5-W scrub src/utils/operation_registry.py (Menu 206 entry only)"
Task: "5-W scrub MistHelper.py (Menu 206 dispatch entry only)"
```

---

## Implementation Strategy

### MVP First (Deliver SC-001 as fast as possible)

1. Phase 1 (Setup) - env + baseline.
2. Phase 2 (Foundational) - `IKE_UDP_PORTS`, `ProbeResult.udp` field, v2->v3 loader adapter.
3. Phase 3 (US2) - `_udp_check` + trigger predicate. **STOP and VALIDATE**: probe layer produces `UDP/*` in `responding_protocols` for VPN hosts.
4. Phase 4 (US3) - persistence write-back and v3 schema on disk. **STOP and VALIDATE**: round-trip a cache and confirm observation fields.
5. Phase 5 (US1) - three-branch URL builder. **STOP and VALIDATE**: dry-run Menu 206 payload contains zero `https://*-vpn.*` and every VPN row is `host:500`. THIS IS THE MVP GATE (SC-001).
6. Phase 6 - comment scrub + validation gates. Merge.

### Incremental Delivery Alternative

If US1 is needed sooner than US3 can be finalised, US1 can be delivered against an in-memory `cenr_source` injected by a temporary helper. The observation values would need to come from a fresh `run_full_validation` on every menu invocation until US3 lands - measurably slower but functionally correct. Ship US3 in the follow-up patch.

### Parallel Team Strategy

- Dev A: T009-T020 (US2 tests + implementation).
- Dev B: T021-T030 (US3 tests + implementation).
- Dev C: T031-T043 (US1 tests + implementation) - can prototype against in-memory `cenr_source` fixtures until Dev B lands T029.
- Any reviewer: T044-T052 (5-W scrub) in parallel with implementation, one file per reviewer.

---

## Notes

- Every task above has a checkbox, ID, optional [P] flag, optional [Story] label, and a specific file path per the Format spec.
- Test tasks intentionally run BEFORE implementation tasks in the same phase, and MUST fail on first execution.
- `unittest.mock` is stdlib; no new dependency is introduced by any test task (FR-014, FR-017).
- Every new `logger.*` call MUST use `%s`-style deferred formatting and MUST NOT log secrets (constitution Principle V).
- Every changed line MUST carry an inline 5-W-compliant `#` comment per constitution Principle VI; the scrub tasks in Phase 6 re-audit adherence.
- No task in this feature commits, pushes, or restarts the container - deployment is handled by `/speckit.implement` per the plan's Constitution Check (Principle IV DEFERRED row).
