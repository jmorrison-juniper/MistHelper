# Specification Quality Checklist: Reviewed Restore and Partial-Operation Recovery

**Purpose**: Check the quality of `spec.md`, `plan.md`, `tasks.md`, and the design artifacts before implementation.
**Created**: 2026-11-26
**Feature**: [spec.md](../../spec.md)

## Content Quality

- [x] CHK001 The specification states the user value of each story. Each story has a priority and an independent test.
- [x] CHK002 The specification names no implementation language in the requirements. Mist and SDK names appear only in the transport section.
- [x] CHK003 Each clarification has a recorded answer and a source.

## Requirement Completeness

- [x] CHK004 Every functional requirement FR-001 to FR-028 has at least one task and at least one test or guard. The coverage table in `analysis.md` lists each mapping.
- [x] CHK005 Every success criterion SC-001 to SC-008 names a measurable check. `analysis.md` maps each criterion to a test or guard.
- [x] CHK006 Each edge case states the expected result.
- [x] CHK007 Each assumption states its value and its owner.
- [x] CHK008 Each out-of-scope item names the issue that owns it.
- [x] CHK009 No placeholder text remains in any deliverable. The only allowed marker is HUMAN-DECISION-REQUIRED.
- [x] CHK010 Each decision names two or more alternatives, the chosen option, the reason, and the risk. `design/research.md` holds decisions D-1 to D-27.
- [x] CHK011 Each Mist function named in the specification exists in the installed SDK. Remote checks 97 to 99 record the definitions.
- [x] CHK012 Each Mist claim cites the local OpenAPI file, and each SDK claim cites an installed SDK file. Remote checks 75 to 104 record them.
- [x] CHK013 Each unverified claim appears in the Unverified list of `design/research.md` with its reason.

## Feature Readiness

- [x] CHK014 The route number matches the base-5 result. Decimal 4646 gives `0/0/1/2/2/0/4/1`.
- [x] CHK015 Each new directory holds five children or fewer. The capacity inventory in `plan.md` records each count.
- [x] CHK016 The human decisions D-14 and D-20 are marked HUMAN-DECISION-REQUIRED. They block writes until the owner decides.
- [x] CHK017 The remote check count is 108 in `design/research.md`, in the STATUS file, and in the summary.
- [x] CHK018 The writing style avoids semicolons, contractions, Latin abbreviations, and phrasal verbs in the deliverables.

## Notes

- Checked items cite the file and the section that holds the evidence.
- Items CHK016 and CHK017 depend on the owner decision and on the count check in the self-review.
