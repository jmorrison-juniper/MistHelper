# Data Safety Checklist: SQLite Device Event Identity

**Purpose**: Check that the migration and the writer protect existing rows.
**Created**: 2026-11-26
**Feature**: `spec.md`, `plan.md`, and `design/contracts/migration-cli.md`.

## Preservation

- [x] CHK001 The migration writes a backup before any change. Source: FR-010 and the apply flow in `design/contracts/migration-cli.md`.
- [x] CHK002 The backup check reads `PRAGMA integrity_check` and compares sizes and row counts. Source: `design/data-model.md`, Backup File.
- [x] CHK003 The migration runs in one transaction and discards it on a count mismatch. Source: FR-013.
- [x] CHK004 The legacy table stays after the migration. Source: FR-015 and Decision D-10.
- [x] CHK005 The migration never deletes a backup file. Source: FR-015.
- [x] CHK006 The writer refuses writes into a legacy table. Source: FR-008 and `design/contracts/writer-result.md`.

## Irreversible Results

- [x] CHK007 The spec states that rows lost before the fix stay lost. The statement starts with `Warning:`.
- [x] CHK008 The deletion of legacy tables is a human decision. Source: Decision D-10 in `design/research.md`.
- [x] CHK009 The production run is a human decision. Source: Decision D-11 in `design/research.md`.

## Operator Control

- [x] CHK010 The migration defaults to a dry run. Source: FR-009.
- [x] CHK011 The migration needs the typed word `MIGRATE`. Source: FR-011.
- [x] CHK012 An export lock stops the migration at `BEGIN IMMEDIATE`. Source: spec Edge Cases.
- [x] CHK013 The migration exit codes separate a refusal from a usage error. Source: `design/contracts/migration-cli.md`.

## Limits

- [x] CHK014 The spec states that identical content merges. The statement starts with `Caution:`.
- [x] CHK015 The spec states that a new Mist field can add a row once. The statement starts with `Caution:`.
- [x] CHK016 The plan records the disk need of the backup plus the new table. Source: `plan.md` Risks and Mitigations.
