# Implementation Plan: Traceback log redaction

**Branch**: `jmorrison-juniper-traceback-log-redaction` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

**Input**: Issue #4704 and its file ownership claim.

## Summary

Extend `SensitiveFilter` to sanitize rendered exception text before a standard handler emits it.
Keep the existing in-place message contract and ordinary credential rules.
Restrict credential separators to the current line.
Match complete authorization headers before the ordinary credential rule.
Redact an authorization scheme and its value together.
Sanitize cached exception text from earlier handlers.
Retain exception types, frames, chain separators, and safe messages.
If formatting fails, replace the unsafe record with a diagnostic that excludes the error value.

## Technical Context

**Language/Version**: Python 3.13 or newer. The local locked environment uses Python 3.14.7.

**Primary Dependencies**: Standard-library logging and pytest.

**Storage**: In-memory streams in tests only.

**Testing**: Focused unit and portal contract tests, plus applicable file-level gates.

**Target Platform**: Windows, macOS, and Linux.

**Project Type**: Shared logging utility.

**Performance Goals**: Do not render a traceback when the record has no exception.

**Constraints**: No caller changes, new credentials, live services, containers, or firmware operations.

**Scale/Scope**: One source file, two existing test files, and unique process records.

## Constitution Check

- The owned source and test paths have no open PR overlap.
- The clean starting commit matches current main.
- The specification uses the managed eight-level numeric route.
- The branch remains app-managed. The tracked feature selector remains unchanged.
- New process records use bounded directories, except the required unique changelog fragment.
- Existing module and test classes exceed structural limits. This repair does not restructure unrelated code.
- The separate remediation action is to divide existing logging tests and process records in a future ownership window.
- Do not add a new module-level production name or remove an existing name.
- Keep each new production method within 25 lines and five parameters.
- Do not log inside a logging filter. Recursive logging can re-enter the failed filter.
- Standard traceback text must remain readable after credential replacement.
- Use a Conventional Commit with `Refs #4704` and the required author trailer.
- The user holds publication. Do not execute the deployment, rebase, push, or PR stages.

## Project Structure

### Documentation (this feature)

The managed feature root contains `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`.
The design directory contains the checklist, research, data model, and quickstart.
No new external interface needs a contract directory.

### Source Code (repository root)

- `src/foundation/support/utils/logger_utils.py`
- `tests/unit/test_logger_utils.py`
- `tests/unit/upgrade_portal/test_logging_contract.py`
- `changelog.d/issue-4704-traceback-log-redaction.md`

**Structure Decision**: Extend existing files only. Keep the existing portal handler installation.

## Complexity Tracking

The existing logging module and test modules exceed five top-level names.
Keep the production symbol set unchanged and add only the regression tests needed for this defect.
The existing process-folder debt remains outside this repair.
Optional commit hooks are deferred to the final local commit.

## Follow-up for Issues #4704 and #4705

Independent real-handler tests found that a newline separator corrupts a safe exception chain ending in `Invalid token`.
They also found that `Authorization: Bearer` values bypass the existing key pattern.
Add failing tests for both findings before changing the pattern.
Keep the original credential keys and add the complete authorization key.
Use horizontal whitespace only in value separators.
Apply the authorization rule first so the ordinary rule cannot remove only the scheme.
Use the same normal, cached, and chained exception paths for both rules.
The scope excludes arbitrary unlabeled secrets.
Add `changelog.d/issue-4705-authorization-log-redaction.md`.
Keep publication held and commit with non-closing references to both issues.

## Structured Authorization Values

The scheme-plus-token rule leaves later Digest and AWS4 parameters visible.
Treat the complete remainder of the labeled header line as private.
Use CR and LF as strict boundaries.
This intentionally removes any same-line diagnostic after the header because no reliable value boundary exists there.
Preserve safe diagnostics on subsequent lines and complete exception chain separators.
Extend the existing parameterized real-handler tests before changing the matcher.
Keep the same owned files and publication hold.

## Verification URL Extension

Extend the existing feature without a new branch or shared feature selector.
The branch hook remains superseded by the explicit app-managed branch requirement.
Optional commit hooks remain deferred to the explicit local commit.
Add exact-route URL recognition before the existing labeled-value rules.
Preserve the route and replace its entire nonempty suffix, including query and fragment.
Stop at whitespace only. Punctuation cannot prove that a private value ended. Do not decode URL values.
Do not match a route embedded in a different path.
Apply the rule through `_redact_text` to messages and fresh or cached exception text.
Use `tests/unit/utils/test_logger_verification_urls.py` for isolated stream and real portal tests.
The dedicated test file follows the explicit ownership handoff instead of editing the renamed test.
The existing test directory exceeds the structural limit. Its separate directory migration remains assigned to the test owner.
The approved analyzer-scope handoff separates three SDK cases into `tests/unit/utils/test_logger_verification_url_sdk_integration.py`.
The original dedicated file retains 131 pure filter cases and no SDK import.
The integration file keeps its explicit SDK import. Analyzer policy remains unchanged.
The bootstrap integration requires explicit credential assignments rather than whitespace-only matches.
Keep colon and equals assignments, quoted keys, horizontal spacing, and all existing authorization and URL rules.
Preserve ordinary menu titles and policy prose. Whitespace-only unlabeled values remain outside the recognition contract.
Do not change bootstrap handlers or exporter callers in this handoff.
Unlabeled response details remain outside this rule. Handler installation and safe exporter diagnostics require separate owners.
Publication and test-rename holds remain active.
