# Tasks: Container deployment workflow

**Input**: `specs/2145-container-deploy/spec.md` and `specs/2145-container-deploy/plan.md`

## Phase 1: Scope and safety proof

- [x] T001 Read issue #2145, add the `in-progress` label, and record the scope decision in the issue.
- [x] T002 Split Docker-specific deployment parity into issue #2721.
- [x] T003 Read `compose.yml`, `scripts\compose.ps1`, deployment docs, systemd units, and guardrail tests.

## Phase 2: Compose automation

- [x] T004 Add `compose.corporate-ca.yml` for the runtime corporate root certificate mount.
- [x] T005 Add `up-corporate-ca` to `scripts\compose.ps1` so the helper merges the overlay safely.

## Phase 3: Documentation

- [x] T006 Update `documentation\container-deployment.md` with the compose workflow and cleanup proof.
- [x] T007 Update the README and wiki run guides to remove direct application `podman run` examples.
- [x] T008 Document the Docker exclusion and link issue #2721.

## Phase 4: Tests

- [x] T009 Extend `tests\guardrails\test_container_policy_docs.py` to reject production volume cleanup commands.
- [x] T010 Extend the same guardrail to require volume and network cleanup proof commands.

## Phase 5: Validation and delivery

- [x] T011 Build the local image and start the application service with `scripts\compose.ps1 up -d --no-deps misthelper`.
- [x] T012 Run the local quality gates from issue #2145.
- [ ] T013 Commit, push, open the pull request, wait for checks, merge, and verify issue closure.
