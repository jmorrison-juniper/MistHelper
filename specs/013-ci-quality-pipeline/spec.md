# Feature Specification: CI/CD Quality Pipeline & Deployment Infrastructure

**Feature Branch**: `013-ci-quality-pipeline`
**Created**: 2026-03-11
**Status**: Draft
**Input**: User description: "Complete CI/CD pipeline with GitHub Issue/PR templates, Python quality gates (Ruff, mypy, pytest, Hypothesis, Bandit, pip-audit), CodeQL scanning, Dependabot, GitHub Actions workflows (CI gates, release artifacts, container images), deployment infrastructure (systemd standalone, Docker Compose, Podman Quadlet), and AI-driven autonomous browser testing of the Gunicorn web UI using VS Code browser agent tools and Playwright."

## Clarifications

### Session 2026-03-11

- Q: What minimum line coverage percentage should the initial threshold be? → A: 70% — strict baseline appropriate for an overhaul
- Q: What is explicitly out of scope for Feature 013? → A: Refactoring MistHelper.py into multiple modules/packages (pipeline infrastructure only, for now)
- Q: Should CI quality gates run sequentially or in parallel, and what is the max wall-clock time? → A: Parallel gates via matrix strategy, 10-minute max wall-clock budget
- Q: Should the new CI workflow replace or extend the existing container-build.yml? → A: Extend — add quality gates as prerequisite jobs to preserve existing Zscaler workaround
- Q: What mypy strictness level should be used? → A: Strict mode (`--strict`) — all functions must be annotated, no implicit `Any`

## Out of Scope

- Refactoring `MistHelper.py` into multiple modules or packages — this feature covers CI/CD pipeline infrastructure only, not internal code restructuring

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automated Quality Gates on Every PR (Priority: P1)

A contributor pushes code changes and opens a pull request. The CI pipeline automatically runs linting, type checking, security scanning, dependency auditing, and tests with coverage enforcement. The contributor sees pass/fail results directly on the PR without any manual intervention. Maintainers can trust that merged code meets minimum quality standards.

**Why this priority**: This is the foundation — without automated quality gates, all other pipeline features (auto-merge, release, deployment) are unsafe. Every downstream story depends on reliable, enforced gates.

**Independent Test**: Can be fully tested by opening a PR with intentional lint errors, type errors, or failing tests and confirming the CI rejects it. Then opening a clean PR and confirming all checks pass.

**Acceptance Scenarios**:

1. **Given** a PR is opened with a Python syntax error, **When** CI runs, **Then** the Ruff lint check fails and blocks merge
2. **Given** a PR is opened with a function missing type annotations, **When** CI runs, **Then** the mypy check fails and blocks merge
3. **Given** a PR is opened with test coverage below the configured threshold, **When** CI runs, **Then** the pytest-cov check fails and blocks merge
4. **Given** a PR is opened with a known-vulnerable dependency, **When** CI runs, **Then** the pip-audit check fails and blocks merge
5. **Given** a PR passes all quality gates, **When** the contributor views the PR, **Then** all checks show green and the PR is merge-eligible

---

### User Story 2 - Structured Feature Specs Drive Development (Priority: P2)

A team member creates a new GitHub Issue using the Feature Spec template. The template guides them to document the problem, interfaces, constraints, security needs, test plan, and acceptance criteria in a structured format. When the corresponding PR is opened, the PR template includes a conformance checklist that maps back to the Spec, ensuring nothing is missed.

**Why this priority**: Structured specs reduce miscommunication, drive consistent quality, and give AI tools (Copilot) the structured context needed for reliable multi-file edits. This story is independent of CI but multiplies the effectiveness of every other story.

**Independent Test**: Can be tested by creating a new Issue with the Feature Spec template and verifying all sections render correctly, then opening a PR and verifying the conformance checklist references the Spec.

**Acceptance Scenarios**:

1. **Given** a contributor clicks "New Issue" and selects "Feature Spec", **When** the template loads, **Then** all required sections (Problem/Goal, Interfaces, Constraints, Security, Test Plan, Migration, Acceptance Criteria, Implementation Notes) are present with guidance comments
2. **Given** a contributor opens a PR, **When** the PR template loads, **Then** the conformance checklist includes items for acceptance criteria, tests, coverage, secrets, and dry-run verification
3. **Given** a PR links to a Spec Issue, **When** a reviewer examines the PR, **Then** they can trace every acceptance criterion from the Spec to the PR checklist

---

### User Story 3 - Automated Release Artifacts on Tag (Priority: P3)

A maintainer tags a release (e.g., `v1.0.0`). The pipeline automatically builds a standalone zip bundle, a Python wheel/sdist, and a container image — then publishes them to the GitHub Release page and GHCR respectively. Operations teams can pull artifacts without manual build steps.

**Why this priority**: Automated artifact publishing eliminates manual build/release errors and ensures every tagged release produces consistent, reproducible deliverables. Depends on CI gates (P1) being established first.

**Independent Test**: Can be tested by pushing a test tag and verifying that the GitHub Release contains the expected zip, wheel, and tarball, and that the GHCR image is pullable.

