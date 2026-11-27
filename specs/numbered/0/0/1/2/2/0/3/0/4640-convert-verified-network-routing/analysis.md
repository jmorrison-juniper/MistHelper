# Specification Analysis Report: Convert Verified Network and Routing Settings

## Result

The spec, plan, tasks, contracts, and research agree on the package layout, the test paths, and the decision list. The change replaces `conversion.py` with a `conversion/` package. It keeps the converter root at five children. It adds no route, no shared portal file, and no Mist call.

The record finds fourteen defects in existing work. Three are high severity. The record makes eighteen decisions. One decision needs a human owner (D-18).

Nothing was executed in this drafting pass. The repository rules forbid tests, linters, and builds here. The read-only checks in `design\research.md`, section Remote Verification, ran against GitHub `main`.

## Metrics

| Measure | Value |
| --- | --- |
| Functional requirements | 17 (FR-001 to FR-017) |
| Success criteria | 6 (SC-001 to SC-006) |
| User stories | 5 (3 at P1 and 2 at P2) |
| Tasks | 19 (15 implementation, prerequisite, or audit tasks and 4 final tasks) |
| Planned test functions | 35 |
| Decisions | 18, of which 1 needs a human owner (D-18) |
| Remote checks | 52 rows in `design\research.md`, section Remote Verification |
| Defects in existing work | 14 |
| Unresolved items | 14 (U-1 to U-14) |

## Remote Evidence Summary

- GitHub `main` is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Local `HEAD` matches it.
- The remote tree lists 11,404 entries and is not truncated.
- The converter root holds five children. `src/interfaces/portals/` holds six. `tests/contract/` holds 17.
- The OpenAPI blob on `main` matches the local file. Its blob SHA is `b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14`.
- The route `specs\numbered\0\0\1\2\2\0\3\0` is absent on `main`. The base-5 route for 4640 matches the route script.
- No pull request names issue 4640. Merged PR #4596 holds the full task map.

## Defects in Existing Work

| ID | Severity | Location | Summary | Disposition |
| --- | --- | --- | --- | --- |
| E-1 | HIGH | `src/interfaces/portals/cisco_config_converter/conversion.py` and live `tasks.md` line 60 | The module holds two top-level names and one class with five methods. The live T014 path adds network families to that module. The module cannot hold them within the five-name and five-member limits. | D-1 replaces the module with a `conversion/` package. |
| E-2 | HIGH | Live `tasks.md` line 59 and `tests/contract/` with 17 children (R04) | The live T013 path adds a direct child to a noncompliant parent. The constitution forbids that change. | D-2 moves the tests under the integration folder. |
| E-3 | HIGH | Live `tasks.md` lines 58 to 60, and live T016 | Live tasks T012, T014, and T016 all edit `conversion.py`. Three parallel implementation tasks would edit one file. | D-3 reserves `hardware/` and `management/`. D-15 sets the order. |
| E-4 | MEDIUM | `conversion.py` line 26 (known-gap text) | The first sentence says only `ip name-server` converts. Domain names and network families make it false. The second sentence at line 27 says all other settings remain unsupported. That sentence becomes false in the composed proposal. | D-10 revises the first sentence in this record. Issue #4641 revises the composed text (U-5). |
| E-5 | MEDIUM | OpenAPI `disabled` property at line 80118, description at line 80120 | The description says `Port admin up (true) / down (false)`. The property name and the description point in opposite directions. | No `shutdown` value is emitted. Test 14 proves the unresolved result. Issue #4634 must resolve the wording (U-2). |
| E-6 | MEDIUM | Issue #4636 summary and STATUS file | The summary states 60 remote checks. The STATUS file lists 24. The brief requires equal counts. | This record uses 52 rows in all three places. Issue #4636 owner must correct the sibling counts (U-4). |
| E-7 | MEDIUM | Issue #4636 decision D-1 | D-1 keeps `conversion.py` for import lines only. This record supersedes that part of D-1 after issue #4636 merges. | The change record names the supersession. Issue #4636 needs no code change (U-4). |
| E-8 | LOW | `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py` | The DNS unit test sits in a folder that does not match its subject. Issue #4636 records the same finding as E-12. | No move in this record. Only the import line changes. |
| E-9 | MEDIUM | Live `spec.md` FR-005 and OpenAPI `gateway_template.type` at line 80768 | The live spec names Branch, Hub, and Standalone. The OpenAPI gateway template enum names spoke and standalone only. The existing code names standalone and spoke (`models.py` line 51). | D-17 keeps the role contract with issue #4638. Hub targets are out of scope here (U-10). |
| E-10 | LOW | Live `tasks.md` line 59 names DHCP exclusions as a test item | The OpenAPI DHCP pool schema has no exclusion field (R38). The item cannot map directly. | D-5 derives the range from exclusions and treats middle exclusions as unresolved. |
| E-11 | MEDIUM | OpenAPI `ae_idx` at line 80089 | The type is `string` or `null`. The description says integer from 0 to 127. | The converter emits a string. The representation stays unverified (U-2). |
| E-12 | LOW | OpenAPI `vars` example at line 117449 | The example holds a credential-like sample value in a WLAN variable schema. | This record does not copy the example. No `vars` key is emitted (U-9). |
| E-13 | LOW | Live `research.md` row C12 at line 96 | Row C12 names DNS suffixes as unsupported. This record adds the DNS suffix. | D-10 adds the mapping. The row stays accurate for the live record. |
| E-14 | LOW | Live `spec.md` FR-007 at line 113 | The live spec asks for WAN and LAN intent without silent assumptions. The current code has no role input. | D-4 takes each role from the explicit assignment only. |

