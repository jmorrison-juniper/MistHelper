# Implementation Plan: Tenant identifier validation

**Branch**: `jmorrison-juniper-tenant-identifier-validation`

**Date**: 2026-10-01

**Spec**: [spec.md](spec.md)

## Summary

Add one shared semantic validator inside `src/api/tenant_fetch.py`.
Move the two existing tenant-name helpers into a separate collector class.
Keep optional record names separate from required organization and site inputs.
Validate all six tenant SDK boundaries.
Validate supplied optional site inputs before any organization SDK call.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing `mistapi`, `requests`, pytest, and Hypothesis.

**Storage**: No new store or schema.

**Testing**: Mocked SDK boundary tests, existing tenant tests, response-integrity
tests, and service-ping discovery tests.

**Target Platform**: Existing Windows, Linux, and macOS environments.

**Project Type**: Internal tenant-discovery library.

**Performance Goals**: Zero SDK calls for invalid scope inputs.

**Constraints**: No live Mist calls, production stores, containers, firmware
actions, dependency changes, or shared configuration edits.

**Scale/Scope**: One audit slice, four public methods, and four private fetch
helpers.

## Constitution Check

The source directory already has seven direct files.
Do not add a production file or package.
The two semantic classes replace two module-level helpers.
That replacement preserves the module-level child count.
The existing tenant-fetch class exceeds five methods, and its network methods
exceed 25 lines. Do not add methods to that class.
Keep the new validator within five methods and 25 lines per method.
Keep `tests/unit/api/` at five direct files after the new test module.

A separate future remediation can divide the existing fetch class by response
source. This repair does not perform that migration.

The app owns the branch. The configured SpecKit Git hook creates or switches
branches, and the other scripts persist shared `.specify/feature.json`.
The authorized file-only fallback uses the current templates.
It writes only this issue-owned specification directory.
It runs specification, planning, tasks, implementation, and consistency review
without branch hooks or shared SpecKit commits.

The parent prohibits publication until it grants a verified `main` revision.
Deployment and protected merge remain outside the local preparation phase.

## Project Structure

### Documentation

```text
specs/2863-tenant-identifier-slice/
  spec.md
  plan.md
  research.md
  tasks.md
  quickstart.md
```

### Source Code

```text
src/api/tenant_fetch.py
tests/unit/api/test_tenant_identifier_validation.py
changelog.d/issue-2863-tenant-identifier-validation.md
```

**Structure Decision**: Use existing production children. Preserve the
read-only caller in `src/websocket/service_ping_discovery.py`.

## Identifier Contract

The shared validator accepts an `object` at the runtime boundary.
It returns the same string if that string has a non-whitespace character.
It raises `ValueError` for every other value.
The error names only the field. Logs contain fixed counts, never input values.

The injected resolver keeps lazy execution.
Its output receives the same required organization check.
The public union methods check required organization and supplied site inputs
before any SDK call.
The private helpers also validate their direct arguments.
Only `None` skips the optional site contribution.

No persistent data model changes.
Tenant-name collection retains its current nonempty-string rule.
It still ignores unknown per-record values.

## Validation Plan

Run new public SDK-boundary tests before the production repair.
Record the failing test count and the observed SDK-call count.
Run the same tests after the repair.
Assert exact refusal text, one refusal, and zero SDK calls.

Run the existing tenant and discovery tests unchanged.
Run HTTP 4xx, HTTP 5xx, and parse-failure cases.
Use Hypothesis for blank strings, non-string inputs, and valid opaque strings.
Measure coverage for `src.api.tenant_fetch`.
Run full configured Ruff, Black, Bandit, and the exact CI mypy scope.
Run the unchanged test-quality ratchet, Markdown links, and configured STE.
Record dictionary limitations without claiming a full dictionary result.
The default ratchet excludes API-importing tests.
Add a stronger file-scoped check with `--include-mist-api`.
Do not change the stored predicate or baseline.

## Exact Local Delivery Manifest

The local commit contains these eight files only.
The initial main revision is
`a5d465a461d2512b717e943278fdff2b1897df84`.
No initial or observed main revision grants publication.

```text
src/api/tenant_fetch.py
tests/unit/api/test_tenant_identifier_validation.py
changelog.d/issue-2863-tenant-identifier-validation.md
specs/2863-tenant-identifier-slice/spec.md
specs/2863-tenant-identifier-slice/plan.md
specs/2863-tenant-identifier-slice/research.md
specs/2863-tenant-identifier-slice/tasks.md
specs/2863-tenant-identifier-slice/quickstart.md
```

Issue #2863 remains open after this bounded local delivery.
The parent controls the later publication and exact-main verification.

## Complexity Tracking

| Existing debt | Bounded treatment | Separate remediation |
| --- | --- | --- |
| Seven files in `src/api/` | Add no direct production child. | Group existing API modules in a separate change. |
| Oversized tenant-fetch class | Add no method to that class. | Divide fetch responsibilities in a separate change. |
| Long network-fetch methods | Add only the required input check. | Extract response handling in a separate change. |
| Broad audit of 102 candidates | Classify only this tenant slice. | Continue the issue without closing it. |
