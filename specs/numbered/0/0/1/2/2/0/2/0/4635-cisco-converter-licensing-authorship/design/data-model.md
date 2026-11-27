# Data Model: Cisco converter licensing and authorship decisions

## Entities

| Entity | Natural key | Fields | Rules |
| - | - | - | - |
| Reuse category | Category name: source-code, text, mapping, or asset | Owner answer, approved scope, blocked scope | Four rows. Each row starts in the blocked state. |
| Decision | D-n, from D-1 to D-15 | Question, options, recommended option, chosen option, human flag, owner | Seven rows carry the human flag. Each legal decision names at least two options. |
| Option | Decision key and letter, for example D-2 and option A | Summary and evidence keys | Each decision lists at least two options. Each decision names one recommended option. |
| Evidence row | RC-nn, from RC-01 to RC-77 | Claim, path, ref, blob SHA, result, and line | Each row appears once in design/research.md and once in the STATUS remote_checks array. |
| Gate | G1 to G5 | Required evidence and blocked work | Rows from the parity plan. G1 is the legal gate. |
| Owner | GitHub login | Role | The login is jmorrison-juniper. Legal review adds a second role. |
| Converter file | Repository path | Blob SHA and audit state | Nine rows in analysis.md. The initial state is not reviewed. |

## State transitions

Reuse category:

- Blocked, the default state, moves to approved when the owner records an approved option and T012 links the record.
- Blocked stays blocked when the owner records no answer.
- Blocked stays blocked when the owner records option A or option C for no reuse.
- Approved moves back to blocked when the owner records a new answer that withdraws approval.

Decision:

- Open, with the HUMAN-DECISION-REQUIRED marker, moves to answered when the owner records an answer in spec.md and research.md.
- Answered moves to applied when T012 links the answer in the parity files.
- Answered moves to superseded when the owner records a later answer with a new date.
- Chosen decisions D-8 to D-15 stay chosen unless a later record supersedes them.

Evidence row:

- Present moves to stale when the blob SHA differs on re-verification.
- Stale moves to present when the maintainer records a new row with the new blob SHA.
- Absent moves to present when a later record creates the path. RC-25 is absent before this record.

Converter file audit:

- Not reviewed moves to one result: matches protected expression, no match found, or not compared.
- A result of matches protected expression opens a separate removal issue.

## Invariants

- A reuse category leaves the blocked state only through an approved decision row.
- The count of evidence rows in research.md equals the count of entries in the STATUS remote_checks array.
- Each decision key appears once in research.md.
- Each legal decision carries the HUMAN-DECISION-REQUIRED marker until the owner answers it.
