# Implementation Plan: Metric Refusal Terminal Status

**Branch**: `jmorrison-jnpr-fix/4031-partial-metric-failure` | **Date**:
2026-10-07 | **Spec**: [spec.md](spec.md)

**Input**: Issue #4031 and the existing feature specification.

## Summary

Menus 74 and 76 already continue after refused metric responses, exclude
refusal bodies, preserve valid rows, count valid rows, and report refusal
details. They still return without a log message that the existing portal
handled-error classifier recognizes. Add one post-batch `Failed to` marker to
each operation only when its refusal log is non-empty. Keep the existing
refusal report and export flow unchanged.

The implementation scope is explicit and limited to:

1. `src/operations/exporting/export/site_insights/site_metric_operation.py`
2. `src/operations/exporting/export/site_insights/device_metric_operation.py`
3. `tests/unit/export/site_insights/test_site_insight_path.py`
4. `tests/unit/export/site_insights/test_device_metric_refusals.py`
5. One `changelog.d/issue-4031-<slug>.md` fragment

Do not create `tasks.md`. Do not edit
`web_portal/services/operation.py`,
`src/operations/exporting/export/site_insights/metric_refusals.py`, or any
other product or test file.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: `mistapi>=0.64.0,<0.65`, existing
`MetricRefusalLog`, Python logging, pytest, Ruff, and Black.

**Storage**: Existing CSV, SQLite, or ArangoDB and Redis output selected by
`DataExporter.write_with_format_selection()`. No new storage.

**Testing**: Focused pytest modules named in the implementation manifest,
`py_compile`, Black, Ruff, and later implementation-phase repository gates.

**Target Platform**: Windows, macOS, Linux, and the existing Podman
deployment.

**Project Type**: Python network operations CLI with a web portal that
classifies captured operation logs.

**Performance Goals**: Preserve one request per metric and existing batch
progress. Add no network request, retry, thread, or data-copy step.

**Constraints**: Preserve successful rows, empty-result behavior, transport
exception behavior, refusal details, output backend selection, and existing
site and device labels. Emit ASCII log text only. Use the existing
`Failed to` handled-error marker. Do not change the portal or shared helper.

**Scale/Scope**: Two existing menu operations, two focused test modules, one
transient refusal condition, and one release-note fragment.

All technical-context unknowns are resolved in
[research.md](research.md).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-research gate

- **Principle I, hierarchy and complexity**: PASS. The plan edits existing
  modules and adds no hierarchy level. The new helper has one context
  parameter and one decision. Existing long methods in the touched modules
  are grandfathered debt. The implementation must not increase their
  complexity. A separate remediation action is to track the existing
  method-length debt outside issue #4031.
- **Principle II, class architecture**: PASS. The marker remains owned by
  `SiteMetricOperation` and `DeviceMetricOperation`. No wrapper function or
  new class is needed.
- **Principle III, safety**: PASS. No new operator input, destructive action,
  credential handling, path handling, or API transport is added.
- **Principle IV, deployment pipeline**: PASS for planning. This phase changes
  only design artifacts. The later implementation must run all applicable
  local gates and the full deployment pipeline before commit and release.
- **Principle V, observability**: PASS. The marker uses ASCII logging and
  preserves the existing operator refusal report.
- **Principle VI, inline comments**: PASS by design. Any later changed code
  line must use the repository's inline `WHY` comment convention.
- **Principle VII, action logging**: PASS by design. The later marker helper
  must log the terminal failure with the existing operation context.
- **Mist Cloud constraints**: PASS. Existing `mistapi` paths remain in use.
  No direct REST request and no WebSocket transport is proposed. No new SDK
  contract test is needed.
- **Process-folder rule**: PASS. The feature directory is an existing
  managed numeric Spec Kit route. The one changelog fragment is the required
  unique process record. Existing direct-child debt in process folders is
  grandfathered and receives separate incremental remediation outside this
  issue.
- **External contract rule**: PASS. No `contracts/` artifact is needed because
  the plan consumes an existing log contract and adds no public interface.

## Phase 0: Research

Research is complete in [research.md](research.md). It resolves:

- The exact portal marker, `Failed to`.
- The marker location, after export finalization and refusal reporting.
- The preservation rule, existing `None` filtering and row count behavior.
- The absence of a new external interface contract.
- The focused validation commands.

## Phase 1: Design

Design artifacts are:

- [data-model.md](data-model.md), which defines the transient refusal
  condition and export-row rules.
- [quickstart.md](quickstart.md), which defines focused tests, static checks,
  and the implementation-scope check.
- No `contracts/` directory, because no new external interface exists.

### Product change design

For each operation:

1. Keep `_collect_metrics()` and `_fetch_one_metric()` behavior unchanged for
   successful, empty, refused, and transport-exception responses.
2. Keep `_finalize()` as the writer boundary so successful partial rows remain
   available.
3. Keep `MetricRefusalLog.report()` as the detailed refusal report.
4. Add a small operation-owned terminal check after the existing report.
5. If refusals exist, log one ASCII `ERROR` line with `Failed to` and the
   operation scope. If no refusals exist, log nothing new.

### Test design

Update only the two named focused modules:

- Site tests cover a mixed batch with successful rows and repeated refusals,
  later requests, refusal details, the single handled-error marker, and the
  no-refusal path.
- Device tests cover the same cases with device scope labels.
- Existing tests for empty payloads, transport exceptions, empty metric lists,
  and export errors remain in place.
- Tests assert writer rows and counts so the terminal marker cannot replace
  or discard successful output.

### Release-note design

Add one issue fragment named
`changelog.d/issue-4031-metric-refusal-terminal-status.md`. State that Menus
74 and 76 now report failed terminal status after refused metric requests while
retaining successful partial rows.

## Post-design Constitution Re-check

- **Scope**: PASS. The design names only the five later-change file classes.
- **Portal boundary**: PASS. The existing portal module remains untouched.
- **Shared helper boundary**: PASS. The existing refusal helper remains
  untouched.
- **Successful output**: PASS. The writer runs before the terminal marker.
- **Refusal reporting**: PASS. The existing report remains the detail source.
- **No-refusal behavior**: PASS. The new branch is conditional on a non-empty
  refusal list.
- **Logging**: PASS. The marker matches the existing handled-error tuple and
  uses ASCII text.
- **API and storage**: PASS. No endpoint, schema, backend, or persistence
  change exists.
- **Complexity**: PASS. The design adds one bounded conditional per operation.
  Existing method-length debt remains separate remediation work.
- **Validation**: PASS. The quickstart names focused tests, compile, Black,
  Ruff, and scope checks. Full deployment gates remain required after product
  code changes.

## Complexity Tracking

| Violation or existing debt | Why it remains | Separate remediation |
|---|---|---|
| Existing methods in the two metric operation modules include methods longer than the constitution target. | Issue #4031 needs a narrow terminal-status repair and must not broaden scope. | Track method decomposition as a separate refactor issue. |
| Existing process folders contain grandfathered direct-child debt. | This feature uses the required managed `specs/numbered/` route and one unique changelog record. | Continue the repository process-folder migration separately. |

## Setup limitation

The documented `python3 .specify/scripts/python/setup_plan.py --json` script is
absent in this checkout. The plan used the available Spec Kit template,
feature specification, constitution, repository guidance, source modules, test
modules, portal marker implementation, and changelog conventions. The branch,
feature directory, and specification path were resolved manually.
