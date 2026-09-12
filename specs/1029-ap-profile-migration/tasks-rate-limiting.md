---
description: "Addendum task list for feature 1029-ap-profile-migration -- adaptive rate limiting on menus 207 and 208"
---

# Tasks: Adaptive Rate Limiting for AP Profile Migration (Addendum)

**Input**: Addendum design documents under `specs/1029-ap-profile-migration/`

**Prerequisites**:
`spec-addendum-rate-limiting.md`, `plan-rate-limiting.md`,
`research-rate-limiting.md`, `data-model-rate-limiting.md`,
`quickstart-rate-limiting.md`. Parent `tasks.md` is complete and merged
on branch `1029-ap-profile-migration`; do NOT edit the parent file.

**Tests**: Required. Pacing behavior is TDD-first. Every pacing test
patches `time.sleep` per FR-A07 so the suite runs hermetically.

**Organization**: Tasks are grouped by phase (Prep -> Tests -> Impl ->
Wiring -> Verification -> Polish). The two user stories map 1:1 to
menus 207 (`US1`) and 208 (`US2`). No new user story is added by the
addendum; every addendum requirement extends the parent's US1 and US2.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Different file or independent seam; safe to parallelize.
- **[Story]**: `US1` = menu 207 (migrate). `US2` = menu 208 (revert).
  Prep, Wiring, Verification, and Polish tasks with no story label are
  cross-cutting.

## Path Conventions

Single-project CLI layout. Source under `src/`, tests under `tests/`.
All paths are relative to the repository root
`c:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper`.
Branch discipline: stay on `1029-ap-profile-migration`. Do not touch
parent `specs/1029-ap-profile-migration/tasks.md`.

---

## Phase 1: Prep (lock the exact seams before any test or edit)

**Purpose**: Fix the exact import shape, patch site, and reference
lines so /speckit.implement cannot re-derive them at implementation time.

- [X] TR001 Read `src/api/api_data_fetcher.py` lines 100-175 and record verbatim in a scratch note: (a) the exact `_apply_rate_limiting` call shape, (b) how it acquires `mh` (`importlib.import_module("MistHelper")`), (c) the `_is_rate_limit_error` two-line status_code check. Source of truth for FR-A01, FR-A03, FR-A07.
- [X] TR002 Read `src/device/ap_profile_migration_manager.py` module header (lines 1-80) and record verbatim in a scratch note: (a) module-scope imports (already include `import time` at line 33 and `_RETRY_BACKOFF_SECONDS` at line 51), (b) the manager's lazy-import pattern for MistHelper (`import MistHelper as _mh` inside method bodies at lines 147, 265, 471, etc.). Confirm this differs from `api_data_fetcher.py`'s `importlib.import_module("MistHelper")`.
- [X] TR003 [P] Read `src/utils/rate_limiting.py` and confirm the public surface consumed by the addendum: `RateLimitingUtils.get_rate_limited_delay(smoothed, apisession, api_usage_cache) -> tuple[float | None, float]`, and the cache-invalidation contract used by `_needs_refresh` (setting `api_usage_cache["initialized"] = False` forces a refresh on the next call). Source of truth for FR-A03.
- [X] TR004 Read `src/device/ap_profile_migration_manager.py` at line 732 (`_reassign_one_ap`), line 777 (`_run_reassignment_loop`), line 358-410 (revert loop inside `revert_ap_profile_migration`), and line 1158 (`_revert_one_ap`). Record the exact signatures and the current `except Exception` sites. Source of truth for FR-A02, FR-A05, and Wiring tasks.
- [X] TR005 [P] Read `tests/unit/device/test_ap_profile_migration_manager.py` and record: (a) how existing tests patch `time.sleep` (the current pattern is `patch("time.sleep")` at the built-in-module level; the addendum pins `patch("src.device.ap_profile_migration_manager.time.sleep")` per Q4 of research), (b) the fake-mh fixture shape (`fake_mh.InputUtils.safe_input.return_value`, etc.) so new pacing tests can extend it with `fake_mh.RateLimitingUtils.get_rate_limited_delay` and `fake_mh._api_usage_cache`, (c) the existing progress-stride fixture and how the revert loop calls `_revert_one_ap`.

**Import decision locked** (recorded here so /speckit.implement does not re-open it):

