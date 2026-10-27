# Implementation Plan: Site Lock Refusal Logging

**Branch**: `jmorrison-juniper-3506-upgrade-portal-lock-refusal-logging` | **Date**: 2026-10-25 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `/specs/numbered/0/0/1/0/3/0/1/1/3506-site-lock-refusal-logging/spec.md`.

## Summary

Add structured action and refusal logs to the site lock routes and lock functions. Preserve all lock behavior and HTTP responses. Use safe identifiers and never log tokens, email addresses, or raw personal data.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: Existing Flask and Python logging modules. Add no dependency.

**Storage**: No new storage.

**Testing**: pytest with fake lock stores and captured log records.

**Target Platform**: Windows 11, macOS, and Linux.

**Project Type**: Python web portal within the MistHelper application.

**Performance Goals**: Add no network call and no blocking work to a lock request.

**Constraints**: Do not change lock decisions, raises, returns, response bodies, statuses, or operation order. Do not log tokens, email addresses, or raw personal data.

**Scale/Scope**: Two lock modules, two existing lock test modules, one guard, one changelog fragment, and one bounded specification.

## Constitution Check

The local change follows the project rules:

- The numeric feature path uses the eight-level base-5 route.
- The change adds no Mist Cloud call, dependency, data store, or user input.
- Log calls use templates and separate values.
- Logs exclude tokens, email addresses, and raw personal data.
- The change preserves lock decisions and response contracts.
- Unit and contract tests use fake stores. No production credential or store is used.
- The test guard reports its examined counts and proves that it rejects a missing log.
- The change does not alter a destructive operation.

The required issue fragment adds one unique file to `changelog.d/`, which has 229 direct files. T010 tracks separate folder-debt remediation after release processing. This change does not move existing fragments.

The constitution requires a complete deployment pipeline. The user has not authorized a push, pull request, merge, auto-merge, or production access. This work stops after local gates and a local commit. Track the remaining pipeline in T011, and do not claim that the deployment gate passed.

**Gate**: Local design and quality criteria apply. The remote deployment gate remains blocked by user scope.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/0/3/0/1/1/3506-site-lock-refusal-logging/
  spec.md
  plan.md
  tasks.md
  design/
    research.md
    quickstart.md
    contracts/
      site-lock-logging.md
    checklists/
      requirements.md
```

### Source Code

```text
src/interfaces/portals/upgrade_portal/app/routes/select.py
src/interfaces/portals/upgrade_portal/runtime/lock.py
tests/contract/upgrade_portal/test_lock.py
tests/unit/upgrade_portal/test_lock.py
tests/guardrails/test_site_lock_refusal_logging.py
changelog.d/issue-3506-site-lock-refusal-logging.md
```

**Structure Decision**: Keep behavior in the existing route and lock modules. Add tests to their existing contract and unit test files. Add one AST guard for the measured refusal paths.

## Complexity Tracking

No constitution gate fails. No added abstraction or dependency is required.
