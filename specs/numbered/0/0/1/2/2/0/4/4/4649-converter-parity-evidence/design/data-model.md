# Data Model and State Safety

## Entities

### Comparison Row

- Natural key: row ID, `C01` to `C40`.
- Fields: observed capability, current state, remote checks, required check, requirement IDs, disposition, owner decision ID, parity tasks, and gate IDs.
- Rule: each key appears once in the register. Each row has exactly one disposition.

### Parity Task Status

- Natural key: parity task ID, `T001` to `T033`.
- Fields: title, status, remote checks, evidence path, blob SHA on main, and line.
- Rule: the status is one of `open`, `verified-present`, `partial`, or `absent`.

### Gate

- Natural key: gate ID, `G1`, `G2`, `G3`, `G4`, `G5`, or `GV`.
- Fields: scope, status, owner role, decision ID, decision date, evidence, and blocked work.
- Rule: the status is `open` or `passed`. A gate passes only with a decision ID and a UTC date.

### Owner Decision

- Natural key: decision ID in the form `OD-` followed by a number.
- Fields: subject ID (a row ID or a gate ID), owner role, approver name, approval date in UTC ISO 8601 form, outcome, and limit text.
- Rule: only an owner writes a decision. An unsupported-approved row needs an approved outcome and limit text.

### Remote Check

- Natural key: check ID, `R01` to `R77`.
- Fields: claim, path, ref, blob SHA, result, and line.
- Rule: the result is `present`, `absent`, `partial`, or `stale`. A line of 0 means that the check covers existence only.

### Audit Run

- Natural key: UTC run time.
- Fields: rows examined, tasks examined, gates examined, links examined, result, and failure messages.
- Rule: the result is `pass` only when every input is readable and every count is above zero.

## State Transitions

### Comparison Row

- `open` to `accepted`: a passing check exists and its blob SHA is recorded.
- `accepted` to `open`: the blob SHA changes, or the check fails.
- `open` to `unsupported-approved`: an owner decision with an approved outcome exists.
- `unsupported-approved` to `open`: the owner withdraws the decision, or the capability becomes supported.

### Gate

- `open` to `passed`: an owner decision exists with a decision ID and a UTC date.
- `passed` to `open`: the scope changes, or the owner revokes the decision.
- Gate G5 is evaluated per cloud write at run time. The register records G5 as `passed` only when its typed-confirmation and permission controls exist with tests.

### Parity Task Status

- `absent` to `partial`: a named deliverable exists in part.
- `partial` to `verified-present`: the task check passes.
- `verified-present` to `partial`: a deliverable or its check disappears.

### Completion Claim

- Refused to allowed: every comparison row is `accepted` or `unsupported-approved`, every gate is `passed`, and every parity task is `verified-present`.
- Allowed to refused: any row, gate, or task leaves its passing state.

## Invariants

1. The register has 40 rows, one for each comparison row.
2. The parity task table has 33 rows, one for each parity task.
3. The gate table has six rows, one for each gate.
4. Each accepted row cites a blob SHA on main that matches the working tree file.
5. Each owner decision names a human owner. The agent writes no decision.
6. No record stores a secret, a token, a credential, or customer configuration.
