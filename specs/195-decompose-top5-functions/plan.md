# Implementation Plan: Decompose Top-5 Complex Functions to CC <= 10

**Branch**: `feat/194-capture-bootstrap-session-refactor` | **Date**: 2026-06-01 | **Spec**: `specs/195-decompose-top5-functions/spec.md`
**Input**: Feature specification from `specs/195-decompose-top5-functions/spec.md`

## Summary

Refactor the five highest-complexity targets in `MistHelper.py` into cohesive modules under `src/` while preserving menu/CLI behavior and operator-facing outputs. The implementation uses an incremental strangler pattern: keep existing entrypoints in `MistHelper.py` as compatibility facades, move decision-heavy logic into extracted classes, and enforce completion only when each target responsibility boundary is at cyclomatic complexity <= 10 with parity tests and quality gates passing.

Baseline complexity snapshot (captured 2026-06-01):

| Target | Location | Baseline CC | Baseline Rank |
| - | - | -: | - |
| `_early_dependency_check` | `MistHelper.py:528` | 49 | F |
| `_execute_site_capture_loop` | `MistHelper.py:7336` | 30 | D |
| `start_org_packet_capture` | `MistHelper.py:7646` | 53 | F |
| `device_events_52w` | `MistHelper.py:12171` | 38 | E |
| `with_wan_overrides` (legacy body) | `MistHelper.py:19454` | 46 | F |

Note: `with_wan_overrides` has a second delegating definition at `MistHelper.py:20048` with CC=1; legacy duplication cleanup is part of this wave.

## Technical Context

**Language/Version**: Python 3.13+  
**Primary Dependencies**: `mistapi>=0.59`, `requests`, `python-dotenv`, `ruff`, `black`, `radon`, existing `src/*` extracted modules  
**Storage**: CSV and SQLite outputs under `data/` (plus optional ArangoDB/Redis via existing exporter paths)  
**Testing**: Existing project test harness (`python MistHelper.py --test`) + targeted unit/integration tests in `tests/` + radon complexity checks  
**Target Platform**: Windows dev + Linux container runtime (Podman primary)  
**Project Type**: Monolithic CLI/menu tool with progressive modular extraction (`MistHelper.py` + `src/`)  
**Performance Goals**: No regression in user-visible flow; API call count for WAN overrides must not increase; streaming/event export must remain memory-safe for 52-week windows  
**Constraints**: Preserve menu IDs/labels/invocation semantics; preserve prompt text and output schema; keep sensitive logging controls; maintain compatibility with existing automation  
**Scale/Scope**: 5 target functions, multi-file extraction under `src/`, regression coverage across packet capture, gateway overrides, bootstrap dependency checks, and long-range device events export

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Pre-design gate evaluation:

| Gate | Status | Notes |
| - | - | - |
| Five-Item Rule discipline | PASS | New logic is split into focused classes/modules; no new giant functions planned. |
| Class-based architecture (no thin wrappers) | PASS | Facades in `MistHelper.py` remain orchestration/compatibility only; core logic moved to extracted classes with real behavior. |
| Safety-first input handling | PASS | Existing `InputUtils.safe_input` pattern remains mandatory in extracted interactive flows. |
| Inline comments/action logging standards | PASS | Implementation tasks require updating touched blocks to meet policy. |
| Security/logging constraints | PASS | No secrets in logs; retain sanitizer path and redaction behavior. |
| Full quality gates | PASS | Plan includes radon + py_compile + ruff + black + test suite gates. |

Post-design re-check: **PASS** (no conflicts introduced by proposed module boundaries or migration sequencing).

## Project Structure

### Documentation (this feature)

```text
specs/195-decompose-top5-functions/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── compatibility-contract.md
└── tasks.md  # generated later by /speckit.tasks
```

### Source Code (repository root)

```text
MistHelper.py
src/
├── bootstrap/
│   ├── dependency_check.py
│   ├── package_installer.py
│   └── uv_runtime.py
├── capture/
│   ├── org_capture_workflow.py
│   ├── site_capture_loop.py
│   └── packet_capture.py
├── export/
│   └── device_events_52w_exporter.py
└── gateway/
    ├── gateway_override_analysis.py
    └── gateway_export_utils.py

tests/
├── unit/
│   ├── test_dependency_check.py
│   ├── test_site_capture_loop.py
│   ├── test_org_capture_workflow.py
│   ├── test_gateway_override_analysis.py
│   └── test_device_events_52w_exporter.py
└── integration/
    └── test_top5_compatibility_paths.py
```

**Structure Decision**: single-project Python CLI with incremental extraction. New logic is placed in existing domain directories (`src/capture`, `src/gateway`, `src/export`) and one new bounded `src/bootstrap` package for dependency bootstrap orchestration.

