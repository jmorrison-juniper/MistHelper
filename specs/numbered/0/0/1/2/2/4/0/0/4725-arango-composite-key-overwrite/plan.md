# Implementation Plan: ArangoDB Identity Keys for Declared Multi-Field Primary Keys

**Branch**: `fix/4725-arango-composite-key-overwrite` | **Date**: 2026-11-26 | **Spec**: `specs\numbered\0\0\1\2\2\4\0\0\4725-arango-composite-key-overwrite\spec.md`

**Input**: Numeric specification from `specs/numbered/0/0/1/2/2/4/0/0/4725-arango-composite-key-overwrite/spec.md`. The route is the base-5 form of 4725, which is `122400` in base 5, padded to eight digits (RC-19).

## Summary

The ArangoDB writer assigns each document key from the first declared key field (`arango_writer.py`, line 4067). The change derives each key from every declared key field for each affected strategy entry. SLE identities, single-field entries, and audited exemptions keep their current keys. The change deletes nothing. Legacy documents stay in place, and any migration waits for an approved plan.

## Technical Context

**Language/Version**: Python 3.15 (`pyproject.toml` line 23, RC-27).

**Primary Dependencies**: python-arango 8.3.7 (`requirements.txt` line 197, RC-32, and `pyproject.toml` line 76, RC-29). mistapi 0.64.1 (`requirements.txt` line 129, RC-31). `pyproject.toml` line 29 names `mistapi>=0.64.1,<0.65` (RC-28). The change adds no dependency. The new code uses only the standard library (`hashlib`, `json`, `decimal`, `math`).

**Storage**: ArangoDB document collections. One collection exists for each API function name, because `_ensure_collection` uses the endpoint name (RC-58). Redis JSON and SQLite legs are unchanged (FR-013).

**Testing**: pytest, with the in-memory fake collection in `tests/unit/config/foundation/persistence/storage/arango_indexes/fakes.py` (RC-93). No live database is used.

**Target Platform**: Windows 11, macOS, and Linux. The runtime ships as a Podman container (`.github/copilot-instructions.md`, section "Containers and ports", RC-08).

**Project Type**: Single Python project with CLI menus and web portals.

**Performance Goals**: No added network call. The change adds one SHA-256 digest for each record in a write batch.

**Constraints**: Five-Item Rule and ASCII logs. Each executable line needs an inline comment. Each batch needs action logging before and after it. No stored data is deleted (RC-09, RC-11, RC-12).

**Scale/Scope**: 121 effective strategy entries use the ArangoDB first-field path at main f03c6c9b. Of these, 120 are composite_pk and 1 is natural_pk (`siteVariableAudit`, RC-72, RC-76). The 2 SLE trend entries are excluded (RC-68).

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after the design.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | pass | The new module enters `src/foundation/persistence/db/writers/`, which holds three children now and four after the change (RC-101). No direct child enters `src/foundation/persistence/db/`, which already holds six children (grandfathered). The new test file enters `arango_writer/`, which holds three children now and four after the change (RC-102). Touched existing violation: `arango_writer.py` has 4,456 lines. Remediation action R-1 is tracked in T018. |
| II. Class-Based Architecture | pass | All identity logic lives in class `CompositeKeyIdentity`. No standalone wrapper function is added. |
| III. Safety-First | pass | The change adds no `input()` call and no destructive operation. FR-010 blocks deletion and rewrite. |
| IV. Full Deployment Pipeline | pass (planned) | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover steps 1 to 9. Steps 10 to 12 (main build, revision check, deploy and health) run after T-MERGE. |
| V. Observability and Logging | pass (planned) | FR-014 requires ASCII log text that reports counts. Secrets stay out of logs. |
| VI. Inline Comments | pass (planned) | T003, T004, and T005 require an inline comment on every executable line. |
| VII. Action Logging | pass (planned) | FR-014 requires an info line before and a debug line after each key derivation batch. |
| Technology: mistapi only | pass | The change adds no REST request. The existing SDK call stays in place (RC-89). |
| Technology: Podman and test containers | pass | Unit tests need no container. Any container run follows `documentation/container-deployment.md` Rules 1 and 2 (RC-34). |
| Technology: Database keys | pass | `ENDPOINT_PRIMARY_KEY_STRATEGIES` stays the source of identity. The table is not edited (FR-013). |
| Technology: Data directory | pass | No product output path changes. |
| Technology: Export boundary | pass | `DataExporter.write_with_format_selection` and the router entry point keep their signatures (RC-86, RC-87). |
| Technology: Operational store | not applicable | The change creates no coordination record. |
| Development workflow: new menu operations | not applicable | Menu 217 keeps its entry and category (RC-90, RC-91). |
| Multi-agent workflow | pass with gate | T001 must finish before the first edit to `arango_writer.py`. |
| Specification escalation | pass | The change touches three or more files and a primary key rule, so the SpecKit workflow applies. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/4/0/0/4725-arango-composite-key-overwrite/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      arango-document-key.md
      mist-bgp-stats-search.md
      identity-audit-format.md
    checklists/
      requirements.md
      preservation.md
