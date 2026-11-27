# Specification Quality Checklist: Radon Job Mando Pin Conflict

## Content Quality

- [x] CHK001 Each requirement has an ID from FR-001 to FR-010. Checked in `spec.md`.
- [x] CHK002 Each success criterion has an ID from SC-001 to SC-004 and a measurable result. Checked in `spec.md`.
- [x] CHK003 Each user story has a priority and an independent test. Checked in `spec.md`.
- [x] CHK004 The spec names the failing check, the failing step, and the failing rule. The check is `Radon (complexity)`, the step is the install step, and the rule is the resolution conflict.
- [x] CHK005 The spec names the commit that the run tested (`5bb4b385`) and the PR head (`e86098cd`). Both are in `design/research.md`.
- [x] CHK006 The spec names the repository paths because the defect lives in them. Explained: the change edits named files only.

## Requirement Completeness

- [x] CHK007 Out of Scope lists each item that this record does not change.
- [x] CHK008 Assumptions list each external fact that the record depends on.
- [x] CHK009 Clarifications record an answer for each question. Explained: the answers come from read-only evidence.
- [x] CHK010 Each requirement maps to at least one task and one test or check. Checked in `analysis.md`, Coverage Summary.
- [x] CHK011 Each remote claim has a row in `design/research.md` and in the STATUS file. Checked against the count of 55.
- [x] CHK012 Each decision names two or more alternatives, a chosen option, a reason, and a risk. Checked in `design/research.md`.

## Feature Readiness

- [x] CHK013 No unfinished text remains in the record. Checked by search for unfinished-text markers and ellipsis marks.
- [x] CHK014 Each task names a file path or states that no path applies. Checked in `tasks.md`.
- [x] CHK015 Each task names one verification command from the local gates table. Explained: the GitHub-only tasks use the Tests row before and after the change.
- [x] CHK016 Each safety statement starts with `Warning:` or `Caution:`. Checked in `plan.md` and `design/quickstart.md`.
- [x] CHK017 No human decision is required. Explained: no decision falls in the categories of brief section 6.
