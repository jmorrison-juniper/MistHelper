# Preservation Procedure Checklist: Stranded branch preservation

**Purpose**: The operator checks each step of the procedure in `design/quickstart.md`.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Before the pilot

- [ ] CHK001 Step 1 prints `rows=505 unique=505`. A different count stops the procedure.
- [ ] CHK002 Step 2 prints `named_on_origin=505`. A lower count lists each missing name.
- [ ] CHK003 Step 3 prints the held and not held counts. Record both counts in the tracking issue.
- [ ] CHK004 Step 4 prints `invalid_names=0`. No `preserve/` tag line appears.
- [ ] CHK005 Step 5 dry run lists five refs and pushes none.

## The pilot

- [ ] CHK006 Step 6 prints `pilot_verified=5 of 5`.
- [ ] CHK007 Step 7 shows no workflow run with a `preserve/` head branch after five minutes.

## The batches

- [ ] CHK008 Step 8 reads the tips again and prints `missing_branches`. Each missing row has the result `absent` in the ledger.
- [ ] CHK009 Each batch exits with code 0. A failed batch stops the procedure, and the ledger names its rows.
- [ ] CHK010 Step 9 prints `tags_verified=505 of 505`. Any lower count lists the rows that failed.
- [ ] CHK011 Step 9 prints `named_branches_still_present` with the same count as the rows that still exist.

## After the batches

- [ ] CHK012 The ledger is posted as two comments on issue 4911.
- [ ] CHK013 The guide and the fragment pass Step 10.
- [ ] CHK014 The duplicate tracking issues are closed with a link, and Step 12 prints `1`.
- [ ] CHK015 The upstream issue and the deletion issue are linked from issue 4911.
- [ ] CHK016 The folder debt issue is linked from issue 4911.
- [ ] CHK017 The record pull request body names `Refs #4911`, and it names `Closes #4911` only after the report names no row.

## Rollback

- [ ] CHK018 Step 13 removes only the `preserve/` tags. The branch names still appear in `git ls-remote --heads origin`.
