# Implementation Plan: SSH database settings

**Date**: 2026-10-01

**Issue**: [#3313](https://github.com/jmorrison-juniper/MistHelper/issues/3313)

**Specification**: [spec.md](spec.md)

## Technical Context

The runtime writer uses Bash and an explicit list of configuration names.
It quotes each value with `printf '%q'`, replaces the file atomically, and sets mode `0400`.
The current list omits all seven database names.

The test environment uses Python 3.13 and the unchanged runtime and development manifests.
The existing Bash capability helper remains unchanged.
New contracts require that capability and fail if it is absent.

## Constitution Check

The production change stays inside the existing writer.
It changes no database implementation, session reader, output default, or dependency.
The tests use semantic classes and bounded methods.
Existing oversized directories and the writer allowlist are established structure.
This repair does not restructure that unrelated debt.
A separate future change can divide the existing container test directory.

Warning: a wider mode can expose the API token and two database passwords to other accounts.
The session file contains these credentials.
Tests use generated fixture values and do not read real credentials.
Reports contain names and counts only.

## Phase 0 - Research

The issue and its comments identify the missing allowlist names.
The actual writer confirms eleven Mist and proxy names only.
The actual `DatabaseConfig.from_env()` confirms all seven database settings.

The live claim has no prior assignee or active reservation.
Every file page of all twelve open pull requests has no overlap with this change.
Reservation comment `5938152840` identifies app session `d3329b2e-83ed-47f1-94c9-e7e5ce30ec9c`.

The legacy SpecKit hooks create branches and modify shared feature state.
The app already created the isolated branch.
Use the specification, plan, tasks, implementation, and analysis as feature-only files.
Do not execute a raw branch command or modify shared `.specify` state.

## Phase 1 - Design and Contracts

Add the seven required names after the existing proxy names.
Update the two credential warnings and the explanation above the list.
Keep the writer algorithm unchanged.

The harness runs the actual Bash writer with a clean environment.
It sources the generated file through positional arguments in a second clean shell.
It sends expected fixture values through standard input, not shell command text.
The probe compares values internally and prints measured counts only.

The configuration probe calls the actual `DatabaseConfig.from_env()`.
It replaces host discovery only, so no network or production store is involved.
The export probe calls the actual `DataExporter` and `DatabaseRouter`.
Owned fixture writers receive and retain the records.
The probe verifies the stored records, the configuration, and the CSV copy.

The SSH fixture uses the existing Paramiko dependency.
It creates temporary keys in memory and authenticates one owned loopback connection.
It accepts one fixed command and starts the fresh-shell export probe.
It closes every socket, transport, channel, and worker before the test ends.
No container profile or production service is required.

## Phase 2 - Implementation

Create the contracts before the production edit.
Record the missing-name and missing-configuration failures through the actual writer.
Then add the names and run the same contracts again.
Update the SSH guide and the unique release-note fragment.

## Validation

Run Bash syntax, existing Bash support tests, configuration contracts, and the isolated SSH export.
Verify all seven names with empty, plain, space, quote, dollar, newline, and Unicode cases.
Verify name-only output, unrelated-secret exclusion, shell data safety, owner, mode, and replacement.
Run the configured Ruff, Black, exact CI mypy scope, Bandit, and unchanged test-quality ratchet.
Run documentation links and configured STE heuristics.
Report the unavailable licensed dictionary explicitly.
Run the strict runtime dependency audit without changing dependency constraints.

## Delivery

Create local Conventional Commits commits with the required co-author trailer.
Report the exact files, commit, red and green evidence, measured SSH layer, and gate results.
Wait for the parent grant before a push or pull request.
After the grant, rebase onto that exact `main` revision and repeat the local gates.
Use the full pull request template and the protected exact-head squash merge.
Run the relevant local tests against the actual merged `main` SHA in this isolated worktree.
