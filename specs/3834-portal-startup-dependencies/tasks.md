---
description: "Implementation tasks for request-safe upgrade portal dependencies"
---

# Tasks: Request-Safe Upgrade Portal Dependencies

**Input**: Design documents in `specs/3834-portal-startup-dependencies/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/request-dependencies.md`, and `quickstart.md`

**Organization**: Tasks follow the three P1 user stories. Tests come before implementation because the specification requires unit, integration, and edge-case tests.

**Scope**: Do not add a direct child to `src/interfaces/portals/upgrade_portal/runtime/`. Do not change a file owned by an open pull request. Do not push, rebase, merge, or set auto-merge.

## Phase 1: Setup

**Purpose**: Confirm file ownership and preserve the planned narrow scope.

- [ ] T001 Recheck `gh pr list --json number,headRefName,files` and `git status --short --branch` for every implementation path in `specs/3834-portal-startup-dependencies/plan.md`; stop before editing any path owned by an open pull request.
- [ ] T002 Before editing, compare the declaration and function-length baseline in `specs/3834-portal-startup-dependencies/plan.md` with the current modules under `src/interfaces/portals/upgrade_portal/`; record any changed ownership or hierarchy count in the implementation handoff.
- [ ] T003 Keep new integration tests under `tests/integration/upgrade_portal/issue_3834/`; add no product module under `src/interfaces/portals/upgrade_portal/runtime/`.

## Phase 2: Foundational Contracts

**Purpose**: Prove external call shapes and block real network and store access before service work.

- [ ] T004 Create `tests/integration/upgrade_portal/issue_3834/__init__.py` before adding issue-specific tests; keep the package at five direct files or fewer, including the marker.
- [ ] T005 Add strict SDK, router, document-store, and audit signature tests in `tests/integration/upgrade_portal/issue_3834/test_external_contracts.py`; bind exact arguments and include HTTP 4xx and 5xx responses.
- [ ] T006 Add test traps in `tests/integration/upgrade_portal/issue_3834/test_external_contracts.py` for DNS, sockets, Mist calls, ArangoDB, Redis, dotenv loading, exporters, and container startup before factory import.

## Phase 3: User Story 1 - Start the Portal with Working Services (Priority: P1)

**Goal**: The default portal factory supplies valid dependencies to supported capture, upgrade, settle, and comparison flows.

**Independent Test**: Start the app through `create_app()` and `wsgi_capture:app` with strict external doubles. Exercise supported routes and verify that each SDK call uses the authenticated operator session and each storage operation uses its real interface.

### Tests for User Story 1

- [ ] T007 [P] [US1] Add default-factory and WSGI startup tests in `tests/integration/upgrade_portal/issue_3834/test_default_provider.py`; exercise real service classes and assert valid router, document-store, and audit dependencies.
- [ ] T008 [P] [US1] Add request-provider unit tests in `tests/unit/upgrade_portal/test_phase2_service_wiring.py`; verify graph construction occurs in an authenticated request and never in shared app configuration.
- [ ] T009 [P] [US1] Extend capture call and persistence tests in `tests/unit/upgrade_portal/test_capture_clients.py` and `tests/unit/upgrade_portal/test_capture_stored_state.py`; verify explicit Mist SDK arguments and durable read-back.
- [ ] T010 [P] [US1] Extend upgrade operation tests in `tests/unit/upgrade_portal/test_upgrade_service.py` and `tests/unit/upgrade_portal/test_upgrade_service_status.py`; verify supported Mist SDK calls, firmware evidence, status reads, and cancellation calls.
- [ ] T011 [P] [US1] Extend settle and comparison service tests in `tests/unit/upgrade_portal/test_settle_gate_service.py` and `tests/unit/upgrade_portal/test_comparison_service.py`; verify real evidence and stored records replace assumed results.

### Implementation for User Story 1

