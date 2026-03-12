# Implementation Plan: CI/CD Quality Pipeline & Deployment Infrastructure

**Branch**: `013-ci-quality-pipeline` | **Date**: 2026-03-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/013-ci-quality-pipeline/spec.md`

## Summary

Establish a production-grade CI/CD pipeline for MistHelper by extending the existing `container-build.yml` workflow with parallel quality gates (Ruff, mypy --strict, pytest-cov at 70%, Bandit, pip-audit), adding GitHub Issue/PR templates, CodeQL/Dependabot, release artifact publishing, deployment templates (systemd, Quadlet, Compose), and an AI-driven browser testing path using Playwright. All infrastructure is config-as-code in the repository; no refactoring of `MistHelper.py` internals.

## Technical Context

**Language/Version**: Python 3.13+ (existing `requires-python = ">=3.13"`)
**Primary Dependencies**: Ruff, mypy, pytest + pytest-cov, Bandit, pip-audit, Hypothesis, Playwright (dev); mistapi, Flask, Gunicorn, Dash (runtime)
**Storage**: N/A (pipeline infrastructure, no new data storage)
**Testing**: pytest (existing `tests/unit/`), new `tests/e2e/` for Playwright
**Target Platform**: GitHub Actions (ubuntu-latest runners), Linux servers (deployment)
**Project Type**: CLI + web-service (existing monolith with Gunicorn web UI)
**Performance Goals**: CI total wall-clock < 10 minutes (parallel matrix); release artifacts < 10 minutes from tag push
**Constraints**: Zscaler blocks local `podman push` — all container builds via GitHub Actions; mypy `--strict` on 28K-line single file; 70% coverage threshold
**Scale/Scope**: Single repository, ~28K lines, 5 GitHub Actions workflows, 3 deployment templates, 2 GitHub templates

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Five-Item Rule | PASS | No new Python code modules; config files organized under existing directories (`.github/`, `deploy/`, `tests/`). Each directory stays within 5 children. |
| II. Class-Based Architecture | PASS | No new Python classes needed — this feature is infrastructure-only. |
| III. Safety-First | PASS | No destructive operations added. `.env.example` documents variables without exposing secrets. |
| IV. Full Deployment Pipeline | PASS | This feature *implements* the pipeline principle. Extended `container-build.yml` enforces Principle IV via CI. |
| V. Observability & Logging | PASS | CI produces structured check results. No new log output in application code. |

**Pre-Phase 0 Gate**: PASS — no violations. Proceeding.

## Project Structure

### Documentation (this feature)

```text
specs/013-ci-quality-pipeline/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
.github/
├── ISSUE_TEMPLATE/
│   └── feature-spec.yml          # FR-001: Feature Spec Issue template
├── PULL_REQUEST_TEMPLATE.md      # FR-002: PR conformance checklist
├── dependabot.yml                # FR-011: Dependabot config
└── workflows/
    ├── container-build.yml       # EXISTING — extended with quality gate prereqs
    ├── ci.yml                    # FR-004: Parallel quality gates (matrix)
    ├── codeql.yml                # FR-010: CodeQL scanning
    └── release.yml               # FR-012: Release artifact publishing

deploy/
├── misthelper.service            # FR-014: systemd unit template
├── misthelper.container          # FR-015: Podman Quadlet template
└── .env.example                  # FR-017: Environment variable docs

tests/
├── conftest.py                   # EXISTING
├── unit/                         # EXISTING
│   ├── test_config_utils.py
│   ├── test_data_processing.py
│   ├── test_pk_strategies.py
│   └── test_telemetry.py
└── e2e/                          # FR-020: Playwright test directory
    └── (AI-generated tests)

.pre-commit-config.yaml           # FR-021: Local quality gate hooks
compose.yml                       # FR-016: EXISTING — updated for .env
pyproject.toml                    # EXISTING — updated with Ruff, mypy, Bandit configs
```

**Structure Decision**: Infrastructure-only feature using existing repository layout. New files go into `.github/` (templates, workflows, dependabot), `deploy/` (systemd/Quadlet), and `tests/e2e/` (Playwright). Root `.env.example` replaced by `deploy/.env.example` to keep root clean per Five-Item Rule. `compose.yml` already exists and will be updated in place.

## Complexity Tracking

No constitution violations to justify.