## Remediation Actions

These actions track structure debt that this record does not touch. Each action belongs in a separate issue.

- R-1: `src/interfaces/portals/` holds six children. Remediation action R-1 in issue #4636 covers this debt.
- R-2: `tests/contract/` holds 17 children. Remediation action R-2 in issue #4636 covers this debt.

## Unresolved Items

| ID | Owner | Action |
| --- | --- | --- |
| U-1 | Reviewer of T004 | Confirm each IOS command form in the tests. No Cisco command reference was fetched in this pass. |
| U-2 | Issue #4634 | Supply G2 rows for each key. Resolve `disabled` wording, `ae_idx` representation, `neighbor_as` representation, and `ip_start` and `ip_end` semantics. |
| U-3 | Issue #4638 | Supply `PortAssignment` values, the port name grammar, and the SRX and SSR family values. |
| U-4 | Issue #4636 owner | Merge `state/proposal.py` first. Correct the remote check count in the summary and STATUS file. |
| U-5 | Issue #4641 owner | Revise the composed known-gap text and merge the DNS output with the network fragment. |
| U-6 | Issue #4634 | Confirm the Mist network name rules for generated names such as `VLAN10`. |
| U-7 | Issue #4638 | Confirm VRF support per SRX and SSR model for `vrf_config.enabled`. |
| U-8 | Issue #4634 | Confirm the meaning of `bgp_config.networks`. Prefixes stay unresolved until confirmed. |
| U-9 | Issue #4634 | Confirm the site variable store location and schema for `{{name}}` values. |
| U-10 | Issues #4638 and #4641 | Verify the `networks` property of `deviceprofile_gateway` for Hub targets. |
| U-11 | Implementer | Record the symbol gate result for the removed `conversion.py` in the pull request. |
| U-12 | Owner | Decide the credential policy for BGP and other secrets (D-18). |
| U-13 | Orchestrator | Decide whether new Markdown records join the STE gate. Issue #4636 U-8 asks the same question. |
| U-14 | Implementer | Measure the Windows run time of the `pytest-chunks` shards before the pull request. |

## Coverage Summary

Each requirement maps to at least one task and at least one test or gate.

