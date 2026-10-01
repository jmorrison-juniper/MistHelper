# Research: History Organization Isolation

**Date**: 2026-09-30

**Feature**: [spec.md](spec.md)

**Inspected revision**: `b14078edd41cb0fe70437ae9ac6f2ec6e8882272`

## Research Boundary

This research used the current exclusive worktree only.
It used no delegated agent, external service, production store, credential, or container.
The specification and checklist contain no unresolved question.

The research confirmed the smallest repair and the exact fixture migrations.
The repair uses existing dependencies and storage.

## R1: Reuse the signed selection and refusal authorities

**Decision**: Read `select.resolve_org(None)`, normalize its result, and call `select.org_refusal` before any history read.

**Rationale**: The resolver reads `selected_org_id` from the signed session.
It rejects incorrectly typed values.
Normalization also rejects whitespace-only values.
The refusal helper supplies the existing missing-selection and authorization responses.

`read_chosen_org` reads a JSON body or form submission.
It is not the saved-selection reader.
History must not use it.

**Alternatives considered**:

- Request-supplied organizations can replace the signed selection.
  Reject this approach.
- The first permitted organization is not the operator's explicit choice.
  Reject this approach.
- A new authorization rule can drift from the current identity policy.
  Reject this approach.

**Evidence**: `src/upgrade_portal/app/routes/select.py:455-477` and `:565-600`.

## R2: Preserve the current privilege-availability distinction

**Decision**: Keep `identity.org_scope_refusal`, `permitted_org_ids`, and `org_is_permitted` unchanged.

**Rationale**: A known empty privilege set permits nothing.
An unavailable privilege list produces `None`.
The current policy deliberately permits environment-token sessions with unavailable privileges.
Every permitted history request still needs an explicit selected organization.

Known privileges must reject removed, unknown, and excluded selections on every request.
Stored history cannot authorize an organization.

**Alternatives considered**:

- Refusing every unavailable privilege list changes global authentication policy.
  Reject this approach.
- Treating an empty set as unavailable permits excluded selections.
  Reject this approach.

**Evidence**: `src/upgrade_portal/runtime/identity.py:913-1059`.

## R3: Scope real adapters without expanding capture and run seams

**Decision**: Keep the current site-and-window signatures.
The real adapters must derive and authorize the signed selection.
They must pass it through the existing `org_id` query field.

**Rationale**: `CaptureQuery` and `RunQuery` already support organization filters.
Both store readers use the same narrowing fields for their count and page queries.
The filters precede the count and page limit.

`call_lister` adapts existing site-only and site-and-window test readers.
It does not need another organization argument.
The comparison picker also calls the capture lister with the site alone.
Changing that seam would cause unnecessary caller and fixture migrations.

**Alternatives considered**:

- Filtering returned rows leaves incorrect totals and page boundaries.
  Reject this approach.
- Expanding every lister call is unnecessary when the trusted adapters own request scope.
  Reject this approach.
- Retrying a site-only query after a scoped-call error recreates the defect.
  Reject this approach.

**Evidence**:

- `src/upgrade_portal/app/routes/review.py:369-415`, `:902-915`, and `:1180-1234`.
- `src/upgrade_portal/app/seam_shapes.py:157-175`.
- `src/upgrade_portal/capture/store.py:1925-2002`, `:2097-2136`, `:2162-2187`, and `:2222-2249`.

## R4: Reuse existing operation scope and ownership rules

**Decision**: Pass the validated organization into the operation section.
Keep `OrgOperationHistory`, the operation lister, and the operation query contract unchanged.

**Rationale**: Operations already filter by organization and optional site.
The shaper controls progress links through the current browser-session owner.
The route must add early refusal without changing that ownership rule.

**Alternatives considered**:

- Permission for multiple organizations does not widen the selected scope.
  Reject that interpretation.
- Hiding all operations from other browser sessions changes existing history behavior.
  Reject that change.

**Evidence**: `src/upgrade_portal/upgrade/org_history.py:64-145` and `src/upgrade_portal/capture/store.py:1897-1918`.

## R5: Require organization scope on audit reads

**Decision**: Add a required keyword-only `org_id` to `read_audit_rows`.
Keep its other arguments in their current order.
Reject an empty organization before opening the trail.

**Rationale**: Audit records already contain `org_id`.
The current reader filters by site only.
The route supplies only `site_id`, so the no-site card can expose the shared trail.

