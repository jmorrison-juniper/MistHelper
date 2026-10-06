# Typed operation outcomes for issue 3168 part B

**Linked issue**: #3168  
**Status**: Draft specification  
**Base**: `origin/main` at `f1505203d1d5ec845c94cb54f55118d613cf4e49`

## Naming decision

Use the name `OperationOutcome` for part B.

The record `specs/1021-testinteractive-reliability-defects/` defines an
`OperationOutcome` for interactive test telemetry. That record is stale for
this contract. Its six implementation issues shipped on `origin/main`:

| Issue | Commit | Result |
|---|---|---|
| #1636 | `b0ef95f2` | Logged operation errors no longer appear clean. |
| #1637 | `de9de19f` | A supplied site selector fails closed. |
| #1638 | `58d12081` | Site context and prompt cancellation are reported. |
| #1639 | `5e9732c1` | The WAN client-events SDK path is corrected. |
| #1640 | `2ad8596e` | The unsupported hyphenated flag is rejected. |
| #1641 | `60477024` | Help runs before deferred initialization. |

The 1021 record remains a draft design record. Its five-field telemetry
`OperationOutcome` has no shipped production type. Its old
`src/mist/intelligence/` paths also do not describe the current package
layout. Part B supersedes that unshipped data model for the handler return
contract. It does not reopen or remove the six shipped fixes.

The new type must describe the portal-facing result:

| Field | Meaning |
|---|---|
| `state` | `completed`, `no_output`, `missing_input`, or `failed`. |
| `message` | The operator-facing completion message. |
| `detail` | Optional structured detail for logs and tests. |

Implement the type later in
`src/foundation/models/operation_outcome.py` as a frozen, slotted
dataclass. Use the shape of `ExportResult` in
`src/interfaces/portals/upgrade_portal/compare/download.py`.

## Fallback decision

`AGENTS.md` wins over acceptance criterion 3 in the issue body.

Part B must not add or keep a prose-matching fallback. The existing marker
tuples and prose classifier are the old path. The implementation must migrate
the supported handlers to `OperationOutcome`, change the portal to consume
that result, and remove the marker tuples and prose readers in the same
cutover batch.

Producer migrations may land before the cutover only when they do not change
portal classification. The portal must not contain a period with two
classification paths. The final cutover is the defined removal point. No
issue may defer that removal or count the prose path as a supported state.

## Problem statement

The portal calls an operation handler at
`web_portal/services/operation.py:1160` and discards the return value.
It then classifies completion from captured log text. This makes a handler
return contract impossible to enforce and makes completion depend on prose.

The classification reaches the operator. The completion message is written
by `_finish_successful_operation`, returned by REST status routes, sent by
SSE, and rendered by the browser. A typed result therefore changes a
user-visible contract and requires portal, API, and focused test coverage.

## Measured scope

The previous worker read the committed files with
`git show origin/main:<path>`. The worker also scanned the committed Python
tree with the standard-library AST parser.

The measurement found:

- 293 menu rows.
- 181 dotted handlers.
- 112 lambda handlers.
- 169 dotted handlers resolved to definitions.
- 6 of 169 resolved handlers return a value.
- 163 of 169 resolved handlers return no value.
- 10 call sites read a handler return.
- 16 call sites discard a handler return.
- 848 of 851 scanned files parsed successfully, with zero parse failures.

A lambda cannot carry a return annotation. The 112 lambda rows therefore
cannot satisfy the typed contract in their current form.

## User scenarios

### Scenario 1: The portal receives a typed result

Given a handler returns an `OperationOutcome`, when the portal completes the
operation, then it must use the returned state and message.

The portal must not infer a state from a log marker when a typed result exists.

### Scenario 2: A typed state reaches the operator

Given a handler returns `completed`, `no_output`, `missing_input`, or
`failed`, when the portal publishes REST or SSE status, then the status must
contain the same state and the correct completion message.

### Scenario 3: No prose classifier remains

Given the typed handler contract is complete, when the code is inspected and
the focused tests run, then the marker tuples and their prose readers must be
absent from the portal classification path.

### Scenario 4: Lambda conversion has a separate boundary

Given a menu handler is a lambda, when the typed migration is planned, then
the handler remains in the untyped inventory until a separate issue converts
it to a named function.

That separate issue owns `MistHelper.py`. It must not be hidden inside a
portal or model change.

## Functional requirements

- **FR-001**: Define one portal-facing `OperationOutcome` type.
- **FR-002**: Use only the four states `completed`, `no_output`,
  `missing_input`, and `failed`.
- **FR-003**: Migrate each supported named handler to return the type.
- **FR-004**: Convert the 112 lambda handlers in a separate issue before
  claiming complete typed coverage.
- **FR-005**: Make the portal consume the typed return value.
- **FR-006**: Remove the marker tuples and prose readers in the same portal
  cutover batch.
- **FR-007**: Preserve the operator-visible completion message contract in
  REST and SSE responses.
- **FR-008**: Keep all validation mock-first and read-only.

## Acceptance criteria

1. The new specification and implementation use one `OperationOutcome` name.
   The stale 1021 telemetry model is not implemented under that name.
2. A named handler that returns each allowed state reaches the portal with
   that state unchanged.
3. The portal no longer uses prose matching or a compatibility fallback after
   the cutover batch.
4. The final cutover removes the marker tuples, private prose readers, and
   tests that require those private readers.
5. The 112 lambda handlers are listed in their own issue and batch. The
   implementation does not claim that lambdas have return annotations before
   that batch lands.
6. The portal REST and SSE responses expose the typed state and message.
7. `tests/unit/export/test_endpoint_family_exporter.py:592` asserts an
   explicit typed outcome for the empty trend result and no silent discard.
8. `tests/unit/marvis/actions/test_alarms.py:30` and `:328` no longer depend
   on `HANDLED_ERROR_MARKERS`. They assert typed outcome behavior.
9. `tests/unit/marvis/actions/test_portal_contract.py:109` and `:113` no
   longer call private prose classifiers. They assert the typed portal
   contract.
10. Focused tests use mocked or stubbed clients and make no Mist write call.

## Out of scope

- Changes to `MistHelper.py` before the dedicated lambda batch.
- Changes to the six shipped fixes from the 1021 issue sequence.
- A compatibility alias for the stale 1021 type.
- A second result type with the same portal meaning.
- Live Mist validation or mutating API calls.
- Changes under `web_portal/`, `src/`, or `tests/` in this specification
  change.

## Dependencies and risks

Pull request #4001 must merge before implementation begins. It changes
`web_portal/services/operation.py` and
`tests/unit/web_portal/test_portal_silent_completion.py`, which part B also
needs.

`MistHelper.py` permits one open pull request. The lambda conversion must
therefore be a separate issue and batch with no unrelated edits.

The portal completion message is user-visible. Any message change requires
REST, SSE, and browser contract tests.

## Evidence sources

- Issue #3168 measured assessment comment
  `issuecomment-6026936236`.
- `AGENTS.md` and `.github/copilot-instructions.md`.
- `specs/1021-testinteractive-reliability-defects/`.
- `web_portal/services/operation.py`.
- `src/interfaces/portals/upgrade_portal/compare/download.py`.
- The five defect-asserting test locations listed above.
