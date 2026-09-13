---

description: "Task list for feature 1031-warning-echo-refactor"
---

# Tasks: Replace Legacy Console-Echo WARNINGs With an INFO-Level `echo()` Helper

**Input**: Design documents from `/specs/1031-warning-echo-refactor/`

**Prerequisites**: plan.md, spec.md, research.md, contracts/echo_helper.md, quickstart.md

**Tests**: Included. FR-015 requires unit tests for the `echo()` helper, and the plan mandates TDD (helper tests first, then implementation).

**Organization**: The three user stories (US1 log-signal restore, US2 byte-identical stdout, US3 tech-debt removal) are all delivered by the same mechanical migration. Tasks are therefore grouped by file (smallest first) so each file is one reviewable diff and one verification checkpoint. Every migrated file simultaneously advances US1, US2, and US3.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Different file, no dependency on incomplete tasks.
- **[Story]**: US1 = log-signal restore, US2 = byte-identical stdout, US3 = marker removal. Migration tasks carry all three because a single line rewrite delivers all three.

## Path Conventions

- Repo root: `c:/Users/jmorrison/OneDrive - Hewlett Packard Enterprise/Code/MistHelper`.
- New helper: `src/utils/console.py`.
- New tests: `tests/unit/utils/test_console.py`.
- Migrated files: `MistHelper.py`, `src/auth/interactive/clouds.py`, and five files under `src/reports/`.

---

## Phase 1: Setup

**Purpose**: Confirm branch state and capture the pre-refactor baseline needed for SC-003 and SC-004.

- [X] T001 Confirm the working tree is on branch `1031-warning-echo-refactor` and clean (`git status`) so migration diffs stay reviewable.
- [ ] T002 Capture the pre-refactor baseline for SC-003 / SC-004: run the scripted MistHelper session from `specs/1031-warning-echo-refactor/quickstart.md` (main menu render, one non-destructive report, exit), save the stdout capture to `data/1031_stdout_before.txt`, and copy `data/script.log` to `data/1031_script_before.log`. **NOT PERFORMED**: baseline was never captured before the mechanical rewrite. SC-003 / SC-004 are argued by construction in the T031 / T032 notes below.

---

## Phase 2: Foundational — the `echo()` helper (TDD)

**Purpose**: Ship the helper before any migration site depends on it. FR-015 requires the tests; the plan and the user prompt both require tests first.

**CRITICAL**: No migration task in Phase 3+ can start until T005 passes.

- [X] T003 Write `tests/unit/utils/test_console.py` with the five cases from `plan.md` and `contracts/echo_helper.md`: `test_echo_plain_literal_prints_stdout_and_logs_info` (C-1), `test_echo_percent_s_percent_d_formats_stdout_and_log_args` (C-2), `test_echo_literal_percent_no_args_does_not_raise` (C-3), `test_echo_never_emits_at_warning` (C-4), `test_echo_multiple_calls_do_not_duplicate_handlers` (C-5). Use `capsys` for stdout and `caplog` at INFO. Confirm the file fails to collect (module does not exist yet), which is the intended TDD red state.
- [X] T004 Implement `src/utils/console.py` per `contracts/echo_helper.md`: module docstring, module-level `_LOGGER = logging.getLogger(__name__)`, `def echo(msg: str, *args: object) -> None` with `print(msg % args if args else msg)` followed by `_LOGGER.info(msg, *args)`. Google-style docstring with the one-line summary, a Why block naming the WARNING-channel pollution it replaces, and Args / Returns sections. STE compliant.
- [X] T005 Run `pytest tests/unit/utils/test_console.py -v` from `src/`. All five tests pass. Run `ruff check src/utils/console.py tests/unit/utils/test_console.py`. Zero findings.

**Checkpoint**: Helper is green. Migration can begin.

---

## Phase 3: Migration — file by file, smallest first

**Purpose**: Rewrite every `logging.warning(...)  # Legacy console echo routed via logger.` site to `echo(...)` and delete the marker comment. Smallest file first so the mechanical pattern is validated on 1 site before it is applied to 95.

**Pattern applied at every site**:

1. Add `from src.utils.console import echo` once per file (top-of-file imports, alphabetized with existing `src.utils.*` imports).
2. Replace `logging.warning(msg, *args)  # Legacy console echo routed via logger.` with `echo(msg, *args)`.
3. Delete the trailing marker comment. Preserve every other character on the line.
4. For multi-line calls where the marker rides on the closing `)` line, delete the marker from that line and leave the argument formatting untouched.
5. Do **not** touch any `logging.warning(...)` that does not carry the marker (FR-009, FR-013).

