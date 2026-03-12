# Tasks: CI/CD Quality Pipeline & Deployment Infrastructure

**Input**: Design documents from `/specs/013-ci-quality-pipeline/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: E2E test infrastructure is included per FR-020. Hypothesis example included per FR-009. Unit test tasks for the pipeline infrastructure itself are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — update pyproject.toml with all tool configurations, clean up stale settings

- [x] T001 Remove stale `[tool.black]` section and update `[tool.mypy]` to target Python 3.13 with strict settings in pyproject.toml
- [x] T002 Add `[tool.ruff]` and `[tool.ruff.lint]` configuration sections to pyproject.toml per R-001 (line-length=120, select E/F/W/I/UP/B/T20, ignore PLR0915/C901/PLR0912/PLR0913, per-file-ignores for tests) — note: `S` (Bandit) rules excluded from Ruff to avoid duplication with standalone Bandit (see F3 remediation)
- [x] T003 [P] Add `[tool.bandit]` configuration section to pyproject.toml per R-001 (targets=MistHelper.py)
- [x] T004 [P] Add `[tool.coverage]` configuration section to pyproject.toml with fail_under=70 and source paths
- [x] T005 Update `[project.optional-dependencies] dev` in pyproject.toml to include ruff, mypy, pytest-cov, bandit, pip-audit, hypothesis, playwright per R-010

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared CI infrastructure that all user stories depend on — the quality gates workflow and container-build extension

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create `.github/workflows/ci.yml` with parallel matrix strategy for 5 quality gates (ruff, mypy, pytest, bandit, pip-audit) per ci-workflow.md contract
- [x] T007 Extend `.github/workflows/container-build.yml` to add `quality-gates` job dependency on `build-and-push` per R-003 (needs: [validate, test, quality-gates])
- [x] T008 [P] Create `.github/dependabot.yml` with pip ecosystem configuration for dependency and security update alerts (FR-011)
- [x] T009 [P] Create `.github/workflows/codeql.yml` for Python code scanning on PRs, pushes to main, and weekly schedule (FR-010)

**Checkpoint**: Foundation ready — CI workflows exist and can trigger on PRs. User story implementation can begin.

---

## Phase 3: User Story 1 — Automated Quality Gates on Every PR (Priority: P1) MVP

**Goal**: Every PR automatically runs linting, type checking, security scanning, dependency auditing, and tests with coverage. Pass/fail results appear directly on the PR. Merge is blocked on any failure.

**Independent Test**: Open a PR with intentional lint errors, type errors, or failing tests and confirm CI rejects it. Open a clean PR and confirm all checks pass green.

### Implementation for User Story 1

- [x] T010 [US1] Create `.pre-commit-config.yaml` with Ruff (lint+format), mypy, and Bandit hooks per R-007 — pinned to specific release versions
- [x] T011 [P] [US1] Verify `ci.yml` matrix entry for `ruff` runs `ruff check . && ruff format --check .` with 5-minute timeout per ci-workflow.md contract
- [x] T012 [P] [US1] Verify `ci.yml` matrix entry for `mypy` runs `mypy MistHelper.py` with phased strict config (--strict --allow-untyped-defs --allow-untyped-calls) per R-002
- [x] T013 [P] [US1] Verify `ci.yml` matrix entry for `pytest` runs `pytest --cov --cov-fail-under=70` with 5-minute timeout per ci-workflow.md contract
- [x] T014 [P] [US1] Verify `ci.yml` matrix entry for `bandit` runs `bandit -r MistHelper.py -c pyproject.toml` per ci-workflow.md contract
- [x] T015 [P] [US1] Verify `ci.yml` matrix entry for `pip-audit` runs `pip-audit -r requirements.txt` per ci-workflow.md contract
- [x] T016 [US1] Document branch protection rule configuration (require status checks: quality-gates (ruff), quality-gates (mypy), quality-gates (pytest), quality-gates (bandit), quality-gates (pip-audit)) in quickstart.md or README.md (FR-003)
- [x] T035 [P] [US1] Create example Hypothesis property-based test in `tests/unit/test_hypothesis_example.py` and document in Feature Spec template how Spec Issues define test properties for Hypothesis (FR-009)

**Checkpoint**: User Story 1 complete — PRs trigger all 5 parallel quality gates and block merge on failure.

---

## Phase 4: User Story 2 — Structured Feature Specs Drive Development (Priority: P2)

**Goal**: GitHub Issue template guides contributors to document problems, interfaces, constraints, security, test plans, and acceptance criteria in a structured format. PR template includes a conformance checklist mapping back to the Spec.

**Independent Test**: Create a new Issue with the Feature Spec template and verify all sections render. Open a PR and verify the conformance checklist references the Spec.

### Implementation for User Story 2

- [x] T017 [P] [US2] Create `.github/ISSUE_TEMPLATE/feature-spec.yml` YAML issue form with 9 sections per E-002 schema (Problem/Goal, Interfaces, Constraints, Security, Test Plan, Migration, Acceptance Criteria, Implementation Notes, UI Behavior & Automated Testing) (FR-001, FR-019)
- [x] T018 [P] [US2] Create `.github/PULL_REQUEST_TEMPLATE.md` with Spec Conformance Checklist per E-003 schema (acceptance criteria, tests, coverage, secrets, dry-run) (FR-002)

**Checkpoint**: User Story 2 complete — Issues and PRs have structured templates enforcing quality.

---

## Phase 5: User Story 3 — Automated Release Artifacts on Tag (Priority: P3)

**Goal**: Pushing a tag `v*.*.*` automatically builds a standalone zip, Python wheel/sdist, and container image — publishing to GitHub Release and GHCR.

**Independent Test**: Push a test tag and verify GitHub Release contains zip, wheel, tarball, and GHCR image is pullable.

### Implementation for User Story 3

- [x] T019 [US3] Create `.github/workflows/release.yml` with tag trigger `v*.*.*` per release-workflow.md contract — three parallel jobs: build-python (wheel+sdist), build-standalone (zip bundle), publish (upload to GitHub Release)
- [x] T020 [US3] Add standalone zip bundle job to release.yml per release-workflow.md contract — include runtime files (MistHelper.py, requirements.txt, pyproject.toml, README.md, LICENSE, `web_portal/`, maps\_manager.py, wsgi.py, `__init__.py`) and exclude dev/build files (`.git/`, tests/, `.github/`, `.specify/`, data/, `.env`, `__pycache__/`, `*.pyc`)
- [x] T021 [US3] Add container image build and push job to release.yml — push to ghcr.io/jmorrison-juniper/misthelper:{version} on tag push (FR-013)
- [x] T022 [US3] Add non-trigger guard to release.yml — ensure pushes to main without tags and PRs do NOT trigger per release-workflow.md non-trigger contract

**Checkpoint**: User Story 3 complete — tagged releases produce 3 artifact types (zip, wheel, container) automatically.

---

## Phase 6: User Story 4 — Deployment via Podman Quadlet or Systemd (Priority: P4)

**Goal**: Operations engineers can deploy MistHelper as a standalone systemd service or a Podman Quadlet container — both using the same `.env` for configuration and secrets, with auto-restart on failure.

**Independent Test**: Deploy systemd unit on a test host and verify start, restart-on-failure, and `.env` loading. Deploy Quadlet and verify same behaviors.

### Implementation for User Story 4

- [x] T023 [P] [US4] Create `deploy/misthelper.service` systemd unit file per deployment.md contract (After=network-online.target, User=misthelper, EnvironmentFile, Restart=always, RestartSec=5) (FR-014)
- [x] T024 [P] [US4] Create `deploy/misthelper.container` Podman Quadlet file per deployment.md contract (Image=ghcr.io/jmorrison-juniper/misthelper:latest, PublishPort=2200+8055, Volume=./data:/app/data:rw, EnvironmentFile, Restart=always, RestartSec=5) (FR-015)
- [x] T025 [P] [US4] Create `deploy/.env.example` documenting all required and optional environment variables per deployment.md env var contract (MIST_API_TOKEN, MIST_ORG_ID, MIST_PAGE_LIMIT, FAST_MODE_MAX_CONCURRENT_CONNECTIONS, CSV_FRESHNESS_MINUTES) (FR-017)
- [x] T026 [US4] Update `compose.yml` to use `env_file` directive for `.env` loading per FR-016

**Checkpoint**: User Story 4 complete — three deployment paths (systemd, Quadlet, Compose) are documented and ready.

---

## Phase 7: User Story 5 — AI-Driven Autonomous Browser Testing of Web UI (Priority: P5)

**Goal**: AI agent in VS Code can open the Gunicorn web UI, read DOM, interact with elements, and generate Playwright tests that run headlessly in CI.

**Independent Test**: Enable VS Code browser agent tools, ask AI to open local Gunicorn URL, and verify it can read page content and interact with UI elements.

### Implementation for User Story 5

- [x] T027 [P] [US5] Create `tests/e2e/conftest.py` with Gunicorn server fixture (start on random port, teardown on test end) per R-008
- [x] T028 [P] [US5] Create `tests/e2e/__init__.py` as empty package marker
- [x] T029 [US5] Add Playwright E2E job to `ci.yml` as a separate matrix entry or standalone job — install chromium, run `pytest tests/e2e/` headlessly (FR-020)
- [x] T030 [US5] Add AI browser testing documentation section to README.md or quickstart.md describing how to enable VS Code browser agent tools for autonomous web UI testing (FR-018)

**Checkpoint**: User Story 5 complete — E2E test infrastructure is ready, AI-generated Playwright tests can be stored and run in CI.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Auto-merge, documentation updates, and final validation across all stories

- [x] T031 [P] Add auto-merge configuration to ci.yml or a separate workflow — enable auto-merge for PRs that pass all required checks, optionally gated by a label (FR-022)
- [x] T032 [P] Update README.md with CI badge, quality gate summary, deployment instructions, and links to deploy/ templates
- [x] T033 Run quickstart.md validation — execute all local quality gate commands from quickstart.md and verify they work end-to-end
- [x] T034 Final pyproject.toml validation — confirm all tool configurations are consistent (Python version, coverage threshold, Ruff rules, mypy strict settings)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) — pyproject.toml must have tool configs before workflows reference them
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — ci.yml must exist
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) — can run in parallel with US1
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) — can run in parallel with US1/US2
- **User Story 4 (Phase 6)**: Depends on Foundational (Phase 2) — can run in parallel with US1/US2/US3
- **User Story 5 (Phase 7)**: Depends on Foundational (Phase 2) — can run in parallel with others, but benefits from US1 completion (CI runs E2E tests)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Foundation only — no dependencies on other stories
- **US2 (P2)**: Foundation only — completely independent of US1
- **US3 (P3)**: Foundation only — independent, but tagged releases are safer after US1 gates exist
- **US4 (P4)**: Foundation only — independent, but benefits from US3 (container image availability)
- **US5 (P5)**: Foundation only — independent, but benefits from US1 (CI runs Playwright tests)

### Within Each User Story

- Shared config (pyproject.toml) before workflow files
- Workflow files before verification/documentation tasks
- Core implementation before integration

### Parallel Opportunities

- T003 + T004 can run in parallel (independent pyproject.toml sections)
- T008 + T009 can run in parallel (independent workflow files)
- T011 + T012 + T013 + T014 + T015 can all run in parallel (independent matrix entry verification)
- T017 + T018 can run in parallel (independent template files)
- T023 + T024 + T025 can run in parallel (independent deployment files)
- T027 + T028 can run in parallel (independent test files)
- T031 + T032 can run in parallel (independent cross-cutting files)
- Once Phase 2 completes, US1 through US5 can all proceed in parallel (if staffed)

---

## Parallel Example: User Story 4

```text
# Launch all deployment template files together:
Task T023: "Create deploy/misthelper.service systemd unit"
Task T024: "Create deploy/misthelper.container Quadlet file"
Task T025: "Create deploy/.env.example environment docs"

# Then sequentially:
Task T026: "Update compose.yml with env_file"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (pyproject.toml cleanup + tool configs)
2. Complete Phase 2: Foundational (ci.yml, container-build.yml extension, dependabot, codeql)
3. Complete Phase 3: User Story 1 (pre-commit, matrix verification, branch protection docs)
4. **STOP and VALIDATE**: Open a test PR — confirm all 5 quality gates run and block merge
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → CI infrastructure operational
2. Add US1 → Quality gates enforced → MVP!
3. Add US2 → Structured specs and PR checklists → Governance layer
4. Add US3 → Automated release artifacts → Delivery pipeline
5. Add US4 → Deployment templates → Operations ready
6. Add US5 → AI browser testing → Full automation
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (quality gates) + US5 (E2E tests)
   - Developer B: US2 (templates) + US3 (release)
   - Developer C: US4 (deployment)
3. Stories complete and integrate independently
