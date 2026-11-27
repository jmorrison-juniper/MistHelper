# Feature Specification: Cisco converter licensing and authorship decisions

**Issue**: #4635, "[Spec]: Resolve Cisco converter licensing and authorship decisions"
**Record path**: specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/
**Status**: Draft. Seven legal decisions wait for the owner. Each one is marked HUMAN-DECISION-REQUIRED.
**Related**: #4224 (parent feature), PR #4596 (parity record), specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/

## Clarifications

### Session 2026-11-26

- Q1. Who holds the copyright in the source, and who may license it? Answer: Not decided. HUMAN-DECISION-REQUIRED (D-1). The owner decides with legal review.
- Q2. May protected source code be reused? Answer: Not decided. HUMAN-DECISION-REQUIRED (D-2). The owner decides with legal review.
- Q3. May protected source text be reused? Answer: Not decided. HUMAN-DECISION-REQUIRED (D-3). The owner decides with legal review.
- Q4. May protected source mappings be reused? Answer: Not decided. HUMAN-DECISION-REQUIRED (D-4). The owner decides with legal review.
- Q5. May protected source assets be reused? Answer: Not decided. HUMAN-DECISION-REQUIRED (D-5). The owner decides with legal review.
- Q6. Which independent-authorship rules apply? Answer: Not decided. HUMAN-DECISION-REQUIRED (D-6). The owner decides with legal review.
- Q7. Which distribution path applies? Answer: Not decided. HUMAN-DECISION-REQUIRED (D-7). The owner decides with legal review.
- Q8. Does this record need a changelog fragment? Answer: No. This record is internal-only. The reason appears in the PR body (D-11).
- Q9. Which branch type applies? Answer: chore. The constitution lists fix, feat, and chore (D-12).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record each reuse decision or its open state (Priority: P1)

The owner reads one decision for each reuse category. Each decision names the options, the evidence, a recommended option, and an owner. Engineering uses the result to see which work stays blocked.

**Why this priority**: Gate G1 blocks every reuse and every release of the Cisco converter. The parity work waits for G1.

**Independent Test**: Read the decisions in design/research.md. Confirm that D-1 to D-7 each show two or more options, the evidence rows, the recommended option, and the owner.

**Acceptance Scenarios**:

1. **Given** the record, **When** the owner reads D-2, **Then** the owner sees at least two options and the evidence for each option.
2. **Given** the owner records no answer, **When** engineering reads the record, **Then** every reuse category stays blocked.

### User Story 2 - Connect the decision to the parity tasks (Priority: P1)

The maintainer verifies that the recorded decision reaches the parity task list. A reuse request waits until this check passes.

**Why this priority**: The issue test plan requires this check before any reuse request proceeds.

**Independent Test**: After the owner records answers, read parity tasks.md line 29. Confirm that T002 names this record path and the approved scope.

**Acceptance Scenarios**:

1. **Given** the owner records an approval, **When** the maintainer reads parity T002, **Then** T002 names the approved scope and this record path.
2. **Given** no answer exists, **When** a reuse request arrives, **Then** the request waits for the gate G1 evidence.

### User Story 3 - See provenance gaps in converter files on main (Priority: P2)

The maintainer sees which converter files on main lack a provenance review. The analysis lists each file, its blob SHA, and its audit state.

**Why this priority**: Converter files merged before the decision can hold protected source expression. The owner needs that fact before any release.

**Independent Test**: Read analysis.md. Confirm that each converter file on main appears with its blob SHA and its audit state.

**Acceptance Scenarios**:

1. **Given** PR #4226 merged the converter files, **When** the maintainer reads the analysis, **Then** each file shows the state not reviewed.

### User Story 4 - Compare distribution paths with publication evidence (Priority: P2)

The owner compares the distribution path options. Each option cites the workflow or repository setting that it affects.

**Why this priority**: Publication can reach users before the legal decision. The owner must see each publication route first.

**Independent Test**: Read D-7 in design/research.md. Confirm that each option cites at least one remote check row.

**Acceptance Scenarios**:

1. **Given** the container build copies src, **When** the owner reads D-7, **Then** the option text names the container build path.

### Edge Cases

