# Implementation Plan: Read-only retry evidence

**Branch**: `jmorrison-juniper-read-only-retry-evidence` | **Date**: 2026-10-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/2752-read-only-retry-evidence/spec.md`.

## Summary

Pass the failed response to the existing `_log_retry_attempt` method.
Log only a guarded integer HTTP status or the fixed word `unavailable`.
Include the final status in the existing exhaustion error.
Keep the retry algorithm and returned object unchanged.

## Technical Context

**Language/Version**: Python `3.13.13`.

**Primary Dependencies**: Existing `mistapi==0.64.0`, standard logging, and the pinned development tools.

**Storage**: No new storage or output schema.

**Testing**: Native `mistapi.APIResponse` objects with mocked transport and endpoint calls.
Use pytest, coverage, and the existing generic fetch, response, status, and export contracts.

**Target Platform**: The existing macOS worktree, with portable source and tests.

**Project Type**: Existing Python CLI.

**Performance Goals**: Preserve every API call, retry ceiling, delay, and sleep count.

**Constraints**: No dependency, policy, baseline, status acceptance, recovery, firmware, or destructive-operation change.
No publication before the parent's explicit full verified-main SHA grant.

**Scale/Scope**: Two existing source methods, one existing helper assertion, and one dedicated diagnostic test file.

## Constitution Check

The existing `APIDataFetcher` owns this behavior. No wrapper, facade, class, or source member is added.
Its existing `26` methods and `8` instance attributes remain separate member-count debt.
A later dedicated refactor can divide that class without changing this slice.

Use required typed arguments and guard diagnostic status values before formatting.
Retain existing HTTP and body rejectors without edits.
Use only the feature-owned documents and release-note fragment.
The parent owns protected publication, merge, deployment, and actual-main tests.

The mandatory PowerShell feature hook failed because `pwsh` is unavailable.
Its exit code was `127`. No branch or shared SpecKit state changed.
Use the current templates directly and keep workflow state in the owned `.spec-context.json`.
Do not run the optional automatic commit hooks.

## Project Structure

### Documentation (this feature)

```text
specs/2752-read-only-retry-evidence/
  spec.md
  plan.md
  tasks.md
  validation.md
  .spec-context.json
```

### Source Code (repository root)

```text
src/api/api_data_fetcher.py
tests/unit/api/test_api_data_fetcher.py
tests/unit/api/test_api_data_fetcher_retry_evidence.py
changelog.d/issue-2752-read-only-retry-evidence.md
```

**Structure Decision**: Keep the existing source class and use its existing retry call and logging pattern.
Keep the old test file's line count unchanged where practical.
Store temporary reports and the complete offline PR draft in the session artifact directory.

## Complexity Tracking

| Existing debt or constraint | Decision | Separate action |
| - | - | - |
| The fetcher has more than five members. | Edit two existing methods without adding a member. | Use a separate issue for a class refactor. |
| The mandatory hook requires unavailable PowerShell. | Preserve the actual failure and use the current templates directly. | The parent controls any shared workflow change. |
| Publication needs the parent's verified base. | Prepare a clean local commit only. | Wait for the explicit position `35` release. |

## Validation Design

Write regression tests before the behavior change.
Measure missing status evidence on the unchanged source.
Measure incorrect first-status evidence with a temporary owned mutation, then remove that mutation.

Assert complete diagnostic messages, record order, endpoint arguments, returned object identity, and precise sleep series.
Block `requests.Session.request` and the export boundary.
Use private sentinel text in the response body, headers, and query.
Inspect only product diagnostics without changing the SDK's logging behavior.
Use explicit `status_codes` keywords in test cases so the existing analyzer recognizes their HTTP coverage.

Run the complete existing fetcher suite and the smallest adjacent contracts.
Measure the changed statement and branch regions separately from whole-module coverage.
Run compilation, configured Ruff, Black, mypy, Bandit, complexity, and the required input preflight.
Measure both the normal ratchet scope and the owned new file with `--include-mist-api`.
Keep the baseline unchanged.

If normal pip-audit cannot create its temporary environment, preserve that failure.
Audit the full hashed runtime closure with `--require-hashes --no-deps --disable-pip`.
Report its measured package count and the Git-only development-tool limitation.
Report STE as partial with `dictionary_unavailable` when no licensed dictionary exists.