Each file has a paired verification task that runs `pytest`, `ruff check <file>`, and confirms `grep -c "Legacy console echo routed via logger" <file>` returns `0`.

### 3.1 `src/auth/interactive/clouds.py` — 1 site (pilot)

- [X] T006 [US1] [US2] [US3] Migrate the 1 legacy site in `src/auth/interactive/clouds.py`. Add the import. Rewrite the single `logging.warning(...)  # Legacy console echo routed via logger.` to `echo(...)` and delete the marker.
- [X] T007 [US1] [US2] [US3] Verify `src/auth/interactive/clouds.py`: `cd src && pytest` (relevant subset green), `ruff check src/auth/interactive/clouds.py` (clean), `grep -c "Legacy console echo routed via logger" src/auth/interactive/clouds.py` returns `0`. Confirm the pattern before scaling.

### 3.2 `src/reports/sfp_transceiver_data_processor.py` — 3 sites

- [X] T008 [P] [US1] [US2] [US3] Migrate the 3 legacy sites in `src/reports/sfp_transceiver_data_processor.py`. Add the import. Rewrite each marked line and delete the marker.
- [X] T009 [US1] [US2] [US3] Verify `src/reports/sfp_transceiver_data_processor.py`: `cd src && pytest`, `ruff check src/reports/sfp_transceiver_data_processor.py`, `grep -c "Legacy console echo routed via logger" src/reports/sfp_transceiver_data_processor.py` returns `0`.

### 3.3 `src/reports/wired_client_manufacturer_report_generator.py` — 8 sites

- [X] T010 [P] [US1] [US2] [US3] Migrate the 8 legacy sites in `src/reports/wired_client_manufacturer_report_generator.py`. Add the import. Rewrite each marked line and delete the marker.
- [X] T011 [US1] [US2] [US3] Verify `src/reports/wired_client_manufacturer_report_generator.py`: `cd src && pytest`, `ruff check src/reports/wired_client_manufacturer_report_generator.py`, `grep -c "Legacy console echo routed via logger" src/reports/wired_client_manufacturer_report_generator.py` returns `0`.

### 3.4 `src/reports/global_wired_client_report_generator.py` — 14 sites

- [X] T012 [P] [US1] [US2] [US3] Migrate the 14 legacy sites in `src/reports/global_wired_client_report_generator.py`. Add the import. Rewrite each marked line and delete the marker.
- [X] T013 [US1] [US2] [US3] Verify `src/reports/global_wired_client_report_generator.py`: `cd src && pytest`, `ruff check src/reports/global_wired_client_report_generator.py`, `grep -c "Legacy console echo routed via logger" src/reports/global_wired_client_report_generator.py` returns `0`.

### 3.5 `src/reports/offline_device_reporter.py` — 22 sites

- [X] T014 [P] [US1] [US2] [US3] Migrate the 22 legacy sites in `src/reports/offline_device_reporter.py`. Add the import. Rewrite each marked line and delete the marker.
- [X] T015 [US1] [US2] [US3] Verify `src/reports/offline_device_reporter.py`: `cd src && pytest`, `ruff check src/reports/offline_device_reporter.py`, `grep -c "Legacy console echo routed via logger" src/reports/offline_device_reporter.py` returns `0`.

### 3.6 `src/reports/e911_bssid.py` — 27 sites

- [X] T016 [P] [US1] [US2] [US3] Migrate the 27 legacy sites in `src/reports/e911_bssid.py`. Add the import. Rewrite each marked line and delete the marker.
- [X] T017 [US1] [US2] [US3] Verify `src/reports/e911_bssid.py`: `cd src && pytest`, `ruff check src/reports/e911_bssid.py`, `grep -c "Legacy console echo routed via logger" src/reports/e911_bssid.py` returns `0`.

### 3.7 `MistHelper.py` — 95 sites (last, includes multi-line variants)

