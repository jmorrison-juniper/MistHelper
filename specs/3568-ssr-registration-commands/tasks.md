# Tasks: SSR registration commands

## Phase 1: Package and model

- [ ] T001 Create `src/gateway/ssr_registration/__init__.py`.
- [ ] T002 Create `src/gateway/ssr_registration/model.py` with response normalization and command text formatting.
- [ ] T003 Create model tests under `tests/unit/gateway/ssr_registration/`.

## Phase 2: Mist API client

- [ ] T004 Create `src/gateway/ssr_registration/client.py` that calls `apisession.mist_get` for `/api/v1/orgs/{org_id}/128routers/register_cmd`.
- [ ] T005 Create client tests that prove the path and `ttl` query handling.

## Phase 3: Operation

- [ ] T006 Create `src/gateway/ssr_registration/operation.py` with class `SsrRegistrationCommands` and static handler `run()`.
- [ ] T007 Add operation tests for console output, y/N file write behavior, non-2xx handling, and log redaction.

## Phase 4: Required artifacts

- [ ] T008 Create `specs/3568-ssr-registration-commands/wiring.md` with every contract section.
- [ ] T009 Create `changelog.d/issue-3568-ssr-registration-commands.md`.

## Phase 5: Deferred integration

- [ ] T010 Defer `MistHelper.py` import and menu registration to the integration pull request.
- [ ] T011 Defer `src/utils/operation_registry.py` category metadata to the integration pull request.
- [ ] T012 Defer generated menu documentation updates to the integration pull request.

## Phase 6: Validation

- [ ] T013 Run py_compile for each new Python file.
- [ ] T014 Run ruff, black, mypy, pydocstyle, pytest, vulture, and interrogate for the package and tests.
- [ ] T015 Run SpecKit analyze and repair all findings.
