# Feature Specification: Code Defaults First Batch

**Feature Branch**: `jmorrison-juniper-code-defaults-specification`

**Created**: 2026-10-21

**Status**: Draft

**Input**: Specify the bounded first batch of issue #2753. Prevent empty defaults from hiding missing required inputs.
Include the stable scan and regression guard contracts. Do not implement changes or decide ownership.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reject Missing Operational Inputs (Priority: P1)

A network operator receives a clear failure when a required value is absent.
The operation does not select an unintended object or report success for incomplete data.

**Why this priority**: A blank identity or missing collection can produce a wrong result that appears successful.

**Independent Test**: Supply incomplete local records to each affected workflow with external services replaced by controlled responses.
Confirm a visible failure before any dependent action.

**Acceptance Scenarios**:

1. **Given** a missing required object identity, **When** a migration processes the record, **Then** it reports failure without selecting or mapping a blank identity.
2. **Given** missing required migration collections, **When** a summary or recovery operation reads them, **Then** it reports incomplete data instead of zero completed actions.
3. **Given** a creation response without an object identity, **When** the migration records its result, **Then** it preserves the existing failure and creates no mapping.
4. **Given** valid required inputs, **When** the same workflow runs against controlled responses, **Then** its selection and result remain unchanged.

---

### User Story 2 - Distinguish Missing Data from Valid Empty Results (Priority: P1)

An operator can distinguish an incomplete analysis or comparison from a valid result with no matches.
An optional display field can remain blank.

**Why this priority**: A false zero result can conceal missing source data and misdirect an operator.

**Independent Test**: Compare incomplete records, explicitly empty valid collections, and complete records with optional display fields absent.

**Acceptance Scenarios**:

1. **Given** a missing required analysis collection, **When** a zone report consumes it, **Then** the report identifies the missing input instead of reporting no deviations.
2. **Given** a missing comparison identity or required address component, **When** a comparison uses it, **Then** it reports failure instead of matching blank values.
3. **Given** an explicitly empty collection permitted by the input contract, **When** the workflow processes it, **Then** the valid zero result remains available.
4. **Given** an absent optional display field, **When** the report renders it, **Then** its existing blank display remains unchanged.
5. **Given** an optional address component, **When** its absence does not prevent a valid comparison, **Then** the comparison remains valid.

---

### User Story 3 - Detect New Unsafe Defaults (Priority: P2)

A maintainer can repeat the candidate inventory and detect an increase in accepted high-severity candidates.
The result identifies its scope and the number of parsed files.

**Why this priority**: A stable measurement prevents changing scan rules from hiding a regression.

**Independent Test**: Run the inventory and guard against controlled tracked-file fixtures.
Add an unsafe selector default, a display-only default, and an unreadable input in separate cases.

**Acceptance Scenarios**:

1. **Given** unchanged tracked inputs and scan rules, **When** the scan repeats, **Then** candidate identities, classifications, and counts remain identical.
2. **Given** one added high-severity candidate above the accepted baseline, **When** the guard runs, **Then** it fails and identifies the increase.
3. **Given** a display-only blank default, **When** the scan classifies it, **Then** it does not increase the high-severity baseline count.
4. **Given** unreadable scan input, a parse failure, or an unreadable baseline, **When** the guard runs, **Then** it fails with the cause.
5. **Given** an empty or incomplete file selection, **When** the guard runs, **Then** it fails rather than reporting a successful zero.

### Edge Cases

- Required string inputs can be absent, null, empty, whitespace-only, or the wrong type.
- A present empty collection can be valid. A missing collection cannot establish that no results exist.
- An address can lack an optional second line without losing its required comparison identity.
- A field used for both display and selection requires validation before selection.
- A missing field in a partially completed migration must not erase prior successful records or create a false success.
- Diagnostic output must identify the field and workflow without exposing credentials or private payloads.
- File moves and completed repairs can change historical counts. They require explicit reconciliation, not an automatic baseline increase.
- Candidates owned by sibling issues or awaiting ownership must remain separately identified.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Behavioral repairs MUST remain within the five source files in the scope table and their directly related tests.
  The stable scan and regression guard are the only additional implementation contracts.
- **FR-002**: Each candidate MUST receive a classification based on its use.
  An empty value used for identity, selection, comparison, filtering, paths, or required result collections requires review.
  A blank value used only for display remains outside the repair scope.
- **FR-003**: The affected workflows MUST validate required inputs before dependent actions.
  Missing or invalid required input MUST produce an explicit failure, not an empty substitute or success-shaped result.
- **FR-004**: Failure messages MUST identify the missing field and workflow.
  Diagnostic records MUST preserve exception context without exposing secrets or private record contents.
- **FR-005**: Valid inputs, permitted empty collections, optional address components, and display-only blanks MUST retain their existing behavior.
  A historical candidate count alone MUST NOT make an optional input mandatory.
- **FR-006**: Migration processing MUST preserve verified earlier results when a later record fails.
  It MUST NOT add a blank identity mapping or report the failed record as successful.
  Existing backups and typed confirmation requirements MUST remain unchanged.
- **FR-007**: Each repaired behavior MUST have unit, workflow integration, and edge-case evidence using controlled external responses.
  Evidence MUST cover missing required input, valid input, and permitted optional absence.
  Tests that formerly required unsafe behavior MUST change with the repair.
- **FR-008**: The implementation MUST commit a stable scan with documented discovery and classification rules.
  It MUST inventory tracked non-test source files and distinguish the assessment's five empty-default shapes from safe non-empty defaults.
  Each candidate MUST identify its file, location, input, classification, and ownership status.
