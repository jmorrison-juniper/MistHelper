# Tasks: Docker deployment parity statement

**Input**: `specs\2721-docker-parity\spec.md` and `specs\2721-docker-parity\plan.md`

## Phase 1: Scope and evidence

- [x] T001 Read issue #2721, issue #2145, and pull request #2723.
- [x] T002 Add the `in-progress` label to issue #2721.
- [x] T003 Read the repository instructions, the constitution, and the existing
  container deployment guide.
- [x] T004 Run `podman --version` and `docker --version`.
- [x] T005 Inspect the running Podman stack without stopping or recreating any
  service.

## Phase 2: File analysis

- [x] T006 Read `compose.yml` for services, ports, volumes, health checks,
  dependencies, and network names.
- [x] T007 Read `Containerfile` and `Dockerfile` for the image runtime,
  non-root user, data folder, ports, and health check.
- [x] T008 Read `scripts\compose.ps1` for Podman provider assumptions.
- [x] T009 Read `deploy\misthelper.container` and `deploy\misthelper.service`
  for systemd deployment boundaries.
- [x] T010 Read `tests\guardrails\test_compose_naming_policy.py` for enforced
  naming and network rules.

## Phase 3: Documentation

- [x] T011 Add the Docker parity section to
  `documentation\container-deployment.md`.
- [x] T012 Create the SpecKit specification, plan, and task files.
- [x] T013 Add the release-note fragment for issue #2721.

## Phase 4: Validation and delivery

- [x] T014 Run the required local validation commands.
- [x] T015 Run the STE linter for each changed Markdown file and record each
  score.
- [x] T016 Refresh `documentation\security\codeql-verdict-register.md` because
  the pull request CodeQL register gate found changed live alert anchors.
- [ ] T017 Commit, push, open the pull request, and wait for checks.
- [ ] T018 Merge the pull request and verify issue closure.
