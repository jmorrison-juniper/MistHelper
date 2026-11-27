# Data Integrity Checklist: OSPF Peer Identity Keys

**Purpose**: Check that the identity keys and the storage rules prevent silent loss

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Key Separation

- [x] Records that differ only in neighbor produce two keys. Test: `test_identity_key_differs_when_neighbor_differs`.
- [x] Records that differ only in VRF produce two keys. Test: `test_identity_key_differs_when_vrf_name_differs`.
- [x] Records that differ only in port produce two keys. Test: `test_identity_key_differs_when_port_id_differs`.
- [x] An absent scope value differs from the text `unknown`. Test: `test_absent_scope_is_distinct_from_literal_unknown`.
- [x] Equal timestamps in two forms produce one key. Test: `test_timestamp_forms_produce_one_key`.

## Silent Loss Prevention

- [x] Two colliding records keep two SQLite rows. Test: `test_ospf_records_with_same_mac_and_timestamp_keep_distinct_neighbors`.
- [x] Two colliding records keep two Redis documents and two ArangoDB documents. Test: `test_ospf_composite_write_uses_identity_key_for_redis_and_arango`.
- [x] A batch with a missing required component writes no output. Tests: `test_ospf_batch_with_missing_neighbor_writes_no_rows` and `test_ospf_invalid_record_returns_failed_write_without_backend_calls`.
- [x] A failed write reports failure and names the component or the table. Tests: `test_ospf_v2_table_with_wrong_primary_key_fails_closed` and the rejection tests above.

## Legacy Preservation

- [x] A legacy SQLite table keeps its schema and row count. Test: `test_ospf_legacy_table_is_unchanged_after_v2_write`.
- [x] No migration or purge runs. Requirement: FR-018. Decision: D-9.
- [x] Legacy Redis keys expire by the TTL and need no action. Source: RV-18.
- [x] Legacy ArangoDB documents remain in the collection. Explained: the operator decides on removal (D-9).

## Accepted Residual Risks

- [x] Duplicates can appear when a batch mixes payloads with and without scope fields. Explained: a duplicate never replaces another record (D-4 and D-3).
- [x] The live payload might omit `neighbor`. Explained: the batch fails with the component name, and U-01 records the open question.
- [x] Real Redis and ArangoDB servers are not exercised. Explained: U-05 records the gap. The fakes match the issue reproduction.