- Inside the two new static helpers (`_apply_pacing`, `_signal_rate_limit_hit`) the manager MUST use `import MistHelper as _mh` (matching the manager's own lazy-import pattern at lines 147, 265, 471), NOT `importlib.import_module("MistHelper")`. Rationale: single lazy-import idiom per module keeps diffs small and matches the file's existing style. Both idioms resolve to the same `MistHelper` module object; the choice is stylistic + audit-friendly.
- Access globals as `_mh.apisession` and `_mh._api_usage_cache`. Do NOT pass them as helper arguments; they are process-wide singletons already used by every other API caller.
- 429 detection helper (`_is_429`) copies the two-line status_code pattern from `api_data_fetcher.py._is_rate_limit_error` verbatim into the manager (no cross-module import of a private helper, per research Q5).

**Checkpoint**: Prep is complete when TR001-TR005 have produced the scratch note. No production or test file has been edited yet.

---

## Phase 2: Tests First (TDD -- write failing tests before any impl)

**Purpose**: Lock the four addendum invariants (pre-PUT pacing call, 429 -> cache invalidation, hermetic patching, non-429 stop-on-failure preserved) with tests that FAIL against the current unpaced code and PASS once Phase 3 lands. All tests live in the existing
`tests/unit/device/test_ap_profile_migration_manager.py`.

Constitution Principle IV (TDD) requires these to be authored and reviewed BEFORE any implementation task in Phase 3 begins.

### Unit tests -- US1 (migrate loop, menu 207)

- [X] TR006 [P] [US1] Add `test_migrate_calls_get_rate_limited_delay_once_per_ap` in `tests/unit/device/test_ap_profile_migration_manager.py`. Patches `src.device.ap_profile_migration_manager.time.sleep` and patches `_mh.RateLimitingUtils.get_rate_limited_delay` to return `(None, 0.0)`. Asserts `get_rate_limited_delay.call_count == len(ap_records)` for a 20-AP fixture and asserts each call precedes the matching `_reassign_one_ap` call (use a `MagicMock` order-observer). Covers FR-A01, SC-A01 shape.
- [X] TR007 [P] [US1] Add `test_migrate_429_invalidates_api_usage_cache` in the same file. Patches `updateSiteDevice` to raise a `mistapi`-style exception whose `.response.status_code == 429` on the 3rd and 7th APs (of 10). Asserts `_mh._api_usage_cache["initialized"]` is toggled to `False` at least twice, and asserts the run completes without invoking the stop-on-failure branch (10 successful APs after retry recovery on 3 and 7). Covers FR-A03, FR-A04, SC-A02.
- [X] TR008 [P] [US1] Add `test_migrate_hermetic_no_wall_clock_sleep` in the same file. Records every call to the patched `time.sleep` mock and asserts the sum of arguments over a 100-AP run is > 0 (proves pacing was invoked) AND asserts `time.time()` wall-clock delta for the whole test is < 0.5 s. Covers FR-A07, SC-A01.
- [X] TR009 [P] [US1] Add `test_migrate_non_429_still_halts_stop_on_failure` in the same file. Patches `updateSiteDevice` to raise an HTTP-500-style exception on the 42nd AP. Asserts the loop halts before the 43rd PUT, that `backup["outcome"] == "partial"`, and that `_mh._api_usage_cache["initialized"]` was NOT toggled to `False` (500 is not routed through the throttle feedback path). Covers FR-A04, SC-A04.
- [X] TR010 [P] [US1] Add `test_migrate_limiter_exception_falls_back_and_continues` in the same file. Patches `_mh.RateLimitingUtils.get_rate_limited_delay` to raise `RuntimeError("PID corrupt")` on the 5th call, then succeed for every later call. Asserts: (a) exactly one WARNING is logged that names the fallback delay, (b) the 5th iteration's `time.sleep` argument equals `0.75` (== `_LIMITER_FALLBACK_DELAY`), (c) the run completes with all APs reassigned. Covers FR-A06, SC-A05.

### Unit tests -- US2 (revert loop, menu 208)

- [X] TR011 [P] [US2] Add `test_revert_calls_get_rate_limited_delay_once_per_ap` in the same file. Fixture is a 20-AP backup file. Same patch shape as TR006. Asserts `get_rate_limited_delay.call_count == 20` and asserts pacing precedes every `_revert_one_ap` call. Covers FR-A02.
- [X] TR012 [P] [US2] Add `test_revert_429_invalidates_api_usage_cache` in the same file. Configures the mocked `updateSiteDevice` to raise 429 on the 3rd and 7th APs (of 10) in the revert loop. Asserts `_mh._api_usage_cache["initialized"]` is toggled to `False` at least twice, revert completes with 10 reverts (not halted), and the JSONL audit line carries `pacing.http_429_seen == 2`. Covers FR-A02, FR-A03, SC-A03.
- [X] TR013 [P] [US2] Add `test_revert_hermetic_no_wall_clock_sleep` in the same file. Mirrors TR008 for the revert loop (100 APs; wall clock < 0.5 s; sum of `time.sleep` args > 0). Covers FR-A07 for US2.
- [X] TR014 [P] [US2] Add `test_revert_non_429_error_does_not_toggle_cache` in the same file. Configures 500 error on the 5th AP. Because the parent revert loop is tolerant (per parent FR-023), the run continues and counts the failure. Asserts `_mh._api_usage_cache["initialized"]` was NOT set to `False` for the 500, but was still set to `False` had a 429 occurred (parametrize with both cases in one test if convenient). Covers FR-A04 semantics on the revert side.

### Cross-cutting tests

- [X] TR015 [P] Add `test_dry_run_does_not_consult_rate_limiter` in the same file. Uses the existing dry-run seam (menu 207 with `"DRY-RUN"` at the confirmation prompt) and patches `_mh.RateLimitingUtils.get_rate_limited_delay`. Asserts `get_rate_limited_delay.call_count == 0`. Covers FR-A08.
- [X] TR016 [P] Add `test_summary_contains_pacing_lines` in the same file. Runs a 5-AP successful migration with two synthetic 429s (via the same 429-injection fixture as TR007) and captures stdout via `capsys`. Asserts the four lines from `data-model-rate-limiting.md` section 2 appear exactly once in the documented order: `Total PUTs issued : 7`, `HTTP 429 responses seen : 2`, `Non-429 failures : 0`, `Rate limiter delay (s) : mean=<f>  max=<f>`. Covers FR-A09, SC-A07.
- [X] TR017 [P] Add `test_jsonl_audit_line_carries_pacing_subdict` in the same file. Runs the same 5-AP + 2-429 fixture, captures the JSONL line via a patched `TelemetryEmitter`, decodes it, and asserts `payload["pacing"] == {"puts_issued": 7, "http_429_seen": 2, "non_429_failures": 0, "delay_seconds_mean": <float>, "delay_seconds_max": <float>}`. Covers FR-A09 for JSONL side.
- [X] TR018 [US1] Add `test_migrate_integration_real_limiter_seeded_cache` in the same file. Does NOT patch `_mh.RateLimitingUtils.get_rate_limited_delay`. Pre-seeds `_mh._api_usage_cache` with `{"initialized": True, "used": 4000, "limit": 5000, "last_updated": <time.time()>, ...}` so `_needs_refresh` returns `False`. Runs a 50-AP migration with a mocked `updateSiteDevice` that returns success. Asserts (a) `time.sleep` (patched at manager module scope) was called 50 times, (b) recorded delays are > 0 (proves real PID math ran against the seeded cache), (c) no exception raised. Covers integration wiring per research Q4.

**Checkpoint**: Phase 2 is complete when all 13 new tests exist, all import cleanly, and `pytest tests/unit/device/test_ap_profile_migration_manager.py` produces failures ONLY on the new tests (existing tests must remain green).

---

## Phase 3: Implementation (make the failing tests pass)

**Purpose**: Add the constant, the three static helpers, and wire them into both loops. Modify only `src/device/ap_profile_migration_manager.py`. No new module, no new dependency (FR-A10).

### Module scope

- [ ] TR019 Add `_LIMITER_FALLBACK_DELAY: float = 0.75  # seconds` at module scope in `src/device/ap_profile_migration_manager.py`, adjacent to `_RETRY_BACKOFF_SECONDS` at line ~51. Include an inline `#` comment naming Mist's 5000/hour ceiling and the 3600/5000 = 0.72 s theoretical minimum (per research Q1). Value locked; do not re-derive.

### Static helpers on `APProfileMigrationManager`

- [ ] TR020 Add `_is_429(err: BaseException) -> bool` as a private static method on `APProfileMigrationManager`. Implementation is the two-line pattern copied verbatim from `api_data_fetcher.py._is_rate_limit_error`: `status_code = getattr(getattr(err, "response", None), "status_code", None); return status_code == 429`. Google-style docstring with a "Why" section that names the copied source of truth and the reason the manager does NOT import the private helper across modules (research Q5). Docstring counts toward the >=90% coverage gate.
- [ ] TR021 Add `_apply_pacing(smoothed: float | None, pacing_stats: dict[str, float | int]) -> float | None` as a private static method on `APProfileMigrationManager`. Body: `import MistHelper as _mh` (lazy, matches lines 147/265/471); try `smoothed, delay = _mh.RateLimitingUtils.get_rate_limited_delay(smoothed, _mh.apisession, _mh._api_usage_cache)`; on any exception log a WARNING that names `_LIMITER_FALLBACK_DELAY` and set `delay = _LIMITER_FALLBACK_DELAY` (FR-A06). Always update `pacing_stats["delay_sum"] += delay`, `pacing_stats["delay_max"] = max(pacing_stats["delay_max"], delay)`, `pacing_stats["delay_count"] += 1`. Finally `time.sleep(delay)` via module-attribute access (FR-A07). Return the updated `smoothed`. Google-style docstring with a "Why" section that explains why the helper takes `pacing_stats` by reference (single-writer, O(1) memory per data-model section 4).
- [ ] TR022 Add `_signal_rate_limit_hit() -> None` as a private static method on `APProfileMigrationManager`. Body: `import MistHelper as _mh`; log a WARNING that names the observed 429 and the fact that the cache is being invalidated as the limiter error signal; set `_mh._api_usage_cache["initialized"] = False`. Wrap the mutation in `try/except (KeyError, TypeError)` so a missing or unexpected cache shape does not crash the loop (edge case in addendum spec: "apisession or the API usage cache is missing"). Google-style docstring with a "Why" section that names the `_needs_refresh` predicate as the consumer.

### Wire into the migrate loop (US1)

- [X] TR023 [US1] In `_run_reassignment_loop` (line ~777) initialize `smoothed: float | None = None` and `pacing_stats: dict[str, float | int] = {"puts_issued": 0, "http_429_seen": 0, "non_429_failures": 0, "delay_sum": 0.0, "delay_max": 0.0, "delay_count": 0}` at the top of the method (before the `for idx, rec in enumerate(...)` loop).
- [X] TR024 [US1] In the same loop body, BEFORE the existing `APProfileMigrationManager._reassign_one_ap(session, rec, target_id)` call at line ~824, call `smoothed = APProfileMigrationManager._apply_pacing(smoothed, pacing_stats)` and `pacing_stats["puts_issued"] += 1`. Preserve the existing progress-log call above; pacing sits between the progress log and the PUT.
- [X] TR025 [US1] In the existing `except Exception as exc:` branch at line ~825, add BEFORE the `backup["outcome"] = "partial"` line: `if APProfileMigrationManager._is_429(exc): APProfileMigrationManager._signal_rate_limit_hit(); pacing_stats["http_429_seen"] += 1; continue  # WHY: FR-A04 -- 429 is a throttle signal, not stop-on-failure.` The `continue` restarts the loop iteration WITHOUT counting the AP as reassigned; the next iteration's `_apply_pacing` sees the invalidated cache and gets a larger delay. NON-429 exceptions fall through to the existing stop-on-failure branch unchanged. Add `pacing_stats["non_429_failures"] += 1` inside the non-429 branch just before the `return backup` line.
- [X] TR026 [US1] Extend the `_run_reassignment_loop` return signature to include `pacing_stats` so `_print_migration_summary` and the audit emitter can consume it. Choice: attach as `backup["_pacing"]` (leading underscore = not persisted in the backup file schema; parent data-model.md section 1 is unchanged). Add an inline `#` comment on the assignment naming the addendum data-model reference. Update the docstring's Returns section to name the added ephemeral key.

### Wire into the revert loop (US2)

- [X] TR027 [US2] In the revert loop inside `revert_ap_profile_migration` (line ~360, immediately before the `for idx, device_id in enumerate(aps_to_revert, start=1):` loop) initialize `smoothed: float | None = None` and `pacing_stats: dict[str, float | int] = {...}` (same shape as TR023).
- [X] TR028 [US2] In the same loop body, BEFORE the existing `APProfileMigrationManager._revert_one_ap(...)` call at line ~378, call `smoothed = APProfileMigrationManager._apply_pacing(smoothed, pacing_stats)` and `pacing_stats["puts_issued"] += 1`.
- [X] TR029 [US2] In the `except Exception as exc:` branch at line ~384, add BEFORE the `failed_ids.append(device_id)` line: `if APProfileMigrationManager._is_429(exc): APProfileMigrationManager._signal_rate_limit_hit(); pacing_stats["http_429_seen"] += 1; continue`. Non-429 exceptions fall through to the existing tolerant failure branch (parent FR-023). Add `pacing_stats["non_429_failures"] += 1` inside the non-429 branch just before the existing `continue`.
- [X] TR030 [US2] After the revert loop terminates, thread `pacing_stats` into the JSONL audit call at line ~429. Extend the payload dict passed to `_emit_revert_audit` with a `"pacing"` key holding the four externally-visible fields per data-model-rate-limiting.md section 3 (`puts_issued`, `http_429_seen`, `non_429_failures`, `delay_seconds_mean`, `delay_seconds_max`). Compute `delay_seconds_mean = round(delay_sum / delay_count, 3) if delay_count > 0 else 0.0`; compute `delay_seconds_max = round(delay_max, 3)`.

### Summary + audit output

- [X] TR031 [US1] In `_print_migration_summary` (line ~864) accept and consume the ephemeral `payload["_pacing"]` sub-dict. Print the four lines from data-model-rate-limiting.md section 2 (exact text, exact order, exact column alignment): `Total PUTs issued        : {puts_issued}`, `HTTP 429 responses seen  : {http_429_seen}`, `Non-429 failures         : {non_429_failures}`, `Rate limiter delay (s)   : mean={mean:.3f}  max={max:.3f}`. Use `# noqa: T201` on the four `print(...)` lines consistent with existing summary lines. Every string must pass ASD-STE100 (FR-A11) -- imperative-free (this is descriptive output, not an instruction), one concept per line, no phrasal verbs.
- [X] TR032 [US1] Extend the migrate-side JSONL audit payload (the equivalent of TR030 on the migrate path, at the site that emits `ap_profile_migration.migrate.completed`) to include the same `pacing` sub-dict. If the migrate path does not yet emit a JSONL line (parent FR-018 shape check), add the emission and mirror the revert-side envelope exactly. Data-model-rate-limiting.md section 3 shows the full envelope.
- [X] TR033 [US2] Extend the revert summary print block (lines ~413-425) with the same four pacing lines (same text, same order) BEFORE the existing `_emit_revert_audit` call. Consistency between menu 207 and menu 208 output is a documented Q1 requirement.

**Checkpoint**: Phase 3 is complete when every test authored in Phase 2 passes locally under `pytest tests/unit/device/test_ap_profile_migration_manager.py -v` and the existing suite remains green.

---

## Phase 4: Wiring Verification (confirm globals are reachable)

**Purpose**: The plan assumes `mh.apisession` and `mh._api_usage_cache` are populated by the MistHelper entry point BEFORE menu 207 or menu 208 dispatches. Confirm that assumption holds, else pass them explicitly from the caller.

- [X] TR034 Grep `src/MistHelper.py` for `apisession =` and `_api_usage_cache =` (both are module-scope assignments in the current codebase, used by `api_data_fetcher.py`). Confirm that menu 207 and menu 208 dispatch happens AFTER those two attributes are set. Record the line numbers in the scratch note. Expected outcome: dispatch happens after login, so both globals are populated by menu-dispatch time -- no plumbing change required.
- [X] TR035 Run one manual smoke check: in a Python REPL, `python -c "import MistHelper as mh; print(hasattr(mh, 'apisession'), hasattr(mh, '_api_usage_cache'), hasattr(mh, 'RateLimitingUtils'))"`. All three MUST print `True`. If any print `False`, STOP and revise the wiring to pass the value from the caller (MistHelper.py entry points for menus 207 and 208) instead of reading it as a module global. Update TR021 and TR022 helper signatures accordingly.
- [X] TR036 [P] Confirm the addendum did NOT modify `src/utils/rate_limiting.py` or `src/api/api_data_fetcher.py`. Run `git diff main -- src/utils/rate_limiting.py src/api/api_data_fetcher.py` and expect empty output. Enforces FR-A03 and FR-A10 (no new limiter API, no new module).

---

## Phase 5: Verification (quickstart-rate-limiting.md scenarios)

**Purpose**: Execute the full quickstart runbook and the ambient CI gates. Fail hard on any red.

- [X] TR037 Run `cd src && pytest ../tests/unit/device/test_ap_profile_migration_manager.py -v`. Expect ZERO failures and every new pacing test (TR006-TR018, thirteen tests) reported as PASSED.
- [X] TR038 Run `cd src && pytest -q`. Expect the full MistHelper suite to exit 0 (SC-A06).
- [X] TR039 [P] Run `cd src && ruff check .`. Expect zero violations (SC-A06).
- [X] TR040 [P] Run `interrogate -c pyproject.toml src/device/ap_profile_migration_manager.py`. Expect docstring coverage >= 90% (SC-A06, FR-A12).
- [X] TR041 [P] Run `pydoclint --style=google src/device/ap_profile_migration_manager.py`. Expect zero violations (DOCS.md rule).
- [X] TR042 Synthetic 10K-AP dry-load check. Add and run a temporary local script (do NOT commit) that: (a) builds a fixture of 10000 mock AP records, (b) patches `_mh.RateLimitingUtils.get_rate_limited_delay` to return `(None, 0.001)`, (c) patches `src.device.ap_profile_migration_manager.time.sleep` to a counting mock, (d) patches `updateSiteDevice` to always succeed, (e) invokes `_run_reassignment_loop`. Assert `time.sleep.call_count == 10000` (once per AP), assert `get_rate_limited_delay.call_count == 10000`, assert `pacing_stats["http_429_seen"] == 0`, assert `pacing_stats["non_429_failures"] == 0`, assert wall-clock elapsed < 2.0 s (SC-A01). Delete the script after the check; the equivalent is already covered by TR006 + TR008 in the committed suite.
- [X] TR043 Synthetic 10K-AP + 100x 429 injection check. Same as TR042 but the mocked `updateSiteDevice` raises a 429-shaped exception on every 100th call. Assert `pacing_stats["http_429_seen"] == 100`, assert stop-on-failure was NOT tripped (loop reached the 10000th AP), assert `_mh._api_usage_cache["initialized"]` was set to `False` >= 100 times. Delete the script after the check.
- [X] TR044 Confirm the FR-A11 ASD-STE100 lint. If the project ships an ASD-STE100 linter under `tools/ste100_lint/` or similar (see AGENTS.md), run it against the changed strings in the four summary lines and the two WARNING messages. Otherwise, hand-review each new operator-visible string against `documentation/ASD-STE100_writing-guide.md`: one word per meaning, active voice, imperative-free for descriptive output, <=20 words per line, no phrasal verbs, no Latin abbreviations.

---

## Phase 6: Polish (post-green cleanup)

- [ ] TR045 [P] Update the `## Recent Changes` block of the project-root `CLAUDE.md` with a single line: `1029-ap-profile-migration (rate limiting addendum): menus 207/208 now consult src/utils/rate_limiting.py before each PUT; 429s feed the PID limiter via cache invalidation; four new pacing fields on summary + JSONL audit.` Do NOT edit other CLAUDE.md sections (per project instructions).
- [ ] TR046 [P] Add a single inline `#` comment in `_run_reassignment_loop` and the revert loop pointing to the addendum specs: `# WHY: pacing per specs/1029-ap-profile-migration/spec-addendum-rate-limiting.md FR-A01/A02.` Constitution Principle VI compliance.
- [ ] TR047 [P] Run `git status` and confirm the changed-file set is EXACTLY two files: `src/device/ap_profile_migration_manager.py` and `tests/unit/device/test_ap_profile_migration_manager.py`. Any third changed file (except `CLAUDE.md` from TR045) is a signal that the addendum scope has leaked; halt and reconcile before commit.
- [ ] TR048 Commit sequence: three commits on `1029-ap-profile-migration`. Commit 1 = TR006-TR018 (failing tests). Commit 2 = TR019-TR033 (impl that turns them green). Commit 3 = TR045-TR046 (polish). Rationale: preserves TDD signal in git history for reviewer audit. Message prefix `feat(1029)` for commit 2, `test(1029)` for commit 1, `docs(1029)` for commit 3.

---

## Dependencies

- **Phase 1 (Prep, TR001-TR005)** MUST complete before Phase 2. TR001, TR002, TR004 are sequential (all read the same scratch note); TR003 and TR005 are `[P]`.
- **Phase 2 (Tests, TR006-TR018)** MUST complete before Phase 3. All thirteen tests are `[P]` with each other (distinct test functions in the same file, but pytest collects them independently). Author them in one editing pass, then run once to confirm they fail before Phase 3 begins.
- **Phase 3 (Impl, TR019-TR033)** is sequenced: TR019 (constant) -> TR020, TR021, TR022 (helpers, all `[P]` with each other) -> TR023-TR026 (US1 wiring, sequential inside the same method) -> TR027-TR030 (US2 wiring, sequential inside the same method) -> TR031-TR033 (summary + audit). US1 wiring and US2 wiring blocks are `[P]` with each other because they touch disjoint methods.
- **Phase 4 (Wiring Verification, TR034-TR036)** MUST run before Phase 5. If TR034 or TR035 fails, revise TR021 and TR022 (helpers take globals via caller-passed args) and re-run Phase 3 impl on the migrate + revert loops.
- **Phase 5 (Verification, TR037-TR044)** runs after Phase 4. TR039, TR040, TR041 are `[P]` with each other (independent lint tools).
- **Phase 6 (Polish, TR045-TR048)** runs last. TR045, TR046, TR047 are `[P]`. TR048 is the final commit sequence and is sequential.

## Parallel Execution Examples

**Prep tasks (safe together)**: TR003 and TR005 both read reference files independently.

```text
Task: TR003 Read src/utils/rate_limiting.py
Task: TR005 Read tests/unit/device/test_ap_profile_migration_manager.py
```

**Test tasks (all safe together)**: all thirteen pacing tests are new, distinct function names in the same file. Author in one pass.

```text
Task: TR006 test_migrate_calls_get_rate_limited_delay_once_per_ap
Task: TR007 test_migrate_429_invalidates_api_usage_cache
Task: TR008 test_migrate_hermetic_no_wall_clock_sleep
Task: TR009 test_migrate_non_429_still_halts_stop_on_failure
Task: TR010 test_migrate_limiter_exception_falls_back_and_continues
Task: TR011 test_revert_calls_get_rate_limited_delay_once_per_ap
Task: TR012 test_revert_429_invalidates_api_usage_cache
Task: TR013 test_revert_hermetic_no_wall_clock_sleep
Task: TR014 test_revert_non_429_error_does_not_toggle_cache
Task: TR015 test_dry_run_does_not_consult_rate_limiter
Task: TR016 test_summary_contains_pacing_lines
Task: TR017 test_jsonl_audit_line_carries_pacing_subdict
Task: TR018 test_migrate_integration_real_limiter_seeded_cache
```

**Helper impl (safe together)**: TR020, TR021, TR022 are three distinct new static methods with no shared state.

```text
Task: TR020 _is_429 helper
Task: TR021 _apply_pacing helper
Task: TR022 _signal_rate_limit_hit helper
```

**Verification lints (safe together)**: TR039, TR040, TR041 invoke independent tools.

```text
Task: TR039 ruff check .
Task: TR040 interrogate coverage
Task: TR041 pydoclint style check
```

## Implementation Strategy

**MVP path**: Phases 1 -> 2 -> 3 (TR019-TR026) -> 4 -> 5 (TR037-TR038) delivers US1 (menu 207 pacing) alone. This is the smallest shippable slice per addendum priority (both US1 and US2 are P1, but menu 207 is the primary risk surface at 10K-AP scale per the problem statement).

**Full delivery**: Phase 3 US2 wiring (TR027-TR030) + summary/audit extensions (TR031-TR033) close the parity gap with the revert path so a 10K-AP revert also self-throttles.

**Test-first ordering (constitutional)**: Every implementation task in Phase 3 has at least one Phase 2 test that names it. TR019 (constant) is covered by TR010. TR020 is covered by TR007, TR009, TR012, TR014. TR021 is covered by TR006, TR008, TR010, TR011, TR013, TR018. TR022 is covered by TR007, TR009, TR012, TR014. TR031 + TR033 are covered by TR016. TR030 + TR032 are covered by TR017.

## Format Validation

Every task above satisfies the checklist format:

- Starts with `- [ ]`.
- Carries a Task ID `TR001`-`TR048`.
- Carries a `[P]` marker only when parallelizable (distinct file OR distinct function OR distinct tool).
- Carries a `[US1]` or `[US2]` story label on tasks that map 1:1 to menu 207 or menu 208. Prep, cross-cutting, Wiring, Verification, and Polish tasks have no story label per the parent-task convention.
- Names either an exact file path or an exact command.
