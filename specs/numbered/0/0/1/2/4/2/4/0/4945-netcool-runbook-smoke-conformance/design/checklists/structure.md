# Structure Requirements Quality Checklist: Netcool Runbook Smoke Package Conformance

**Purpose**: Check that the structure requirements and their measures are complete and testable.
**Created**: 2026-11-26
**Feature**: `spec.md` FR-001 to FR-010, `plan.md`, and `design/research.md` decisions D-1 to D-8

## Function Limits

- [x] CHK101 The code-line limit names what it excludes. Evidence: FR-001 excludes docstring lines, comment-only lines, and blank lines. Decision D-1 records the rule.
- [x] CHK102 The parameter limit names what it excludes. Evidence: FR-002 excludes `self` and `cls`.
- [x] CHK103 The block limit names the block and the statement count. Evidence: FR-003 and decision D-2 name the body block, the five-block limit, and the five-statement limit per block.
- [x] CHK104 The fourteen named functions match the measure. Evidence: `research.md` section Structure measurements reports 14 functions, the issue lists 14, and the rows R74 to R87 cite each one.

## Class, Module, and Directory Limits

- [x] CHK105 The class limit names the counted members. Evidence: FR-004 and decision D-5 name methods only.
- [x] CHK106 The module limit names the logger rule. Evidence: FR-005 and decision D-3 count the logger.
- [x] CHK107 The directory limit names the excluded file. Evidence: FR-006 and decision D-4 exclude `__init__.py`, as the nested guard does (row R55).

## Layout and Naming

- [x] CHK108 The target layout names each new path. Evidence: `plan.md`, section File-by-file change map.
- [x] CHK109 The import rule names the old and the new path for each name. Evidence: `design/contracts/package-layout.md`.
- [x] CHK110 The no-shim rule has a test. Evidence: FR-008 and TEST-10.
- [x] CHK111 The entry point rule has a test. Evidence: FR-010, TEST-10, and the runbook command in row R48.
