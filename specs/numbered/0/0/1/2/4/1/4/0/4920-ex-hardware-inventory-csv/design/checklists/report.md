# Report and Scope Requirements Quality Checklist: EX Hardware Inventory CSV

**Purpose**: Test whether the report, scope, and concurrency requirements are complete, clear, and consistent

**Created**: 2026-11-24

**Feature**: [spec.md](../../spec.md)

**Note**: `[x]` means the reviewer found the requirement quality criterion satisfied. It does not mean that code exists.

## Report Content

- [x] CHK001 Is one authoritative place named for the column list and the column order? [Clarity, Contract report-csv, Spec §FR-025]
- [x] CHK002 Is "every field that the switch returned" defined to include nested values and attributes? [Clarity, Spec §FR-024, Data model §FlattenedItem]
- [x] CHK003 Is the row for a switch that returned no valid reply specified, with its allowed status values? [Completeness, Spec §FR-022, Data model §ReportRow]
- [x] CHK004 Is the way that a partial run shows in the console summary and the manifest specified? [Clarity, Spec §FR-018]
- [x] CHK005 Is the behavior for a run with no target specified? [Edge Case, Spec §FR-042]
- [x] CHK006 Is the natural key of a row specified and unique for every row type? [Measurability, Data model §ReportRow]
- [x] CHK007 Are the handling of repeated host names and shared serial numbers across organizations stated? [Coverage, Spec §Edge Cases, Data model §ReportRow]

## Scope Detection

- [x] CHK008 Are the criteria for MSP scope and for organization scope unambiguous and mutually exclusive? [Clarity, Spec §FR-003]
- [x] CHK009 Is the behavior for a refused or unreadable profile stated? [Coverage, Spec §FR-004]
- [x] CHK010 Is the behavior for an MSP list that fails in any way stated? [Coverage, Spec §FR-006]
- [x] CHK011 Is the set of organizations in MSP scope defined to include direct grants without repeats? [Completeness, Spec §FR-005]
- [x] CHK012 Is the rule for a credential with several grants and no MSP grant stated? [Gap, Spec §FR-005, Clarifications]

## Concurrency and Limits

- [x] CHK013 Are the variable name, default, range, and bad-value behavior all stated? [Completeness, Spec §FR-016]
- [x] CHK014 Does the spec say that the CLI and the portal read the same variable? [Consistency, Spec §FR-017]
- [x] CHK015 Is the target limit stated with its meaning for the CLI and for the portal? [Clarity, Spec §FR-013]
- [x] CHK016 Is the cancel behavior stated for queued and active targets? [Coverage, Spec §FR-018]

## Notes

- Review 2026-11-24 against the spec, the plan, and the contracts: all items pass after the spec edits that this review prompted.
