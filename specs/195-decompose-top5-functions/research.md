# Research: Decompose Top-5 Complex Functions

## Decision 1: Use facade-preserving strangler migration from `MistHelper.py` to `src/`

- **Decision**: Keep existing public entrypoints in `MistHelper.py` and move deep logic into extracted classes under `src/`.
- **Rationale**: This preserves menu/CLI compatibility and allows rollback by toggling delegation without changing operator workflows.
- **Alternatives considered**:
  - Big-bang rewrite directly in `MistHelper.py` (rejected: high regression risk).
  - Immediate removal of legacy methods during extraction (rejected: weak rollback path).

## Decision 2: Introduce bounded bootstrap package for dependency checks

- **Decision**: Extract `_early_dependency_check` into `src/bootstrap/{dependency_check.py,package_installer.py,uv_runtime.py}`.
- **Rationale**: The function currently combines parsing, uv discovery, install strategy, retries, and policy decisions (CC 49).
- **Alternatives considered**:
  - Keep logic in `MistHelper.py` and only split helpers inline (rejected: still leaves monolith growth pressure).
  - Move into generic `src/utils/` (rejected: weak domain ownership).

## Decision 3: Split packet capture orchestration into org workflow + loop runner

- **Decision**: Add `src/capture/org_capture_workflow.py` and `src/capture/site_capture_loop.py` and call from `src/capture/packet_capture.py`.
- **Rationale**: `start_org_packet_capture` and `_execute_site_capture_loop` are orchestration-heavy and already partly represented in extracted capture modules.
- **Alternatives considered**:
  - Keep both methods entirely inside existing `packet_capture.py` and just add helpers (rejected: likely CC remains >10 and hard to test independently).

## Decision 4: Consolidate WAN override logic into dedicated analyzer module

- **Decision**: Create `src/gateway/gateway_override_analysis.py` and delegate from `GatewayExportUtils.with_wan_overrides`.
- **Rationale**: Existing logic is multiphase (cache bootstrap, filtering, API minimization, concurrency, report synthesis) and duplicated in `MistHelper.py`.
- **Alternatives considered**:
  - Keep only wrapper delegates with no analyzer class (rejected: thin-wrapper anti-pattern).
  - Leave duplicate legacy body permanently (rejected: maintainability and drift risk).

## Decision 5: Extract 52-week event export into streaming exporter class

- **Decision**: Create `src/export/device_events_52w_exporter.py` with explicit checkpoint + pagination lifecycle.
- **Rationale**: `device_events_52w` mixes transport, persistence, schema, and retry concerns (CC 38).
- **Alternatives considered**:
  - Retain method and add local nested helpers only (rejected: testability and ownership remain poor).

## Decision 6: Validation gate stack must include radon + existing project gates

- **Decision**: Require both complexity and existing quality commands before completion.
- **Rationale**: Feature success is defined by maintainability + parity, not only lint/test pass.
- **Alternatives considered**:
  - Lint/tests only (rejected: does not prove CC target).
  - Radon only (rejected: does not prove functional parity).

## Baseline Data Used

- `_early_dependency_check` CC=49 (F)
- `_execute_site_capture_loop` CC=30 (D)
- `start_org_packet_capture` CC=53 (F)
- `device_events_52w` CC=38 (E)
- `with_wan_overrides` legacy CC=46 (F)
- `with_wan_overrides` delegated duplicate CC=1 (A)

Captured via local radon AST walk on 2026-06-01.
