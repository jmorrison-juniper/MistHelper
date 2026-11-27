# Specification Analysis Report: Cisco converter licensing and authorship decisions

## Findings

| ID | Severity | Area | Evidence | Finding | Action |
| - | - | - | - | - | - |
| A-1 | HIGH | Approval | RC-32, RC-34, RC-37, RC-39 | Gate G1 stays open. Parity T002 and the G1 row stay unchecked. The legal review box stays unchecked. | T004 to T012 record the answers and link this record. |
| A-2 | HIGH | Existing work | RC-45 to RC-47, RC-48, RC-68 to RC-73 | PR 4226 merged nine converter files to main (RC-48). The repository holds no provenance review for them. | T011 runs the audit. A separate issue handles any removal. |
| A-3 | HIGH | Existing work | RC-42, RC-43, RC-44 | The 4224 record forbids copying before license approval. The converter files merged after that record. The audit that the record requires is missing. | T011 runs the audit. Item A-2 applies. |
| A-4 | MEDIUM | Distribution | RC-27, RC-28, RC-29 | The Containerfile copies src into the image. The container build runs on pushes to main for listed paths. The published image may hold converter files. Unverified item U-2 covers the image contents. | D-7 asks the owner for the distribution path. |
| A-5 | MEDIUM | Distribution | RC-62, RC-63 | Both repositories are public. Converter files on main are already visible. | D-7 covers the options. This record changes no visibility setting. |
| A-6 | MEDIUM | Process | RC-14, RC-17, RC-31 | The constitution requires one changelog fragment for each change. The changelog README exempts internal-only changes. PR 4596 added no fragment. | D-11 follows the README. The maintainer resolves the constitution text. |
| A-7 | MEDIUM | Licensor | RC-02, RC-50, RC-51 | The source license names no holder. The MistHelper license names jmorrison-juniper as holder. | D-1 asks the owner to confirm the licensor. |
| A-8 | LOW | Process | RC-07, RC-15 | AGENTS.md lists docs as a branch type. The constitution lists fix, feat, and chore only. | D-12 uses the chore type. |
| A-9 | LOW | Consistency | RC-32, RC-67 | Parity T002 names design/research.md of the parity record as the decision location. This record places answers in spec.md and design/research.md. | T012 adds a link in the parity files. The parity text keeps its meaning. |
| A-10 | LOW | Source state | RC-38, RC-49 | The source default branch equals the pinned commit on 2026-11-26. | The maintainer verifies the blob SHAs again before each decision. |
| A-11 | INFO | Route | RC-25, RC-26 | The route leaf is absent. The level specs/numbered/0/0/1/2/2 holds three children before this record and four after it. | None. The Five-Item Rule holds. |
| A-12 | INFO | Converter layout | RC-73 | The converter unit test sits under the marvis resources path. The location does not affect licensing. | None in this record. The maintainer may move the file in a separate issue. |
| A-13 | INFO | Consistency | Local drafts 4636 (D-14) and 4644 (D-21) | Two related drafts allow independent authorship only, until gate G1 closes. This matches D-6 option A and D-8. | None. |
| A-14 | MEDIUM | Merge control | RC-75, RC-76 | Adding the auto-merge label starts the merge once checks pass. An unreviewed legal decision could then merge. | D-13 holds the label until review. T-MERGE applies the rule. |

## Converter provenance (input to T011)

The audit covers nine converter files on main. The current state of each file is "not reviewed". T011 replaces each state with one of three results: matches protected expression, no match found, or not compared.

| File on main | Blob SHA | Remote check | State |
| - | - | - | - |
| src/interfaces/portals/cisco_config_converter/__init__.py | 5e34b005c2ae54d3f2a766dd8ab0be7ceab40a7e | RC-70 | not reviewed |
| src/interfaces/portals/cisco_config_converter/conversion.py | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | RC-69 | not reviewed |
| src/interfaces/portals/cisco_config_converter/models.py | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | RC-68 | not reviewed |
| src/interfaces/portals/cisco_config_converter/presentation/converter.html | 270c3e40e226c026a54aef846f9b341d6a76eee9 | RC-46 | not reviewed |
| src/interfaces/portals/cisco_config_converter/presentation/converter.js | 9c7ad354600aade5b3a37bbd536ac49486edfd6e | RC-47 | not reviewed |
| src/interfaces/portals/cisco_config_converter/routes.py | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | RC-45 | not reviewed |
| tests/integration/web_portal/cisco_config_converter/__init__.py | 43a141c1406a21b339a111b3791274aa3eee784d | RC-71 | not reviewed |
| tests/integration/web_portal/cisco_config_converter/test_routes.py | a7ad7067ca7727ca5fad5508cc36de133b478d27 | RC-72 | not reviewed |
| tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py | 31a84e3795665ebea1a9346fd835fffc619a9fe7 | RC-73 | not reviewed |

## Requirement coverage

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 Options, evidence, recommendation, and owner for each legal question | T004 to T010 | TS-03 |
| FR-002 HUMAN-DECISION-REQUIRED marker, with no legal decision in this record | T004 to T010 | TS-03 |
| FR-003 Four separate reuse categories | T005 to T008 | TS-03 |
| FR-004 Distribution path options, unresolved | T010 | TS-03 |
| FR-005 Independent-authorship rule options, unresolved | T009 | TS-03 |
| FR-006 Protected source expression blocked until approval | T005, T012 | TS-05 |
| FR-007 Gate G1 separate from G2 to G5 | T012 | TS-05 |
| FR-008 No authorization of implementation, reuse, publication, or release | T-MERGE | TS-05 |
| FR-009 Source license citation with path, ref, blob SHA, and line | T001 | TS-04 |
| FR-010 MistHelper license citation with path, ref, blob SHA, and line | T002 | TS-04 |
| FR-011 Provenance state of each converter file | T002, T003, T011 | TS-05 |
| FR-012 Link from parity T002 and gate G1 | T012 | TS-05 |
| FR-013 Related issues named with their link to issue 4635 | T003 | TS-03 |
| FR-014 No legal communications, customer data, tokens, or secrets | T-PR | TS-06 |
| FR-015 STE writing and STE gate score of 80 or above | T-LOCAL-GATES, T-REMOTE-CI | TS-01 |
| FR-016 Constitution rules for route, structure, documentation, branch, and labels | T-LOCAL-GATES, T-PR | TS-02 |
| FR-017 needs-human-review kept and auto-merge blocked until review | T-PR, T-MERGE | TS-05 |
| FR-018 Each remote check listed once in research.md and once in STATUS | T001, T002, T003, T-LOCAL-GATES | TS-04 |

## Count consistency

| Item | Count | Where it appears |
| - | - | - |
| Functional requirements | 18 | spec.md FR-001 to FR-018 |
| Success criteria | 5 | spec.md SC-001 to SC-005 |
| Tasks | 16 | tasks.md: T001 to T012, T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE |
| Tests | 6 | tasks.md: TS-01 to TS-06 |
| Decisions | 15 | research.md: D-1 to D-15, and STATUS decisions |
| Human decisions | 7 | research.md: D-1 to D-7, and STATUS decisions with human_decision_required true |
| Remote checks | 77 | research.md: RC-01 to RC-77, and STATUS remote_checks |

## Unresolved items

- UR-1: The owner answers D-1 to D-7 (T004 to T010).
- UR-2: The provenance audit reports a result for each of the nine converter files (T011).
- UR-3: The published image contents are unknown (research.md, U-2).
- UR-4: The constitution and the changelog README conflict on fragments (A-6).
- UR-5: Legal review availability and timing are unknown (research.md, U-6).
