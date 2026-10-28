# Tasks: Upgrade Mutation Routes

**Input**: [spec.md](spec.md), [plan.md](plan.md), and the supporting files in `design/`

**Implementation strategy**: Finish the shared provider first. Then complete each story with a fake-backed refusal test before route changes. Keep read-only comparison access unchanged.

## Dependencies

- The provider and its isolation tests are foundational. Complete them before route work.
- User Story 1, User Story 2, and User Story 3 depend on the provider work.
- The three stories use separate route files, but the shared integration test module requires sequential edits.
- The suggested MVP is User Story 1. The issue requires all three stories before completion.

## Phase 1: Setup

- [x] T001 Confirm the managed feature files and changed-file scope in `specs/numbered/0/0/1/1/1/4/0/2/3977-upgrade-mutation-routes/plan.md`

## Phase 2: Foundational

**Goal**: Supply request-bound services and prove request isolation before any route uses them.

**Independent Test**: Provider tests show request caching, distinct request routers and services, and refusal before service creation when authentication or resource construction fails.

- [x] T002 Add provider isolation and dependency refusal tests in `tests/integration/upgrade_portal/issue_3977/test_mutation_route_dependencies.py`
- [x] T003 Add a request-owned mutation-service factory and bind it to the request record in `src/interfaces/portals/upgrade_portal/app/wiring.py`

## Phase 3: User Story 1 - Start or cancel a firmware upgrade

**Goal**: Use the active operator's cloud session and request router for firmware service routes.

**Independent Test**: Fake services receive only the current request's session. Missing dependencies return an error and make no service mutation call.

- [x] T004 Add route tests for request-bound firmware services and missing-dependency refusal in `tests/unit/upgrade_portal/test_phase2_phase3_route_connections.py` and `tests/integration/upgrade_portal/issue_3977/test_mutation_route_dependencies.py`
- [x] T005 Resolve firmware services from request dependencies in `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py`

## Phase 4: User Story 2 - Submit or reconcile a run action

**Goal**: Resolve the existing durable action store through the authenticated request dependency record.

**Independent Test**: A fake durable store receives actor-scoped actions only after existing authorization, confirmation, preview, and site-lock checks pass.

- [x] T006 Add run-control provider tests, including missing-store refusal, in `tests/integration/upgrade_portal/issue_3977/test_mutation_route_dependencies.py`
- [x] T007 Read the action store from request dependencies in `src/interfaces/portals/upgrade_portal/api/run_controls/routes.py`

## Phase 5: User Story 3 - Approve comparison results

**Goal**: Use the active request's database router and comparison service for approval only.

**Independent Test**: A fake router records approval and audit writes for the authenticated operator. Missing dependencies produce no writes or success response.

- [x] T008 Add comparison-approval provider tests in `tests/integration/upgrade_portal/issue_3977/test_mutation_route_dependencies.py`
- [x] T009 Resolve comparison approval dependencies from the request provider in `src/interfaces/portals/upgrade_portal/app/routes/comparison.py`

## Phase 6: Polish

- [x] T010 Add the issue release note in `changelog.d/issue-3977-upgrade-mutation-routes.md`
- [x] T011 Run the focused tests, lint, format, and type checks listed in `specs/numbered/0/0/1/1/1/4/0/2/3977-upgrade-mutation-routes/design/quickstart.md`
- [x] T012 Review the final diff and confirm that `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` and `.specify/feature.json` remain unchanged

## Parallel Execution

Complete Phase 2 first. After that, firmware route work and comparison approval work use separate production files. Keep the shared integration test edits sequential. Run the run-control story after provider tests because it uses the same action store boundary.

## Completion Criteria

- All three stories have passing fake-backed tests.
- Missing dependencies and failed guards cause no mutation and no success response.
- The release note names issue #3977.
- The selector for issue #4258 and all out-of-scope routes remain unchanged.
