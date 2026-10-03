# Implementation Plan: Token Refusal Messages

**Issue**: [MistHelper #3290](https://github.com/jmorrison-juniper/MistHelper/issues/3290)

**Branch**: `jmorrison-juniper-token-refusal-messages`

**Date**: 2026-10-01

**Specification**: [spec.md](spec.md)

**Initial base**: `856e5065413d3026f9c0f6d5222d9d379ec79d8b`

## Summary

Change message selection at four existing refusal returns in `src/interfaces/portals/upgrade_portal/app/routes/auth.py`.
Keep all authentication checks, status codes, error codes, logging, and successful responses unchanged.
Add no authentication logic, cloud access, wrapper, setting, or stored data.

## Technical Context

The worktree uses Python 3.13.13, Flask, pytest, pytest-cov, and Chromium.
The current dependency manifests supply all required packages.
The existing seeded browser harness owns its loopback server and isolated dependencies.
No test may use a live Mist credential or production store.

## Constitution Check

The change reuses existing route functions and the existing refusal helper.
It adds no production class, function, or module.
The reserved test additions need no restructuring of shared test directories.
Later developer guidance limits comments to non-obvious intent.
The repair preserves current credential-safe logging instead of adding unrelated logging.

## Research and Design Decisions

The existing `credential_refusal(message=BAD_CREDENTIALS_MESSAGE)` helper accepts a selected message.
It already preserves HTTP 400 and `error.code="bad_credentials"`.
Its default must remain unchanged for provider login.

Add these fixed public messages beside the existing refusal messages:

| Constant | Exact message |
| --- | --- |
| `API_REFUSAL_MESSAGE` | `The portal could not sign you in. Check the token, then try again.` |
| `EMPTY_API_FIELD_MESSAGE` | `The token field is empty. Type your token, then try again.` |

These names describe public messages and do not require a security suppression.

| Existing return | Selected message |
| --- | --- |
| `finish_token_session`, exception handler | `API_REFUSAL_MESSAGE` |
| `start_browser_token_session`, startup denial | `API_REFUSAL_MESSAGE` |
| `start_browser_token_session`, empty field | `EMPTY_API_FIELD_MESSAGE` |
| `start_browser_token_session`, exception handler | `API_REFUSAL_MESSAGE` |

Keep startup denial before the empty-field check.
Keep environment absence and cloud rejection indistinguishable in their refusal messages.
Keep exception text out of responses and logs.
Keep the common address check, provider messages, and accepted-token session behavior unchanged.

## Reserved File Set

```text
src/interfaces/portals/upgrade_portal/app/routes/auth.py
tests/unit/upgrade_portal/test_auth.py
tests/unit/upgrade_portal/test_token_refusal_messages.py
tests/contract/upgrade_portal/test_token_refusal_messages.py
tests/e2e/upgrade_portal/test_token_refusal_messages.py
specs/3290-token-refusal-messages/spec.md
specs/3290-token-refusal-messages/plan.md
specs/3290-token-refusal-messages/tasks.md
specs/3290-token-refusal-messages/checklists/requirements.md
changelog.d/issue-3290-token-refusal.md
```

The existing missing-environment-token unit test needs one changed message expectation and its comment.
All other changes in existing tests are outside this repair.
Keep shared test stores, fixtures, JavaScript, templates, and other owners' source files unchanged.
Keep `README.md`, `CHANGELOG.md`, dependency manifests, baselines, suppressions, and exclusions unchanged.

## Test Plan

First add tests that collect without the new production constants.
Then record genuine failures from route message assertions against unchanged production source.
Fixture failures and missing tools do not prove the defect.

Unit tests check supplied messages, the unchanged helper default, and actual token refusal decisions.
Offline route contracts check complete literal messages for JSON and HTML clients.
The contracts cover absent, empty, and space-only token fields.
They cover startup denial, environment absence, builder faults, identity faults, and session faults.
They also check provider refusals and accepted tokens in both modes.

Use nonsecret sentinel values in request fields and exception text.
Check response bodies, headers, cookies, session metadata, registry descriptions, and captured logs.
Require zero sentinel exposure and no registry change after a refusal.
Record boundary calls by safe names and counts, not credential values.

Real browser tests use the existing `signed_out_page` and seeded token fixtures.
A normal rejected-token click must show the exact token refusal.
A normal empty-token click must keep the existing client-local cure and make no sign-in request.
A native form submission bypasses only client validation and proves the server empty-field message.
Keep CSRF, server checks, response ownership, readiness, and teardown active.

Check the displayed alert, the cleared field, safe evidence, server logs, and cookies.
Retain only safe screenshots and test results under `data/issue-3290/`.

## Validation and Local Handoff

Run the smallest combined auth tests and the selected Chromium journeys.
Measure executable changed-line coverage and require 100 percent for the production change.
Run configured full Ruff, Black, and Bandit checks.
Read the exact `MYPY_PATHS` from `.github/workflows/ci.yml` before the type check.
Run the unchanged test-quality ratchet against the changed test files.
Run Markdown link and STE checks for issue-owned artifacts and changed Python files.

Run the runtime dependency audit against `requirements.txt`.
If macOS temporary `ensurepip` fails, use the authorized hashed uv requirements resolution.
Name any Git-only development-tool audit limitation.
A missing capability is not a passed check.

Run the required read-only SpecKit analysis after implementation.
Commit locally with Conventional Commits and the required Copilot trailer.
Report the exact prepared HEAD, files, and validation results to the parent.
Queue position 13 follows issue #3310.
Do not push or create a pull request before the parent's explicit publication release.

## Complexity Tracking

This narrow repair adds two constants to the existing route module.
Moving authentication code or restructuring shared test directories would exceed the reserved scope.
The feature needs no schema, data model, new interface contract, or deployment change.

The existing route module and test directories exceed the constitution's five-child limit.
The requested scope permits only the fixed messages and issue-owned tests.
This plan records that structural exception instead of claiming full hierarchy compliance.
A separate incremental repair can organize the existing authentication module and test directories.
That repair needs separate authorization and is not part of issue #3290.

The read-only SpecKit analysis finds no functional defect and maps all 17 requirements to tasks.
It records four literal constitution variances.
These concern hierarchy limits, comment expansion, branch naming, and commit/deployment policy.

The app owns the branch name.
Later developer guidance limits comments to non-obvious intent.
Current Git instructions require Conventional Commits.
The parent forbids publication and production deployment before explicit release.
The analysis does not authorize changes outside those boundaries.
