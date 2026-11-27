# Implementation Plan: Cisco converter licensing and authorship decisions

## Summary

This plan adds one decision record for issue 4635. The record supports gate G1 of the parity plan. The record adds no code. It lists seven legal decisions for the owner. It keeps all protected source expression blocked until the owner records an approved path.

## Technical Context

- **Language**: Markdown only. The record changes no Python, JavaScript, or configuration file.
- **Dependencies**: None added. The record uses ste-linter for the STE gate and pytest for the process folder guard.
- **Storage**: None.
- **Evidence method**: GitHub read calls, local draft reads, and public Creative Commons legal code. The source repository is read through its public API only.
- **Constraints**: No protected source expression is copied. No release, publication, or cloud write is authorized.
- **Testing**: Local gates VC-STE and VC-GUARD, plus manual tests TS-03 to TS-06, as listed in tasks.md.

## Constitution Check

Path: `.specify/memory/constitution.md`. The line numbers refer to the file on main.

| Rule | Result | Reason |
| - | - | - |
| Principle I, Five-Item Rule (line 38) | Pass | Each route level holds the digits 0 to 4, so each level holds at most five children. The leaf is absent before this record (RC-25). The level specs/numbered/0/0/1/2/2 holds three children before this record (RC-26) and four children after it. |
| Principle I, managed roots and base-5 route (line 57) | Pass | The record uses the managed root specs/numbered/. The route digits 0 0 1 2 2 0 2 0 equal the base-5 digits of 4635 padded to eight places. See research.md, section Route derivation. |
| Principle II, Class-Based Architecture (line 91) | Pass | Not applicable: the record adds no code. |
| Principle III, Safety-First (line 113) | Pass | Not applicable: the record adds no input handling. |
| Principle IV, Full Deployment Pipeline (line 143) | Pass | The pipeline applies after a code change. This record changes no code. T-LOCAL-GATES still runs the applicable local gates. The container build does not run, because no listed product file changes (RC-28). |
| Principles V, VI, and VII (lines 182, 204, 235) | Pass | Not applicable: the record adds no code, no logging statement, and no comment in code. |
| Testing, compile check before each commit (lines 361 and 370) | Pass | T-LOCAL-GATES runs the compile gate before the commit. The expected output is no output. |
| Documentation, README update (lines 398 and 400) | Pass | Not applicable: the record changes no operation and no behavior. |
| Documentation, release fragment (line 409) | Fail, recorded | The constitution requires one fragment for each change. The changelog.d README (line 58) states that an internal-only change adds no fragment. This record follows the README (D-11). Analysis item A-6 asks the maintainer to resolve the conflict. |
| Audience Standard (line 416) | Pass | The record uses plain words for junior NOC engineers. |
| Issue-first (line 461) | Pass | Issue 4635 exists. T-PR adds the in-progress label before it creates the branch. |
| Fleet coordination, claim and overlap check (lines 500 to 505) | Pass | T-PR checks the open pull requests for the same files before it creates the branch. T012 changes parity files only after the owner records answers. |
| Branch naming (line 478) | Pass | The branch name chore/4635-cisco-converter-licensing-authorship uses an allowed type (D-12). |
| Required labels (line 489) | Pass | The pull request carries a type label, the scope label docs, and the in-progress label while work continues. |
| PR checklist (line 518) | Pass | T-PR writes Closes #4635, the local gate results, and the CI status in the pull request body. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    checklists/
      requirements.md
      decisions.md
      provenance.md
```

The design/contracts folder is omitted. No interface contract applies to a decision record (D-14).

### Source Code (repository root)

Not applicable: the record changes no source file. The converter files under src/interfaces/portals/cisco_config_converter/ stay unchanged.

## File Change Map

| Action | Repository path | Purpose | Task |
| - | - | - | - |
| Add | specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/spec.md | Requirements, clarifications, and user stories | T-PR |
| Add | specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/plan.md | Constitution check and file change map | T-PR |
| Add | specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/tasks.md | Ordered tasks and tests | T-PR |
| Add | specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/analysis.md | Consistency review and findings | T-PR |
| Add | specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md | Decisions, remote checks, and sources | T-PR |
| Add | specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/data-model.md | Decision entities and state transitions | T-PR |
| Add | specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/quickstart.md | Reproduction and verification commands | T-PR |
| Add | specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/checklists/requirements.md | Specification quality checklist | T-PR |
| Add | specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/checklists/decisions.md | Decision completeness checklist | T-PR |
| Add | specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/checklists/provenance.md | Provenance audit checklist | T-PR |
| Modify | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | Add the record link to T002 at line 29 | T012 |
| Modify | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/plan.md | Add the record link to the G1 row at line 125 | T012 |
| Delete | None | None | Not applicable |

No change occurs to LICENSE, README.md, CHANGELOG.md, changelog.d/, src/, or tests/.

## Dependencies

- The owner answers D-1 to D-7. Every reuse task depends on these answers.
- Parity tasks T022, T028, and T033 list T002 as a prerequisite (RC-67). T012 therefore unblocks those tasks only after the owner records answers.
- No package install is required. T-LOCAL-GATES uses the repository virtual environment during implementation.
- GitHub CLI calls are read-only in this drafting pass. T-PR and T-REMOTE-CI use write and watch actions in the implementation pass.
- Merges follow one serial merge slot until the owner validates a merge queue (RC-76).

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| The owner decides a reuse category without legal review | Legal exposure | D-1 to D-7 name legal review. TS-05 checks the review before any reuse request. |
| Converter files on main already hold protected source expression | Existing exposure | T011 audits the files against the pinned commit. A separate issue handles any removal. |
| The repositories are already public | Converter code is already visible | D-7 lists the publication options. This record changes no visibility setting. |
| The constitution and the changelog README conflict on fragments | Process confusion | D-11 applies the README rule. Analysis item A-6 asks the maintainer to resolve the text. |
| Auto-merge lands the record before human review | Legal decision text merges without review | FR-017, D-13, and T-MERGE keep the review point. |
| The source changes after the pinned commit | Stale evidence | The record keeps blob SHAs. The maintainer verifies them again before each decision. |

## Rollback Steps

1. Open a new pull request that reverts the merge commit of the record pull request. Do not force-push to main.
2. Confirm that the record folder and the two parity link lines are absent from main.
3. Caution: The revert removes the decision evidence from main. Keep a copy of the issue comment that names the record path.

## Complexity Tracking

Not applicable: the record adds no code and no hierarchy violation. Each new folder holds at most five children.
