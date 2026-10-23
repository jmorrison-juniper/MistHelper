# Implementation Plan: Concurrent operations portal access

**Branch**: `jmorrison-juniper-operations-portal-concurrency` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

## Summary

Protect lazy executor creation with one module lock and a second configuration check inside the lock.
Release the lock before routes execute operations or deliver streams.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: Flask and the standard threading library.

**Storage**: Existing application configuration. No persistent schema change.

**Testing**: Pytest with local synthetic Flask requests and controlled constructor delays.

**Target Platform**: Windows, macOS, and Linux.

**Project Type**: Existing web application.

**Performance Goals**: One executor for 16 simultaneous first requests. Initialized reads do not acquire the initialization lock.

**Constraints**: No Mist cloud requests, operation-service edits, deployment, issue closure, merge, or automatic merge.

**Scale/Scope**: One process. Application instances retain separate executors.

## Constitution Check

- Preserve the app-managed branch. Keep the feature selector command-scoped.
- Add only the issue-owned release fragment and managed feature record.
- Existing `web_portal/routes/operations.py` exceeds the module-name limit. The repair does not add a new function or class.
- Existing test and changelog directories exceed five children. The requested regression file and required release fragment use established locations.
- Separate remediation: group future concurrency tests into a bounded package and divide route responsibilities in a dedicated refactor.
- Use only synthetic requests. Keep existing safety checks and production behavior.
- Run focused regression, event-bus, stream, and portal smoke tests.
- Run applicable lint, format, complexity, docstring, security, symbol, and test-quality checks.
- Follow the explicit user restriction against merge and deployment.
- Post-design check: no dependency, schema, transport, endpoint, or response change is required.

## Project Structure

- `web_portal/routes/operations.py`: synchronize `_get_executor()`.
- `tests/unit/web_portal/test_operation_executor_concurrency.py`: forced first-access race, application isolation, failure retry, and lock-release tests.
- `changelog.d/issue-4026-operation-executor-race.md`: user-visible repair note.
- This directory: specification, plan, tasks, analysis, and bounded design records.

## Complexity Tracking

The module lock serializes only initialization across applications in one process.
An application-local lock would require additional setup ownership without improving ordinary request behavior.
The existing helper remains below 25 lines and cyclomatic complexity 10.
