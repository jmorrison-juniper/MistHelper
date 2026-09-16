<!-- site-read-handoff:06-task-list -->
# Artifact 06: tasks.md

**Input:** The complete specification, research, plan, data model, contracts, and twenty packets in this issue.
**Status:** All implementation tasks are intentionally unchecked.
**Execution rule:** One owner executes shared-file tasks sequentially. No task is parallel unless marked `[P]`.
**Completion rule:** Mark a task complete only after its named evidence exists. Save command, exit code, and result in the feature's verification record.

## Phase 1: Preflight and setup

- [ ] T001 [US1] Verify authorization, GitHub account, current source issue states, and active claims. Follow `quickstart.md` exactly. Map: FR-001, FR-015.
- [ ] T002 [US1] Claim this handoff and create its isolated worktree from current `origin/main`. Build its own `.venv`. Require the full SDK import check to pass. Map: FR-003, FR-015.
- [ ] T003 [US4] Materialize every issue artifact under `specs/2339-site-read-exports/`. Set local feature context. Run the native prerequisites and read-only analysis. Do not invoke auto-implementation hooks. Map: FR-016.
- [ ] T004 [US4] Record baseline test results for the existing exporter, writer, redactor, registry, and public API guards named in `plan.md`. Record unrelated failures separately. Map: FR-014, FR-015.

## Phase 2: Foundational contracts

