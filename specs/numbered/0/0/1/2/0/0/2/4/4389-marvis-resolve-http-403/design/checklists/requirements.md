# Requirements Quality Checklist: Marvis resolve HTTP 403 handling

**Purpose**: Check the quality of `spec.md` before the plan and the tasks depend on it.
**Created**: 2026-11-26
**Feature**: `spec.md` in the parent folder

## Content quality

- [x] CHK001 Each user story states one operator outcome. The stories cover the reason, the stop, and the docs.
- [x] CHK002 Each user story has an independent test that needs no live Mist call.
- [x] CHK003 Each user story has priority P1 or P2, and the reason for the priority.
- [x] CHK004 The spec names no code structure except in the transport section. The transport section is a template requirement.
- [x] CHK005 The spec uses plain words for the operator outcomes.

## Requirement completeness

- [x] CHK006 Each functional requirement uses MUST or MAY, and names one behavior.
- [x] CHK007 Each functional requirement maps to at least one task and one test. The map is in `analysis.md`.
- [x] CHK008 The edge cases cover the no-answer case, the 429 case, the stop signal, the cap, and the empty acknowledgement.
- [x] CHK009 The out-of-scope list names the category change, the pre-flight role check, and the live calls.
- [x] CHK010 The assumptions name the evidence that the issue supplies.
- [x] CHK011 The clarifications record each answer with its source line.

## Success criteria

- [x] CHK012 Each success criterion is measurable with a count, a result, or a gate score.
- [x] CHK013 SC-001 names the base commit, so a reviewer can run the test on that commit.
- [x] CHK014 SC-004 points to the gates in `tasks.md`, so the criterion is testable.

## Transport and safety

- [x] CHK015 The transport section names the mistapi method and the local SDK line.
- [x] CHK016 The transport section states that no endpoint method exists, with the evidence.
- [x] CHK017 The contract-test evidence covers SDK insufficiency, authentication, parity, failure safety, and redaction.
- [x] CHK018 The spec states that the typed confirmation stays unchanged.
- [x] CHK019 The spec keeps the cause unverified and names the evidence that a human must collect.

## Writing style

- CHK020 No unfilled template text appears in the spec. The only markers are the mask markers that the contract defines.
- [x] CHK021 No semicolon, contraction, or Latin abbreviation appears in the spec.
- [x] CHK022 Each functional requirement has 20 words or fewer per sentence.
