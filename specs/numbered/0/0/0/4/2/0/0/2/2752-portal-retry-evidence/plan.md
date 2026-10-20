# Implementation Plan: Portal retry evidence

**Branch**: `jmorrison-juniper-portal-retry-evidence` | **Date**: 2026-10-19 | **Spec**: [spec.md](spec.md)

## Summary

Retain failure diagnostics at three existing portal retry boundaries.
Preserve all return values, final exceptions, retry limits, delays, paths, and locks.
No upgrade request changes.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: Existing structlog and standard logging.

**Storage**: Existing atomic tracker file.

**Testing**: pytest with mocked collaborators and temporary files.

**Target Platform**: Windows, macOS, and Linux.

**Project Type**: Internal portal services.

**Performance Goals**: No additional retry or delay.

**Constraints**: Three production modules and their direct tests only.

**Scale/Scope**: Capture timeouts, tracker file failures, and the settle ping dependency.

## Constitution Check

This repair adds no production module, class, setting, transport, or public symbol.
It preserves existing structural debt rather than restructuring the upgrade path.
The unique process record uses the existing numeric route for 2752.
The route has eight base-5 segments and resolves to `0/0/0/4/2/0/0/2`.
Each new specification directory has five children or fewer.
The release fragment uses the process-folder exception.
The established changelog folder exceeds five children.
Separate incremental remediation remains with the existing process-folder migration, outside this diagnostic repair.
Tests use only temporary files. Product paths remain unchanged.
Conventional Commits applies to the commit and PR title.
Human review is required. Automatic merge is prohibited.

## Project Structure

- `capture/service.py`: Bind the timeout and include its class and message in the existing warning.
- `settle/service.py`: Promote ping failure evidence to warning level and include its exception class.
- `upgrade/driver.py`: Log file failure causes before retry and protect the final replacement exception during cleanup.
- Direct tests: Extend capture wiring, settle service, and upgrade driver tests.

## Research and Decisions

The current base is `27847360d43f62de7d4f2a339ec06c04b3afb4b6`.
PRs #4309 and #4313 already repaired the preceding paths.
The recovery branch contains earlier fetcher work, not a portal repair to reuse.
The latest issue assessment identifies these remaining portal boundaries.
The existing portal baseline passes 131 tests.

Use warning diagnostics rather than a changed result schema or a first-exception replacement.
The acceptance criteria permit logs, and callers rely on the final exception contract.
Use the existing secret masker for capture and ping messages.
Tracker failures come from local file operations. Never include the tracker rows in a diagnostic.
An absent file remains silent. Other read failures receive warnings before a later result can replace their evidence.
Each failed replacement receives a warning.
Cleanup failure receives a separate error record and does not replace the final replacement exception.

The API, firmware, and neighbor settle methods return placeholder results.
They have no external operation to fail, so logger-failure tests would not prove a real retry defect.
Keep those methods unchanged. Test ping through `_ping_once`, not through logging failures.

## Data and Contracts

No data model, API contract, or run state changes.
Capture still returns a capture or `None`.
Ping still returns the dependency result or raises the last exception.
Tracker reads still return text or `None`.
Replacement still raises the final replacement exception after ten failures.
Scratch cleanup still runs after exhaustion and reports a separate cleanup failure.

## Validation Guide

Run the three direct test modules before and after the repair.
Use controlled failure sequences to prove evidence after empty results, distinct failures, recovery, and exhaustion.
Measure exact calls, sleeps, exception identity, atomic file contents, and scratch cleanup.
Run Ruff, Black, mypy, complexity, Bandit, symbol preservation, documentation, and test-quality gates.
Run the required test-quality preflight and committed comparison separately.
Retain exact results in the PR.

## Tool Constraints

The app creates the branch before the feature hook.
The mandatory hook reports that this branch already exists.
PowerShell is unavailable, so the managed route and active templates supply the records directly.
No shared feature pointer or agent context changes.
Optional commit hooks are deferred until the coherent change is ready.
The disabled companion hooks do not run.
Supporting design is consolidated here because this repair adds no model or external interface.

## Validation Results

The unchanged-code regression run reported 12 failures and one pass.
The final direct and wiring selection passed 163 tests.
Combined coverage for the three production modules reached 90.25%, above the configured 90% threshold.
The five changed methods covered 64 of 67 statements.
The three uncovered statements are unchanged defensive returns after bounded loops.

Compilation, Ruff, Black, mypy, complexity, Bandit, pylint, dead-code, and docstring checks passed.
The three symbol comparisons reported no module-level name change.
The committed test-quality comparison checked three files and reported zero new findings.
The full analyzer checked 1191 files and reported zero new findings.
The required preflight read and validated four inputs.
The managed-folder and changelog guards passed 28 tests with one documented skip.
The changed Markdown link check examined five files and found zero broken links.
All changed Markdown files exceeded the STE threshold.

The standard dependency audit failed because its temporary environment could not run `ensurepip`.
The fully resolved, hashed runtime audit passed without known vulnerabilities through the supported `--disable-pip` mode.
No dependency or gate setting changed.

Cross-artifact analysis mapped all six requirements to the implementation tasks without a contract conflict.
The current-main assessment leaves no additional real production retry gap in the bounded issue manifest.
The address and port-statistics retries already preserve first-failure evidence.
The lock-audit loop processes independent records rather than retrying one operation.
PR checks and CodeQL must pass on the published head before delivery.
The PR remains open for human review.