- **FR-009**: The scan MUST exclude test paths, test modules, test configuration modules, virtual environments, caches, and untracked files.
  It MUST report discovered files, parsed files, parse failures, and separate severity totals.
  Repeated runs against identical tracked content MUST produce identical ordered results.
- **FR-010**: A regression guard MUST compare accepted high-severity candidates with an explicit, readable baseline.
  The accepted first-batch scope MUST remain separate from other scopes and unresolved ownership.
  The guard MUST report parsed-file counts and fail for increases, missing scope files, unreadable inputs, invalid baselines, or parse failures.
  Baseline decreases MUST remain visible. Automatic baseline increases MUST NOT conceal new candidates.
- **FR-011**: Guard evidence MUST include a passing fixture and a failing fixture with one added high-severity candidate.
  Separate fixtures MUST prove that display-only defaults do not trigger the high-severity guard and that unreadable inputs cannot pass.
- **FR-012**: This specification and its validation MUST make no Mist cloud request and perform no device action.
  Later implementation verification MUST use controlled responses without production credentials.
  This batch MUST NOT change transports, menu registration, repository settings, issue ownership, or sibling scopes.

### Key Entities

- **Required input**: A value necessary for a correct selection, comparison, migration, or result interpretation.
- **Candidate**: A measured empty default whose use still requires classification. A candidate is not automatically a confirmed defect.
- **Accepted baseline**: A reviewed inventory with a fixed scope, scan criteria, revision, and accepted high-severity count.
- **Failure result**: A visible unsuccessful outcome that identifies the required input without replacing it with blank data.
- **Scope boundary**: The five-file repair set, related verification, and scan/guard contracts, excluding other owners and unresolved candidates.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every confirmed first-batch required-input defect has a missing-input case that visibly fails before a dependent action.
- **SC-002**: All valid-input and permitted optional-input cases preserve their expected results across the five affected workflows.
- **SC-003**: No migration verification case records success or an identity mapping for a response without its required object identity.
- **SC-004**: Two inventories of identical content produce identical candidate identities, classifications, and counts.
- **SC-005**: The regression guard rejects one added high-severity candidate and every unreadable-input fixture.
  Every guard result states how many files it parsed.
- **SC-006**: Every historical first-batch candidate has a recorded disposition: repaired, already repaired, valid optional input, display-only, or excluded ownership.
  No ownership decision or remaining program candidate becomes completed work through this batch.
- **SC-007**: Specification work and verification cause zero Mist cloud requests and zero device actions.

## Assumptions

### Evidence and Bounded Scope

The source is the [assessment on issue #2753](https://github.com/jmorrison-juniper/MistHelper/issues/2753#issuecomment-6026962937).
Section 8 defines this first batch. Section 10 provides its exact test command and local gate commands.
Those commands are future implementation evidence, not commands executed by this specification task.

| Source file | Historical high count | Related test modules from the assessment |
| --- | --- | --- |
| `src/mist/resources/device/ap_profile_migration_manager.py` | 18 | `tests/unit/device/test_ap_profile_migration_manager.py` |
| `src/mist/intelligence/analytics/zone_analyzer.py` | 17 | `tests/unit/test_zone_analyzer.py` |
| `src/mist/resources/inventory/csv_comparator.py` | 10 | `tests/unit/test_csv_comparator.py`, `tests/unit/inventory/test_csv_comparator_broad_handlers.py`, `tests/unit/refactors/test_inventory_csvcomparator.py` |
| `src/foundation/support/utils/address_utils.py` | 9 | `tests/unit/test_address_utils.py` |
| `src/mist/resources/org/org_config_migration_manager.py` | 5 | `tests/unit/org/test_org_config_migration_conflicts.py`, `tests/unit/org/test_org_config_migration_workflow.py` |

The assessment measured 59 high-severity candidates in these files.
These are historical review targets, not a newly measured baseline or a requirement to remove 59 defaults.
Planning must reconcile current locations and completed repairs before accepting the baseline.
Planning must preserve the assessment's descending per-file priority.

[Pull request #4310](https://github.com/jmorrison-juniper/MistHelper/pull/4310) already repaired the missing created-object identity in organization migration.
The current source and tests retain that failure behavior.
This specification includes regression coverage, not a second implementation of that repair.
The current remaining candidate count has not been measured.

### Ownership and Exclusions

The assessment measured 1,836 net candidates across 303 files: 667 high-severity candidates and 1,169 low-severity output-only candidates.
These figures describe the larger program at its assessment revision, not completion targets or current measurements for this batch.

Credentials belong to [#2861](https://github.com/jmorrison-juniper/MistHelper/issues/2861).
Organization and site identifiers belong to [#2863](https://github.com/jmorrison-juniper/MistHelper/issues/2863).
The original acceptance priorities do not authorize this batch to absorb those scopes.

Closed [#2862](https://github.com/jmorrison-juniper/MistHelper/issues/2862) deferred 99 upgrade-input candidates.
Their ownership remains unresolved. This specification neither absorbs them nor decides whether that issue must reopen.
The assessment's other ambiguous ownership candidates also remain outside this batch until their owner resolves them.

Low-severity display-only defaults, the larger program, and production migration or upgrade execution remain outside this specification.
No requirement in this document claims to close issue #2753.

### Planning Dependencies

The original assessment scan exists only in its author's session folder.
This task does not access that folder or claim that the scan is committed.
Implementation must provide the committed reproducible scan required by FR-008 before accepting its baseline.

The implementation plan must resolve current test locations and applicable gates from the repository and assessment section 10.
It must include the documented test-quality preflight and ratchet without changing their baseline to conceal findings.
The guard's own tests supplement, rather than replace, the first-batch test boundary.

Only this specification and its quality checklist are authored now.
The feature selector remains command-scoped. The shared `.specify/feature.json` pointer remains unchanged.