- [ ] T005 [US1] Write tests for immutable metadata and runtime models in `tests/unit/export/site_read/test_catalog.py`. Test invalid page limits and unknown operations. Map: FR-001, FR-002, FR-003.
- [ ] T006 [US1] Create the five models in `src/export/site_read/models.py` and inert package initialization. Keep all field and parameter limits. Map: FR-014.
- [ ] T007 [US1] Create `SiteReadCatalog` in `src/export/site_read/catalog.py`. Resolve only explicit metadata. Build kwargs without guessing SDK support. Endpoint rows arrive through the packet tasks. Map: FR-001, FR-003.
- [ ] T008 [US2] Write prompt tests in `test_service.py` for valid choices, blank input, q, 0, EOF, Ctrl+C, negative values, text, nondecimal Unicode, and out-of-range numbers. Map: FR-002, FR-006.
- [ ] T009 [US2] Implement request selection in `service.py` using injected context resolvers and `InputUtils.safe_input`. Validate canonical site and organization UUIDs. Map: FR-002, FR-006.
- [ ] T010 [US2] Write page-guard tests in `test_fetch.py` for every status, invalid body, mixed rows, repeated continuation, absolute URL, changed site/path, null next response, and both bounds. Map: FR-004, FR-006.
- [ ] T011 [US2] Implement `SiteReadPageGuard` and the checked SDK continuation loop in `fetch.py`. Return rows only after complete validation. Map: FR-004, FR-006.
- [ ] T012 [US1] Write fake-pacer and configured-session identity tests in `test_fetch.py`. Confirm one pacing call per initial or continuation request and no independent retry loop. Map: FR-003, FR-005.
- [ ] T013 [US1] Connect pacing and the existing SDK session to the fetcher. Keep network and sleep operations injectable in tests. Map: FR-003, FR-005.
- [ ] T014 [US3] Extend `tests/unit/security/test_credential_redaction.py` with nested keywrap_kek, keywrap_mack, and magic sentinels. Verify the caller's input stays unchanged. Map: FR-007, FR-008.
- [ ] T015 [US3] Extend the canonical redactor's exact-key set for those fields. Preserve existing behavior and tests. Map: FR-008.
- [ ] T016 [US3] Write record tests in `test_service.py` for missing identity, conflicting scope, inherited source_site_id, duplicate keys, nested arrays, and safe filenames. Map: FR-007, FR-010, FR-011.
- [ ] T017 [US3] Implement record validation, scope enrichment, deep-copy redaction, and flattening in `service.py`. Validate encoded key size before writing. Never invent an API id. Map: FR-007, FR-008, FR-010, FR-011.
- [ ] T018 [US3] Write deterministic scoped-key and collision property tests in `tests/unit/db/test_storage_keys.py`. Include delimiter characters, Unicode, missing fields, and the Arango length bound. Map: FR-011, FR-012.
- [ ] T019 [US3] Implement `StorageKeyEncoder` in `src/db/storage_keys.py` using the exact versioned encoding contract. Do not hash credential material or truncate identity. Map: FR-011, FR-012.
- [ ] T020 [US3] Extend `tests/unit/test_arango_writer.py` to prove opt-in scoped keys differ by site and every old strategy keeps its key. Map: FR-011, FR-012.
- [ ] T021 [US3] Add the explicit opt-in branch in `ArangoDBWriter._prepare_document`. Do not alter global graph identity or ordinary `_compute_key` behavior. Map: FR-012.
- [ ] T022 [US3] Extend `tests/unit/test_redis_writer.py` to prove the new scoped key mode and byte-identical old Redis JSON keys. Map: FR-011, FR-012.
- [ ] T023 [US3] Carry the opt-in field list through `RedisJSONWriter` batches and key formatting. Do not change TimeSeries behavior or TTL policy. Map: FR-012.
- [ ] T024 [US3] Write persistence tests in `test_storage.py` using real temporary SQLite DDL, recording database clients, and false writer outcomes. Do not use mocked DDL to claim upsert correctness. Map: FR-009, FR-011, FR-013.
- [ ] T025 [US3] Implement `SiteReadPersistence.write` with the canonical writer and redacted raw-data option. Interpret the primary boolean without hiding mirror warnings. Map: FR-009, FR-013.
- [ ] T026 [US2] Write safe error-reporting tests in `test_service.py`. Include an exception message containing a secret sentinel. Require frame context but no raw message or local values. Map: FR-006, FR-008.
- [ ] T027 [US2] Implement safe error outcomes and reporting. Keep cancellation, empty, saved, and error states distinct. Map: FR-006, FR-013.
- [ ] T028 [US4] Add import and architecture guards to the feature tests. Prohibit a new `MistHelper` import, import-time I/O, arbitrary SDK enumeration, and write endpoints. Map: FR-003, FR-014.
- [ ] T029 [US4] Check new class size, function size, comments, logging, Ruff, Black, and mypy for the foundation. Do not use suppressions to meet these limits. Map: FR-014, FR-015.
- [ ] T030 [US1] Verify the foundation with fake EndpointSpec fixtures before adding production catalog rows. Record every failing or skipped check. Map: FR-015.

## Phase 3: Twenty endpoint increments

Insert T031 through T150 from the twenty packets here, in their published order. The published task list includes the same concrete lines below. Complete #1313 end to end first. Do not wire the menu until the full catalog and safety tests pass.