- [ ] T012 [US1] Replace eager dependency installers in `src/interfaces/portals/upgrade_portal/app/wiring.py` with a typed, class-owned provider and a bounded request graph; retain the complete E2E override early return.
- [ ] T013 [US1] Use `DatabaseConfig.from_env()` and `DatabaseRouter(config, strategies)` with portal-setting validation in `src/interfaces/portals/upgrade_portal/app/wiring.py`; create a distinct request-owned document handle and the real audit service.
- [ ] T014 [US1] Replace unsupported capture client methods and router writes in `src/interfaces/portals/upgrade_portal/capture/service.py` with explicit Mist SDK calls, existing document-store operations, and verified capture persistence.
- [ ] T015 [US1] Replace unsupported upgrade client methods and router reads or writes in `src/interfaces/portals/upgrade_portal/upgrade/service.py` with supported SDK, inventory, firmware-version, and document-store calls.
- [ ] T016 [US1] Replace placeholder settle checks in `src/interfaces/portals/upgrade_portal/settle/service.py` with current request-session calls and supported gate evidence; return an explicit failure when evidence is unavailable.
- [ ] T017 [US1] Replace dummy comparison data and unsupported router calls in `src/interfaces/portals/upgrade_portal/compare/service.py` with actual capture, settle, and comparison records.
- [ ] T018 [US1] Align `AuditLogger.log_operation` arguments and persistence calls in `src/interfaces/portals/upgrade_portal/audit/logger.py` and its affected service call sites; keep audit failures visible.
- [ ] T019 [US1] Resolve capture dependencies from the request graph in `src/interfaces/portals/upgrade_portal/app/routes/capture.py`; preserve the existing 202 response fields.
- [ ] T020 [US1] Resolve upgrade start, status, and cancel dependencies from the request graph in `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py`; preserve the single status-route owner and existing mutation guards.
- [ ] T021 [US1] Resolve comparison dependencies in `src/interfaces/portals/upgrade_portal/app/routes/comparison.py`; preserve existing stored-result response fields and do not start comparison work on GET.
- [ ] T022 [US1] Change factory lifecycle integration only if required in `src/interfaces/portals/upgrade_portal/app/factory.py`; preserve no-argument startup, complete E2E overrides, and owned-resource teardown.

## Phase 4: User Story 2 - Refuse Work When a Dependency Is Unavailable (Priority: P1)

**Goal**: Authentication, storage, operation, and persistence failures stop work before unsafe mutation or success-shaped responses.

**Independent Test**: Send registered-route requests with missing identity, invalid or unavailable storage, failed writes, and failed operations. Verify the established refusal response and zero later cloud mutations.

### Tests for User Story 2

- [ ] T023 [P] [US2] Add missing-authentication and missing-storage route tests in `tests/integration/upgrade_portal/issue_3834/test_dependency_failures.py`; verify existing 401 behavior, 503 envelope, zero forbidden calls, and secret redaction.
- [ ] T024 [P] [US2] Add malformed input, missing-record, organization refusal, CSRF, lock, and write-gate regressions in `tests/unit/upgrade_portal/test_phase2_phase3_route_connections.py` and `tests/unit/upgrade_portal/test_comparison_routes.py`.
- [ ] T025 [P] [US2] Add failed-write and read-back edge cases in `tests/unit/upgrade_portal/test_capture_stored_state.py` and `tests/unit/upgrade_portal/test_comparison_service.py`; reject CSV-only, zero-record, false, and mismatched durable results.
- [ ] T026 [P] [US2] Add settle, comparison approval, and cancellation failure cases in `tests/unit/upgrade_portal/test_settle_gate_service.py`, `tests/unit/upgrade_portal/test_comparison_routes.py`, and `tests/unit/upgrade_portal/test_upgrade_service_prohibitions.py`; verify no success identifier or false completion.

### Implementation for User Story 2

- [ ] T027 [US2] Gate Mist-dependent work on `identity.current_session()` and a usable operator cloud session in `src/interfaces/portals/upgrade_portal/app/wiring.py`; reject before storage or Mist work when identity is invalid.
- [ ] T028 [US2] Validate database settings and required ArangoDB readiness in `src/interfaces/portals/upgrade_portal/app/wiring.py`; refuse standalone or unavailable required storage with the established 503 error envelope.
- [ ] T029 [US2] Add authenticated request scope to comparison consumers in `src/interfaces/portals/upgrade_portal/app/routes/comparison.py`; preserve current authorization and refusal codes before store access.
- [ ] T030 [US2] Replace unbound run identifiers in document-store queries and updates across `src/interfaces/portals/upgrade_portal/upgrade/service.py`, `src/interfaces/portals/upgrade_portal/compare/service.py`, and `src/interfaces/portals/upgrade_portal/app/routes/comparison.py` with bound AQL parameters or collection APIs.
- [ ] T031 [US2] Stop failed operations in `src/interfaces/portals/upgrade_portal/capture/service.py`, `src/interfaces/portals/upgrade_portal/upgrade/service.py`, `src/interfaces/portals/upgrade_portal/settle/service.py`, `src/interfaces/portals/upgrade_portal/compare/service.py`, and `src/interfaces/portals/upgrade_portal/app/routes/capture.py`, `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py`, and `src/interfaces/portals/upgrade_portal/app/routes/comparison.py`; use safe fixed error text and never expose dependency exception text.

