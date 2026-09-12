# Implementation Plan: `--testinteractive` Reliability Defects

**Branch**: `1021-testinteractive-reliability-defects` (planning identifier only; do not create it in this workflow) | **Date**: 2026-07-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/1021-testinteractive-reliability-defects/spec.md`

## Summary

Correct the reliability signals of the existing `--testinteractive` CLI harness without broad refactoring. The work is a **single serial workstream** comprising six existing GitHub issues: make handler-originated error logs fail telemetry, fail closed on a non-exact site selector, expose meaningful site/cancellation context, use the installed WAN SDK namespace, reject the unsupported hyphenated flag clearly, and parse help before dependency initialization. Each issue adds its own regression tests; the specification's Story 7 is a cross-cutting completion criterion, not a seventh issue or PR.

This planning session creates only local SpecKit documentation. It does not create branches, commits, issues, PRs, remote changes, application-source changes, test changes, or configuration changes.

## Technical Context

**Language/Version**: Python 3.13+ (`pyproject.toml` requires `>=3.13`)

**Primary Dependencies**: Standard-library `argparse`, `logging`, and `inspect`; `mistapi>=0.63.1` (the verified installed surface is `0.63.3`)

**Storage**: Local append-only JSONL telemetry only; future interactive-test artifacts must remain under an explicitly controlled `data/` subdirectory. No remote persistence or mutations.

**Testing**: `pytest`; focused runner, telemetry-emitter, entrypoint, and WAN-exporter unit tests with `MagicMock`/stubbed Mist SDK objects. Optional smoke tests are read-only and run only after focused tests pass.

**Target Platform**: Windows 11 development and Linux/Podman runtime; all paths remain platform-neutral.

**Project Type**: Python CLI/network-operations application with local telemetry files.

**Performance Goals**: Preserve the current one-pass, ordered interactive-safe operation loop; added per-operation observation must be bounded to the duration of that invocation and must not add network calls.

**Constraints**: Exact selector matching only when `MIST_INTERACTIVE_TEST_SITE` is supplied; no silent substitution; Mist API verification is read-only; mock-first tests; no new dependencies; no unrelated registry/handler migration; preserve supported `--testinteractive`; `--help` and `-h` must exit before dependency/import initialization.

**Scale/Scope**: Six independently merged fixes, in issue order `#1636` through `#1641`; current registry count is approximately 44 interactive-safe operations, but behavior must not depend on that number remaining fixed.

## Constitution Check

### Pre-Research Gate — PASS

| Principle / gate | Plan compliance |
|---|---|
| Five-Item Rule | Future implementation keeps small, semantically grouped outcome/context value objects; functions retain the existing class-based seams and must stay within the documented limits. |
| Class-Based Architecture | Extend `InteractiveTestRunner`, `TelemetryEmitter`, `InputUtils`, `MainEntrypoint`, and `WanClientEventsExporter` only where necessary; do not add wrapper functions. |
| Safety-First | A supplied unmatched selector fails before any operation runs; no credentials are added to output; read-only remote policy is explicit. |
| Full Deployment Pipeline | Not applicable to this planning-only session. Each future code PR must run required local quality gates and follow the repository's PR/merge process before the next serial issue starts. |
| Observability / Logging | The telemetry correction is based on scoped `ERROR` records, and implementation must preserve ASCII, pre/post action logging, and secret redaction. |
| Inline Comments / Action Logging | Mandatory for every changed implementation line/block in future work; tests must assert behavior rather than relying on log formatting alone. |
| Multi-Agent Git Workflow | No remote GitHub action occurs now. Future branches start from updated `main`, are one issue per PR, are non-stacked, and are merged before the next issue begins. |

**Gate result**: PASS. No principle violation is required by the design.

## Serial Delivery and Issue Mapping

