# Feature Specification: Remove deprecated SLE operations

**Feature Branch**: `jmorrison-juniper-deprecated-sle-operations`

**Created**: 2026-10-01

**Status**: Metadata removal verified on the granted publication base. Fresh PR checks and actual-main proof remain pending.

**Input**: User description: "Remove two deprecated site Service Level Expectations (SLE) operations for issue #3335. Preserve both supported trend operations and correct the coupled menu labels."

**Issue**: [#3335](https://github.com/jmorrison-juniper/MistHelper/issues/3335)

**Reservation**: [Reserved file scope](https://github.com/jmorrison-juniper/MistHelper/issues/3335#issuecomment-5936510347)

**Base Revision**: `856e5065413d3026f9c0f6d5222d9d379ec79d8b`

**Previous Local Refresh Base**: `1a06f1516223a20eef715d91a32255e6219331db`

The coordinator authorizes this immutable base for local refresh only.
It does not authorize publication or actual-main delivery.
The original preparation remains preserved at `623a48c88feb4cf5716f3986587f4971a51ffb6a`.
The later publication grant must name the actual verified issue #3366 merge revision.

**Granted Publication Base**: `df6889a40464db9dd7281765b5a58b993e33a7ed`

The coordinator now grants sole position-16 publication and delivery on this exact verified Maps revision.
This grant supersedes the earlier local-only permission.
The coding session preserves both prior preparations and rebases only its own isolated worktree.
Strict protection, all 15 required contexts, fresh quality/title/STE/CodeQL checks, and exact-head squash remain mandatory.
Actual resulting main requires local verification and a persistent pull request receipt.
The grant does not authorize source behavior, dependency, governance, production, or companion-defect changes.

**Feature Directory**: `specs/3335-deprecated-sle-operations`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select supported SLE operations (Priority: P1)

As a network operator, I need the site SLE export menu to offer only supported operations.
I must not select an operation that upstream plans to remove.

**Why this priority**: A deprecated selection can fail when its upstream operation disappears.
Removing the selection prevents that failure without removing the supported trend operations.

**Independent Test**: Inspect the active choices, catalog, and primary-key metadata.
Confirm that both deprecated operations are absent and both trend operations remain available.

**Acceptance Scenarios**:

1. **Given** the site SLE export menu, **When** the operator opens menu 263, **Then** it offers exactly 15 operations.
   Neither `getSiteSleSummary` nor `getSiteSleClassifierDetails` appears.
2. **Given** the active catalog and primary-key metadata, **When** the maintainer checks either deprecated operation, **Then** neither registration exists.
3. **Given** the remaining operation families, **When** the maintainer compares their operation lists, **Then** only the two deprecated site SLE operations are absent.
   Both trend operations and all unrelated operations retain their identities.

---

### User Story 2 - Retain offered SLE trends (Priority: P1)

As a network operator, I need both trend replacement entries to remain available in menu 263.
Their SDK resolution, required prompts, routing, and existing key metadata must remain unchanged.

**Why this priority**: Removing deprecated entries must not remove either offered replacement entry.

**Independent Test**: Resolve each offered trend operation with the real software development kit (SDK) version 0.64.0.
Use local transport and output mocks instead of live services.
Confirm unchanged resolution, prompts, SDK calls, and existing processing of generic response fixtures.
This preservation test does not establish export of the documented trend objects.

**Acceptance Scenarios**:

1. **Given** SDK 0.64.0, **When** the operator selects `getSiteSleSummaryTrend`, **Then** resolution returns the real SDK function.
   The operation retains its identifier, required tuple, keys, and invocation path.
2. **Given** SDK 0.64.0, **When** the operator selects `getSiteSleClassifierSummaryTrend`, **Then** resolution returns the real SDK function.
   The operation retains its identifier, classifier prompt, keys, and invocation path.
3. **Given** repeated generic response fixtures, **When** the local invocation repeats, **Then** existing rows and routing metadata remain unchanged.
   This feature adds no trend deduplication guarantee.
4. **Given** simulated absence of both deprecated SDK attributes, **When** the operator selects either trend operation, **Then** resolution and invocation remain available.
   The SDK version constraint remains unchanged.
5. **Given** missing required answers or the SLE refusal covered by issue #3305, **When** the operator requests an export, **Then** the existing refusal behavior remains unchanged.

---

### User Story 3 - Read accurate menu information (Priority: P2)

As a network operator, I need the command-line menu, portal label, and documentation to describe the same available operations.
I need menu 263 to remain in its current location and safety category.

**Why this priority**: A stale count causes operators to expect choices that no longer exist.
The label correction is part of the removal, not a menu redesign.

**Independent Test**: Compare the three fixed labels and six generated reference files with the active operation lists.
Confirm the new SLE count and unchanged top-level menu information.

**Acceptance Scenarios**:

1. **Given** the three fixed labels for menu 263, **When** the operator reads them, **Then** each label states 15 operations.
   The fixed labels are in `MistHelper.py`, `web_portal/menu_registry.py`, and `documentation/menu-highlights.md`.
2. **Given** regenerated menu references, **When** the operator reads the entry for menu 263, **Then** it agrees with the 15 available operations.
   No active operation map advertises either deprecated operation.
3. **Given** the existing top-level menu, **When** the maintainer compares its entries, **Then** menu numbers, entry counts, categories, and safety flags remain unchanged.
4. **Given** historical specifications, upstream references, and the vendored discovery index, **When** the maintainer reviews the change, **Then** those records remain unchanged.
5. **Given** the release fragment for issue #3335, **When** the maintainer reviews it, **Then** it describes both removals and both retained trend operations.
   The shared changelog remains unchanged.

---

### User Story 4 - Detect a deprecated registration (Priority: P2)

As a maintainer, I need tests that fail when either deprecated operation returns to an active registration.
I need the test results to state how many records they inspected.

**Why this priority**: A passing test provides no protection if it never checks the actual operation lists or cannot detect a deprecated entry.

**Independent Test**: Run the absence tests before and after removal.
Inject each deprecated operation into each registration source and exercise the guard decision directly.

**Acceptance Scenarios**:

1. **Given** the current registrations before removal, **When** the absence tests run, **Then** they fail for both deprecated operations.
   After removal, the same tests pass.
2. **Given** either deprecated operation in a selectable row, catalog entry, or primary-key strategy, **When** the corresponding guard decision runs, **Then** it fails.
   The result reports the actual checked count.
3. **Given** unreadable required guard input, **When** the guard runs, **Then** it fails rather than reporting a passing result.
4. **Given** the unchanged neighboring families and portal tests, **When** the regression tests run, **Then** they confirm unchanged counts, required answers, and refusal behavior.

### Edge Cases

- A deprecated operation name is a prefix of a retained trend name.
  Removal must match the two exact identifiers, not a shared prefix.
- Both deprecated SDK attributes are absent.
  Active operation discovery and both offered trend entries must still resolve.
- A historical document or vendored index still names a deprecated operation.
  That reference is not an active caller and must remain.
- The SDK collection returns no records.
  The existing empty-result behavior must remain unchanged.
- A generic response fixture repeats record data.
  Existing routing, keys, and database upsert behavior must remain unchanged.
- A documented trend object has no `results` field.
  Its existing output defect belongs to the separate issue below, not this metadata removal.
- Required answers are missing, invalid, or interrupted.
  Existing input handling and the separate issue #3305 SLE refusal must remain unchanged.
- A guard receives one injected deprecated entry, or cannot read required input.
  It must fail and report the actual checked count.
- A generation run changes a file outside the reserved scope.
  The maintainer must stop and report the unexpected change.
  This feature must not include that file.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The application MUST remove `getSiteSleSummary` and `getSiteSleClassifierDetails` from selectable rows, catalog entries, and primary-key metadata.
  Caller removal MUST stay within the three identified registration modules.
- **FR-002**: The application MUST retain `getSiteSleSummaryTrend` and `getSiteSleClassifierSummaryTrend` as selectable operations.
  Neither operation may become an alias for a deprecated operation.
- **FR-003**: Both trend operations MUST retain the existing `EndpointFamilyExporter` workflow.
  This includes resolution, required-answer prompts, SDK calls, normalization, and the `DataExporter` path.
- **FR-004**: All retained operations MUST preserve their identifiers, scope values, keys, output choices, and database upserts.
  The feature MUST NOT change existing export record identities or persistence behavior.
- **FR-005**: The active operation counts MUST match the following values.
  The only count reduction comes from the two deprecated operations.

  | Operation set | Before removal | After removal |
  | --- | ---: | ---: |
  | `_SITE_SLE_OPS` | 17 | 15 |
  | `ALL_STAGE_TWO_ENDPOINT_OPS` | 134 | 132 |
  | `ENDPOINT_CATALOG` | 286 | 284 |

- **FR-006**: Every unrelated family MUST retain its existing operations and count.

  | Family | Required unchanged count |
  | --- | ---: |
  | `SITE_MAP` | 7 |
  | `SITE_DETAIL` | 33 |
  | `ORG_DETAIL` | 61 |
  | `MSP_DETAIL` | 10 |
  | `OTHER_DETAIL` | 6 |

- **FR-007**: The top-level menu MUST retain all menu numbers, entry counts, categories, and safety flags.
  Menu 263 MUST remain available.
- **FR-008**: The three fixed labels for menu 263 MUST state 15 operations.
  The six generated reference files MUST agree with the active operation lists.
- **FR-009**: Historical specifications, upstream API references, and the vendored SDK discovery index MUST remain unchanged.
  A repository-wide ban on the deprecated names MUST NOT replace checks of active registrations.
- **FR-010**: The feature MUST preserve the SLE refusal covered by issue #3305.
  It MUST preserve existing portal handling of labels and required answers.
- **FR-011**: The feature MUST NOT add wrappers, compatibility shims, silent fallbacks, new production classes, schemas, or store operations.
  It MUST NOT redirect a deprecated selection to a retained trend operation.
- **FR-012**: The dependency constraint `mistapi>=0.64.0,<0.65` MUST remain unchanged.
  The feature MUST NOT change dependency manifests or install dependencies during this specification phase.
- **FR-013**: The later implementation MUST include the unique release fragment `changelog.d/issue-3335-deprecated-sle-operations.md`.
  The fragment MUST describe the two removals and retained trend operations without changing the shared changelog.

### Key Entities *(include if feature involves data)*

- **Operation registration**: An existing selectable operation, catalog entry, and associated primary-key metadata.
  Its identifier determines whether the application offers and exports that operation.
- **Operation family**: An existing group of related export operations.
  Each family has a fixed membership and an operation count.
- **Trend export record**: An existing normalized SLE result for the selected site and metric or classifier.
  Its existing identity determines how repeated exports update records.
- **Menu reference**: An existing label or generated document that describes a menu operation.
  Its count and safety information must agree with the active menu.

### Scope and Delivery Constraints

This specification covers existing issue #3335 only.
Issue #3334 fingerprint work is outside the scope.
The feature does not add an operation or redesign a menu.

The publication coordinator confirmed metadata-only scope after the documented response check.
This feature retains offered entries, not a claim of verified exports for their documented object responses.
[Issue #3699](https://github.com/jmorrison-juniper/MistHelper/issues/3699) owns that separate existing output defect.
This branch must not change `_run`, response handling, or the shared export workflow.

The specification phase writes only these files:

- `specs/3335-deprecated-sle-operations/spec.md`
- `specs/3335-deprecated-sle-operations/checklists/requirements.md`

The reservation permits the following files for later implementation and feature documents.
This list does not authorize those edits during the specification phase.

| Group | Reserved paths |
| --- | --- |
| Production registrations | `src/export/endpoint_family_exporter.py`, `src/export/endpoint_catalog.py`, `src/refactors/endpoint_primary_key_strategies.py` |
| Fixed menu labels | `MistHelper.py`, `web_portal/menu_registry.py`, `documentation/menu-highlights.md` |
| Changed tests | `tests/guardrails/test_endpoint_catalog.py`, `tests/unit/export/test_endpoint_family_exporter.py` |
| Generated wiki references | `documentation/menu_reference.md`, `documentation/wiki/Menu-Reference.md` |
| Generated operation maps | `documentation/menu-api/README.md`, `documentation/menu-api/interactive-safe.md`, `documentation/wiki/Menu-API-Endpoints.md`, `documentation/wiki/Menu-API-Endpoints-Interactive-Safe.md` |
| Release fragment | `changelog.d/issue-3335-deprecated-sle-operations.md` |
| Current feature documents | `specs/3335-deprecated-sle-operations/spec.md`, `specs/3335-deprecated-sle-operations/checklists/requirements.md` |
| Later feature design documents | `specs/3335-deprecated-sle-operations/plan.md`, `specs/3335-deprecated-sle-operations/research.md`, `specs/3335-deprecated-sle-operations/data-model.md`, `specs/3335-deprecated-sle-operations/quickstart.md` |
| Later feature execution documents | `specs/3335-deprecated-sle-operations/contracts/endpoint-removal.md`, `specs/3335-deprecated-sle-operations/tasks.md` |

The feature MUST NOT change baselines, suppressions, exclusions, dependency manifests, or agent instructions.
It MUST NOT change `README.md`, `CHANGELOG.md`, `.github/copilot-instructions.md`, or `operator-guide.md`.
It MUST NOT create or change `.specify/feature.json`, `.spec-context.json`, or another shared artifact that records feature state.

### Verification Constraints

- **VC-001**: Absence tests MUST fail before removal and pass after removal for both deprecated identifiers.
  They MUST inspect real selectable rows, catalog entries, and primary-key strategies.
- **VC-002**: Direct guard tests MUST reject each deprecated identifier injected into each of the three registration sources.
  This requires six rejection cases.
  Guard results MUST report actual checked counts.
  Unreadable required input MUST fail.
  Skipped checks or empty inspected sets MUST NOT count as proof.
- **VC-003**: Trend tests MUST resolve and exercise both real SDK 0.64.0 operations.
  Only local transport and output boundaries may use mocks.
  Tests MUST NOT replace SDK operation methods, resolution, required-answer handling, normalization, or export dispatch with substitute implementations.
  Tests MUST also simulate absent deprecated SDK attributes without changing the dependency constraint.
- **VC-004**: Regression evidence MUST cover retained operation identifiers, keys, database upserts, neighboring families, and the issue #3305 refusal.
  The following existing tests MUST run without edits:
  - `tests/unit/web_portal/test_portal_label_accuracy.py`
  - `tests/unit/web_portal/test_portal_required_answers.py`
- **VC-005**: After source changes, the maintainer MUST renew the live conflict check against exact file lists before generation.
  The later generation commands are `rtk proxy .venv/bin/python scripts/generate_menu_wiki.py` and `rtk proxy .venv/bin/python -m scripts.menu_api_map`.
  The operation map MUST pass `rtk proxy .venv/bin/python -m scripts.menu_api_map --check`.
  Repeated wiki generation MUST produce identical file contents.
- **VC-006**: The later implementation MUST pass focused unit and contract tests.
  It MUST also pass configured full Ruff and Black checks, the exact CI `MYPY_PATHS`, and configured Bandit.
  The test-quality ratchet MUST use the unchanged repository configuration and baseline.
  Markdown link checks, Simplified Technical English checks, and the runtime dependency audit MUST pass.
  A failed gate MUST NOT justify a baseline, suppression, exclusion, or dependency change.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can select exactly 15 site SLE operations.
  Neither deprecated operation appears in an active selection, catalog entry, or primary-key registration.
- **SC-002**: The stage-two export set contains 132 operations, and the full export catalog contains 284 operations.
  Each set loses only the two deprecated operations.
- **SC-003**: Both offered trend entries resolve to the real SDK 0.64.0 functions in every local acceptance case.
  Their identifiers, required prompts, routing, and primary-key metadata remain unchanged.
- **SC-004**: All three fixed labels and all six generated reference files agree with the active menu.
  They contain zero stale operation counts for menu 263.
- **SC-005**: All five neighboring families retain their exact counts and memberships.
  Zero top-level menu numbers, entry counts, categories, or safety flags change.
- **SC-006**: Maintainers detect all six deprecated-entry injection cases.
  Every guard result states its actual checked count.
- **SC-007**: Both offered trend entries retain SDK resolution and invocation when the two deprecated operations are unavailable.
  Generic response fixtures and existing persistence regressions show no new processing or key change.
- **SC-008**: Operators retain the existing required-answer and SLE refusal behavior in all relevant regression cases.
  The removal introduces no silent substitution for a deprecated operation.

## Assumptions

- The authoritative issue states that upstream deprecated both operations in SDK 0.59.2 and plans their removal in SDK 0.65.0.
  The parent verified the public upstream changelog through the GitHub API.
- Actual deprecated callers occur only in the three identified registration modules.
  Historical specifications, upstream references, and the vendored discovery index are not callers.
- The existing SDK 0.64.0 provides both retained trend operations.
  This feature does not approve an SDK 0.65.0 upgrade.
- Existing site access, required-answer handling, export backends, and database key definitions remain unchanged for the offered trend entries.
  No new data model or operational store is necessary.
- The parent confirmed the existing claim and checked the exact file lists of all 12 open pull requests.
  The linked reservation defines this feature's file boundary.
- The parent handles supported Python setup and publication.
  Publication remains at queue position 16 after issue #3366.
- The coordinator's scope decision excludes the documented object-output defect from this feature.
  The separate issue records the real SDK proof and the required future repair.
- The explicit position-16 grant now names the actual verified issue #3366 merge SHA above.
  A different main revision or conflicting owner requires a new coordinator decision before publication.
  Protected merge and actual-main verification remain required, not inferred from earlier local checks.
