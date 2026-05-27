# Research: Main decomposition wave 2 (serial)

## Decision 1: Keep strict serial decomposition gates (one phase active at a time)
- **Decision**: Enforce phase-by-phase hard gate with no overlap.
- **Rationale**: Minimizes blast radius and aligns with spec FR-003/FR-004 and SC-001..SC-004.
- **Alternatives considered**:
  - Parallel phase execution: rejected due to high merge/coupling risk on `MistHelper.py` hot zones.
  - Two-phase batching: rejected because it weakens rollback granularity.

## Decision 2: Use class-preserving extraction to semantically aligned `src/` modules
- **Decision**: Keep class names stable while moving implementations to `src/analytics`, `src/export`, `src/gateway`, `src/site`, `src/troubleshooting`, `src/websocket`, `src/capture`, and `src/inventory`.
- **Rationale**: Preserves behavior and reduces call-site churn; supports incremental gate validation.
- **Alternatives considered**:
  - Full redesign to function-based services: rejected (too risky, violates no-wrapper/no-scope-expansion intent).
  - Single mega-module in `src/`: rejected (would recreate monolith, fails maintainability goals).

## Decision 3: Enforce one-way dependency direction and import-cycle checks per phase
- **Decision**: `MistHelper.py` as orchestration only; extracted modules cannot import entrypoint/menu internals.
- **Rationale**: Directly addresses RC-001..RC-004 and prevents circular imports.
- **Alternatives considered**:
  - Soft convention without automated checks: rejected (insufficient for hard-gate process).

## Decision 4: Per-phase parity strategy uses targeted tests + smoke checks + standard quality commands
- **Decision**: For each phase, add/update module tests and menu smoke checks, then run syntax/lint/format/test gate commands.
- **Rationale**: Keeps phase feedback fast while preserving parity guarantees for CSV/SQLite/polyglot paths.
- **Alternatives considered**:
  - Full end-to-end after every commit: rejected as too slow for nine gates.

## Decision 5: Terminal documentation synchronization as post-phase-9 completion gate
- **Decision**: Add dedicated final phase for README, CHANGELOG, mermaid/architecture docs, and wiki synchronization with checklist verification.
- **Rationale**: Implements FIN-001..FIN-004 and prevents architecture drift.
- **Alternatives considered**:
  - Continuous doc edits during each phase only: rejected; risks incomplete cross-doc consistency.

## Clarifications resolved
- No unresolved technical clarifications remain.
- `GlobalImportManager` remains explicitly out of scope.
- Existing partial extraction (`src/capture/packet_capture.py`) will be completed in Phase 9 with single-source ownership.
