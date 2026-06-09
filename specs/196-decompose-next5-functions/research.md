# Research: Decompose Next 5 High-Complexity Functions

## Decision 1: Use compatibility facades in `MistHelper.py` with extracted class-owned logic in `src/`

- **Decision**: Keep original function entrypoints callable in `MistHelper.py` and migrate branch-heavy internals into domain classes under `src/`.
- **Rationale**: This minimizes regression risk while allowing incremental rollout and rollback per target.
- **Alternatives considered**:
  - Big-bang full rewrite in `MistHelper.py` (rejected: high blast radius).
  - Immediate entrypoint relocation without facades (rejected: breaks operator and automation compatibility).

## Decision 2: Split multi-AP scan capture orchestration into dedicated capture workflow

- **Decision**: Extract `_start_site_scan_capture_all_aps` into `src/capture/multi_ap_scan_workflow.py` (`MultiApScanCaptureWorkflow`).
- **Rationale**: Current logic combines AP discovery, parameter gathering, payload assembly, API execution, and result routing in one body.
- **Alternatives considered**:
  - Keep logic in `packet_capture.py` with helper methods only (rejected: keeps orchestration complexity concentrated).

## Decision 3: Separate site and org wait/download workflows instead of one generic implementation

- **Decision**: Implement `SitePcapWaitDownloadWorkflow` and `OrgPcapWaitDownloadWorkflow` as sibling modules.
- **Rationale**: Site and org APIs share pattern but diverge in endpoint semantics and failure surfaces; separate classes reduce condition explosion.
- **Alternatives considered**:
  - Single generic workflow with many mode flags (rejected: recreates complexity through branching).

## Decision 4: Introduce Wi-Fi client exporter boundary under `src/export/`

- **Decision**: Move `wifi_clients` orchestration into `src/export/wifi_clients_exporter.py`.
- **Rationale**: Function currently mixes selection, retrieval, shaping, and output concerns; exporter boundary improves testability and schema guardrails.
- **Alternatives considered**:
  - Keep static function and extract only utility helpers (rejected: weak ownership and persistent monolith coupling).

## Decision 5: Introduce interactive test runner boundary under `src/troubleshooting/`

- **Decision**: Move `run_interactive_test` logic into `src/troubleshooting/interactive_test_runner.py`.
- **Rationale**: Prompt/dispatch/failure paths are easier to validate when isolated from global script context.
- **Alternatives considered**:
  - Keep all branching in one global function (rejected: persistent high complexity and weak unit-test isolation).

## Decision 6: Treat inline comments and action logging as explicit implementation gates

- **Decision**: Add explicit quality constraints that every touched executable line includes intent comments and every meaningful action has before/after logs.
- **Rationale**: Constitution v1.4.0 marks these as non-negotiable and they directly support maintainability and incident diagnostics.
- **Alternatives considered**:
  - Rely on reviewer discretion only (rejected: inconsistent enforcement).

## Decision 7: Validation stack combines complexity, quality, and parity evidence

- **Decision**: Require VC-001 through VC-007 completion, with mapping evidence from original functions to extracted classes/tests.
- **Rationale**: Complexity reduction alone does not guarantee behavioral parity or operational safety.
- **Alternatives considered**:
  - Complexity-only signoff (rejected: can hide behavior drift).
  - Test-only signoff (rejected: does not guarantee maintainability goals).

## Unknowns Resolution Summary

All technical-context placeholders are resolved. No `NEEDS CLARIFICATION` items remain for planning.
