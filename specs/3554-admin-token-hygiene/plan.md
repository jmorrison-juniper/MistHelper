# Implementation Plan: Admin Token Hygiene

**Branch**: `3554-admin-token-hygiene` | **Date**: 2026-09-29 | **Spec**: `specs/3554-admin-token-hygiene/spec.md`

**Input**: Feature specification from `specs/3554-admin-token-hygiene/spec.md`

## Summary

Add menu 273 as a read-only admin and organization API token hygiene report.
The implementation will add `src/mist/intelligence/reports/admin_token_hygiene/` with a client,
models, and an operation class. The operation will fetch administrators,
organization API tokens, and organization settings with the installed `mistapi`
SDK, score hygiene findings, and write `data/AdminHygiene.csv` and
`data/TokenHygiene.csv`. The operation will never write token keys to logs,
console output, or report files. Menu wiring is deferred to
`specs/3554-admin-token-hygiene/wiring.md`.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: `mistapi>=0.64.0,<0.65`, standard library
`dataclasses`, `datetime`, `logging`, `os`, and existing MistHelper helpers.

**Storage**: CSV files under `data/` through
`DataExporter.write_with_format_selection()`. Multi-backend output must stay
available for the two hygiene row sets.

**Testing**: `pytest` unit tests under
`tests/unit/reports/admin_token_hygiene/`. Add a token redaction test that
proves token keys never reach logs or output files.

**Target Platform**: Windows local development, Linux container runtime, and
SSH container sessions.

**Project Type**: Single Python CLI application with menu-driven operations.

**Performance Goals**: Complete in less than 30 seconds for a normal
organization when the Mist API responds normally. Keep one row per
administrator and one row per organization token.

**Constraints**: Read-only Mist API access only. No prompts in `--test`.
Default `TOKEN_IDLE_DAYS` is `90`. If `TOKEN_IDLE_DAYS` is invalid, log a clear
error and use the default only when repository patterns allow that fallback.
Never write token keys to logs, console output, files, or exceptions.

**Scale/Scope**: One organization per run. The operation reads
`listOrgAdmins`, `listOrgApiTokens`, and `getOrgSettings`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
| - | - | - |
| Five-Item Rule | PASS | New code enters the nested package `src/mist/intelligence/reports/admin_token_hygiene/`, with four module files and no new direct child under `src/`. |
| Class-Based Architecture | PASS | The design uses classes in `client.py`, `model.py`, and `operation.py`. It adds no wrapper functions. |
| Safety-First | PASS | The operation is read-only, needs no prompt, and redacts token keys at the model boundary. |
| Full Deployment Pipeline | PASS | This step creates planning artifacts only. Implementation tasks must run local gates before commit. |
| Observability and Logging | PASS | The design requires `info` before actions and `debug` summaries after actions, with no secrets. |
| Inline Comments | PASS | Implementation tasks must add inline comments on AI-generated executable lines. |
| Action Logging | PASS | Implementation tasks must log each API read, transform, and export. |
| Technology and Compatibility | PASS | The installed SDK has the required functions. No direct Mist HTTP call is needed. |
| Output Backends | PASS | The reports must use `DataExporter.write_with_format_selection()`. |
| Database Keys | PASS | Record primary key strategy entries in `wiring.md` before implementation. Use `row_id` for admin rows, and `id` for token rows. |

No violation needs a waiver.

## Project Structure

### Documentation (this feature)

```text
specs/3554-admin-token-hygiene/
+-- plan.md
+-- research.md
+-- data-model.md
+-- quickstart.md
+-- wiring.md
+-- contracts/
|   +-- hygiene-report.md
+-- tasks.md
```

### Source Code (implementation target)

```text
src/
+-- reports/
    +-- admin_token_hygiene/
        +-- __init__.py
        +-- client.py
        +-- model.py
        +-- operation.py

tests/
+-- unit/
    +-- reports/
        +-- admin_token_hygiene/
            +-- test_client.py
            +-- test_model.py
            +-- test_operation.py
            +-- test_redaction.py

data/
+-- AdminHygiene.csv
+-- TokenHygiene.csv
```

**Structure Decision**: Use a new nested report package because the direct
`src/` hierarchy is already broad. Keep menu wiring out of source files during
this planning step. Document the later wiring in `wiring.md`.

## Complexity Tracking

No constitution violation is present.

## Phase 0 Research Summary

Research is complete in `research.md`.

Resolved decisions:

1. Use the installed `mistapi` functions for all three Mist API reads.
2. Reuse the existing exporter pattern from menu 47 and menu 48 for populated
   rows, and write header-only CSV files when source data is empty.
3. Use `SourceDependencyResolver.apisession` and the existing organization ID
   resolver inside the operation package.
4. Treat token keys as forbidden data at the model boundary.
5. Use `TOKEN_IDLE_DAYS=90` as the default idle threshold.

## Phase 1 Design Summary

Design artifacts are complete.

- `data-model.md` defines source payloads, report rows, findings, and summary.
- `contracts/hygiene-report.md` defines CSV columns, console summary, and
  redaction rules.
- `quickstart.md` defines validation scenarios and expected results.
- `wiring.md` defines the deferred menu, registry, README, test, and release
  note integration contract.

## Risk Controls

| Risk | Control |
| - | - |
| Token key exposure | Drop `key` before logging, scoring, output, and exceptions. Add a unit test with a sentinel key. |
| Missing optional API fields | Keep the row and write `unknown` or a blank value per the contract. |
| Conflicting role scope data | Score the highest effective privilege, because Mist applies the highest privilege when API-created scopes conflict. |
| Invalid idle threshold | Validate `TOKEN_IDLE_DAYS` at startup and report the problem explicitly. |
| Menu wiring drift | Keep the wiring checklist in `wiring.md` until the integration pull request applies shared file changes. |

## Post-Design Constitution Check

| Principle | Status | Evidence |
| - | - | - |
| Five-Item Rule | PASS | The design adds one nested package and four module files. |
| Class-Based Architecture | PASS | The data model and operation design use classes. |
| Safety-First | PASS | The feature is read-only and redacts secrets. |
| Output Backends | PASS | The contract requires `DataExporter.write_with_format_selection()`. |
| Database Keys | PASS | The wiring manifest names required primary key strategy entries for the integration pull request. |

No unresolved clarification remains.