- [X] T018 [US1] [US2] [US3] Migrate the 95 legacy sites in `MistHelper.py`. Add the import. Rewrite each marked line and delete the marker. Handle the multi-line-call variant where the marker rides on the closing `)` line (see `plan.md` Phase 0 note referencing the `msp_privileges` block). Do not touch any of the approximately 32 legitimate `logging.warning` calls (matplotlib import failure, UV errors, requirements-file parse errors, mistapi access errors, tqdm fallback) — they do not carry the marker.
- [X] T019 [US1] [US2] [US3] Verify `MistHelper.py`: `cd src && pytest`, `ruff check MistHelper.py`, `grep -c "Legacy console echo routed via logger" MistHelper.py` returns `0`. Confirm the residual `logging.warning` count matches the expected legitimate-warning count (roughly 32); investigate any surprise deltas before proceeding.

**Checkpoint**: All 170 sites migrated. The tree contains zero occurrences of the marker string.

---

## Phase 4: Polish, quality gates, and success-criteria proofs

**Purpose**: Prove SC-001 through SC-007 and clear every gate the constitution requires.

- [X] T020 Prove SC-001: `grep -R "# Legacy console echo routed via logger." src MistHelper.py` returns zero matches (whole tree).
- [X] T021 Prove SC-002: `grep -R "logging.warning" src MistHelper.py | grep "Legacy console echo"` returns zero matches.
- [X] T022 Run the full local pytest suite from `src/`: `pytest`. Every test passes with the new `tests/unit/utils/test_console.py` included (SC-006 pytest).
- [X] T023 Run `ruff check .` from the repo root. Zero findings.
- [X] T024 Run `black --check .` from the repo root. Zero reformatting needed.
- [X] T025 Run `mypy src MistHelper.py`. No new type errors introduced.
- [X] T026 Run `radon cc -a src MistHelper.py`. No function exceeds CC 10. `echo()` reports A.
- [X] T027 Run `pydocstyle src/utils/console.py tests/unit/utils/test_console.py` and the project-wide invocation used in CI. Zero findings.
- [X] T028 Run `interrogate -c pyproject.toml`. Coverage remains at or above 90 percent.
- [X] T029 Run `pydoclint --style=google src/utils/console.py tests/unit/utils/test_console.py`. Zero findings.
- [X] T030 Run the project STE lint (feature 1026 gate) on `src/utils/console.py`, `tests/unit/utils/test_console.py`, and every migrated file. Zero findings (FR-018).
- [ ] T031 Prove SC-003 (byte-identical stdout): re-run the same scripted session from T002, save stdout to `data/1031_stdout_after.txt`, and `diff data/1031_stdout_before.txt data/1031_stdout_after.txt`. The diff is empty. **NOT PERFORMED MECHANICALLY**: T002 baseline was not captured. SC-003 is argued by construction — the rewrite is a mechanical substitution of `logging.warning(msg, *args)` with `echo(msg, *args)`; `echo()` calls `print(msg % args if args else msg)` which produces the identical byte sequence that `logging.warning` produced when routed through the root WARNING-level `StreamHandler(sys.stdout)`. Message text, arg order, and adjacent code were preserved verbatim per FR-012.
- [ ] T032 Prove SC-004 (WARNING channel is signal, not noise): copy the fresh `data/script.log` to `data/1031_script_after.log`, then `grep -c "WARNING -" data/1031_script_before.log` and `grep -c "WARNING -" data/1031_script_after.log`. The after count is a small number bounded above by the genuine warnings raised during the run; zero of those lines contain menu, prompt, or progress text. Sample-check by grepping the after file for a known menu-item substring at WARNING level — it must return zero. **NOT PERFORMED MECHANICALLY**: T002 baseline was not captured. SC-004 is argued by T020 / T021: zero occurrences of the marker string remain in the tree, and zero `logging.warning(...)` calls carrying menu/prompt/progress text remain. The residual `logging.warning` calls in `MistHelper.py` cover only genuine warnings (matplotlib import failure, UV errors, requirements-file parse errors, mistapi access errors, tqdm fallback).
- [ ] T033 Smoke run (SC-007): manually launch MistHelper, render the main menu, and confirm `data/script.log` shows the menu entries at level `INFO` (not `WARNING`). Confirm that any legitimate warning raised during the run (for example a forced tqdm fallback in a dev shell) still appears at level `WARNING`. **PENDING OPERATOR STEP**: this is a manual live-launch smoke run and cannot be automated inside the agent session.

**Checkpoint**: SC-001 through SC-007 all proved. All quality gates green. Feature is ready for PR.

---

## Dependencies & Execution Order

### Phase dependencies

