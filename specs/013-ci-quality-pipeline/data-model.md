# Data Model: CI/CD Quality Pipeline & Deployment Infrastructure

**Feature**: 013-ci-quality-pipeline | **Date**: 2026-03-11

## Overview

This feature is infrastructure-only — no new application entities, database tables, or runtime data models are introduced. The "entities" are configuration files consumed by GitHub Actions, systemd, Podman, and pre-commit. This document defines their schemas and relationships.

## Entity Definitions

### E-001: Quality Gate Configuration

**Location**: `pyproject.toml` + `.github/workflows/ci.yml`

**Fields**:
| Field | Type | Source | Validation |
|-------|------|--------|------------|
| ruff.line-length | int | pyproject.toml | Must be > 0, default 120 |
| ruff.target-version | string | pyproject.toml | Must match `requires-python` |
| ruff.lint.select | list[str] | pyproject.toml | Valid Ruff rule codes |
| ruff.lint.ignore | list[str] | pyproject.toml | Valid Ruff rule codes |
| mypy.python_version | string | pyproject.toml | Must be "3.13" |
| mypy.strict | bool | pyproject.toml | Must be true |
| coverage.fail_under | int | pyproject.toml | Must be >= 70 |
| bandit.targets | list[str] | pyproject.toml | Must include "MistHelper.py" |

**Relationships**: Referenced by `ci.yml` matrix jobs and `.pre-commit-config.yaml`.

### E-002: GitHub Issue Template (Feature Spec)

**Location**: `.github/ISSUE_TEMPLATE/feature-spec.yml`

**Schema** (YAML Issue Form):
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | yes | "Feature Spec" |
| description | string | yes | Template description |
| title | string | yes | Default title prefix |
| body[].type | enum | yes | input, textarea, dropdown, checkboxes |
| body[].id | string | yes | Unique field identifier |
| body[].label | string | yes | Human-readable label |
| body[].validations.required | bool | yes | Whether field is mandatory |

**Sections** (mapped from FR-001):
1. Problem / Goal (textarea, required)
2. Interfaces & Behavior (textarea, required)
3. Constraints / Performance (textarea, optional)
4. Security & Secrets (textarea, required)
5. Test Plan (textarea, required)
6. Migration / Compatibility (textarea, optional)
7. Acceptance Criteria (textarea, required)
8. Implementation Notes (textarea, optional)
9. UI Behavior & Automated Testing (textarea, optional — FR-019)

### E-003: PR Template

**Location**: `.github/PULL_REQUEST_TEMPLATE.md`

**Schema** (Markdown checklist):
| Section | Items |
|---------|-------|
| Spec Conformance | Links to Spec Issue, acceptance criteria met |
| Quality | Tests added/updated, coverage >= 70%, no new Ruff violations |
| Security | No hardcoded secrets, Bandit passes, pip-audit clean |
| Deployment | Dry-run verified, .env changes documented |

### E-004: Deployment Unit — Systemd

**Location**: `deploy/misthelper.service`

**Fields**:
| Directive | Section | Value | Notes |
|-----------|---------|-------|-------|
| Description | [Unit] | "MistHelper Network Operations Tool" | |
| After | [Unit] | network-online.target | Requires network |
| Type | [Service] | simple | |
| ExecStart | [Service] | /usr/bin/python3 /opt/misthelper/MistHelper.py | Configurable path |
| EnvironmentFile | [Service] | /opt/misthelper/.env | Loads all config |
| WorkingDirectory | [Service] | /opt/misthelper | |
| Restart | [Service] | always | FR-014 |
| RestartSec | [Service] | 5 | Edge case: crash loop |
| User | [Service] | misthelper | Non-root per constitution |
| WantedBy | [Install] | multi-user.target | |

### E-005: Deployment Unit — Podman Quadlet

**Location**: `deploy/misthelper.container`

**Fields**:
| Directive | Section | Value | Notes |
|-----------|---------|-------|-------|
| Image | [Container] | ghcr.io/jmorrison-juniper/misthelper:latest | |
| PublishPort | [Container] | 2200:2200, 8055:8055 | SSH + Web |
| Volume | [Container] | ./data:/app/data:rw | Persistent data |
| EnvironmentFile | [Container] | ./.env | Secrets |
| Restart | [Service] | always | FR-015 |
| RestartSec | [Service] | 5 | |
| WantedBy | [Install] | default.target | |

## State Transitions

### CI Pipeline State Machine

```text
PR Opened/Updated
    ↓
[quality-gates] ── matrix parallel ──→ ruff | mypy | pytest-cov | bandit | pip-audit
    ↓ (all pass)                        ↓ (any fail)
[merge-eligible]                     [blocked]
    ↓ (merged to main)
[container-build.yml triggers]
    ↓
[validate] → [test] → [build-and-push]
    ↓
[GHCR image published]
```

### Release Pipeline State Machine

```text
Tag v*.*.* pushed
    ↓
[release.yml triggers]
    ↓ (parallel)
[build-python] ── wheel + sdist
[build-standalone] ── zip bundle
[build-container] ── GHCR image with version tag
    ↓ (all complete)
[GitHub Release created with artifacts]
```

## Validation Rules

- All tool versions in `pyproject.toml` MUST target Python 3.13+
- Coverage threshold MUST be >= 70 (configurable upward only in CI)
- `.env.example` MUST document every variable referenced by `os.environ.get()` or `os.getenv()` in MistHelper.py
- Quadlet `Image=` MUST reference the same GHCR registry as `container-build.yml`
- Pre-commit hook versions MUST be pinned to specific releases (not `latest`)