- [ ] T031 [US1] Add the #1313 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteAssetFilters, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T032 [US1] Add only the #1313 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.assetfilters and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T033 [US3] Add storage_key_fields [site_id, id] to the existing listSiteAssetFilters strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T034 [US2] Add #1313 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T035 [US3] Add #1313 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T036 [US4] Correct specs/805-mist-list-site-asset-filters/spec.md for the verified SDK module and family menu. Run the #1313 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.
- [ ] T037 [US1] Add the #1314 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteAssets, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T038 [US1] Add only the #1314 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.assets and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T039 [US3] Add storage_key_fields [site_id, id] to the existing listSiteAssets strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T040 [US2] Add #1314 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T041 [US3] Add #1314 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T042 [US4] Correct specs/806-mist-list-site-assets/spec.md for the verified SDK module and family menu. Run the #1314 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.
- [ ] T043 [US1] Add the #1330 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteOtherDevices, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T044 [US1] Add only the #1330 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.otherdevices and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T045 [US3] Add storage_key_fields [site_id, id] to the existing listSiteOtherDevices strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T046 [US2] Add #1330 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T047 [US3] Add #1330 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T048 [US4] Correct specs/822-mist-list-site-other-devices/spec.md for the verified SDK module and family menu. Run the #1330 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.
- [ ] T049 [US1] Add the #1335 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteRssiZones, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T050 [US1] Add only the #1335 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.rssizones and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T051 [US3] Add storage_key_fields [site_id, id] to the existing listSiteRssiZones strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T052 [US2] Add #1335 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T053 [US3] Add #1335 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T054 [US4] Correct specs/827-mist-list-site-rssi-zones/spec.md for the verified SDK module and family menu. Run the #1335 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.
- [ ] T055 [US1] Add the #1357 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteWxRules, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T056 [US1] Add only the #1357 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.wxrules and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T057 [US3] Add storage_key_fields [site_id, id] to the existing listSiteWxRules strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T058 [US2] Add #1357 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T059 [US3] Add #1357 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T060 [US4] Correct specs/849-mist-list-site-wx-rules/spec.md for the verified SDK module and family menu. Run the #1357 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.
- [ ] T061 [US1] Add the #1358 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteWxTags, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T062 [US1] Add only the #1358 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.wxtags and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T063 [US3] Add storage_key_fields [site_id, id] to the existing listSiteWxTags strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T064 [US2] Add #1358 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T065 [US3] Add #1358 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T066 [US4] Correct specs/850-mist-list-site-wx-tags/spec.md for the verified SDK module and family menu. Run the #1358 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.
- [ ] T067 [US1] Add the #1359 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteWxTunnels, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T068 [US1] Add only the #1359 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.wxtunnels and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T069 [US3] Add storage_key_fields [site_id, id] to the existing listSiteWxTunnels strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T070 [US2] Add #1359 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T071 [US3] Add #1359 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T072 [US4] Correct specs/851-mist-list-site-wx-tunnels/spec.md for the verified SDK module and family menu. Run the #1359 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.
- [ ] T073 [US1] Add the #1323 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteEvpnTopologies, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T074 [US1] Add only the #1323 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.evpn_topologies and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T075 [US3] Add storage_key_fields [site_id, id] to the existing listSiteEvpnTopologies strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T076 [US2] Add #1323 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T077 [US3] Add #1323 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T078 [US4] Correct specs/815-mist-list-site-evpn-topologies/spec.md for the verified SDK module and family menu. Run the #1323 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.
- [ ] T079 [US1] Add the #1307 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteAAMWProfilesDerived, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T080 [US1] Add only the #1307 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.aamwprofiles and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T081 [US3] Add storage_key_fields [site_id, id] to the existing listSiteAAMWProfilesDerived strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T082 [US2] Add #1307 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T083 [US3] Add #1307 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T084 [US4] Correct specs/799-mist-list-site-a-a-m-w-profiles-derived/spec.md for the verified SDK module and family menu. Run the #1307 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.
- [ ] T085 [US1] Add the #1310 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteAntivirusProfilesDerived, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T086 [US1] Add only the #1310 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.avprofiles and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T087 [US3] Add storage_key_fields [site_id, id] to the existing listSiteAntivirusProfilesDerived strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T088 [US2] Add #1310 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T089 [US3] Add #1310 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T090 [US4] Correct specs/802-mist-list-site-antivirus-profiles-derived/spec.md for the verified SDK module and family menu. Run the #1310 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.
- [ ] T091 [US1] Add the #1324 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteIdpProfilesDerived, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T092 [US1] Add only the #1324 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.idpprofiles and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T093 [US3] Add storage_key_fields [site_id, id] to the existing listSiteIdpProfilesDerived strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T094 [US2] Add #1324 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T095 [US3] Add #1324 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T096 [US4] Correct specs/816-mist-list-site-idp-profiles-derived/spec.md for the verified SDK module and family menu. Run the #1324 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.
- [ ] T097 [US1] Add the #1311 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteApTemplatesDerived, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T098 [US1] Add only the #1311 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.aptemplates and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T099 [US3] Add storage_key_fields [site_id, id] to the existing listSiteApTemplatesDerived strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T100 [US2] Add #1311 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T101 [US3] Add #1311 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T102 [US4] Correct specs/803-mist-list-site-ap-templates-derived/spec.md for the verified SDK module and family menu. Run the #1311 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.
- [ ] T103 [US1] Add the #1319 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteDeviceProfilesDerived, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T104 [US1] Add only the #1319 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.deviceprofiles and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T105 [US3] Add storage_key_fields [site_id, id] to the existing listSiteDeviceProfilesDerived strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T106 [US2] Add #1319 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T107 [US3] Add #1319 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T108 [US4] Correct specs/811-mist-list-site-device-profiles-derived/spec.md for the verified SDK module and family menu. Run the #1319 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.
- [ ] T109 [US1] Add the #1332 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteRfTemplatesDerived, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T110 [US1] Add only the #1332 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.rftemplates and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T111 [US3] Add storage_key_fields [site_id, id] to the existing listSiteRfTemplatesDerived strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T112 [US2] Add #1332 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T113 [US3] Add #1332 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T114 [US4] Correct specs/824-mist-list-site-rf-templates-derived/spec.md for the verified SDK module and family menu. Run the #1332 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.
- [ ] T115 [US1] Add the #1337 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteSecIntelProfilesDerived, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T116 [US1] Add only the #1337 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.secintelprofiles and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T117 [US3] Add storage_key_fields [site_id, id] to the existing listSiteSecIntelProfilesDerived strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T118 [US2] Add #1337 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T119 [US3] Add #1337 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T120 [US4] Correct specs/829-mist-list-site-sec-intel-profiles-derived/spec.md for the verified SDK module and family menu. Run the #1337 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.
- [ ] T121 [US1] Add the #1338 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteServicesDerived, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T122 [US1] Add only the #1338 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.services and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T123 [US3] Add storage_key_fields [site_id, id] to the existing listSiteServicesDerived strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T124 [US2] Add #1338 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T125 [US3] Add #1338 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T126 [US4] Correct specs/830-mist-list-site-services-derived/spec.md for the verified SDK module and family menu. Run the #1338 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.
- [ ] T127 [US1] Add the #1339 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteSiteTemplatesDerived, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T128 [US1] Add only the #1339 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.sitetemplates and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T129 [US3] Add storage_key_fields [site_id, id] to the existing listSiteSiteTemplatesDerived strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T130 [US2] Add #1339 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T131 [US3] Add #1339 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T132 [US4] Correct specs/831-mist-list-site-site-templates-derived/spec.md for the verified SDK module and family menu. Run the #1339 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.
- [ ] T133 [US1] Add the #1328 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteMxEdgesStats, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T134 [US1] Add only the #1328 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.stats and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T135 [US3] Add storage_key_fields [site_id, id, mac] to the existing listSiteMxEdgesStats strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T136 [US2] Add #1328 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T137 [US3] Add #1328 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T138 [US4] Correct specs/820-mist-list-site-mx-edges-stats/spec.md for the verified SDK module and family menu. Run the #1328 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.
- [ ] T139 [US1] Add the #1336 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteRssiZonesStats, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T140 [US1] Add only the #1336 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.stats and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T141 [US3] Add storage_key_fields [site_id, id, map_id] to the existing listSiteRssiZonesStats strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T142 [US2] Add #1336 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T143 [US3] Add #1336 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T144 [US4] Correct specs/828-mist-list-site-rssi-zones-stats/spec.md for the verified SDK module and family menu. Run the #1336 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.
- [ ] T145 [US1] Add the #1360 case to tests/unit/export/site_read/conftest.py and test_catalog.py. Verify listSiteZonesStats, its SDK signature, and its exact GET path. Map: FR-001, FR-003.
- [ ] T146 [US1] Add only the #1360 metadata row to src/export/site_read/catalog.py. Use mistapi.api.v1.sites.stats and the packet keyword mode. Map: FR-001, FR-003, FR-004.
- [ ] T147 [US3] Add storage_key_fields [site_id, id, map_id] to the existing listSiteZonesStats strategy in src/refactors/endpoint_primary_key_strategies.py. Keep type and primary_key unchanged. Map: FR-011, FR-012.
- [ ] T148 [US2] Add #1360 happy, empty, malformed, cancelled, and failed-page cases to test_fetch.py and test_service.py. Assert exact rows and no partial write. Map: FR-004, FR-006, FR-007.
- [ ] T149 [US3] Add #1360 repeat-write, site-separation, key-component, and redaction assertions to test_storage.py. Apply the packet's unique checks. Map: FR-008, FR-009, FR-010, FR-011, FR-013.
- [ ] T150 [US4] Correct specs/852-mist-list-site-zones-stats/spec.md for the verified SDK module and family menu. Run the #1360 focused cases and the shared suite. Record evidence before marking this packet complete. Map: FR-014, FR-015, FR-016.