## Architecture & Module Boundaries

### Decision 1: Bootstrap dependency logic extraction (`_early_dependency_check`)

- **Current pain**: one function mixes requirement parsing, uv discovery, installs/upgrades, fallback logic, and retry/error policy.
- **New boundaries**:
  - `src/bootstrap/dependency_check.py`: orchestration class `DependencyCheckOrchestrator` (entrypoint used by `MistHelper.py`).
  - `src/bootstrap/package_installer.py`: install/upgrade strategies (`uv` then `pip`, per-package fallback).
  - `src/bootstrap/uv_runtime.py`: `uv` detection/install/version check helpers.
- **Entry compatibility**: keep `_early_dependency_check()` in `MistHelper.py` as a compatibility facade that delegates to `DependencyCheckOrchestrator.run()`.

### Decision 2: Packet capture organization workflow extraction (`start_org_packet_capture`)

- **Current pain**: mixed UI prompts, API fetches, selection logic, payload build, confirmation, and execution.
- **New boundaries**:
  - `src/capture/org_capture_workflow.py`: class `OrgCaptureWorkflow` with methods for MxEdge discovery, selection, interface resolution, payload build, and confirmation.
  - `src/capture/packet_capture.py`: `PacketCaptureManager.start_org_packet_capture()` reduced to orchestration calls only.
- **Entry compatibility**: menu operation remains unchanged; same call path to `PacketCaptureManager.start_org_packet_capture()`.

### Decision 3: Site capture loop decomposition (`_execute_site_capture_loop`)

- **Current pain**: infinite-loop orchestration contains fetch, download, readiness checks, capture start, sleep policy, and interruption handling.
- **New boundaries**:
  - `src/capture/site_capture_loop.py`: class `SiteCaptureLoopRunner` with explicit stages: `fetch_completed`, `download_new`, `maybe_start_capture`, `compute_sleep`, `handle_interrupt`.
  - `src/capture/packet_capture.py`: retains thin orchestration method that wires dependencies and invokes the runner.

### Decision 4: Gateway WAN overrides analysis extraction (`with_wan_overrides`)

- **Current pain**: CSV bootstrap/cache generation, lookup materialization, multi-pass API strategy, fast-mode concurrency, and report synthesis in one body.
- **New boundaries**:
  - `src/gateway/gateway_override_analysis.py`: class `GatewayOverrideAnalyzer` responsible for end-to-end analysis/report generation.
  - `src/gateway/gateway_export_utils.py`: keep public method `with_wan_overrides()` delegating to analyzer.
- **Migration cleanup**: remove legacy duplicate body from `MistHelper.py` once delegation is fully validated.

### Decision 5: 52-week device events streaming export extraction (`device_events_52w`)

- **Current pain**: checkpointing, pagination, retry/backoff, CSV/SQLite split, and header synthesis are tightly coupled.
- **New boundaries**:
  - `src/export/device_events_52w_exporter.py`: class `DeviceEvents52wExporter` encapsulating fetch-page, preload-header, stream-append, checkpoint lifecycle.
  - `MistHelper.py` `OrgAlarmEventExporter.device_events_52w()` becomes stable facade.

## Migration Strategy (Strangler Pattern)

1. **Introduce extracted modules first** with no behavior change; wire behind existing facades.
2. **Dual-path verification** where practical (legacy vs extracted path output equivalence on sampled datasets).
3. **Flip default to extracted classes** once parity tests pass for each target.
4. **Delete legacy heavy bodies** (especially duplicate `with_wan_overrides` legacy block) only after green regression gates.
5. **Stabilize interfaces**: keep menu IDs, prompt strings, filename conventions, and API function names unchanged.

Rollback strategy:

- Keep legacy-compatible facades during wave implementation.
- If a regression appears, switch facade back to legacy implementation for the affected target only.
- Do not remove compatibility facades in same commit as major extraction to keep rollback atomic.

## Implementation Phases

### Phase 0: Research & proof decisions

- Confirm exact behavior invariants per target (prompts, files, side effects, retry semantics).
- Confirm existing extracted modules to reuse (`src/capture/packet_capture.py`, `src/gateway/gateway_export_utils.py`).
- Produce `research.md` with final architecture decisions and alternatives.

### Phase 1: Design artifacts & contracts

- Produce `data-model.md` for refactor entities and lifecycle states.
- Produce compatibility contract under `contracts/`.
- Produce operator/developer execution flow in `quickstart.md`.

### Phase 2: Autonomous implementation sequence (for `/speckit.implement`)