**Acceptance Scenarios**:

1. **Given** a maintainer pushes a tag matching `v*.*.*`, **When** the release workflow runs, **Then** a GitHub Release is created with a standalone zip, wheel, and sdist attached
2. **Given** a maintainer pushes a tag matching `v*.*.*`, **When** the container workflow runs, **Then** a container image is pushed to GHCR with the tag name as the image tag
3. **Given** no tag is pushed, **When** code is pushed to main, **Then** release and container workflows do not trigger

---

### User Story 4 - Deployment via Podman Quadlet or Systemd (Priority: P4)

An operations engineer deploys MistHelper on a single-node server. They can choose between running it as a standalone Python service under systemd (with `.env` loaded via `EnvironmentFile`) or as a Podman container managed by systemd Quadlet (declarative, auto-start, auto-restart). Both modes use the same `.env` file for configuration and secrets.

**Why this priority**: Deployment infrastructure is the final delivery step. It depends on container images (P3) and a working codebase (P1). Operations teams need clear, tested deployment paths.

**Independent Test**: Can be tested by deploying the systemd unit on a test host and verifying the service starts, restarts on failure, and reads `.env`. Separately, deploying a Quadlet container unit and verifying the same behaviors.

**Acceptance Scenarios**:

1. **Given** the systemd unit file is installed and `.env` is present, **When** `systemctl start misthelper` is run, **Then** MistHelper starts and reads configuration from `.env`
2. **Given** the Quadlet `.container` file is placed in the correct directory and `.env` is present, **When** `systemctl --user daemon-reload && systemctl --user start misthelper` is run, **Then** the Podman container starts with environment variables from `.env`
3. **Given** the MistHelper process crashes, **When** systemd detects the failure, **Then** the service is restarted automatically within 5 seconds

---

### User Story 5 - AI-Driven Autonomous Browser Testing of Web UI (Priority: P5)

The MistHelper Gunicorn web UI (Maps Manager, ops portal) can be tested by an AI agent inside VS Code without any human taking screenshots or describing what they see. The AI uses VS Code browser agent tools to open the local web page, read the DOM, click buttons, fill forms, validate outcomes, and generate Playwright tests — all autonomously.

**Why this priority**: This is the most advanced story and depends on the web UI already being functional and the CI pipeline (P1) being in place to run the generated Playwright tests. It eliminates a significant manual testing burden and enables continuous UI regression coverage.

**Independent Test**: Can be tested by enabling VS Code browser agent tools, asking the AI to open the local Gunicorn URL, and verifying it can read the page content and interact with UI elements.

**Acceptance Scenarios**:

1. **Given** the Gunicorn web UI is running locally and VS Code browser agent tools are enabled, **When** the AI is asked to open the web page, **Then** it successfully navigates to the URL and reads the page content
2. **Given** the AI has opened the web UI, **When** it is asked to click a navigation element, **Then** the page transitions to the expected view and the AI confirms the new content
3. **Given** the AI has interacted with the web UI, **When** it is asked to generate Playwright tests for the interactions, **Then** it produces valid Playwright test files that can run headlessly in CI
4. **Given** Playwright E2E tests are committed to the repository, **When** a PR is opened, **Then** the CI pipeline runs the Playwright tests and reports pass/fail

---

### Edge Cases

- What happens when a CI workflow is triggered but the runner has no network access (e.g., GitHub Actions outage)? The workflow should fail gracefully with a clear error rather than hanging.
- How does the pipeline handle a PR that modifies only non-code files (e.g., README, docs)? Quality gates should still run but should not fail on irrelevant checks.
- What happens when the Gunicorn web UI is not running but the AI attempts to open it? The browser tool should return a clear connection error that the AI can report.
- How does the system handle `.env` files with missing required variables? The application should fail fast with a clear error message naming the missing variable.
- What happens when Podman Quadlet encounters an image pull failure (e.g., GHCR is unreachable behind a corporate proxy)? The systemd unit should report the failure and allow manual retry.

## Requirements *(mandatory)*

### Functional Requirements

#### GitHub Templates & Governance

- **FR-001**: Repository MUST include a GitHub Issue template for Feature Specs with standardized sections: Problem/Goal, Interfaces & Behavior, Constraints/Performance, Security & Secrets, Test Plan, Migration/Compatibility, Acceptance Criteria, and Implementation Notes
- **FR-002**: Repository MUST include a GitHub Pull Request template with a Spec Conformance Checklist that covers acceptance criteria, test updates, coverage threshold, secret hygiene, and dry-run verification
- **FR-003**: Branch protection rules MUST require all CI quality gate checks to pass before a PR can be merged

#### CI Quality Gates

