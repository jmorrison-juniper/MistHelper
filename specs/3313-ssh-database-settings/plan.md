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

## Local Refresh on 2026-10-03

The [local-only grant](https://github.com/jmorrison-juniper/MistHelper/issues/3313#issuecomment-5967867728) limits this phase to local refresh.
Preserve the original range ending at `0970aad563681ca601ec49837f9ba123d8ba1038`.
Use the accepted predecessor `18127a874259732e9e6770de027e9485388b7592`.
Set `rebase.updateRefs=false` for the bounded migration.
Do not restore shared history or move a peer reference.

The migration has no conflict.
Every original reserved-path byte remains equal before the evidence refresh.
The fresh configuration and SSH export probes pass without a fixture correction.
Keep the existing synthetic discovery and backend boundaries.
Do not add another bypass or modify production database code.

Run the current DNS, constructor, index, natural-key, writer, output, and refusal tests.
Run the native guide and analyzer behavior suite.
Run the required six-input preflight before each quality analyzer command.
Compare every field of all complete findings against the preserved report.
Do not modify the baseline, detector, exclusion, or threshold.

Prepare the current 23-item pull request template as a session artifact only.
Record exact commands, current results, and missing capabilities.
Preserve historical red evidence separately from current green evidence.
Commit the evidence locally and verify the exact source, tree, lineage, and twelve-path boundary.
Then pause for the coordinator.

The earlier protected delivery plan remains conditional.
This local-only grant authorizes none of its remote steps.

## Second Local Refresh on the Terminal Predecessor

The coordinator directs only local refresh on `fa71c32dcc25ddb95ca1c73146e072e24b4286b1`.
The complete accepted tree is `4ab7c58cc6decdfd511f7aeb011341f0931aff25`.
Preserve the complete previously accepted three-commit range and all 42 artifact hashes before migration.
Keep the original two-commit range intact.

The bounded own-branch rebase uses `rebase.updateRefs=false`.
It has no conflict and preserves all three patches.
All eight original non-specification blobs and nineteen current protected blobs remain equal.
No peer reference, shared history, or separately owned fixture changes.

The fresh owned scope contains the same 91 unique cases.
The related scope contains the same 951 unique cases.
Both ordered memberships match the accepted evidence.
The related scope retains one existing registry skip only.
The native guide and analyzer causal scope contains 530 passing cases.

The current full analyzer discovers 1,048 files and analyzes 1,000 modules.
Every field of all 725 findings matches both original and accepted reports.
The configuration and all 48 exclusion records remain equal.
The selected committed comparison is separate from the full scan.
Its omitted-root and stale-baseline records are not pytest skips.

Refresh only the four owned specification records and an offline template artifact.
Use ordinary local Git commit behavior with no hook skip override.
Keep the expected native audit abort and all capability limits explicit.
Seal the exact final head, tree, lineage, protected bytes, template, and local evidence.
Then freeze for the coordinator without any remote action.
