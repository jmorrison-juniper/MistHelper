# Implementation Plan: Container deployment workflow

**Branch**: `chore/2145-container-deploy` | **Date**: 2026-09-16 | **Spec**: `specs/2145-container-deploy/spec.md`

**Input**: Feature specification from `specs/2145-container-deploy/spec.md`

## Summary

Update the Podman-first deployment workflow so the operator uses compose automation for the supported stack, including the corporate CA case. Add guardrail tests that prove cleanup examples cannot remove the two production store volumes.

## Technical Context

**Language/Version**: Python 3.13 for tests. PowerShell 5+ for the compose helper.

**Primary Dependencies**: Standard library, PyYAML from existing requirements, and podman-compose from the existing bootstrap path.

**Storage**: No schema changes. The production data volumes stay `misthelper-arangodb-data` and `misthelper-redis-data`.

**Testing**: Ruff, Black, mypy, pytest guardrails, collection check, and diagram reference lint.

**Target Platform**: Windows host with Podman and the MistHelper compose stack.

**Project Type**: Documentation and deployment automation.

**Performance Goals**: The helper adds no long-running step beyond the requested compose command.

**Constraints**: Do not run `podman volume prune`. Do not pass `-v` to compose `down`. Do not edit generated API documentation.

**Scale/Scope**: One deployment workflow, one compose overlay, and guardrail tests for the safety rules.

## Constitution Check

- Five-Item Rule: This change adds no new Python package and no new source hierarchy child.
- Class-Based Architecture: No application class is required because no Python application logic changes.
- Safety-First: The cleanup guardrail protects the two production store volumes.
- Full Deployment Pipeline: The plan includes local gates, a branch, a pull request, CI, and merge verification.
- Observability: The PowerShell helper prints the selected compose path before it runs.
- Test-First: The guardrail test is part of the deliverable and proves the safety rule.
- Documentation: The quick start and run guides use the same compose workflow.

## Project Structure

### Documentation for this feature

```text
specs/2145-container-deploy/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code

```text
deploy\compose.corporate-ca.yml
scripts/compose.ps1
tests/guardrails/test_container_policy_docs.py
```

### Documentation

```text
README.md
documentation/container-deployment.md
documentation/wiki/Container-Setup.md
documentation/wiki/Web-Portal.md
documentation/wiki/SSH-Remote-Access.md
changelog.d/issue-2145-container-deploy.md
```

## Changed files

- `deploy\compose.corporate-ca.yml`: Add a compose overlay for the runtime corporate root certificate mount.
- `scripts/compose.ps1`: Add `up-corporate-ca` so the helper controls the overlay.
- `tests/guardrails/test_container_policy_docs.py`: Prove cleanup examples cannot remove production store volumes.
- `documentation/container-deployment.md`: Make the compose workflow the deployment source of truth.
- `documentation/wiki/Container-Setup.md`: Replace direct run examples with compose commands.
- `documentation/wiki/Web-Portal.md`: Replace direct run examples with compose commands.
- `documentation/wiki/SSH-Remote-Access.md`: Replace direct run examples with compose commands.
- `README.md`: Clarify Podman-first support and cleanup proof.
- `changelog.d/issue-2145-container-deploy.md`: Add the release note fragment.

## Complexity Tracking

No constitution violation is required for this feature.