## Phase 5: User Story 3 - Keep Operator Sessions and Test Dependencies Separate (Priority: P1)

**Goal**: Each request owns its service graph and resources, while complete E2E overrides retain every supplied object.

**Independent Test**: Overlap two authenticated requests with separate test clients and a barrier. Verify distinct sessions, routers, graphs, correct cleanup, and zero production constructors for complete E2E overrides.

### Tests for User Story 3

- [ ] T032 [P] [US3] Add two-operator isolation tests in `tests/integration/upgrade_portal/issue_3834/test_request_isolation.py`; use real registry records, separate Flask clients, and a barrier to verify every SDK call uses only its request session.
- [ ] T033 [P] [US3] Add complete and incomplete E2E override tests in `tests/integration/upgrade_portal/issue_3834/test_default_provider.py`; assert object identity, the response owner header, early rejection, and zero production constructor or connector calls.
- [ ] T034 [US3] Add partial-construction, failure-recovery, and worker-lifetime cases in `tests/integration/upgrade_portal/issue_3834/test_request_isolation.py`; verify owned resources close once and borrowed sessions remain open.

### Implementation for User Story 3

- [ ] T035 [US3] Cache the dependency graph only in Flask `g` and close only request-owned router and document resources in `src/interfaces/portals/upgrade_portal/app/wiring.py`; never mutate shared service instances or close registry-owned sessions.
- [ ] T036 [US3] Bind the authenticated session and worker-owned storage before background work starts in `src/interfaces/portals/upgrade_portal/app/wiring.py`; do not pass request proxies or close worker resources at request teardown.
- [ ] T037 [US3] Verify complete `E2EFactoryOverrides` validation and the production-free early return in `src/interfaces/portals/upgrade_portal/app/factory.py` and `src/interfaces/portals/upgrade_portal/app/wiring.py`; do not add override fields.

## Phase 6: Polish and Cross-Cutting Validation

**Purpose**: Document the shipped behavior, verify all requirements and quality gates, and commit only the feature files.

- [ ] T038 [P] Update `documentation/upgrade_capture_portal.md` with request ownership, authentication and storage refusals, operation failures, and safe test requirements.
- [ ] T039 Add `changelog.d/issue-3834-portal-startup-dependencies.md` with one `###` heading and a `Fixed` bullet that names issue #3834; describe only behavior verified by the completed implementation.
- [ ] T040 Run the focused commands in `specs/3834-portal-startup-dependencies/quickstart.md`, the new package `tests/integration/upgrade_portal/issue_3834/`, and `tests/e2e/upgrade_portal`; record each result and each live-call trap count.
- [ ] T041 Run Ruff and Black on changed Python files under `src/interfaces/portals/upgrade_portal/` and `tests/integration/upgrade_portal/issue_3834/`; require both commands to pass.
- [ ] T042 Read `MYPY_PATHS` from `.github/workflows/ci.yml` and run `python -m mypy $MYPY_PATHS --config-file pyproject.toml`; do not replace the live selector with a smaller path set.
- [ ] T043 Run Bandit on `src/interfaces/portals/upgrade_portal/` and run `radon cc src/interfaces/portals/upgrade_portal/ -j | complexity-gate --max 10`; repair findings in changed code without suppressions.
- [ ] T044 Run `symbol-diff --base <intended-base>` on every changed Python file listed in `specs/3834-portal-startup-dependencies/plan.md`; require no module-level name changes unless the task documents and tests an intentional replacement.
- [ ] T045 Run `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`, then run the documented STE and Markdown-link gates on `documentation/upgrade_capture_portal.md` and `changelog.d/issue-3834-portal-startup-dependencies.md`.
- [ ] T046 Compare the final changed paths and hierarchy against `specs/3834-portal-startup-dependencies/plan.md`; confirm no owned open-pull-request file changed, no runtime child was added, and every touched declaration remains within the recorded structural limits.
- [ ] T047 Commit the verified source and test paths in `specs/3834-portal-startup-dependencies/plan.md`, `documentation/upgrade_capture_portal.md`, and `changelog.d/issue-3834-portal-startup-dependencies.md` with a Conventional Commit subject, `Closes #3834`, and `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`; stage explicit paths only and do not push, rebase, merge, or set auto-merge.
- [ ] T048 After T047 commits the implementation tests, run the test-quality preflight and the exact `test-quality-analyzer --gate` command from `.github/copilot-instructions.md`; preserve the intended base and report the gate result. If a repair is needed, create a follow-up commit without amending.

