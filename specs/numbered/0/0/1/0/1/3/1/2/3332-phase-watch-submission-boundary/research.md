# Research: Phase-Watch Submission Boundary

## Decision 1: Keep Child 1 Wording-Only

**Decision**: Correct the promise without changing the firmware path.

**Rationale**: Issue #3332 states that the portal submits all device families
before the phase watch starts. Child 1 needs no firmware behavior decision.

**Alternatives considered**:

- Gate firmware submission by phase. Rejected because this is Child 2 behavior.
- Add a settle timeout or reachability rule. Rejected because the owner has not
  approved those decisions.

## Decision 2: Use One Canonical Boundary

**Decision**: Use these exact statements:

1. `The phase watch starts after the portal sends the upgrade requests.`
2. `It observes the submitted work and sends no firmware request.`
3. `It does not prove that the cloud accepted each request or that the portal sent device types in this order.`

**Rationale**: The three statements define time, action, and proof limits. They
do not imply a behavior change.

**Alternatives considered**:

- State that the phase watch protects submission order. Rejected because the
  current submission sends all families before the watch.
- State that the cloud accepted each request. Rejected because a submitted
  request can have an uncertain result.

## Decision 3: Use One Direct Safety Warning

**Decision**: Use this exact operator warning:

`Warning: If a submission result is uncertain, do not start another upgrade. A second upgrade can target the same devices.`

**Rationale**: The warning gives one safe instruction. It defines no retry,
recovery, or resume behavior.

**Alternatives considered**:

- Tell the operator to retry. Rejected because retry behavior is excluded.
- Tell the operator to resume. Rejected because resume behavior is excluded.
- Name a timeout. Rejected because settle timing is excluded.

## Decision 4: Assert Rendered Text Directly

**Decision**: Add direct literal assertions for all four strings in
`test_org_phase_watch_contract.py`.

**Rationale**: The operator contract is the rendered text. A selector-only test
would not detect a false submission promise.

**Alternatives considered**:

- Assert a helper constant only. Rejected because that does not prove the page.
- Assert fragments such as `firmware write`. Rejected because fragments do not
  prove the full boundary.

## Decision 5: Audit Every Test File

**Decision**: Search all files under `tests/` for the old promise and all four
new exact strings.

**Rationale**: A full test-tree audit finds hidden wording dependencies. It
also proves that the direct contract test is the only new wording authority.

**Alternatives considered**:

- Search the approved contract file only. Rejected because another test can
  retain the false statement.
- Search production files only. Rejected because the requirement names
  `tests/`.

## Decision 6: Run the Complete Upgrade Portal Browser Suite

**Decision**: Run `tests/e2e/upgrade_portal` with strict browser enforcement.

**Rationale**: The change alters operator-facing Jinja text. The complete suite
checks the phase card and adjacent portal flows.

**Alternatives considered**:

- Run only the phase cascade journey. Rejected because the user requires the
  complete upgrade portal run.
- Run browser tests without strict mode. Rejected because a missing browser
  could report skips as success.

## Decision 7: Use One Push

**Decision**: Rebase first, rerun affected gates, and then push one time with
`--force-with-lease`.

**Rationale**: One push avoids duplicate CI runs. The lease protects another
writer from an overwrite.

**Alternatives considered**:

- Push before the rebase. Rejected because it creates avoidable CI work.
- Use `--force`. Rejected because it can overwrite remote work.

## Resolved Clarifications

No clarification remains. The implementation scope, exact strings, test
boundary, excluded behavior, release-note path, and review checks are defined.
