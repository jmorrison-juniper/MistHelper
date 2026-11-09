# Implementation Plan: Capture Request Dependencies

**Branch**: `3999-fix-capture-dependencies` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

**Input**: Issue #4653 and the specification at this feature root.

## Summary

The normal portal factory installs `CaptureService` without its required Mist session or database router. Keep explicit test overrides, defer the default service until an authenticated request, and build it with the existing request dependency provider.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: Flask, existing portal dependency provider, `mistapi` session

**Storage**: Existing request-owned `DatabaseRouter`; no schema changes

**Testing**: `pytest`, with mocked Mist session and database router

**Target Platform**: Windows, macOS, and Linux

**Project Type**: Python web application

**Performance Goals**: Do not add startup connections or duplicate request resources.

**Constraints**: Authenticate before storage construction. Do not make live Mist or database calls in tests. Do not start a firmware upgrade.

**Scale/Scope**: One existing capture route, one service resolver, and focused regression tests.

## Constitution Check

- **Safety**: The route will use the signed-in operator session. Missing authentication or storage will refuse capture before service work. Firmware upgrade routes remain unchanged.
- **Request ownership**: Reuse the provider's request cache and existing database teardown. Do not close the borrowed Mist session.
- **Structure**: Add source changes only to the route and dependency wiring. Put tests under an issue-specific integration directory.
- **Documentation**: Update the portal guide and add one issue-named changelog fragment. Do not edit the shared changelog.
- **Mist transport**: Reuse the current `mistapi` session methods named in [the specification](spec.md). Add no endpoint or transport.
- **Repository structure**: The `specs/` root has 795 direct children. This feature adds no direct child there and uses the managed eight-level numeric route. Track root cleanup as a separate incremental maintenance action.
- **Validation**: Run focused integration and route tests, changed-file lint and format checks, type checks, and Markdown checks. Keep external calls blocked.

**Gate result**: Pass. The existing provider supplies the required identity and router lifecycle. No new external access or firmware action is needed.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/2/2/1/0/3/4653-fix-capture-dependencies/
├── spec.md
├── plan.md
├── tasks.md
└── design/
    ├── checklists/requirements.md
    ├── research.md
    ├── data-model.md
    ├── quickstart.md
    └── contracts/capture-route.md
```

### Source Code

```text
src/interfaces/portals/upgrade_portal/
├── app/
│   ├── wiring.py
│   └── routes/capture.py
└── capture/service.py

tests/integration/upgrade_portal/issue_4653/
└── test_capture_request_dependencies.py

documentation/upgrade_capture_portal.md
changelog.d/issue-4653-capture-request-dependencies.md
```

**Structure Decision**: Extend the existing request-scoped service resolver and capture route. Keep the existing service and route modules. Add one integration test module for the normal factory path.

## Design Decisions

1. Defer the default capture service when startup lacks its Mist client or database router.
2. Resolve that service from the authenticated request graph when the capture route runs.
3. Keep a configured capture-service override for isolated tests and established callers.
4. Return the existing authentication refusal or service-unavailable response when request resources cannot be built.
5. Do not change firmware start, cancel, site-lock, authorization, or audit behavior.

## Complexity Tracking

No new abstraction or database schema is required. The existing `specs/` root excess remains outside this issue. A separate cleanup change must reduce that count without adding another direct child.