Only one production route calls this reader.
One existing test file contains 14 direct calls.
A required argument makes every relevant caller migrate explicitly.
No global default or compatibility path is necessary.

**Alternatives considered**:

- A default empty organization preserves an unrestricted path.
  Reject this approach.
- Filtering rendered audit rows is too late for inference and bounded limits.
  Reject this approach.

**Evidence**: `src/upgrade_portal/app/routes/review.py:2070-2102` and `src/upgrade_portal/compare/lock_audit.py:161-252`.

## R6: Filter before inference and retain complete matching context

**Decision**: Match organization and optional site before inference.
Use `(org_id, site_id)` as the in-memory holder key in both inference paths.
Apply result limits after matching and inference.

**Rationale**: The current holder key uses site text only.
A foreign take, release, or takeover can therefore alter another organization's inferred events.
A tuple separates reused site text across organizations.

Inference needs older matching records, not foreign records or records from another site.
Filtering the complete matching sequence preserves earlier holds.
Truncating the raw trail before inference loses that context.

The bounded deque must contain matching output rows only.
Foreign events must not consume its positions.
The unbounded path must use the same transitions before its existing final slice.

Preserve `shaped[:limit]` on the legacy path.
Zero still returns no rows.
A negative value retains the existing slice meaning.
`None` retains an unbounded slice.

**Alternatives considered**:

- Site-only state keys connect foreign sequences.
  Reject this approach.
- A global holder connects unrelated sites.
  Reject this approach.
- Keeping the last raw lines before filtering can discard every matching result.
  Reject this approach.

**Evidence**: `src/upgrade_portal/compare/lock_audit.py:88-128` and `:198-252`.

## R7: Use direct contracts and real query paths

**Decision**: Test complete responses with synthetic database readers and audit trails.
Do not add a browser journey.

**Rationale**: The repair changes server-side scope only.
No template, JavaScript, style, firmware control, or browser transition needs a change.
Direct HTML and JSON contracts can inspect visible and hidden content.

The synthetic database must honor filters actually present in each query.
The tests must call the real adapters, query types, and store readers.
An injected lister that always returns selected rows cannot prove this defect.

The red contract must expose incorrect content, counts, or source calls.
A failure caused only by a proposed signature is insufficient.

**Alternatives considered**:

- Signature-only tests miss the unrestricted real query.
  Reject this evidence.
- Browser duplication adds cost without testing a separate behavior.
  Reject this evidence.
- Expected results built wholly by the production shaper can repeat its defect.
  Reject this evidence.

**Evidence**: The specification's verification requirements and `tests/unit/upgrade_portal/test_store_history.py:66-119`.

## R8: Limit migrations and validation writes

**Decision**: Migrate six directly coupled test files after parent ownership checks.
Keep shared fixtures, seam metadata, authentication policy, and browser environment files unchanged.

**Rationale**: Three signed clients omit selection.
One operation test expects a successful missing-selection page.
One adapter test uses a three-field query stand-in without a request context.
One audit test file omits the new required organization at 14 call sites.

`test_lock_free_reads.py` already supplies a selected organization.
The #3482 and #3486 tests inspect presentation independently of history requests.
They need regression runs, not migration edits.

The installed environment already supplies every required validation tool.
The CI workflow defines the strict mypy paths and test-quality ratchet.
No dependency installation or baseline rewrite is necessary.

**Alternatives considered**:

- A global selected-organization fixture can hide missing-selection tests.
  Reject this approach.
- Editing the browser environment expands the issue's ownership surface.
  Reject this approach.
- Changing the quality baseline hides new findings.
  Reject this approach.

**Evidence**:

- `tests/contract/upgrade_portal/test_history_routes.py:270-312`.
- `tests/contract/upgrade_portal/test_history_device_type.py:153-193`.
- `tests/contract/upgrade_portal/test_upgrade_routes/test_stale_views.py:77-94`.
- `tests/contract/upgrade_portal/test_history_operations.py:238-246`.
- `tests/unit/upgrade_portal/test_review_store_seams.py:32-52` and `:130-209`.
- `tests/contract/upgrade_portal/test_lock_audit_log.py:180-348`.
- `.github/workflows/ci.yml:83`, `:409-424`, and `:575-605`.
- `.github/test-quality-config.toml`.

## Resolved Outcome

No design clarification remains.
The only implementation hold is ownership approval for the six additional test files.
The exact list appears in [plan.md](plan.md#exact-additional-test-migration-list).
This research does not authorize implementation or delivery.
