# Research: CI/CD Quality Pipeline & Deployment Infrastructure

**Feature**: 013-ci-quality-pipeline | **Date**: 2026-03-11

## R-001: Ruff Configuration for Single-File Monolith

**Question**: How should Ruff be configured for a 28K-line single Python file?

**Decision**: Configure Ruff in `pyproject.toml` with project-specific rule exclusions for the monolith pattern.

**Rationale**: Ruff natively handles large files without performance issues (written in Rust). The key challenge is rule selection — a 28K-line single file will trigger rules like `PLR0915` (too many statements), `C901` (complexity), and `E501` (line length) at massive scale. These must be selectively disabled or configured with higher thresholds.

**Alternatives Considered**:
- Per-file ignore comments (`# noqa`): Rejected — too many annotations, clutters code
- Running Ruff only on changed lines: Rejected — GitHub Actions doesn't support this natively
- Ignoring the file entirely: Rejected — defeats the purpose

**Configuration Approach**:
- Enable `E`, `F`, `W`, `I`, `UP`, `B`, `S` (Bandit), `T20` rulesets
- Exclude `PLR0915`, `C901`, `PLR0912`, `PLR0913` (unavoidable complexity in monolith)
- Set `line-length = 120` (wider than default 88 for readability in a dense codebase)
- Use `per-file-ignores` for test files to reduce noise

## R-002: mypy --strict on Existing 28K-Line Codebase

**Question**: How to make mypy --strict viable when MistHelper.py likely has minimal type annotations?

**Decision**: Enable `--strict` in `pyproject.toml` but phase in enforcement by initially running mypy with `--warn-return-any` and `--allow-untyped-defs` as overrides, then tightening over time. The CI gate will enforce the current configuration (not `--strict` as an aspirational goal vs immediate blocker).

**Rationale**: The user chose strict mode (Clarification Q5), but applying pure `--strict` on day one to a 28K-line file with no annotations would produce thousands of errors and block every PR. The practical path is:
1. Start with `--strict --allow-untyped-defs --allow-untyped-calls` to catch errors in annotated code
2. Track annotation progress by monitoring the number of suppressions
3. Remove suppressions as annotations are added

**Alternatives Considered**:
- Full `--strict` from day one: Not viable — would make CI permanently red
- Default mode only: Rejected — user explicitly chose strict
- Per-module ignore: N/A — single file

**Configuration**:
```toml
[tool.mypy]
python_version = "3.13"
strict = true
allow_untyped_defs = true
allow_untyped_calls = true
ignore_missing_imports = true
warn_return_any = true
warn_unused_configs = true
```

## R-003: Extending container-build.yml with Quality Gates

**Question**: How to add quality gate prerequisite jobs to the existing container-build.yml without breaking the Zscaler-safe push workflow?

**Decision**: Create a separate `ci.yml` workflow for quality gates (triggered on PRs and pushes to main). Modify `container-build.yml` to add a `needs: [quality-gates]` dependency via workflow_call or by adding the matrix jobs directly as prerequisites to the `build-and-push` job.

**Rationale**: The existing `container-build.yml` has 3 jobs: `validate`, `test`, `build-and-push`. The cleanest extension pattern is:
1. Add a new `quality-gates` job with a matrix strategy running all 5 checks in parallel
2. Make the existing `build-and-push` job depend on `quality-gates` (in addition to existing `validate` and `test`)
3. Keep the Zscaler workaround intact — `build-and-push` only runs on `main` pushes, not PRs

**Alternatives Considered**:
- Separate workflow with `workflow_run` trigger: More complex, harder to debug, race conditions
- Inline all checks as steps in existing `validate` job: Sequential, violates 10-minute parallel budget
- Reusable workflow (`workflow_call`): Over-engineered for this use case

**Implementation**:
- New file: `.github/workflows/ci.yml` — runs on PRs and pushes to main
- Modified: `.github/workflows/container-build.yml` — add quality-gates job, `build-and-push` gains `needs: [validate, test, quality-gates]`

## R-004: GitHub Issue Template (YAML Form)

**Question**: Best format for the Feature Spec issue template?

**Decision**: Use YAML-based issue form (`.github/ISSUE_TEMPLATE/feature-spec.yml`) instead of Markdown template.

**Rationale**: YAML issue forms provide structured input fields (dropdowns, textareas, checkboxes) that enforce completeness. Contributors can't accidentally delete sections. This matches FR-001's requirement for "standardized sections with guidance comments."

**Alternatives Considered**:
- Markdown template (`.md`): Allows freeform editing, contributors can delete sections
- Multiple templates (bug, feature, question): Over-scoped for this feature — only Feature Spec needed

## R-005: Podman Quadlet .container File Best Practices

