# Tasks: Compliance analyzer parallel jobs

**Input**: `specs/2428-parallel-compliance-analyzer/spec.md`

**Prerequisites**: Measurement notes in the session workspace and issue #2428.

## Phase 1: Specification and branch

- [x] T001 Create GitHub issue #2428 for the measured performance feature.
- [x] T002 Create branch `feat/2428-parallel-compliance-analyzer` from `origin/main`.
- [x] T003 Add SpecKit artifacts under `specs/2428-parallel-compliance-analyzer/`.

## Phase 2: Analyzer implementation

- [x] T004 Add `jobs` to `ComplianceAnalyzer.analyze_targets`.
- [x] T005 Add bounded worker-count resolution.
- [x] T006 Add importable batch worker support with explicit `spawn`.
- [x] T007 Preserve the sequential path for default and small scans.

## Phase 3: CLI implementation

- [x] T008 Add `-j` and `--jobs` to the CLI.
- [x] T009 Forward the parsed worker count to the analyzer.

## Phase 4: Tests

- [x] T010 Add sequential and parallel report parity coverage.
- [x] T011 Add output order coverage.
- [x] T012 Add small-input fallback coverage.
- [x] T013 Add parse-error and missing-file failure coverage.
- [x] T014 Add CLI argument forwarding coverage.

## Phase 5: Validation

- [x] T015 Run targeted pytest.
- [x] T016 Run lint, format, compile, and type checks.
- [x] T017 Run sequential and parallel report content comparison.
- [x] T018 Record the final speed and correctness evidence in the pull request.
