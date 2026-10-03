# Implementation Plan: CSV suffix preservation

**Branch**: `jmorrison-juniper-csv-suffix-preservation`

**Date**: 2026-10-03

**Spec**: [spec.md](spec.md)

## Summary

Change only the CSV suffix decision in `DataExporter._write_csv_format`.
Compare the final four characters without changing the supplied filename.
Use the existing writer for every output file.

## Technical Context

**Language/Version**: Python 3.13 or newer. The owned environment uses 3.13.13.

**Primary Dependencies**: Existing standard-library CSV tools, mistapi 0.64.0,
and the pinned repository test tools.

**Storage**: Temporary CSV files and a temporary SQLite database only.
Private fakes replace every external store.

**Testing**: Dedicated unit, contract, and native integration modules.

**Target Platform**: The existing macOS, Linux, Windows, and container paths.

**Project Type**: The existing CLI application with shared output services.

**Performance Goals**: Examine four suffix characters. Add no network call.

**Constraints**: No publication, production action, schema change, or shared-file edit.

**Scale/Scope**: One existing product method and three dedicated test modules.

## Constitution Check

The product change stays in an existing class and method. It adds no wrapper,
alias, parameter, module, or schema. The method remains below 25 lines and
complexity 10.

`DataExporter` already exceeds the hierarchy limits. This repair does not add
a member. A separate structural repair must address that existing debt.
The dedicated test files use the reserved existing test trees. This bounded
repair does not restructure another issue's tests.

The existing write log remains before the write. A result log follows the
successful write. The changed suffix decision explains name preservation.
No secret or live request enters a test.

The parent limits delivery to a local commit. That limit overrides the older
constitution text that requests immediate deployment. The current Git workflow
requires a Conventional Commits message.

## Feature-Only SpecKit Procedure

The documented prerequisite command failed before execution:

```text
rtk proxy pwsh -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -Json
rtk: Failed to execute command: pwsh: No such file or directory (os error 2)
```

This feature uses the current templates in order: specification, contract,
plan, tasks, implementation, and final consistency review. No shared
`.specify` record, Git hook, governance file, or agent context changes.
This procedure is a feature-only equivalent, not a successful PowerShell run.

The normal bootstrap also failed in `venv.EnvBuilder` with an `ensurepip`
`SIGABRT`. The local trace remains in the session artifacts. UV recovered only
the ignored `.venv`, with seed packages, copied links, and system certificates.
No bootstrap source changed.

## Project Structure

```text
src/export/data_exporter.py
tests/unit/export/test_csv_suffix_preservation.py
tests/contract/export/test_csv_suffix_backends_and_discovery.py
tests/integration/export/test_menu64_csv_suffix_preservation.py
specs/3738-csv-suffix-preservation/spec.md
specs/3738-csv-suffix-preservation/plan.md
specs/3738-csv-suffix-preservation/tasks.md
specs/3738-csv-suffix-preservation/contracts/csv-suffix.md
changelog.d/issue-3738-csv-suffix-preservation.md
```

## Design Decisions

Use a case-normalized final suffix for comparison only. Retain the original
target in the successful branch. Do not normalize a directory or stem.
Retain non-string refusal, including bytes, at the existing dispatch boundary.

The data browser already checks extensions without a case distinction.
`FilePathUtils` preserves supplied names and explicit paths. Actual tests must
prove both contracts. The scanner must execute against the owned output directory.

SQLite keeps its case-sensitive suffix removal. Tests must prove the unchanged
constructor target and the actual resulting sanitized table. The router keeps
the same data and API function name.

## Verification Plan

1. Prove the defect with the actual menu 64 handler and real SDK functions.
2. Prove all suffix cases through the actual writer and file reader.
3. Prove backend names, data, metadata, errors, and output discovery.
4. Restore the old case check temporarily and prove the uppercase contract fails.
5. Run the complete selected existing tests and every applicable local gate.

The native proof seeds `SiteList.csv` separately through the real writer.
It uses the actual prompt reader and controls only the site answer and SDK
transport. It counts cache setup separately from the final client output.

Run compile, Ruff, and Black.
Run mypy with the paths that CI uses.
Run strict typing for the owned tests.
Run Bandit, complexity, symbols, guide preflight, and the unchanged test-quality gate.
Run local links and writing checks. Check generated menu references without
writing them.

Measure the changed method's lines and both suffix decisions. Do not describe
that measurement as complete repository coverage. Record unavailable licensed
dictionary grading separately from structural writing checks.

## Publication Boundary

Commit only the nine reserved files. Keep the issue open and assigned.
Record the full local SHA and clean state. Send a local handoff to the parent.
Do not push, create a pull request, start Actions, merge, or deploy.

## Local Results

The final selected test run passed 393 tests. The owned tests passed with
resource warnings treated as errors. The changed method covered all five
statements. Coverage records no branch for its conditional expression.
The real writer tests prove both filename outcomes and all eight suffix cases.
The exporter module reached 95.99 percent combined coverage. This result does
not measure the complete repository.

The source comparison found one changed method and 26 unchanged methods.
Forty protected files kept their original bytes. The CSV method has complexity 2.
The symbol check found no added or lost module-level name.

The complete test-quality gate checked 1,014 files and 725 accepted findings.
It found zero new findings and zero parse errors. It analyzed 965 files and
retained 49 existing exclusions. No settings or baseline changed.
The required preflight read six inputs and checked three guide procedures.

The normal dependency audit failed with the same `ensurepip` `SIGABRT`.
It did not pass. The hashed UV alternative audited 105 applicable runtime
packages with strict hash requirements. It found zero vulnerabilities and
skipped zero packages. This result does not audit the development tool's Git
source or package variants for another operating system.

The structural writing checks passed. The licensed dictionary is absent, so
vocabulary grading remains unavailable. No dictionary or allowlist changed.