- **FR-004**: CI quality gate checks (Ruff, mypy, pytest-cov, Bandit, pip-audit) MUST run in parallel via a GitHub Actions matrix strategy, with a maximum total wall-clock time of 10 minutes
- **FR-004a**: CI pipeline MUST run Ruff for linting and format checking on every PR and push to main
- **FR-005**: CI pipeline MUST run mypy in strict mode (`--strict`) for static type checking on every PR and push to main, requiring full type annotations on all functions with no implicit `Any`
- **FR-006**: CI pipeline MUST run pytest with coverage reporting and enforce a configurable coverage threshold on every PR and push to main
- **FR-007**: CI pipeline MUST run Bandit for security linting on every PR and push to main
- **FR-008**: CI pipeline MUST run pip-audit for dependency vulnerability scanning on every PR and push to main
- **FR-009**: CI pipeline MUST support property-based testing via Hypothesis where test properties are defined in Spec Issues

#### Code Scanning & Supply Chain

- **FR-010**: Repository MUST have CodeQL enabled for Python code scanning, running on PRs, pushes to main, and on a weekly schedule
- **FR-011**: Repository MUST have Dependabot configured for dependency and security update alerts

#### Release & Artifact Publishing

- **FR-012**: On tagged releases (`v*.*.*`), the pipeline MUST build and attach a standalone zip bundle, Python wheel, and sdist to the GitHub Release
- **FR-013**: On tagged releases, the pipeline MUST build and push a container image to GHCR with the tag version as the image tag

#### Deployment Infrastructure

- **FR-014**: Project MUST provide a systemd unit file template for standalone host deployment, using `EnvironmentFile` to load `.env`
- **FR-015**: Project MUST provide a Podman Quadlet `.container` unit file template for single-node containerized deployment, using `EnvironmentFile` for secrets
- **FR-016**: Project MUST provide a Docker Compose file for containerized deployment, using `env_file` for configuration
- **FR-017**: `.env.example` MUST be committed to the repository documenting all required and optional environment variables with descriptions

#### AI Browser Testing

- **FR-018**: Project documentation MUST describe how to enable VS Code browser agent tools for autonomous web UI testing
- **FR-019**: Feature Spec template MUST include a "UI Behavior & Automated Testing Expectations" section for features involving the web UI
- **FR-020**: AI-generated Playwright tests MUST be storable in a standard directory (e.g., `tests/e2e/`) and runnable headlessly in CI

#### Developer Experience

- **FR-021**: Project MUST include a pre-commit configuration that mirrors CI quality gates locally, covering Ruff, mypy, and Bandit
- **FR-022**: Auto-merge MUST be available for PRs that pass all required checks (optionally gated by a label)

### Key Entities

- **Feature Spec Issue**: A GitHub Issue created from the Feature Spec template; serves as the authoritative contract for a feature's requirements, acceptance criteria, and test plan
- **Quality Gate**: A CI check (lint, type, test, security, audit) that must pass before code can be merged; configured as required status checks under branch protection
- **Release Artifact**: A deliverable produced on tag push — standalone zip, wheel/sdist, or container image — published to GitHub Releases or GHCR
- **Deployment Unit**: A systemd service file (standalone) or Quadlet `.container` file (Podman) that declares how MistHelper runs in production, including restart behavior and environment loading
- **Playwright Test**: An end-to-end browser test generated by the AI or written manually, stored in `tests/e2e/`, and executed headlessly during CI

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every PR to main triggers all quality gate checks (lint, type, test, security, audit) and blocks merge on any failure — zero PRs can bypass gates
- **SC-002**: Contributors can create a fully structured Feature Spec Issue in under 5 minutes using the template, with all mandatory sections pre-populated with guidance
- **SC-003**: Tagged releases produce all 3 artifact types (zip, wheel, container image) without manual intervention, within 10 minutes of tag push
- **SC-004**: A fresh deployment using either the systemd unit or Quadlet template starts successfully on the first attempt, given a valid `.env` file
- **SC-005**: The AI agent in VS Code can autonomously open the Gunicorn web UI, read page content, and perform at least one interaction (click/type) without human assistance
- **SC-006**: Playwright E2E tests generated by the AI run successfully in headless CI, catching regressions in the web UI before merge

## Assumptions

- The repository is hosted on GitHub and has access to GitHub Actions runners (ubuntu-latest)
- Python 3.13+ is the target runtime (matching existing MistHelper requirements)
- The existing `container-build.yml` workflow will be extended (not replaced) by adding quality gate jobs as prerequisites, preserving the tested Zscaler workaround
- Ruff configuration will be adapted for MistHelper's single-file architecture (`MistHelper.py` at ~28K lines) — some rules may need project-specific exclusions
- The existing `.env` loading via python-dotenv in MistHelper.py is already functional and will be preserved
- Coverage threshold is set at 70% minimum line coverage — a strict baseline reflecting the overhaul nature of this initiative
- VS Code browser agent tools are available in the team's VS Code version (requires recent Insiders or Stable with the experimental setting enabled)
- The Gunicorn web UI (Maps Manager) is launched via an existing code path in MistHelper and is reachable on a configurable local port
- Podman is the primary container runtime; Docker compatibility is maintained but Podman Quadlet is the recommended production path
- The `ghcr.io/jmorrison-juniper/misthelper` container registry and existing Zscaler workaround (build via GitHub Actions, not local push) remain in effect
