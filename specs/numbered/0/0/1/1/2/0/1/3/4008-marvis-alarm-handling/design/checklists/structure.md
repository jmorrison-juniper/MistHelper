# Structure Checklist: Isolate Marvis Alarm Handling Modules

**Purpose**: Confirm that each structural level stays within the five-child limit and that each function measurement is recorded.
**Created**: 2026-11-26
**Feature**: `plan.md`, section Touched existing violations

## Child Counts

- [x] CHK001 The actions package holds five children after the move: `alarm_handling`, `client.py`, `model.py`, `operation.py`, and `selection.py` (research R01 and R04, tasks T004).
- [x] CHK002 The `alarm_handling` package holds two children after the move: `acknowledgement.py` and `alarms.py` (tasks T003 and T004).
- [x] CHK003 The record root holds five children: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/` (plan, Project Structure).
- [x] CHK004 The `design/` folder holds four children: `research.md`, `data-model.md`, `quickstart.md`, and `checklists/`. The `contracts/` folder is omitted (plan, Contracts).
- [x] CHK005 The `design/checklists/` folder holds three children: `requirements.md`, `structure.md`, and `publication.md` (plan, Project Structure).
- [x] CHK006 The route parent `specs/numbered/0/0/1/1` already holds five children. The route reuses child `2`, so no child is added there (research R64).

## Function Measurements

- [x] CHK007 `acknowledgement.py` holds 6 functions, with a maximum of 3 parameters in `__init__`, and `_send_batches` at 28 lines (plan, Function and parameter counts).
- [x] CHK008 `alarms.py` holds 10 functions, with a maximum of 3 parameters in `_keep`, and `apply` at 29 lines (plan, Function and parameter counts).
- [x] CHK009 The maximum logical block count in each moved module is 3, below the limit of 5 (plan, Function and parameter counts).
- [x] CHK010 The operations-per-statement limit is not counted, and the reason is recorded in the Unverified list (research U-6).

## Module Names

- [x] CHK011 `acknowledgement.py` holds 7 top-level names, `alarms.py` holds 6, and `operation.py` holds 25. Each count exceeds the limit of 5, and each is recorded (plan, Touched existing violations, research E-6).
- [x] CHK012 The moved modules add no top-level name, so the move creates no new violation (plan, Constitution Check).
