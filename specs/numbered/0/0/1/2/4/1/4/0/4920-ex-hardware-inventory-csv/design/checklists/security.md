# Security Requirements Quality Checklist: EX Hardware Inventory CSV

**Purpose**: Test whether the security and safety requirements are complete, clear, and consistent

**Created**: 2026-11-24

**Feature**: [spec.md](../../spec.md)

**Note**: `[x]` means the reviewer found the requirement quality criterion satisfied. It does not mean that code exists.

## Credential and Secret Handling

- [x] CHK001 Are the places where a credential must never appear (console, log, report, saved files, issue text) all named? [Completeness, Spec §FR-037]
- [x] CHK002 Is the handling of a device reply that carries a credential specified as a rejected reply with a failed outcome? [Coverage, Spec §US5 AC2, §FR-015]
- [x] CHK003 Is the redaction point stated at the logging boundary and not at each caller? [Clarity, Spec §FR-037, Plan §Constitution Check]
- [x] CHK004 Are the rules for the shared request ledger and the organization binding free of any credential exposure? [Coverage, Plan §Complexity Tracking]

## Consent and Command Safety

- [x] CHK005 Is the confirmation phrase specified exactly, including its dependence on the target count? [Clarity, Spec §FR-029, Contract cli-menu]
- [x] CHK006 Are the outcomes for a wrong phrase, end of input, and an interrupt all stated? [Coverage, Spec §US1 AC5, §FR-029]
- [x] CHK007 Is the fixed, read-only command stated, with a rule that operator text never reaches a device? [Clarity, Spec §FR-014]
- [x] CHK008 Is the rule that the run covers only confirmed targets stated for a long run? [Gap, Contract cli-menu §Run rules]
- [x] CHK009 Is the portal shell lock kept and stated as unchanged? [Consistency, Contract portal §Locks and limits]

## Data Exposure and Limits

- [x] CHK010 Are the cell characters that a spreadsheet can read as a formula listed the same way in the spec and the contract? [Consistency, Spec §FR-026, Contract report-csv]
- [x] CHK011 Is a size limit for the report stated? [Completeness, Spec §FR-041]
- [x] CHK012 Is the handling of HTTP 429 stated so that no tight retry loop can form? [Clarity, Spec §FR-039]
- [x] CHK013 Is the data exposure of an MSP report to several customers acknowledged? [Assumption, Spec §Assumptions]
- [x] CHK014 Is live validation limited to read-only commands on one organization? [Clarity, Spec §FR-040]

## Notes

- Review 2026-11-24 against the spec and the plan after clarify: all items pass. The review added FR-026 characters, FR-039 on HTTP 429, FR-041, and the MSP data assumption to the spec.
