# Checklist: Preservation and Compatibility

**Purpose**: Check that the change keeps existing ArangoDB data, existing keys, and existing contracts.
**Created**: 2026-11-26
**Feature**: `spec.md` (FR-007 to FR-012) and `design/contracts/arango-document-key.md`.

## Stored Data

- [x] The writer deletes no document. Evidence: FR-010. Test 13 asserts that the collection handle receives only `import_bulk` calls.
- [x] The writer rewrites no legacy document. Evidence: FR-010. Test 13. The legacy document keeps its key and its content (S13 in `quickstart.md`).
- [x] The writer changes no index or collection. Evidence: FR-010. `_ensure_collection` (RC-58) and the index path stay unchanged.
- [x] Legacy documents stay in place after the change. Evidence: D-7. A later migration needs approval.

## Keys

- [x] SLE keys do not change. Evidence: FR-008. Test 11. Existing tests in RC-97 and RC-98.
- [x] Single-field keys do not change. Evidence: FR-007. Test 10.
- [x] The one changed existing expectation is named. Evidence: D-10 and T010. The `searchOrgDeviceEvents` expectation at `test_preservation.py` line 36 (RC-95) changes to the identity key.
- [x] Exempt collections keep their legacy key. Evidence: FR-009. Test 12. The exemption set starts empty.

## Import Contract

- [x] `on_duplicate="replace"` stays in place. Evidence: FR-011, RC-53, and RC-96.
- [x] `WriteResult` counts keep their meaning. Evidence: D-12, RC-54, and RC-92.
- [x] The router contract stays unchanged. Evidence: plan, Constitution Check, export boundary row.

## Migration and Rollback

- [x] Migration waits for a backup and an approved policy. Evidence: FR-012, T015, T016, T017, and D-7.
- [x] The rollback leaves no broken document. Evidence: `plan.md`, Rollback and Migration. Identity documents are valid documents.
- [x] The rollback states its duplicate effect. Evidence: the Caution statement in `plan.md`.
- [x] Warning statements name the irreversible steps. Evidence: the two Warning statements in `plan.md` and `data-model.md`.

## Other Stores

- [x] SQLite behavior does not change. Evidence: FR-013 and D-8. RC-84 and RC-85 describe the current behavior.
- [x] Redis behavior does not change. Evidence: FR-013 and D-8. RC-83 describes the current behavior.