**Question**: What's the correct structure for a Podman Quadlet `.container` unit file?

**Decision**: Create `deploy/misthelper.container` following the Quadlet specification (Podman 4.4+).

**Rationale**: Quadlet files are placed in `~/.config/containers/systemd/` (rootless) or `/etc/containers/systemd/` (rootful) and `systemd-generator` automatically creates a corresponding systemd unit. Key directives:
- `[Container]` section: `Image=`, `PublishPort=`, `EnvironmentFile=`, `Volume=`
- `[Service]` section: `Restart=always`, `RestartSec=5`
- `[Install]` section: `WantedBy=default.target`

**Alternatives Considered**:
- Raw `podman run` in a shell script: Not declarative, no auto-restart
- Docker Compose only: Already covered by FR-016, Quadlet is the Podman-native path

## R-006: Release Artifact Strategy

**Question**: How to build and publish standalone zip, wheel/sdist, and container image on tag push?

**Decision**: Create `.github/workflows/release.yml` triggered by `v*.*.*` tags. Three jobs: `build-python` (wheel+sdist via `build` package), `build-standalone` (zip bundle), `publish` (upload to GitHub Release + GHCR push).

**Rationale**: The `build` package is the standard Python build tool. Standalone zip = the repo minus dev files. Container image reuses the existing `Containerfile`.

**Alternatives Considered**:
- PyPI publishing: Out of scope — MistHelper is not a public library
- GitHub Packages (npm-style): Not applicable for Python

## R-007: Pre-commit Hook Configuration

**Question**: Which hooks should mirror CI quality gates locally?

**Decision**: Configure `.pre-commit-config.yaml` with Ruff (lint+format), mypy, and Bandit. Exclude pytest and pip-audit from pre-commit (too slow for commit hooks).

**Rationale**: Pre-commit should be fast (<30 seconds). Ruff is near-instant. mypy on a single file is ~5-10 seconds. Bandit is ~2-3 seconds. pytest test suite and pip-audit require network/venv and are too slow for commit-time.

**Alternatives Considered**:
- All 5 checks in pre-commit: Too slow, developers will bypass with `--no-verify`
- Ruff only: Misses type errors and security issues that are cheap to catch locally

## R-008: Playwright E2E Test Architecture

**Question**: How should Playwright tests be structured for MistHelper's Gunicorn web UI?

**Decision**: Create `tests/e2e/` directory with Playwright Python tests. Tests start the Gunicorn server as a fixture, run headless Chromium, and verify page content + interactions.

**Rationale**: Playwright for Python (`playwright` package) integrates with pytest natively (`pytest-playwright`). The fixture pattern:
1. `conftest.py` starts Gunicorn on a random port
2. Tests navigate to `http://localhost:{port}`
3. Teardown stops Gunicorn

CI runs these in a separate job with `playwright install --with-deps chromium`.

**Alternatives Considered**:
- Selenium: Heavier, slower, less reliable
- Cypress: JavaScript-only, doesn't fit Python project
- Manual browsing + screenshots: Eliminated by FR-018/019/020

## R-009: Coverage Threshold Enforcement

**Question**: How to enforce 70% coverage in CI without blocking PRs that can't reasonably improve legacy code coverage?

**Decision**: Use `pytest-cov` with `--cov-fail-under=70` in CI. Exemptions via `# pragma: no cover` for genuinely untestable code (e.g., interactive `input()` loops, SSH session handling).

**Rationale**: 70% is a strict baseline. The existing `tests/unit/` tests cover config utils, data processing, PK strategies, and telemetry. Getting to 70% will require significant new test development, but this is consistent with the "overhaul" intention.

**Alternatives Considered**:
- Coverage badges without enforcement: Not a quality gate — decoration only
- Differential coverage (only enforce on new code): More complex, less impactful for an overhaul

## R-010: pyproject.toml Cleanup

**Question**: The existing pyproject.toml has stale Python 3.8 targets for black and mypy. What needs updating?

**Decision**: Remove black configuration entirely (replaced by Ruff formatter). Update mypy target to 3.13. Add Ruff, Bandit, and coverage configurations.

**Rationale**: 
- Black is superseded by Ruff's formatter (`ruff format`)
- mypy `python_version = "3.8"` conflicts with `requires-python = ">=3.13"`
- flake8 is superseded by Ruff linter
- `[project.optional-dependencies] dev` needs to list all new dev tools

**Changes**:
- Remove: `[tool.black]` section
- Update: `[tool.mypy]` to target 3.13 with strict settings
- Add: `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.bandit]`
- Update: `[project.optional-dependencies] dev` to include ruff, mypy, pytest-cov, bandit, pip-audit, hypothesis, playwright
