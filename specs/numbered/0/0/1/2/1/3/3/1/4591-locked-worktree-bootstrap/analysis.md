# Analysis: Locked Worktree Bootstrap

**Scope**: Consistency across `spec.md`, `plan.md`, `tasks.md`, and the remote code on `main`. Evidence IDs (RC-nn, U-nn, S-nn) refer to `design/research.md`.

## 1. Consistency Review

| ID | Check | Result | Action |
|---|---|---|---|
| AN-01 | FR-002 (no frozen fallback) against `scripts/bootstrap_worktree.py` on `main` | Consistent. The locked sync runs at line 466 (RC-01). The file holds no `--frozen` text. | None |
| AN-02 | FR-006 (no `UV_NATIVE_TLS`) against `documentation/development-setup.md` | Conflict. The environment table lists `UV_NATIVE_TLS=1` at line 73 (RC-26). | T011 removes the row. |
| AN-03 | FR-007 against `documentation/development-setup.md` line 28 | Conflict. The sentence says the bootstrap installs the requirements files (RC-25). The code runs the locked sync. | T011 replaces the sentence. |
| AN-04 | TC-01 against the existing assertion at `tests/unit/scripts/test_bootstrap_worktree_uv.py` lines 258 to 270 (RC-24 context) | Conflict in form. The test asserts the exact text of the index cause message. | T007 updates the assertion. |
| AN-05 | SC-002 against the CI jobs on `main` | Consistent. The lock check and the container lock step pass (RC-39, RC-40). | T-REMOTE-CI confirms on the pull request. |
| AN-06 | FR-010 against the change map in `plan.md` | Consistent. No dependency file appears in the map. | T-PR checks the diff. |
| AN-07 | Five-item debt in `plan.md` against the repository | Consistent. `scripts/` holds 58 direct children, recorded as grandfathered. | None in this change. |
| AN-08 | Constitution Principle II against the module-level helpers in the bootstrap | Existing debt. `read_lock_registry`, `configured_index`, and `normalize_index` stay module-level (RC-09, RC-10). | Recorded in `plan.md`. |
| AN-09 | Issue label `needs-human-review` against T-MERGE | Consistent. The label stays until the owner reviews the pull request. | T-MERGE states the rule. |
| AN-10 | `.github/copilot-instructions.md` line 21 (`mistapi>=0.64.0,<0.65`) against `pyproject.toml` line 29 (`>=0.64.1,<0.65`) | Stale document (RC-28, RC-18). | UNR-04 |
| AN-11 | Constitution text ("mistapi: 0.59+") against `pyproject.toml` | Stale constitution text (version 1.9.0). The pin is `>=0.64.1,<0.65`. | UNR-04 |
| AN-12 | Reporter-era bootstrap (`c57c9b704`) against the current bootstrap | Changed after the report. PR #4880 added the diagnosis, the cause messages, and the option. The reporter log has none of these lines (RC-32, RC-35). | Recorded in `research.md`, section 1.1. |

## 2. Defects in Existing Work

| ID | Defect | Evidence | Fix |
|---|---|---|---|
| DEF-01 | The development setup document names the requirements files as the install path of the bootstrap. | RC-25 (stale), RC-01 | T011 |
| DEF-02 | The child environment sets `UV_NATIVE_TLS`, so uv prints a deprecation warning on each locked sync. The reporter log shows that warning. | RC-02, RC-37, section 1.1 | T009 |
| DEF-03 | The cause message names no variable. An operator cannot see which source conflicts. The owner asked for the names (issue comment of 2026-11-11). | RC-06, RC-07 | T008, T010 |
| DEF-04 | The diagnosis names the index cause only for the primary index. A failure caused only by an extra index gets the drift message. The drift advice (`uv lock` on a branch) is then wrong. The impact is unverified (U-05). | RC-05, RC-10, RC-07 | Names in the message (T008) show the active variable. UNR-01 tracks the rule. |
| DEF-05 | `read_lock_registry` reads only the first registry source. A lock with two registry sources would be read partly. | RC-09 | UNR-02 |
| DEF-06 | `configured_index` reads `UV_DEFAULT_INDEX` as the second source. `InstallationPolicy.apply` removes that variable first, so the branch never sees a value in the bootstrap path. | RC-47, RC-48 | Recorded. The change does not alter the branch. T008 tests the names with `UV_INDEX_URL` and `UV_EXTRA_INDEX_URL` only. |

## 3. Unresolved Items

| ID | Item | Condition to resolve | Effect on this record |
|---|---|---|---|
| UNR-01 | An extra index alone may keep the lock usable (U-05). The diagnosis rule ignores extra indexes (DEF-04). | Task T006 and the reporter data (gate G-1). | The drift message may appear for an extra-index failure. |
| UNR-02 | `read_lock_registry` ignores a second registry source (DEF-05). | A lock with two registry sources is introduced. | None for the current lock. |
| UNR-03 | Public index reachability for the reporter network (U-06). | Reporter data (gate G-1). | Decides whether `--public-lock-index` works for the reporter. |
| UNR-04 | Stale version text: `.github/copilot-instructions.md` line 21 says 0.64.0, and the constitution says 0.59+ (AN-10, AN-11). | A separate documentation change. | None for this change. |
| UNR-05 | `scripts/` holds 58 direct children (grandfathered). | A separate remediation issue after gate G-1. | None for this change. |
| UNR-06 | The bootstrap uses the uv found on PATH and does not check its version. The project pins uv 0.13.9 (RC-19). | A separate decision on a version check. | The minimum uv 0.11.0 appears in the documentation only (R-01). |
| UNR-07 | Five local files differ from `HEAD`: `src/foundation/support/utils/logger_utils.py`, `src/interfaces/wan_performance/collection/request_admission.py`, `src/mist/intelligence/reports/subscription_expiry/client.py`, `tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py`, and `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py`. | The owner's local work. | None. The evidence uses committed blobs. |
| UNR-08 | The reporter uv version and full output are absent (U-01, U-02). | Gate G-1. | Blocks code and test changes. |
| UNR-09 | Live reproduction is not run (U-04). | Task T006 after gate G-1. | Confirms or rejects D-1. |

## 4. Requirement Coverage

- FR-001: T001, T002, T006.
- FR-002: T002, T003.
- FR-003: T004, T006, T007, T008.
- FR-004: T007, T008, T010.
- FR-005: T004, T007.
- FR-006: T002, T007, T009.
- FR-007: T011.
- FR-008: T007, T-LOCAL-GATES.
- FR-009: T012.
- FR-010: T-PR, T-LOCAL-GATES.
- FR-011: T005, T-MERGE.

Each FR maps to at least one task and at least one test or command. SC-001 holds.
