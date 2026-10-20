# Feature Specification: SLE trend primary keys

**Feature Branch**: `jmorrison-juniper-sle-trend-primary-keys`

**Created**: 2026-10-20

**Status**: Specified

**Input**: Repair issue #4003 without deleting or migrating existing rows.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Repeat a trend export (Priority: P1)

The operator exports the same SLE window twice. The second export updates the new keyed record, without adding another record.

**Why this priority**: Duplicate windows cause incorrect trend totals.

**Independent Test**: Export a fake window twice with changed values. Confirm one keyed record contains the second values.

**Acceptance Scenarios**:

1. **Given** an empty store, **When** the operator exports one window twice, **Then** one record contains the latest values.
2. **Given** one stored window, **When** the operator exports another window, **Then** both windows remain.
3. **Given** equal windows with different identifiers, **When** the operator exports both, **Then** both records remain.

### User Story 2 - Preserve existing records (Priority: P1)

The operator retains all legacy records when the export uses the new identity.

**Why this priority**: An unattended repair must not remove existing data.

**Independent Test**: Create a legacy store, export the same window twice, and compare every legacy record before and after.

**Acceptance Scenarios**:

1. **Given** legacy auto-increment records, **When** the operator exports a matching window, **Then** the legacy records remain unchanged.
2. **Given** that first new export, **When** the operator repeats it, **Then** only the new keyed record changes.

### User Story 3 - Detect another incorrect strategy (Priority: P2)

The maintainer measures the complete strategy table and can detect missing or incorrect trend entries.

**Why this priority**: A two-entry check must not hide another instance of this defect.

**Independent Test**: Scan the complete table, report counts, and inject an incorrect trend entry and an empty table.

**Acceptance Scenarios**:

1. **Given** the complete table, **When** the guard runs, **Then** it reports a stable count line and every matching defect.
2. **Given** zero entries, **When** the guard runs, **Then** it fails.

### Edge Cases

- Missing, empty, or invalid identity fields stop the write with a visible error.
- Response identifiers must not override the selected request identifiers.
- Classifier responses contain a nested classifier object, not a scalar classifier identifier.
- Equal windows with different sites, scopes, metrics, or classifiers remain separate.
- A legacy store may already contain multiple duplicates. The repair preserves every duplicate.
- An empty response retains the existing no-data behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Both summary-trend endpoints MUST use `composite_pk`.
- **FR-002**: `getSiteSleSummaryTrend` MUST use `site_id`, `scope`, `scope_id`, `metric`, `start`, and `end`.
- **FR-003**: `getSiteSleClassifierSummaryTrend` MUST use those fields plus `classifier_name`, before `start` and `end`.
- **FR-004**: Export rows MUST contain every identity field before persistence.
- **FR-005**: Repeated exports MUST replace the same keyed record in SQLite and ArangoDB.
- **FR-006**: Different identifiers and different windows MUST retain separate keyed records.
- **FR-007**: The repair MUST preserve every legacy record without migration, deletion, or value updates.
- **FR-008**: The first matching export MAY add one keyed record beside legacy records. Later exports MUST reuse that keyed record.
- **FR-009**: The guard MUST inspect the complete endpoint strategy table and report all other confirmed trend-window misclassifications.
- **FR-010**: The guard MUST print a stable count line and fail when the table or the expected trend selection is empty.
- **FR-011**: The changelog and pull request MUST state the legacy-record decision and the backend-specific previous behavior.
- **FR-012**: Existing unrelated endpoint behavior MUST remain unchanged.

### Mist Cloud Transport Requirements

The existing SDK methods are `mistapi.api.v1.sites.sle.getSiteSleSummaryTrend` and `getSiteSleClassifierSummaryTrend`.
The repair adds no transport. Tests use fake responses without production credentials or network requests.

### Key Entities

- **Trend window**: One site, scope, scope identifier, metric, optional classifier, start, and end.
- **Legacy record**: A previously stored auto-increment row or UUID document that retains its original identity.
- **Strategy table**: The complete endpoint registry used to select persistence identity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Two exports of one window produce exactly one new keyed record with the latest values.
- **SC-002**: Two distinct windows or identifier sets produce exactly two keyed records.
- **SC-003**: Every legacy record remains unchanged after two matching exports.
- **SC-004**: The guard examines 100 percent of registry entries and reports the examined and matching counts.
- **SC-005**: Empty input and an injected incorrect trend strategy both fail the guard.

## Assumptions

- Preserve every existing row. Do not migrate, delete, or deduplicate legacy data.
- Accept one additional keyed record for a matching legacy window on the first export after this change.
- Existing duplicate legacy records remain visible. This repair does not correct historical totals.
- SQLite previously refreshed auto-increment tables. ArangoDB previously added UUID documents on each export.
- A non-destructive schema extension may identify new SQLite rows without changing legacy row values or primary keys.
- The `needs-human-review` label requires a ready-for-review pull request without auto-merge or merge.
