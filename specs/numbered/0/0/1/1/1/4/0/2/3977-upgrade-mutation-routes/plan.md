# Implementation Plan: Upgrade Mutation Routes

**Branch**: `3997-upgrade-mutation-routes` | **Date**: 2026-10-24 | **Spec**: [spec.md](spec.md)

**Input**: [Feature specification](spec.md)

## Summary

Issue #3977 reports that protected firmware, run-control, and comparison approval routes read process-wide dependencies. The change will use the authenticated request provider for those routes, while it keeps current authorization, confirmation, lock, audit, and durable-storage rules.

## Technical Context

**Language/Version**: Python 3.13 or newer

**Primary Dependencies**: Flask, the existing Mist SDK, and current portal service classes

**Storage**: The request-owned database router and the existing durable ArangoDB action repository

**Testing**: pytest with fake Mist sessions, service classes, routers, and action stores

**Target Platform**: Windows, macOS, Linux, and the existing container

**Project Type**: Python web service

**Performance Goals**: Resolve resources once per request. Add no cloud request before an existing service call.

**Constraints**: Do not use production credentials, cloud devices, or production stores. Do not change unrelated startup installers.

**Scale/Scope**: Firmware service routes, run-control action storage, comparison approval, their focused tests, and issue documentation.

## Constitution Check

- **Managed records**: The specification uses the fixed eight-segment base-5 route under `specs/numbered/`. The parent-count check passed. The tracked selector still points to issue #4258, so this change will not commit a selector update.
- **Hierarchy limits**: The new feature root holds `spec.md`, `plan.md`, `tasks.md`, and `design/`. The design folder holds five children or fewer.
- **File ownership**: No open pull request owns the four production files. `org_upgrade.py`, `factory.py`, and unrelated installers remain out of scope.
- **Safety**: Route tests use fakes and assert no mutation on refusal. No live cloud call or production-store operation is allowed.
- **Dependencies**: No package change is needed.
- **Existing debt**: The wiring module and the route handlers already exceed the repository's size limits. This feature will add one small request-service type and will not rewrite unrelated functions. A separate cleanup must split the existing oversized modules and handlers.
- **Deployment**: This change stops before merge and production deployment. The issue request forbids production operations.

## Design Decisions

1. Extend the existing request dependency record with one request-owned mutation-service factory.
2. Build upgrade and comparison services lazily from the current operator's cloud session and the request-owned database router. Bind each audit logger to that router.
3. Keep the durable action repository shared because it holds no Mist session and enforces actor-scoped records.
4. Keep read-only comparison results on their existing path. Change only approval to use request dependencies and the authenticated operator identity.
5. Keep global service installers in place for other existing consumers. Do not move startup work into this issue.
6. Map absent mutation dependencies to a refusal before any service mutation or success response.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/1/1/4/0/2/3977-upgrade-mutation-routes/
  spec.md
  plan.md
  tasks.md
  design/
    checklists/
      requirements.md
    contracts/
      mutation-routes.md
    data-model.md
    quickstart.md
    research.md
```

### Source Code

```text
src/interfaces/portals/upgrade_portal/
  api/run_controls/routes.py
  app/routes/comparison.py
  app/routes/upgrade.py
  app/wiring.py

tests/
  integration/upgrade_portal/issue_3834/
  integration/upgrade_portal/issue_3977/
  unit/upgrade_portal/test_phase2_phase3_route_connections.py
```

**Structure Decision**: Keep the change in the existing upgrade-portal packages. Add integration tests under an issue-specific directory. Do not add a new runtime package.

## Validation Strategy

Use the focused route and provider tests. Use test doubles that fail if they contact Mist or a production store. Then run Ruff, Black, mypy for the changed Python paths, and the relevant portal contract tests.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Existing oversized wiring module and route handlers | The requested dependencies and routes already live in these modules. | Moving modules would change import paths and exceed this issue's scope. |
| Existing tracked feature selector points to #4258 | The selector belongs to another feature and must remain unchanged. | Committing a replacement selector would overwrite another feature's active pointer. |
