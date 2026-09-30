# Tasks: SSR registration commands

## Phase 1: Package and model

- [x] T001 Create `src/gateway/ssr_registration/__init__.py`.
- [x] T002 Create `src/gateway/ssr_registration/model.py` with response normalization and command text formatting.
- [x] T003 Create model tests under `tests/unit/gateway/ssr_registration/`.

## Phase 2: Mist API client

- [x] T004 Create `src/gateway/ssr_registration/client.py` that calls `apisession.mist_get` for `/api/v1/orgs/{org_id}/128routers/register_cmd`.
- [x] T005 Create client tests that prove the path and `ttl` query handling.

## Phase 3: Operation

- [x] T006 Create `src/gateway/ssr_registration/operation.py` with class `SsrRegistrationCommands` and static handler `run()`.
- [x] T007 Add operation tests for console output, y/N file write behavior, non-2xx handling, and log redaction.

## Phase 4: Required artifacts

- [x] T008 Create `specs/3568-ssr-registration-commands/wiring.md` with every contract section.
- [x] T009 Create `changelog.d/issue-3568-ssr-registration-commands.md`.

## Phase 5: Deferred integration

- [x] T010 Defer `MistHelper.py` import and menu registration to the integration pull request.
- [x] T011 Defer `src/utils/operation_registry.py` category metadata to the integration pull request.
- [x] T012 Defer generated menu documentation updates to the integration pull request.

## Phase 6: Validation

- [x] T013 Run py_compile for each new Python file.
- [x] T014 Run ruff, black, mypy, pydocstyle, pytest, vulture, and interrogate for the package and tests.
- [x] T015 Run the complexity gate with maximum complexity 10.
- [x] T016 Run the test quality ratchet against `origin/main`.
- [x] T017 Run SpecKit analyze and repair all findings.
