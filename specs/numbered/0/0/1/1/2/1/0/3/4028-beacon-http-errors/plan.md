# Implementation Plan: Reject failed beacon responses

**Branch**: `jmorrison-juniper-menu-209-http-error-export` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

## Summary

Check the returned HTTP status before beacon payload normalization. Raise a status-only runtime error through the existing failure and retry paths.

## Technical Context

- **Language/Version**: Python 3.13.
- **Primary Dependencies**: mistapi 0.64.1, pytest, requests response doubles.
- **Storage**: Existing exporter backends remain unchanged.
- **Testing**: Existing exporter unit module plus an installed SDK response contract check.
- **Target Platform**: Windows, macOS, Linux.
- **Project Type**: CLI and portal operation.
- **Performance Goals**: No extra requests or delays.
- **Constraints**: No live cloud calls, payload logs, new dependencies, or portal changes.
- **Scale/Scope**: One production method, its existing test module, and a release fragment.

## Constitution Check

The change preserves SDK transport, authentication, arguments, storage routing, and module-level names.
The tests cover output, failures, and retries without credentials.
No response body enters the new error text.
The existing retry method exceeds the line limit. This narrow repair adds no class or module abstraction.
A separate future extraction can reduce the retry method without changing its behavior.
The existing test class exceeds five methods. Parameterized cases avoid another class or module.
The process folders have existing debt. This change adds only its unique fragment and managed record.
A separate future migration can reduce the existing process-folder debt.
All new feature directories have five children or fewer.
Product outputs remain under `data/`. Tests use mocks.
The commit uses `fix(export): reject failed site beacon responses`.
The post-design check preserves these decisions.

## Project Structure

- `src/operations/exporting/export/site_client_exporter.py`: status check before normalization.
- `tests/unit/export/test_site_client_exporter.py`: returned-status regression and success/retry checks.
- `changelog.d/issue-4028-menu-209-http-error-export.md`: operator-visible repair.
- This feature directory contains the specification, plan, tasks, analysis, and `design/`.

## Complexity Tracking

The repair adds one conditional to the existing retry method.
The method must remain within cyclomatic complexity 10.
No shared HTTP helper is used because its boolean return does not enter the required retry path.
PowerShell was initially unavailable. A session-local portable copy later verified `Resolve-SpecFeaturePath` and the route contracts.
The app-managed branch and shared feature selector remain unchanged.