| Order | GitHub issue | Spec story | Planned branch / PR rule | Scope and merge gate |
|---:|---:|---|---|---|
| 1 | #1636 — telemetry false-pass semantics | P1; Story 1 | Fresh `fix/1636-interactive-telemetry` from current `main`; one PR targeting `main` | Capture handler-scoped `ERROR` records, emit a distinguishable outcome/count, return non-zero on operation errors, add regressions; validate and squash-merge before #1637. |
| 2 | #1637 — selector fallback | P2; Story 2 | Fresh `fix/1637-interactive-selector-fallback` from the **merged** `main` | Fail closed on a supplied selector that does not exactly match id/full name; report requested and resolved target when applicable; add regressions; validate and merge before #1638. |
| 3 | #1638 — meaningful site context | P3; Story 3 | Fresh `fix/1638-interactive-site-context` from the **merged** `main` | Report injected versus unavailable site context and structured prompt cancellation distinctly; add regressions; validate and merge before #1639. |
| 4 | #1639 — WAN SDK namespace | P4; Story 4 | Fresh `fix/1639-wan-sdk-namespace` from the **merged** `main` | Replace only the obsolete nested endpoint path with the verified installed SDK callable; add mock SDK regression; validate and merge before #1640. |
| 5 | #1640 — unsupported flag UX | P5; Story 5 | Fresh `fix/1640-unsupported-test-flag` from the **merged** `main` | Reject `--test-interactive` with an actionable suggestion; keep `--testinteractive` as the supported spelling; add parser/entrypoint regression; validate and merge before #1641. |
| 6 | #1641 — side-effect-free help | P6; Story 6 | Fresh `fix/1641-side-effect-free-help` from the **merged** `main` | Parse help before deferred imports/dependency setup, including `-h` and combined flags; add ordering regressions; validate and merge. |

**Serial-workstream controls**

1. No branch may be created from another issue branch. Before every future issue, update local `main` only after the prior PR has passed required checks and been squash-merged.
2. Do not open a later PR while the current issue is unmerged. This prevents the hot `MistHelper.py` and runner files from becoming a stacked series.
3. Every issue includes the regression tests that prove its behavior. Story 7 is satisfied cumulatively by those tests; do not create a separate issue, branch, or PR for it.
4. During this planning session, remote GitHub and Mist state are read-only: no branch/PR/issue/commit/push/merge or Mist write call. In future validation, use mocks by default and only explicitly read-only Mist API calls for an optional smoke check.
5. Local telemetry/log artifacts are isolated under the controlled `data/` test-artifact location and must be removed or retained according to the existing retention policy; never write outside `data/`.

## Research Decisions

Research is recorded in [research.md](research.md). The chosen design is:

- scoped `ERROR`-record capture around one handler invocation rather than classifying a normal return as success unconditionally;
- fail closed when an explicitly supplied selector has no exact id/full-name match, leaving the existing no-selector behavior out of scope;
- use structured outcome/context metadata and an explicit safe-input cancellation observation, not inference from blank returns or free-form log text;
- call the direct `sites.wan_clients.searchSiteWanClientEvents` SDK member verified for `mistapi==0.63.3`;
- reject rather than alias `--test-interactive`, preserving future CLI namespace flexibility;
- parse `--help`/`-h` before deferred imports, while preserving the normal entrypoint sequence for non-help invocation.

## Project Structure

### Documentation (this feature)

```text
specs/1021-testinteractive-reliability-defects/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── interactive-test-telemetry.md
    └── cli-invocation.md
```

### Future implementation surfaces

```text
MistHelper.py                                  # Parser registration and mode dispatch
src/
├── analytics/telemetry_emitter.py             # JSONL operation/summary event emission
├── dataclasses/progress_event.py              # Typed summary/context value objects
├── export/wan_client_events_exporter.py       # Option 203 SDK callable
├── refactors/main_entrypoint.py               # Dependency initialization ordering
├── troubleshooting/interactive_test_runner.py # Selector, invocation, outcome summary
└── utils/input_utils.py                       # Explicit EOF/interrupt observation seam
tests/
├── unit/analytics/test_telemetry_emitter.py
├── unit/refactors/test_main_entrypoint.py
├── unit/troubleshooting/test_interactive_test_runner.py
└── unit/                                    # Existing/new focused WAN and parser tests
```

**Structure Decision**: Keep the present single Python CLI layout. The six fixes touch only the named existing seams and their focused tests; there is no new service, database, package, menu operation, or external dependency.

## Post-Design Constitution Check

**Result: PASS.** The data model groups execution context, observations, and counts so future code can remain within the Five-Item Rule. The contracts require operator-visible error/context outcomes, controlled local artifacts, exact selector safety, and mock-first/read-only validation. No new wrapper, storage backend, remote mutation, or unrelated refactor is introduced.

## Complexity Tracking

No constitution violation requires justification.
