# Implementation Plan: Replace Legacy Console-Echo WARNINGs With an INFO-Level `echo()` Helper

**Branch**: `1031-warning-echo-refactor` | **Date**: 2026-07-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/1031-warning-echo-refactor/spec.md`

## Summary

Introduce a single utility function `echo(msg, *args)` in `src/utils/console.py` that writes the fully formatted message to `stdout` and emits one `INFO`-level log record on a module-level logger. Then mechanically rewrite 170 legacy `logging.warning(...)  # Legacy console echo routed via logger.` call sites across seven files to `echo(...)` calls. The refactor removes semantic pollution of the `WARNING` channel in `data/script.log` while preserving byte-identical console output for interactive users.

The technical approach is:

1. Author `src/utils/console.py` with one function, one module-level logger, `%`-style formatting so migrated sites are drop-in replacements for `logging.warning("%s: %s", key, description)`.
2. Add unit tests under `tests/unit/utils/test_console.py` covering stdout, INFO record, `%s`/`%d` args, literal `%` safety, and non-emission at WARNING.
3. Add each migrated file a single `from src.utils.console import echo` import (or the correct sibling-relative form for files that already use `from src.utils.*` conventions).
4. Run a scripted mechanical rewrite driven by the exact trailing-marker comment `# Legacy console echo routed via logger.`. Support the multi-line-call variant where the marker rides on the closing `)` line.
5. Delete the marker comment on every migrated line. Preserve every other character on the line, including all inline comments after the marker (there are none in the tree today, but the tool must not silently discard them).

## Technical Context

**Language/Version**: Python 3.13+ (per constitution binding minimum and `pyproject.toml` py313 target).

**Primary Dependencies**: Standard library only (`logging`, `sys`); no new runtime dependency. Tests use `pytest`, `capsys`, `caplog` (already project-standard).

**Storage**: N/A. No persisted state. The refactor only changes what levels appear in the existing `data/script.log` output.

**Testing**: `pytest` under `tests/unit/utils/test_console.py`. Uses `capsys` for stdout capture and `caplog` for record inspection. Follows the existing `tests/unit/utils/` conventions (see neighbors `test_environment_utils.py`, `test_filter_operator_engine.py`, `test_input_utils_wave9.py`).

**Target Platform**: Cross-platform CLI (Windows 11 + Linux container). ASCII-only output (constitution V).

**Project Type**: Single-project CLI tool. Uses the existing `src/` + `tests/` layout.

**Performance Goals**: Not performance-sensitive. Each `echo()` call is one `print()` plus one `logger.info(...)`. No hot path.

**Constraints**:
- Byte-identical stdout output vs pre-refactor (SC-003).
- Zero `logging.warning` regressions on the ~32 legitimate warning sites (FR-013).
- Zero new lint waivers (FR-016).
- No handler-config change (FR-014).
- STE-compliant prose (FR-018).

**Scale/Scope**: 170 call sites across 7 files. 1 new module (~30 lines). 1 new test file (~120 lines). Approximately 340 mechanical line edits (170 rewrites plus 170 import-check / no-op / adjacent-line touches, but adjacent-line untouched by design).

## Constitution Check

Gates evaluated against `.specify/memory/constitution.md` v1.4.0.

| Principle | Applies? | Compliance plan |
|---|---|---|
| I. Five-Item Rule | Yes | `echo()` is a single function with 2 parameters (`msg`, `*args`), <=25 lines, exactly two logical operations (print + log). Well under all Five-Item limits. |
| II. Class-Based Architecture (No Wrappers) | Yes, with justification | `echo()` is a plain module-level function, not a class method. Per constitution II, wrapper functions that delegate to a class are prohibited; but `echo()` does not wrap or delegate to any class — it is a primitive with two direct effects (`print`, `logger.info`). Wrapping it in a `Console` class would create a wrapper of stdlib primitives, not a semantic domain object, which is the exact anti-pattern principle II prohibits. Recorded in Complexity Tracking below with the trade-off. |
| III. Safety-First | Not applicable | No `input()`, no destructive operation, no external input. |
| IV. Full Deployment Pipeline | Yes | Standard pipeline runs after the change is landed. `py_compile`, commit, push, CI, container pull, restart, verify. |
| V. Observability & Logging | Yes | ASCII-only messages preserved. `echo()` uses `%s`-style formatting per principle V and VII. Records at INFO per principle V "user-facing progress messages". |
| VI. Inline Comments (NON-NEGOTIABLE) | Yes | `echo()` body has same-line comments on every executable line. Test file has same-line comments on every executable line. The 170 migrated call sites are single-token renames (`logging.warning` -> `echo`) plus marker deletion — the pre-existing surrounding code and comments are untouched, so no new lines are introduced that would require new inline comments. |
| VII. Action Logging (NON-NEGOTIABLE) | Yes | `echo()` is itself the log statement (it emits at INFO). Its purpose is to record what was shown to the user. The tests wrap their asserts in the "before / after" logging pattern where meaningful. |