## Phase 4: Menu, documentation, and delivery

- [ ] T151 [US4] Write a mocked menu-dispatch test and extend registry coverage expectations for exactly one new `interactive_safe` entry. Determine the free menu number from current `MistHelper.py`. Map: FR-001, FR-016.
- [ ] T152 [US4] Add private imports and lazy runtime composition in `MistHelper.py`. Register the same number in `src/utils/operation_registry.py`. Keep existing menu numbers and `__all__` unchanged. Map: FR-001, FR-014, FR-016.
- [ ] T153 [US4] Update `README.md` with the family choice table. Regenerate `documentation/menu_reference.md` and `documentation/wiki/Menu-Reference.md` together. Run the generator twice to prove stability. Map: FR-016.
- [ ] T154 [US4] Add one truthful `CHANGELOG.md` entry. Reconcile the twenty source spec statuses and their family-menu references. Do not mark an unverified endpoint shipped. Map: FR-016.
- [ ] T155 [US4] Run every full local gate in `quickstart.md` using the worktree interpreter and current CI scopes. Keep the new-package branch coverage at 90 percent or higher. Map: FR-015.
- [ ] T156 [US3] Run the full endpoint matrix and property tests together. Recheck redaction sentinels, site separation, every key component, and no partial-page persistence. Map: FR-004, FR-008, FR-011, FR-015.
- [ ] T157 [US4] Complete the mocked manual menu journey. Run service-dependent checks only with disposable local services, or record them as unverified for CI. Do not touch production volumes. Map: FR-015, FR-016.
- [ ] T158 [US4] Repeat read-only SpecKit analysis on the materialized artifacts. Review the complete diff, requirements coverage, task status, and source issue list. Resolve new critical findings before a PR. Map: FR-014, FR-015, FR-016.
- [ ] T159 [US4] Commit once with Conventional Commits and create a PR from the supplied template. Link this handoff and only the verified source issues. Wait for required checks, including CodeQL. Map: FR-015, FR-016.
- [ ] T160 [US4] Record final verification and merge references in the issue. Close only completed source issues. Leave #1807 and #991 open. Remove only your own worktree after merge. Map: FR-016.

## Dependency rules

T001-T004 block all source work. Test tasks precede their implementation tasks. T019 blocks T021 and T023. T014-T027 block endpoint persistence. T030 blocks T031. Each packet depends on the completed prior packet because catalog and storage metadata are shared files. T151 depends on all twenty packets. T155-T158 block T159.

No source task carries `[P]`. Read-only investigation and independent review may run in parallel. Do not confuse independent endpoint behavior with permission to edit the shared catalog simultaneously.

## Evidence to record for each packet

Record the exact SDK callable and query, endpoint-specific test results, two-page behavior where relevant, empty/error behavior, repeated-write count, redaction result, and source spec correction. State `not run` for any live smoke test that did not occur.
