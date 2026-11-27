# Contract Evidence Checklist: Mist API Contract Evidence for the Cisco Converter

**Purpose**: Check that each contract row has complete, traceable evidence and that each gap is recorded.
**Created**: 2026-11-26
**Feature**: `design\contracts\mist-write-operations.md`, `mist-read-operations.md`, `mist-payload-fields.md`, and `mist-sdk-behavior.md`

## Row Completeness

- [x] CON001 Each of the 22 write rows cites the OpenAPI object, the YAML line, the SDK function line, and the SDK call line.
- [x] CON002 Each of the 18 read rows cites the OpenAPI object, the YAML line, and the SDK function line.
- [x] CON003 Each write row carries three statuses. Each read row carries two statuses.
- [x] CON004 The excluded operation `deleteOrgServicePolicy` has a scope, a decision reference, and no caller.
- [x] CON005 Each SDK call verb and path match the OpenAPI verb and path, checked for all 40 rows.

## Source Traceability

- [x] CON006 Each SDK function name exists in the pinned source. The names `updateOrgSite` and `updateOrgInventory` are absent (RV-79).
- [x] CON007 Each OpenAPI object location resolves in the bundled JSON file. The file blob equals the blob on main (RV-37 and RV-39).
- [x] CON008 The YAML line numbers match the record 4644 table for the eight families it lists (RV-41).
- [x] CON009 Each retry and timeout value cites the source line in `mist-sdk-behavior.md`.

## Gaps and Unverified Items

- [x] CON010 Each field without service evidence appears in an unverified item with a reason (U-01 to U-18).
- [x] CON011 Each stale or incorrect fact appears in analysis findings A-01 to A-23 with an owner.
- [ ] CON012 Each synthetic fixture passes its test. Explanation: tasks T013 to T015 create the fixtures and the tests.
- [ ] CON013 The pin text drift is corrected in the three documents that disagree. Explanation: a separate issue owns this correction (A-11).
- [x] CON014 No upstream URL is recorded as evidence, because no upstream URL was fetched (`research.md`, Sources).
