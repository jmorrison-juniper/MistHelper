# Implementation Plan: SLE trend primary keys

**Branch**: `jmorrison-juniper-sle-trend-primary-keys` | **Date**: 2026-10-20 | **Spec**: [Specification](spec.md)

## Summary

Use complete window identities for both SLE trend endpoints.
Enrich response rows with request identifiers before export.
Use a shared SLE identity helper for validation and deterministic document keys.
Extend old SQLite tables with a nullable unique identity column.
Old rows keep NULL in that column. New rows receive a complete identity.
This permits one new keyed row beside legacy rows without migration or deletion.

## Technical Context

**Language/Version**: Python 3.13.
**Primary Dependencies**: mistapi 0.64, sqlite3, python-arango, pytest.
**Storage**: SQLite and ArangoDB. CSV retains request identifiers.
**Testing**: Real SQLite files under `tmp_path`, fake Arango collections, fake SDK responses.
**Target Platform**: Windows, macOS, Linux.
**Project Type**: Existing CLI export and persistence pipeline.
**Performance Goals**: One identity calculation per row and no legacy table scan or rebuild.
**Constraints**: Preserve every existing row and all unrelated endpoint key behavior.
**Scale/Scope**: Two repaired endpoints. Measure all 584 current registry entries.

## Constitution Check

The schema work has a specification before implementation.
The mandatory branch hook completed and reused the app-managed branch.
The managed numeric route contains eight base-5 segments.
New feature directories remain within five children.
Existing large modules and classes exceed structural limits. Narrow edits do not increase package children.
The shared helper enters the owned strategy module, which previously had one top-level declaration.
The schema utility module stays unchanged because its five top-level declarations already reach the limit.
New helper methods remain within 25 lines and five parameters.
Existing process-folder debt remains in `changelog.d/`. Add only the unique issue fragment.
Separate remediation: reduce existing folder and class debt through the established structure ratchet, not this schema repair.
The repair adds no transport or destructive operation.
Tests use no production credential and write only temporary files.
Use a Conventional Commit subject and PR title.
Do not enable auto-merge or merge because human review remains required.
Post-design result: these constraints remain satisfied.

## Project Structure

Edit the existing strategy registry, endpoint exporter, SQLite writer, and Arango writer.
Edit existing exporter, SQLite, and Arango tests.
Place the full-table guard in an existing guardrail module.
Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root.
Report the read-only analysis in the PR body.
Keep research, data model, quickstart, and checklists under `design/`.
No new external interface requires a contracts directory.

## Complexity Tracking

| Existing debt | Narrow change | Separate remediation |
| --- | --- | --- |
| Large strategy registry | Change only the two entries | Domain-based registry division |
| Large writer and exporter classes | Reuse current entry points with small helpers | Existing structure ratchet |
| Large test modules | Add focused scenarios without a new child | Test package grouping |
| Established changelog folder | One issue fragment | Process-folder migration |