1. Implement `src/bootstrap/*` and wire `_early_dependency_check` facade.
2. Implement `src/capture/org_capture_workflow.py`; reduce `start_org_packet_capture` CC to <=10.
3. Implement `src/capture/site_capture_loop.py`; reduce `_execute_site_capture_loop` CC to <=10.
4. Implement `src/export/device_events_52w_exporter.py`; reduce `device_events_52w` facade CC to <=10.
5. Implement `src/gateway/gateway_override_analysis.py`; remove legacy duplicate `with_wan_overrides` body; keep delegated interface.
6. Add/adjust unit + integration parity tests.
7. Run full validation gates and capture evidence artifacts.

## Testing Strategy

### Unit tests (module-level)

- `test_dependency_check.py`: requirement parsing, uv discovery fallback, pip fallback, retry/backoff behavior.
- `test_org_capture_workflow.py`: MxEdge selection parsing, payload construction, validation branches.
- `test_site_capture_loop.py`: loop-stage sequencing, wait/sleep policy, conflict handling, keyboard interrupt exit path.
- `test_gateway_override_analysis.py`: override detection accuracy, API-call minimization path, report schema integrity.
- `test_device_events_52w_exporter.py`: checkpoint resume, header stabilization, streaming append to CSV/SQLite.

### Integration/parity tests

- `test_top5_compatibility_paths.py`: execute each target through existing menu/entry facade with controlled fixtures and assert:
  - prompt sequence compatibility,
  - expected output filenames/schemas,
  - side-effect compatibility,
  - error-path compatibility.

### Non-functional checks

- Validate no increase in API call count for WAN override fast path.
- Validate no secret leakage in logs from touched modules.

## Validation Gates (Explicit)

Required complexity gates:

- `python -m radon cc MistHelper.py -s -a`
- `python -m radon cc src -s -a`
- `python -m radon cc MistHelper.py src -s -a`

Acceptance rule: retained entrypoints for the five targets are `CC <= 10`.

Required project quality gates:

- `python -m py_compile MistHelper.py`
- `python -m ruff check MistHelper.py src`
- `python -m black --check MistHelper.py src`
- target parity/regression command set (minimum): `python MistHelper.py --test` plus targeted tests added in this wave.

Evidence required in implementation PR:

1. Baseline vs final CC table for all five targets.
2. Test run summary with parity tests called out.
3. Confirmation of unchanged menu IDs/labels/entry semantics.

## Risks & Controls

| Risk | Impact | Control |
| - | - | - |
| Prompt/flow drift during extraction | Operator confusion | Golden prompt snapshots in integration tests; facade-first migration. |
| Hidden side-effect changes | Runtime regressions | Dual-path comparisons and side-effect assertions. |
| Over-refactoring into thin wrappers | Maintainability illusion | Require extracted classes to own logic, validation, retries, and transformations. |
| Retry/timeout behavior changes | Operational instability | Explicit unit tests for retry counts/backoff and timeout boundaries. |
| Sensitive data leakage | Security/compliance issue | Preserve sanitizer path and add redaction assertions in touched logging paths. |

## Complexity Tracking

No constitution violations requiring exception are planned. Any temporary CC > 10 during intermediate commits is permitted only on non-release intermediate work and must be resolved before final validation.

## Final Implementation Summary (2026-06-01)

Completed outcomes:

1. Extracted bootstrap dependency orchestration into `src/bootstrap/` (`dependency_check.py`, `package_installer.py`, `uv_runtime.py`) and reduced `_early_dependency_check` facade complexity.
2. Extracted packet capture orchestration helpers into `src/capture/org_capture_workflow.py` and `src/capture/site_capture_loop.py`, wired via `src/capture/packet_capture.py` and compatibility facades.
3. Extracted 52-week device events export into `src/export/device_events_52w_exporter.py` and delegated `device_events_52w` entrypoint.
4. Kept gateway override analyzer in extracted module, added compatibility alias path `src/gateway/gateway_override_analysis.py`, and replaced legacy heavy MistHelper entry body with delegation.
5. Added targeted US1/US2/US3 tests and compatibility matrix assertions.

Post-refactor target CC status:

| Target | Final CC | Status |
| - | -: | - |
| `_early_dependency_check` | 1 | PASS |
| `_execute_site_capture_loop` | 1 | PASS |
| `start_org_packet_capture` | 1 | PASS |
| `device_events_52w` | 1 | PASS |
| `with_wan_overrides` | 1 | PASS |

Evidence links:

- `evidence/baseline_cc_report.md`
- `evidence/final_cc_report.md`
- `evidence/quality_gates.md`
- `evidence/test_results.md`
- `evidence/verification_bundle.md`
