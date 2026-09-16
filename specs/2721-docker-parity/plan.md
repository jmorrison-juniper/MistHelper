# Implementation Plan: Docker deployment parity statement

**Branch**: `docs/2721-docker-parity` | **Date**: 2026-09-16 | **Spec**: `specs/2721-docker-parity/spec.md`

**Input**: Feature specification from `specs\2721-docker-parity\spec.md`

## Summary

Document the Docker deployment parity position without claiming an untested
Docker run. Extend the existing container deployment guide with a parity table,
the source files used for analysis, and a future Docker verification list.

## Technical Context

**Language/Version**: Markdown only. No application language changes.

**Primary Dependencies**: Existing documentation, GitHub CLI, Podman, and the
STE linter.

**Storage**: No schema changes. No container volumes changed.

**Testing**: Ruff, Black, diagram reference lint, citation check, guardrail
tests, pytest collection, and STE lint for changed Markdown.

**Target Platform**: Windows documentation workflow. Docker was not installed on
the validation host.

**Project Type**: Documentation.

**Performance Goals**: Not applicable.

**Constraints**: Do not start or stop the production data stores. Do not edit
generated API documentation. Do not publish Docker commands as supported
deployment steps.

**Scale/Scope**: One documentation section, three SpecKit files, one
release-note fragment, and one CodeQL register refresh required by CI.

## Constitution Check

- Five-Item Rule: This change adds only documentation files in the feature
  specification folder.
- Class-Based Architecture: No code changes are required.
- Safety-First: The document keeps the Podman production path and avoids
  untested Docker instructions.
- Full Deployment Pipeline: The plan includes local validation, a pull request,
  CI checks, and merge verification.
- Observability: No runtime logging change is required.
- Test-First: The change uses existing guardrails and the STE linter.
- Documentation: The container deployment guide becomes the source of truth for
  Docker parity status.

## Project Structure

### Documentation for this feature

```text
specs/2721-docker-parity/
├── spec.md
├── plan.md
└── tasks.md
```

### Documentation

```text
documentation/container-deployment.md
changelog.d/issue-2721-docker-parity.md
```

## Changed files

- `documentation\container-deployment.md`: Add the Docker parity status,
  evidence list, and future verification checklist.
- `specs\2721-docker-parity\spec.md`: Record scope, verified facts, analysis,
  and acceptance criteria.
- `specs\2721-docker-parity\plan.md`: Record the implementation plan and file
  set.
- `specs\2721-docker-parity\tasks.md`: Record the ordered work.
- `changelog.d\issue-2721-docker-parity.md`: Add the release-note fragment for
  issue #2721.
- `documentation\security\codeql-verdict-register.md`: Refresh three alert line
  anchors so the existing CodeQL register gate passes.

## Complexity Tracking

No constitution violation is required for this feature.