```

### Source Code (repository root)

```text
src/foundation/persistence/db/writers/
  arango_writer.py                  (modify: write, _prepare_document, _compute_key)
  composite_key_identity.py         (add: class CompositeKeyIdentity)
tests/unit/config/standalone/foundation/persistence/arango_writer/
  test_arango_composite_keys.py     (add: 17 test functions)
tests/unit/config/foundation/persistence/storage/arango_indexes/
  test_preservation.py              (modify: line 36 expectation, D-10)
documentation/diagrams/core/database-strategy.md   (modify: Source of Truth)
changelog.d/issue-4725-arango-composite-key-overwrite.md   (add)
```

**Structure Decision**: The identity rule sits in a new module beside the writer. The strategy table, the SQLite writers, and the Redis writers stay unchanged. The change reuses the existing SLE identity classes (RC-65, RC-66).

## Change Map

| Path | Action | Requirements | Notes |
| - | - | - | - |
| `src/foundation/persistence/db/writers/composite_key_identity.py` | add | FR-001 to FR-006, FR-009 | Class `CompositeKeyIdentity` with `applies`, `derive`, and the exemption set. |
| `src/foundation/persistence/db/writers/arango_writer.py` | modify | FR-001, FR-007, FR-008, FR-010, FR-011, FR-014 | `write` (line 3987), `_prepare_document` (line 4047), `_compute_key` (line 4058). `_batch_import` keeps `on_duplicate="replace"` (line 4034). |
| `tests/unit/config/standalone/foundation/persistence/arango_writer/test_arango_composite_keys.py` | add | FR-001 to FR-015 | 17 test functions. See `design/quickstart.md`. |
| `tests/unit/config/foundation/persistence/storage/arango_indexes/test_preservation.py` | modify | FR-011 | Line 36 expects `record-1` for `searchOrgDeviceEvents` (RC-95). The expectation changes to the identity key (D-10). |
| `documentation/diagrams/core/database-strategy.md` | modify | FR-016 | Source of Truth section, lines 173 to 177 (RC-39). |
| `changelog.d/issue-4725-arango-composite-key-overwrite.md` | add | FR-016 | One `Fixed` bullet that names issue #4725. |

Delete: none (FR-010). Unchanged: `src/foundation/support/refactors/endpoint_primary_key_strategies.py` (RC-64, FR-013), `src/foundation/support/refactors/sqlite_database_writer.py` (RC-85), `src/foundation/persistence/db/writers/redis_writer.py` (RC-83).

## Approach

1. **Gate (T001 to T002).** Confirm ownership and handoffs. Write the identity audit rows for the 121 entries. Only then edit the writer.
2. **Writer (T003 to T005).** Add `CompositeKeyIdentity`. Route `_compute_key` through it after the SLE checks. Add the batch logs.
3. **Tests (T006 to T012).** Add the 17 tests. Update the one preservation expectation. Run the SLE tests without edits.
4. **Docs and changelog (T013 to T014).** Update the Source of Truth section and add the fragment.
5. **Gates and delivery (T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE).** Run the applicable gates. Open the pull request. Watch CI. Merge after authorization.
6. **Migration (T015 to T018).** Gated by D-7. Only after an approved backup plan.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| Key churn. Each affected entry writes new documents beside legacy ones. | Caution: Duplicate documents and larger collections. | D-7 approval before any migration. FR-010 blocks deletion. Caution statement in Rollback. |
| Ownership conflict on `arango_writer.py`. | Warning: Lost work cannot be recovered. Caution: Merge conflicts block the pull request. | T001 handoffs. The open pull request check found no overlap (analysis, A-16). The strategy table stays unchanged. |
| A wrong exemption. | Caution: A silent identity mismatch for that collection. | An exemption needs OpenAPI evidence (D-3). Test 15 reads the table. |
| The preservation expectation changes. | Caution: A regression could hide behind the change. | D-10 names the change. Tests 13 and 14 keep the replace and preservation contracts. |
| Numeric type drift. | Caution: One observation stored as two documents. | FR-004 and test 6. |
| Extra cost per record. | Caution: Slower batches. | One digest for each record. No network call is added. |
| Silent fallback. | Caution: Records accumulate without an operator notice. | FR-006 counts each fallback and logs a warning. |

## Rollback and Migration

**Rollback.** Revert the change commit. New writes use legacy keys again. Identity-key documents stay in place and need no action.

Caution: re-exported records then exist once under each key family until a migration removes one copy.

**Migration (not part of this change).**

- M1. Census (T015): count all documents and legacy-key documents in each affected collection. Read only.
- M2. Backup (T016): create a verified backup of each affected collection before any change.
- M3. Dry run: derive each legacy document identity key from its stored fields. Report counts and collisions. Write nothing.
- M4. Decision (T017, D-7): the operator chooses the legacy-document policy.

Warning: removing legacy documents is irreversible without the M2 backup.

Warning: a legacy key can already hide a replaced record. A migration cannot restore that record.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| `arango_writer.py` (4,456 lines) remains above the structural limit and is touched. | The defect sits in its write path. | A full split is a separate refactor. It is tracked as remediation action R-1 (T018). |
| `_compute_key` gains the collection name as a parameter. | Exemptions are audited per collection. | A global exemption flag cannot express per-collection audits. |