| Requirement | Tasks | Tests or gate |
| --- | --- | --- |
| FR-001 | T002, T007, T008 | Tests 33 and the existing DNS tests |
| FR-002 | T004, T010 | Tests 1 to 4 |
| FR-003 | T004, T010 | Tests 5 and 6 |
| FR-004 | T004, T010 | Tests 8 to 10 |
| FR-005 | T004, T010 | Tests 11 and 12 |
| FR-006 | T005, T011 | Tests 18 to 21 |
| FR-007 | T006, T012 | Tests 26 and 27 |
| FR-008 | T006, T012 | Tests 28 and 29 |
| FR-009 | T006, T012 | Tests 30 to 32 |
| FR-010 | T005, T013 | Tests 22 and 23 |
| FR-011 | T005, T008 | Tests 24 and 25 |
| FR-012 | T004, T010 | Tests 16 and 17 |
| FR-013 | T003, T007, T014 | Test 35 |
| FR-014 | T004, T009, T010 | Tests 4 to 7 check the reason text |
| FR-015 | T007, T009 | Tests 31 and 34 |
| FR-016 | T001, T004 to T007, T015 | Red-state records and the gates in T-LOCAL-GATES |
| FR-017 | T008, T014, T015 | Symbol gate, guardrails, and the structure counts in `plan.md` |

## Success Criteria Coverage

| Criterion | Evidence |
| --- | --- |
| SC-001 | Tests 1 to 32 cover each family with positive and negative cases. |
| SC-002 | Test 33 compares the DNS output and the domain key. |
| SC-003 | Test 34 blocks sockets, file writes, and Mist calls. |
| SC-004 | Test 35 proves each emitted key has a register row with an OpenAPI line. |
| SC-005 | T-LOCAL-GATES lists each applicable gate with its expected result. |
| SC-006 | T015 and the counts in `plan.md`, section Capacity and Structure Inventory. |

## Test List

These names are the canonical list. Tasks T004 to T007 cite the numbers.

| No. | Module | Test function | Requirement |
| --- | --- | --- | --- |
| 1 | `test_network.py` | `test_wan_address_maps_to_port_ip_config` | FR-002 |
| 2 | `test_network.py` | `test_lan_address_maps_to_network_ip_config` | FR-002 |
| 3 | `test_network.py` | `test_contiguous_masks_convert_to_prefix_length` | FR-002 |
| 4 | `test_network.py` | `test_invalid_address_or_mask_is_unresolved` | FR-002, FR-014 |
| 5 | `test_network.py` | `test_missing_port_assignment_is_unresolved` | FR-003, FR-014 |
| 6 | `test_network.py` | `test_missing_or_conflicting_role_is_unresolved` | FR-003, FR-014 |
| 7 | `test_network.py` | `test_dhcp_client_addressing_is_unresolved` | FR-002, FR-014 |
| 8 | `test_network.py` | `test_access_and_trunk_vlans_map_to_networks` | FR-004 |
| 9 | `test_network.py` | `test_vlan_range_violations_are_unresolved` | FR-004 |
| 10 | `test_network.py` | `test_second_wan_vlan_on_one_port_is_unresolved` | FR-004 |
| 11 | `test_network.py` | `test_aggregate_maps_members_and_lacp_mode` | FR-005 |
| 12 | `test_network.py` | `test_aggregate_member_conflict_is_unresolved` | FR-005 |
| 13 | `test_network.py` | `test_untagged_lan_network_is_srx_only` | FR-004 |
| 14 | `test_network.py` | `test_shutdown_is_unresolved_until_meaning_is_verified` | FR-002, FR-014 |
| 15 | `test_network.py` | `test_speed_mapping_is_unresolved` | FR-014 |
| 16 | `test_network.py` | `test_allowed_variable_fields_keep_tokens` | FR-012 |
| 17 | `test_network.py` | `test_unlisted_variable_field_is_unresolved` | FR-012 |
| 18 | `test_services.py` | `test_dhcp_pool_maps_verified_fields` | FR-006 |
| 19 | `test_services.py` | `test_dhcp_middle_exclusion_is_unresolved` | FR-006 |
| 20 | `test_services.py` | `test_dhcp_overlap_or_gateway_in_range_is_unresolved` | FR-006 |
| 21 | `test_services.py` | `test_dhcp_invalid_mask_or_lease_is_unresolved` | FR-006 |
| 22 | `test_services.py` | `test_ntp_ipv4_servers_map` | FR-010 |
| 23 | `test_services.py` | `test_ntp_hostname_ipv6_or_option_is_unresolved` | FR-010 |
| 24 | `test_services.py` | `test_domain_name_maps_to_dns_suffix` | FR-011 |
| 25 | `test_services.py` | `test_conflicting_domain_names_are_unresolved` | FR-011 |
| 26 | `test_routing.py` | `test_static_routes_map_to_extra_routes` | FR-007 |
| 27 | `test_routing.py` | `test_route_forms_outside_verified_fields_are_unresolved` | FR-007 |
| 28 | `test_routing.py` | `test_vrf_membership_maps_networks` | FR-008 |
| 29 | `test_routing.py` | `test_vrf_distinguisher_and_vrf_routes_are_unresolved` | FR-008 |
| 30 | `test_routing.py` | `test_bgp_session_maps_verified_fields` | FR-009 |
| 31 | `test_routing.py` | `test_bgp_prefixes_and_credentials_are_not_emitted` | FR-009, FR-015 |
| 32 | `test_routing.py` | `test_bgp_transport_must_derive_from_subnet` | FR-009 |
| 33 | `test_compat.py` | `test_dns_output_changes_only_in_known_gap_sentence_and_domain_key` | FR-001 |
| 34 | `test_compat.py` | `test_offline_conversion_blocks_sockets_and_file_writes` | FR-015 |
| 35 | `test_compat.py` | `test_emitted_keys_appear_in_mapping_register` | FR-013 |

