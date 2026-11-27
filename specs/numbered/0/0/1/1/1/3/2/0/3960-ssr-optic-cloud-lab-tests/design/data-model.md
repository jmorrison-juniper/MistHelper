# Data Model: SSR optic and Mist cloud path lab tests

This model names the records that the process uses. Each record has a natural key and a state. No database stores these records. The runbook, the changelog fragment, and the issue thread hold them.

## LabStep

- **Natural key**: The step identifier, one of H-0 to H-8.
- **Fields**:
  - Identifier: H-0 to H-8, as tasks.md names them.
  - Release string: the software release that the router reports.
  - Command: the command text, copied without change.
  - Target: the runbook line or table row that receives the output.
  - Owner: owner-only for every step in this model.
- **States**: open, then recorded, then applied, then merged. H-6 adds two states between open and recorded: confirmed, then blocked, then restored.
- **Transitions**:
  - open to confirmed: the owner types the confirmation phrase from D-8 with the router name. Only H-6 uses this transition.
  - confirmed to blocked: the owner blocks TCP port 443 on the lab router.
  - blocked to restored: the owner removes the block rule and repeats H-5.
  - recorded to applied: the implementer writes the sanitized output to the target (T012).
  - applied to merged: the pull request merges (T-MERGE).

## Statement

- **Natural key**: The row number in the section 14 verification table, from 360 to 365.
- **Fields**:
  - Statement: the text in the first column. The text does not change.
  - Source: the text in the second column. The text does not change.
  - Lab test: the text in the third column. The text starts as Not run.
- **States**: Not run, then Run on a release string.
- **Transitions**: Not run to Run on. The transition needs one recorded output for the matching LabStep (FR-005, FR-016).

## SanitizedOutput

- **Natural key**: The LabStep identifier and the release string.
- **Fields**:
  - Text: the copied output after sanitization.
  - Removed item count: a count of each removed type. The record never stores a removed value.
  - Check result: pass or fail against the checklist in contracts/lab-output-record.md.
- **States**: draft, then checked, then committed. A draft that fails the check returns to the owner. A checked output enters the runbook as a committed change.

## RemoteCheck

- **Natural key**: The check identifier, from C-01 to C-69.
- **Fields**: claim, path, ref, blob SHA, result, and line. The values match design/research.md.
- **States**: present, absent, partial, or stale.
- **Transitions**: A check changes state only when a new read of main shows a different result. The record then needs a new check identifier.

## Decision

- **Natural key**: The decision identifier, from D-1 to D-8.
- **Fields**: decision, alternatives considered, rationale, risk, and the human decision flag.
- **States**: decided. The record marks no decision as open, because no decision needs a human answer.

## Task

- **Natural key**: The task identifier, from T001 to T014, T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE.
- **Fields**: status, owner, requirements, paths, gate, and dependencies.
- **States**: open, verified-present, partial, or absent.
- **Transitions**: open to verified-present when the read-back command in design/quickstart.md passes.

## Relationships

- One LabStep maps to one Statement row. H-2 maps to row 361 and to a new section 11 row. H-1 maps to row 360.
- One Statement holds at most one SanitizedOutput at a time.
- One Task names zero or more LabStep identifiers and zero or more RemoteCheck identifiers.
- One Decision maps to one or more requirement identifiers. D-2 maps to FR-001 and FR-002. D-3 maps to FR-007. D-8 maps to FR-012.
