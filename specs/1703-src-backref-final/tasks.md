# Tasks: Source Back-Reference Removal

**Input**: Design documents from `specs/1703-src-backref-final/`

**Prerequisites**: `plan.md`, `spec.md`

**Tests**: Guardrail test, import smoke tests, static grep proof, and local quality gates.

## Phase 1: Setup

- [ ] T001 Record measured source back-reference counts from `origin/main`.
- [ ] T002 Create `specs/1703-src-backref-final/spec.md` and `plan.md`.

## Phase 2: Foundational

- [ ] T003 Add the source dependency resolver in `src/config/source_dependency_resolver.py`.
- [ ] T004 Bind the extracted main entrypoint to the root module without importing the root module from `src`.

## Phase 3: User Story 1 - Source imports stay inside `src` (Priority: P1)

- [ ] T005 Replace executable `import MistHelper` statements under `src` with the source resolver.
- [ ] T006 Replace executable `importlib.import_module("MistHelper")` calls under `src` with the source resolver.
- [ ] T007 Remove source comments and docstrings that match the final grep proof patterns.

## Phase 4: User Story 2 - Runtime state remains available (Priority: P2)

- [ ] T008 Route session, organization, MSP, output format, telemetry, and settings reads through the source seam.
- [ ] T009 Route helper-class reads through canonical `src` modules.

## Phase 5: User Story 3 - The guard measures its input (Priority: P3)

- [ ] T010 Add `tests/guardrails/test_source_misthelper_backrefs.py`.
- [ ] T011 Add a negative test that injects a deliberate source back-reference.
- [ ] T012 Confirm `python -m tools.guard_proof_audit` does not report the new guard.

## Phase 6: Validation and delivery

- [ ] T013 Run `python -m tools.symbol_diff --base origin/main <file>` for every changed Python file.
- [ ] T014 Run the local gate list from issue #1703.
- [ ] T015 Add `changelog.d/issue-1703-src-backref.md`.
- [ ] T016 Commit, push, open the pull request, wait for required checks, and merge when green.
