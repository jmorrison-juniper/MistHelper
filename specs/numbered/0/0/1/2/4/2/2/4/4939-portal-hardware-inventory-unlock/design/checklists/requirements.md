# Requirements checklist: Portal hardware inventory unlock without the free-form shell

- [x] Every requirement has an ID from FR-001 to FR-016 in spec.md.
- [x] Every requirement maps to at least one task and at least one test case (analysis.md, section 1).
- [x] Every success criterion from SC-001 to SC-005 names its test IDs.
- [x] Edge cases cover invalid flag values, both flags true, flag change after preview, browser fields, MSP scope, and menu 309.
- [x] Scope is bounded by the non-goals list in spec.md.
- [x] Assumptions name the flag read rule (RC-124, RC-125) and the 300 second preview lifetime (RC-080).
- [x] Clarifications record each question and answer.
- [x] The open decision is marked `HUMAN-DECISION-REQUIRED` (D-1) and names the recommended option 1.
- [x] Each code claim cites a path and a line checked on GitHub `main` (research.md, remote verification table).
- [x] Each claim that could not be verified appears in research.md under Unverified (U-1 to U-10).
- [x] Style: prose has no semicolons, contractions, or Latin abbreviations. Each irreversible-harm statement starts with `Warning:`.
- [x] Explained: the Mist Cloud Transport section names code paths. The owner choice depends on which code path receives the unlock.
- [x] Explained: the edge case for an unknown output format stays in spec.md. Its current behavior is Unverified (U-9).
