# Quickstart: Mist Organization Licensing Comparison

**Date**: 2026-10-13
**Feature**: [spec.md](spec.md)

This guide records checks for the licensing comparison page in the shared portal.

## Prerequisites

- Use Python 3.13 or newer and the repository virtual environment.
- Use synthetic Mist responses. Do not use a production credential.
- Read the route and data shapes in [the interface contract](contracts/licensing-comparison.md).

## Validate the Isolated Package

Run the service, route, export, and browser tests:

```bash
./.venv/bin/python -m pytest -q tests/integration/web_portal/licensing_comparison tests/e2e/web_portal/licensing_comparison tests/e2e/web_portal/test_portal_smoke.py --cov=src/interfaces/portals/licensing_comparison --cov-report=term-missing
```

Observed result: 52 focused licensing and portal smoke tests passed in 2.28 seconds. Feature coverage was 93.05 percent. The tests cover authorized organizations, input validation, HTTP 4xx and 5xx responses, pagination, one retry after HTTP 429, bundle balances, CSV output, source attribution, and browser session state.

## Validate the Mist SDK

The focused test suite checks the installed SDK methods, explicit inventory pagination arguments, and use of the supplied Mist session:

```bash
./.venv/bin/python -m pytest -q tests/integration/web_portal/licensing_comparison/test_transport_contract.py tests/integration/web_portal/licensing_comparison/test_service.py
```

Run the repository type check:

```bash
./.venv/bin/mypy src/ --config-file pyproject.toml
```

Observed result: `Success: no issues found in 850 source files`.

## Validate Browser Session State

Run the browser test for session-only input:

```bash
./.venv/bin/python -m pytest -q tests/e2e/web_portal/licensing_comparison/test_session_state.py
```

Observed result: one browser test passed. It checks reload, same-tab navigation, and an empty new browser session.

## Quality Gates

- Ruff passed for the licensing package, the portal factory, and the portal smoke tests.
- Black passed. It left all 17 checked Python files unchanged.
- Mypy passed with no issues in 850 source files.
- Bandit passed for the licensing package.
- The complexity gate found no function above the limit of 10.
- The documentation linter passed for the six checked Markdown files. Their scores ranged from 96 to 100 out of 100.
- The local Markdown link scan checked 47 links across six files and found no broken local links. The documented link-check command is not installed in this worktree.
- The test-quality gate checked seven test files, found zero findings, and reported zero new findings.

## Portal Integration

The app registers the licensing comparison blueprint and navigation link in the existing portal. The link appears only when its route exists. The portal smoke tests verify the page selectors and the missing-session response. The package guards pass with five direct feature modules and five E2E root entries. The feature adds no server, database, Redis service, or public port.
