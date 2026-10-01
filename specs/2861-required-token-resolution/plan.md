# Implementation Plan: Required token resolution

**Branch**: `jmorrison-juniper-required-token-resolution` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/2861-required-token-resolution/spec.md`.

## Summary

Add direct string and nonblank guards to the existing `_resolve_token` method.
Keep provider methods and exception handlers unchanged.
Use `strip()` only to test usability. Return each accepted token without modification.
Keep the existing no-token exception message. Add secret-free diagnostics with checked-source counts.

Part of [#2861](https://github.com/jmorrison-juniper/MistHelper/issues/2861). The campaign remains open.
Prepare one local commit. Do not publish before the parent grants the full verified-main SHA for position 36.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Existing `mistapi`, `hvac`, Redis, pytest, and configured development tools.

**Storage**: Existing token cache only. Tests replace Redis and Vault with controlled mocks.

**Testing**: Actual imported `MistSessionFactory`, actual `create_session`, and a mocked SDK constructor.

**Target Platform**: The backend on macOS for local evidence. Existing Linux CI remains authoritative after publication.

**Project Type**: Existing Python backend.

**Performance Goals**: Preserve source bypass and provider call counts. Add no network call.

**Constraints**: No exception-handler change, credential format rule, credential mutation, schema change, or dependency change.

**Scale/Scope**: One production method, one dedicated test directory, one feature directory, and one unique release-note fragment.

## Constitution Check

- Keep the existing semantic factory. Add no class, method, wrapper, alias, or adapter.
- Keep new methods within five parameters, five logical blocks, and 25 lines.
- Keep the new test directory within five direct files.
- Preserve all secret boundaries. New diagnostics contain source names and counts, never candidate values.
- Preserve current provider failure policies. Do not change any `except` block.
- Keep shared `.specify` state and the main checkout unchanged.
- Keep local validation separate from publication and deployment authorization.

The existing factory has ten methods. The constitution permits this existing debt.
The module retains its five semantic declarations. The repair adds no child to either hierarchy.
A separate change can define semantic provider boundaries after an independent reservation and specification.

### SpecKit capability record

The current templates and `speckit.specify`, `speckit.plan`, `speckit.tasks`, and `speckit.analyze` instructions define this feature.
The app already owns the branch. The Git feature hook cannot change it.
The optional commit hooks must not create partial commits.
The PowerShell planning command failed because `pwsh` is unavailable.
The companion command failed because `speckit.companion.after-specify` is unavailable.
No companion executable exists under `.specify/extensions/companion/`.
Use the current templates directly. Do not claim that unavailable hooks ran.
Do not write `.specify/feature.json` or any other shared feature state.

### Design decisions

The three direct guards avoid a new abstraction and preserve lazy provider access.
Provider-level validation would spread the behavior change across exception-handling methods.
A shared validator would increase the existing factory hierarchy without a necessary semantic boundary.
Neither alternative is needed for this bounded repair.

The token remains opaque. A short token, punctuation, Unicode, or surrounding whitespace does not invalidate a nonblank string.
Redis alone keeps its existing byte decoding. Unsupported non-string values continue to the next source with a diagnostic.
The final `RuntimeError` keeps its exact current message.

## Project Structure

### Documentation (this feature)

```text
specs/2861-required-token-resolution/
  spec.md
  plan.md
  tasks.md
  quickstart.md
  checklists/requirements.md
```

### Source Code (repository root)

```text
mist-ops-platform/src/shared/mist/session.py
mist-ops-platform/tests/unit/mist/token_resolution/
  conftest.py
  test_required_resolution.py
  test_provider_contracts.py
  test_session_boundary.py
changelog.d/issue-2861-required-token-resolution.md
```

**Structure Decision**: Keep the production change in the existing factory. Put new tests in the reserved nested directory.

## Complexity Tracking

No new hierarchy violation is necessary.
The existing factory and module retain their current declaration counts.
Do not use this slice to restructure unrelated code.

## Validation and publication boundary

Create an owned backend environment after the documented missing-environment failure.
Install the backend from `pyproject.toml` and supplemental `requirements-dev.txt`.
Use a separate owned root environment for root imports and gates.
Never install both editable `src` projects into one environment.

Run the three original cases before the source edit.
Run the full focused matrix after the repair.
Run the backend auth, session, rate-limit, SDK, collection, and complete coverage checks.
Preserve the live CI floors. Record named optional-SDK skips separately from required tests.
Run compile, Ruff, types, Black, Bandit, applicable root checks, dependency audits, and the unchanged test-quality preflight and ratchet.
If the analyzer excludes the new files, measure them explicitly without changing its settings or baseline.

Preserve the complete 23-item PR template in an offline draft.
Keep whole-campaign, remote CI, verified-main, deployment, and publication items incomplete where applicable.
Use `Part of #2861`, never an issue-closing keyword.

### Measured limits

The strict backend check reports 176 existing findings across 31 files.
The original-source shadow check reports the same 176 findings.
The targeted factory and new tests retain only four existing findings in unchanged provider methods.
No new test or resolver type finding remains.

The backend advisory Ruff report retains 394 existing findings.
The configured correctness check and the full rule set for owned Python files pass.
Do not change a baseline, setting, exclusion, suppression, or threshold to remove these limits.

The first complete run blocked four attempts from existing scope probes to use the default async Redis client.
No connection succeeded.
The final offline runner gives those four probes an in-memory rate limiter.
It still executes the existing rate-limit code.
The final run records zero transport attempts. No production or existing test file changes.

The direct requirements audit reproduced the macOS EnvBuilder failure from issue #3701.
Its temporary `ensurepip` process stopped with `SIGABRT`.
An owned UV-seeded environment with copied packages and system certificates recovered the requirements-only audit.
The audit covered all 106 resolved packages with no findings.

The initial seeded pip reported eight advisory entries.
Only the two owned environments changed from pip 26.0.1 to 26.2.1.
The final root audit covers 159 packages. The final backend audit covers 158 packages.
The audits cannot assess the Git-only devtools package through PyPI.
The backend audit also excludes the editable local project through its standard package-source check.

The writing check reports partial coverage.
The licensed dictionary artifact is unavailable.
The root SDK contract check also records ten unresolved calls and 366 unverifiable signatures.
These results do not provide full certification or publication authorization.