- The source license changes after commit d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c. The evidence becomes stale. The maintainer verifies the blob SHA again before any decision.
- The owner approves one reuse category only. The other three categories stay blocked.
- The owner approves a path that needs permission from a holder. The path stays blocked until written permission exists.
- The source repository becomes private or is removed. The record keeps the pinned commit SHA and the blob SHA as the reviewed evidence.
- An audit finds protected source expression in converter files. The owner opens a separate issue for the removal. One issue holds one concern.
- Legal review does not finish. All reuse categories stay blocked. No default approval exists.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The record MUST list each legal question with its options, the evidence for each option, a recommended option, and an owner.
- **FR-002**: The record MUST mark each legal decision HUMAN-DECISION-REQUIRED and MUST NOT decide it.
- **FR-003**: The record MUST assess source-code, text, mapping, and asset reuse as four separate reuse categories.
- **FR-004**: The record MUST list the distribution path options and mark the approved path unresolved.
- **FR-005**: The record MUST list the independent-authorship rule options and mark the approved rules unresolved.
- **FR-006**: The record MUST keep all protected source expression blocked until an explicit compatible path is approved.
- **FR-007**: The record MUST keep gate G1 separate from gates G2, G3, G4, and G5 of the parity plan.
- **FR-008**: The record MUST NOT authorize implementation, source reuse, publication, or release.
- **FR-009**: The record MUST cite the source license with its path, ref, blob SHA, and line.
- **FR-010**: The record MUST cite the MistHelper license with its path, ref, blob SHA, and line.
- **FR-011**: The record MUST report the provenance state of each converter file on main.
- **FR-012**: The record MUST link this record from parity T002 and gate G1 after the owner records answers.
- **FR-013**: The record MUST name each related issue and state its link to issue 4635.
- **FR-014**: The record MUST exclude legal communications, customer data, tokens, and secrets.
- **FR-015**: The record MUST use Simplified Technical English and pass the STE gate with a score of 80 or above.
- **FR-016**: The record MUST follow the constitution rules for the route, the five-item structure, documentation, branch names, and labels.
- **FR-017**: The record MUST keep the needs-human-review label and block auto-merge until a human review completes.
- **FR-018**: The record MUST list each remote check once in design/research.md and once in the STATUS remote_checks array.

### Key Entities

- **Reuse category**: One of source-code, text, mapping, or asset. The key is the category name.
- **Decision**: One legal question or one technical choice. The key is D-n.
- **Remote check**: One evidence row for a path, a commit, or a source. The key is RC-nn.
- **Gate**: One approval point in the parity plan. The keys are G1 to G5.
- **Protected source expression**: Any code, text, mapping, or asset from the source repository.
- **Independent authorship**: Writing the converter without copying protected source expression.
- **Distribution path**: The route that publishes converter code. The routes are a repository, a release, or a container image.
- **Owner**: The repository owner who records each answer. The account is jmorrison-juniper.
- **Maintainer**: The person who verifies that a recorded answer reaches the parity tasks.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Four of four reuse categories show a decision and an owner. Each open category carries the HUMAN-DECISION-REQUIRED marker.
- **SC-002**: The record lists 77 remote checks. The STATUS remote_checks array and design/research.md show the same 77 rows.
- **SC-003**: Each Markdown file in the record scores 80 or above in the STE gate.
- **SC-004**: All 18 functional requirements map to at least one task and at least one test.
- **SC-005**: No task authorizes protected source expression before the owner records an approval.

## Out of Scope

- Writing a license, a copyright notice, or any other legal text.
- Deciding copyright ownership, license validity, or license compatibility.
- Writing, changing, or removing converter code or converter tests.
- Publishing, tagging, or releasing a version or a container image.
- Cloud authorization, Mist write behavior, and operator approval (gates G4 and G5).
- Editing CHANGELOG.md or adding a changelog fragment.

## Assumptions

- The issue body and the owner comment dated 2026-11-08 remain current on 2026-11-26.
- Commit d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c is the default branch head of the source on 2026-11-26.
- The GitHub account jmorrison-juniper acts as the owner. The issue comment carries the OWNER association.
- Legal review exists for this decision. The evidence does not name the counsel.
- The needs-human-review label stays on issue 4635 until the owner completes the review.