## Consistency Review

| Check | Result |
| --- | --- |
| Spec requirements appear in the plan and tasks | Pass. Each FR appears in the coverage table. |
| Each plan file path appears in a task | Pass. The package modules, the moved module, the import lines, and the four test modules each appear in a task. |
| Test counts agree across documents | Pass. The spec, plan, tasks, analysis, and STATUS file state 35. |
| Module names agree across plan and contracts | Pass. The contracts use the names in the replacement layout. |
| Decision references agree | Pass. Decisions D-1 to D-18 appear in `research.md`. Each reference in this record points to an existing decision. |
| Remote checks match the research table | Pass. The research table, the STATUS file, and the summary state 52. |
| Directory counts match the remote listing | Pass. Counts appear in `plan.md` and `research.md`. |
| Dates and PR states match the remote record | Pass. PR #4596 is merged. No pull request names issue #4640. |
| Writing style of the record | Pass after self-review. Each file was searched for semicolons, contractions, Latin abbreviations, unfinished markers, and phrasal verbs. |

## Constitution Alignment

The constitution check in `plan.md` lists each rule with its result. One rule fails until the owner resolves issue #4636 unresolved item U-2: the structured-log requirement in Principle V. Inline comments and action logging pass only after tasks T009 to T015 run.

## Validation Commands and Results

| Command | Result |
| --- | --- |
| `python -m ruff check .` | Not run. The drafting rules forbid linters in this pass. |
| `python -m black --check .` | Not run. The drafting rules forbid formatters in this pass. |
| `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | Not run. The drafting rules forbid type checks in this pass. |
| `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py` | Not run. The drafting rules forbid tests in this pass. |
| `python -m pytest tests/guardrails/test_nested_package_structure.py` | Not run. The drafting rules forbid tests in this pass. |
| `git -C <repo> hash-object` and `gh api` reads | Run. Results appear in `design\research.md`, section Remote Verification. |
| `Get-Content` and `[IO.File]::ReadAllLines` on the local checkout | Run. Results appear in `design\research.md`, section Sources. |

The T-LOCAL-GATES task in `tasks.md` names every command that the implementer must run before the pull request.