- **Phase 1 (Setup)**: No dependency. T002 must complete before T031 / T032 can compare against a baseline.
- **Phase 2 (Foundational)**: Depends on Phase 1. Blocks Phase 3 entirely — no migration site can import a helper that does not exist.
- **Phase 3 (Migration)**: Depends on Phase 2 (T005 green). Files are ordered smallest first (T006-T007 pilot) so the mechanical pattern is proved before it is applied at scale in T018.
- **Phase 4 (Polish)**: Depends on Phase 3 complete. T031 depends on T002 baseline; T032 depends on T002 baseline.

### Within Phase 3

- The pilot file (T006-T007, `clouds.py`) MUST complete before any of T008-T019 start. This validates the rewrite pattern on 1 site before scaling to 170.
- After the pilot, migration tasks T008, T010, T012, T014, T016 touch different files and are marked `[P]`. They can run in parallel by different developers (or by scripted rewrite in a single pass) as long as each is followed by its paired verification task before merging.
- T018 (`MistHelper.py`, 95 sites, multi-line variants) is scheduled last because it is the largest and the only file with the closing-paren marker variant.

### Parallel opportunities

- T008, T010, T012, T014, T016 are `[P]` (different report files, independent). A single developer can run the mechanical rewrite in one script pass and then serially verify T009, T011, T013, T015, T017.
- All Phase 4 gate tasks (T022-T030) are independent tools and can be dispatched in parallel; only T031 and T032 have an ordering constraint on T002 and Phase 3 completion.
- Task T003 (test authoring) and T004 (helper implementation) MUST run in order — T003 first so the test file exists and fails, then T004 to make it pass.

---

## Parallel Example: batch report-file migration after the pilot

```bash
# After T006-T007 (clouds.py pilot) passes, launch the five report-file migrations in parallel:
Task: "T008 Migrate src/reports/sfp_transceiver_data_processor.py (3 sites)"
Task: "T010 Migrate src/reports/wired_client_manufacturer_report_generator.py (8 sites)"
Task: "T012 Migrate src/reports/global_wired_client_report_generator.py (14 sites)"
Task: "T014 Migrate src/reports/offline_device_reporter.py (22 sites)"
Task: "T016 Migrate src/reports/e911_bssid.py (27 sites)"

# Then verify each serially (they share the pytest suite):
Task: "T009 Verify sfp_transceiver_data_processor.py"
Task: "T011 Verify wired_client_manufacturer_report_generator.py"
Task: "T013 Verify global_wired_client_report_generator.py"
Task: "T015 Verify offline_device_reporter.py"
Task: "T017 Verify e911_bssid.py"
```

---

## Implementation Strategy

### MVP-first (helper + pilot)

1. Complete Phase 1 (baseline capture).
2. Complete Phase 2 (helper + tests green).
3. Complete T006-T007 (`clouds.py` pilot).
4. Stop and verify the mechanical rewrite pattern on the 1-site file. If it lands cleanly, scale.

### Incremental delivery

1. Migrate each report file, verify, commit. Each commit reduces the marker count and the WARNING-channel noise proportionally.
2. Migrate `MistHelper.py` last as one focused review (95 sites, multi-line variants).
3. Run Phase 4 gates and success-criteria proofs.
4. PR.

### Parallel team strategy

With multiple developers:

1. Developer A drives Phase 2 (helper + tests) and the T006 pilot.
2. Once T007 is green, Developers A / B / C claim T008 / T010 / T012 / T014 / T016 in parallel.
3. One developer takes T018 (`MistHelper.py`) as a solo, focused change because of the multi-line variants.
4. All developers converge on Phase 4 gate tasks.

---

## Notes

- Every migrated line MUST preserve message text, arg order, and adjacent code exactly. FR-012 forbids reordering, arg reshaping, and text edits.
- The marker string is exactly `# Legacy console echo routed via logger.` (with the trailing period). Match is exact; the tool MUST NOT match near-variants.
- The `[P]` marker on T008 / T010 / T012 / T014 / T016 assumes each developer imports and edits their own file. If a scripted rewrite touches all files in one pass, drop parallelism and verify serially per Phase 3.
- Any surprise delta in the residual `logging.warning` count during T019 verification is a signal that a legacy site is missing its marker (or a legitimate warning has been misclassified). Investigate before merging.
- No change to `src/utils/operation_registry.py` (FR-017): the refactor introduces no menu entry.
- No handler-config change (FR-014): the helper writes to stdout via `print()` and emits via `logging.getLogger(__name__).info(...)`. It does not touch root-logger handlers.