## Dependencies and Execution Order

### Phase Dependencies

- **Setup**: Complete T001 through T003 before any product or test file edit.
- **Foundational**: Complete T004 through T006 before the user-story test tasks. T004 creates the package required by T005 and T006.
- **User Story 1**: Complete T007 through T011 before T012 through T022.
- **User Story 2**: Complete T023 through T026 after the User Story 1 dependency graph exists; then complete T027 through T031.
- **User Story 3**: Complete T032 through T034 after the request provider exists; then complete T035 through T037.
- **Polish**: Complete T038 through T046 before T047. Complete T048 after T047 because the test-quality ratchet requires committed tests. If T048 requires a repair, create a follow-up commit without amending the existing commit.

### User Story Dependencies

- **US1** starts after Foundational. It provides the default service graph.
- **US2** depends on US1 because it adds refusal and failure behavior to the established graph and its routes.
- **US3** depends on US1 because isolation and cleanup tests exercise the request graph. It does not depend on US2.

### Parallel Opportunities

- T004 and T006 can run in parallel because they use separate test files.
- Within each story, test tasks marked `[P]` use separate test files and can start together after their listed prerequisites.
- T038 and T039 can run in parallel after implementation because they use separate files.
- Do not parallelize edits to `app/wiring.py`, shared service files, or any file that gains an open-pull-request owner.

## Parallel Examples

### User Story 1

```text
Run T007 in tests/integration/upgrade_portal/issue_3834/test_default_provider.py.
Run T009 in tests/unit/upgrade_portal/test_capture_clients.py and test_capture_stored_state.py.
Run T010 in tests/unit/upgrade_portal/test_upgrade_service.py and test_upgrade_service_status.py.
Run T011 in tests/unit/upgrade_portal/test_settle_gate_service.py and test_comparison_service.py.
```

### User Story 2

```text
Run T023 in tests/integration/upgrade_portal/issue_3834/test_dependency_failures.py.
Run T024 in tests/unit/upgrade_portal/test_phase2_phase3_route_connections.py and test_comparison_routes.py.
Run T025 in tests/unit/upgrade_portal/test_capture_stored_state.py and test_comparison_service.py.
Run T026 in tests/unit/upgrade_portal/test_settle_gate_service.py and test_upgrade_service_prohibitions.py.
```

### User Story 3

```text
Run T032 and T034 in tests/integration/upgrade_portal/issue_3834/test_request_isolation.py.
Run T033 in tests/integration/upgrade_portal/issue_3834/test_default_provider.py.
```

## Implementation Strategy

1. Complete Setup and Foundational tasks. Recheck open-pull-request ownership before each edit batch.
2. Complete US1 and verify default startup with strict test doubles.
3. Complete US2 and verify every refusal and failed operation stops before unsafe work.
4. Complete US3 and verify request isolation, resource lifetime, and E2E override identity.
5. Complete documentation, changelog, hierarchy review, focused tests, and quality gates.
6. Commit the verified feature. Run the test-quality ratchet after the commit.
7. Do not push, rebase, merge, or set auto-merge.

**Suggested MVP**: Complete User Story 1 with its default-factory integration test. Do not deploy this MVP until US2 and US3 pass, because the portal can change production firmware.