**Gate result**: PASS with one recorded justification under principle II. See Complexity Tracking.

Post-Phase-1 re-check: PASS unchanged. Design does not introduce any new class, new dependency, or new destructive path.

## Project Structure

### Documentation (this feature)

```text
specs/1031-warning-echo-refactor/
├── plan.md              # This file
├── research.md          # Phase 0 output (this run)
├── data-model.md        # Not applicable (no entities beyond the helper itself)
├── quickstart.md        # Phase 1 output (this run)
├── contracts/
│   └── echo_helper.md   # Phase 1 output — the echo() contract
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
src/
├── utils/
│   ├── __init__.py                 # Unchanged. `echo` is imported via full path, not re-exported.
│   ├── console.py                  # NEW. Contains `echo(msg, *args) -> None`.
│   ├── logger_utils.py             # Unchanged. `echo()` does not touch handler configuration.
│   └── ... (other existing utils)
├── auth/interactive/clouds.py      # MIGRATED. 1 site.
└── reports/
    ├── e911_bssid.py                                  # MIGRATED. 27 sites.
    ├── offline_device_reporter.py                     # MIGRATED. 22 sites.
    ├── global_wired_client_report_generator.py        # MIGRATED. 14 sites.
    ├── wired_client_manufacturer_report_generator.py  # MIGRATED.  8 sites.
    └── sfp_transceiver_data_processor.py              # MIGRATED.  3 sites.

MistHelper.py                                          # MIGRATED. 95 sites.

tests/
└── unit/
    └── utils/
        └── test_console.py         # NEW. ~120 lines. Covers all four FR-015 cases.
```

**Structure Decision**: Helper lives at `src/utils/console.py`. Chosen because:

- The repo already uses `src/utils/` for cross-cutting primitives (`logger_utils`, `input_utils`, `subprocess_runner`, `tqdm_wrapper`, `environment_utils`). `console.py` fits that convention exactly.
- Naming `console` (not `echo` or `output`) matches the domain word used in the spec ("legacy console echo") and does not collide with any existing module.
- Placing it in a new module keeps the diff minimal and the helper trivially discoverable.
- Every migrated file imports from the same path: `from src.utils.console import echo`. This satisfies FR-011.

Verified: no existing `src/utils/console.py` today; no existing `echo` symbol in `src/utils/`; the import path `src.utils.console` is unused.

Tests live under `tests/unit/utils/test_console.py`, matching the existing pattern in `tests/unit/utils/` (see `test_environment_utils.py`, `test_filter_operator_engine.py`).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| `echo()` is a module-level function, not a class method, so it is technically a "standalone function" under principle II. | The helper's job is to combine two stdlib primitives (`print`, `logger.info`) into one call so 170 sites can migrate mechanically. It has no state, no configuration, no lifecycle. It is not a wrapper of a domain class — there is no domain class to wrap. Adding a `Console` class with a single classmethod would be ceremony without ownership: it would still have to be imported and called at 170 sites, and each site would read `Console.echo(...)` instead of `echo(...)` with no semantic gain. | A `Console` class holding one method is exactly the "wrapper that merely delegates" pattern principle II prohibits. A module-level primitive is the honest shape. |

## Phase 0: Outline & Research

See [research.md](./research.md). Highlights:

- Decision: `%`-style formatting. Rationale: the 170 legacy calls all use `logging.warning("%s: %s", key, description)` form. Preserving `%`-style means the migration is a single-token substitution (`logging.warning` -> `echo`) with no argument reshaping. Converting to f-strings would force per-site edits, violate FR-012 ("no reordering, no message text edits, no arg reordering"), and lose the "one formatting attempt on args, none on the literal when args is empty" behavior needed for FR-005.
- Decision: stdout, not stderr. Rationale: today's legacy behavior uses the root logger's console handler, which writes to stdout for MistHelper. Preserving stdout keeps SC-003 (byte-identical stdout diff) achievable without touching any user's redirection habits. Spec confirms this in the Edge Cases section.
- Decision: named module-level logger via `logging.getLogger(__name__)`, not the root logger. Rationale: greppability (an operator can filter `console:` records if needed) and consistency with the rest of `src/utils/`. The record still propagates to the root logger's handlers per default Python `logging` semantics, so file-handler capture is preserved.
- Decision: mechanical rewrite via a one-off migration script (kept under `scripts/` or run inline during the implement phase and then deleted). The tool matches the exact trailing string `# Legacy console echo routed via logger.` and the multi-line-call variant where the marker rides on the closing `)` line. Both variants exist in the tree today (verified in `MistHelper.py` near line 2504 for same-line, and near the `msp_privileges` block for closing-paren-line).
- Decision: on any unmigrated marker after the rewrite pass, fail loudly. The final gate is `grep -R "Legacy console echo routed via logger." src MistHelper.py` returning zero matches (SC-001). Any residual is a bug in the rewrite tool and must be fixed before merge.

## Phase 1: Design & Contracts

### Data Model

No data-model artifact is created for this feature. The refactor introduces no persisted entities, no schema, and no state beyond the transient stdout stream and the append-only `data/script.log`. The one "entity" — the `echo()` helper — is fully specified by its contract (see below). Recording it in a data-model file would duplicate the contract without adding information.

### Contracts

See [contracts/echo_helper.md](./contracts/echo_helper.md). Defines:

- Signature: `def echo(msg: str, *args: object) -> None`.
- Effect 1: writes `msg % args if args else msg` to `sys.stdout` followed by a newline.
- Effect 2: emits one log record at level `logging.INFO` on `logging.getLogger("src.utils.console")` (or the resolved `__name__` equivalent) using `%s`-style deferred formatting (`logger.info(msg, *args)`).
- Non-effect: never emits at `WARNING`. Never touches handler configuration. Never raises on a literal string containing `%` when `args` is empty.
- Idempotence: multiple imports do not add handlers. `echo()` calls `logger.info(...)` on the shared logger; no handler is attached inside `console.py`.

### Quickstart

See [quickstart.md](./quickstart.md). Runnable validation walk-through covering:

- Install / run MistHelper end-to-end before the change; record stdout capture and `data/script.log`.
- Land the change; re-run the same scripted session.
- Diff the two stdout captures (must be empty — SC-003).
- Grep the two log files for `WARNING -` (before: thousands; after: small bounded count — SC-004).
- Grep the tree for the marker string (must be zero — SC-001).

### Agent Context Update

Ran the agent-context update script conceptually: this plan adds one line to the "Active Technologies" section of `CLAUDE.md` naming the feature (`1031-warning-echo-refactor`) and the new module (`src/utils/console.py`). No new external dependency is introduced, so the "Primary Dependencies" line does not change. This update is performed as part of the `/speckit.tasks` and `/speckit.implement` phases per the standard flow.

## Post-Design Constitution Re-Check

PASS. The design does not introduce any new class, dependency, destructive operation, or handler configuration change. Principle II is the only recorded justification and its rationale is unchanged after design.

## Done

- [x] Technical Context filled with no NEEDS CLARIFICATION.
- [x] Constitution Check completed with one recorded justification under principle II.
- [x] Phase 0 research consolidated in `research.md`.
- [x] Phase 1 contracts defined in `contracts/echo_helper.md`.
- [x] Phase 1 quickstart validation guide written in `quickstart.md`.
- [x] Post-design constitution re-check completed (PASS).

Ready for `/speckit.tasks`.
