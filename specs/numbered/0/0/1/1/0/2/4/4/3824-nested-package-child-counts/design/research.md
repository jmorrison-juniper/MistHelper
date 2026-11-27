# Research: Nested Source Package Child Counts

## Decisions

Each decision names the chosen option, the alternatives, the reason, and the risk. Each decision has `human_decision_required` set to false. No decision needs licensing, legal, data destruction, credential, or product priority review.

### D-1: Progress measure is total excess

- **Chosen**: A slice lowers total excess, the sum of `max(0, count - 5)`. Each slice adds no violation.
- **Alternatives**: The issue text asks for a violation count reduction. A count rule fails for large directories. Extracting five modules from `src/operations/exporting/export` changes 48 children to 43. The violation count stays at 33.
- **Reason**: The guard already enforces total excess (C-04, C-05). The issue comment 4 proposal states the same rule.
- **Risk**: A slice can lower excess and leave a violation open. Each violation has an end state in `tasks.md`.

### D-2: Wave order starts with small groups

- **Chosen**: Wave 1 covers eight small or medium groups with no hold. Wave 2 covers nine groups with at most one hold. Wave 3 covers hot, held, or nested groups.
- **Alternatives**: Start with the largest excess first. The export folder and the refactors directory have holds H-1, H-3, H-4, and H-7.
- **Reason**: Wave 1 removes eight violations and 23 excess with no hold.
- **Risk**: Wave 3 starts late. Its holds clear only when other pull requests merge.

### D-3: One slice runs at a time

- **Chosen**: Each slice merges before the next slice starts.
- **Alternatives**: Parallel slices with rebases. Every slice edits the same baseline file, the same expected totals, and the same symbol map (H-2).
- **Reason**: Parallel edits conflict on the same lines. A rebase repeats the measure after each merge.
- **Risk**: Lower throughput. Each slice stays small to limit the cost.

### D-4: No compatibility path

- **Chosen**: Each slice removes the old module paths. Each slice updates every consumer in the same pull request.
- **Alternatives**: Keep re-export modules at the old paths for one release.
- **Reason**: Principle II of the constitution and the AGENTS.md rules prohibit shims and fallback paths.
- **Risk**: A missed consumer fails at import time. The `git grep` task and the import-path tests catch that failure.

### D-5: Ownership split for Juniper RMA and the export folder

- **Chosen**: The two Juniper RMA violations stay under issue 4168, as the baseline records. The export folder stays under issue 3824, with hold H-7.
- **Alternatives**: Move Juniper RMA to issue 3824. Move the export folder to issue 4168.
- **Reason**: The baseline names issue 4168 for Juniper RMA (C-82 and C-83). The baseline names issue 3824 for export (C-81). The title of issue 4168 names the export folder (C-48).
- **Risk**: The export folder has two owners until issue 4168 confirms the split.

### D-6: Wave 1 excludes hot, reserved, and held paths

- **Chosen**: Wave 1 never moves `MistHelper.py`, `operation_registry.py`, `endpoint_primary_key_strategies.py`, `zscaler_catalogue.py`, `initialize_mist_session.py`, or `data_exporter.py`.
- **Alternatives**: Move `operation_registry.py` in wave 1. Repair the refactors directory first.
- **Reason**: Hot-file rules (C-17 to C-19), reservations (C-20), and open pull requests (C-21, C-22) forbid those moves.
- **Risk**: Wave 1 cannot clear the refactors or utils directories.

### D-7: Legacy records stay unchanged

- **Chosen**: This record uses a new route folder, `3824-nested-package-child-counts`. The two legacy records keep their current content. Their claims are checked in the legacy table below.
- **Alternatives**: Reuse `3824-audit-renderer-structure`. Overwrite it.
- **Reason**: The audit record covers two merged slices, and it names stale totals and a stale Python version. Reuse hides that history. Overwrite destroys the evidence.
- **Risk**: Two records share one route folder. The legacy table names each record and its status.

### D-8: Repair the nested gate row in the first slice

- **Chosen**: Task T004 adds the ratchet test to the local command of the nested source package row.
- **Alternatives**: Leave the row unchanged.
- **Reason**: The local gate table must predict the CI result. The row names a test that checks guidance text, not the ratchet (C-12, C-13).
- **Risk**: Low. The change is one line in documentation.

### D-9: Module groups for waves 2 and 3 are set in each slice

- **Chosen**: Each slice writes its module groups in its change notes and in its pull request description. The slice checks each group against the rule that each package holds five or fewer counted children.
- **Alternatives**: Write every group now. About 370 module names need a design before wave 1 produces evidence.
- **Reason**: Wave 1 measures the real effect of the moves. Later groups depend on the names that wave 1 leaves in place.
- **Risk**: A later group can change the end state in `tasks.md`. Each slice updates `tasks.md` when it starts.

### D-10: Labels and size

- **Chosen**: Add the label `stage:speckit-artifacts-emitted`. Keep the label `in-progress`. Set the size to XL.
- **Alternatives**: Add the label `docs`. Set the size to L.
- **Reason**: `stage:speckit-artifacts-emitted` exists in the repository label list. The label `docs` describes content, not the stage. The record covers 33 violations and 30 slices, so the size is XL.
- **Risk**: None known.

### D-11: Slice pull requests name the issue with `Refs`

- **Chosen**: Each slice pull request uses `Refs #3824` in its body. The orchestrator closes issue 3824 by hand after issue 4168 closes its violations.
- **Alternatives**: Use `Closes #3824`, as AGENTS.md states for single-issue changes.
- **Reason**: Issue comment 6 records that the close-linked-issues workflow closed issue 3824 after pull request 4552 merged.
- **Risk**: The closure is manual. The orchestrator must remember it.

## Remote Verification Table

Each row is one check. The table lists 83 checks. Check IDs match `remote_checks` in `META_DIR\3824-STATUS.json`. A blob or tree SHA marks the state of the path on remote main. The line is 0 when the claim names a whole file or a whole directory.

| # | Claim | Path | Ref | Blob or tree SHA | Result | Line |
| - | - | - | - | - | - | - |
| 01 | Remote main ref equals local HEAD | refs/heads/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| 02 | Recursive tree lists 11404 entries, not truncated | git/trees/main?recursive=1 | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| 03 | Guard file exists | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 1 |
| 04 | Guard expects 33 violations and 236 total excess | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 177 |
| 05 | Guard defines the ratchet function validate_ratchet | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 129 |
| 06 | Guard prints the examined directory count | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 157 |
| 07 | Baseline file exists | tests/guardrails/nested_package_baseline.json | main | 0d6c5ca933d83a4721c0bcc7220f69905fcf81f5 | present | 1 |
| 08 | Baseline holds 33 entries that match the measured counts | tests/guardrails/nested_package_baseline.json | main | 0d6c5ca933d83a4721c0bcc7220f69905fcf81f5 | present | 0 |
| 09 | Measured totals are 190 directories, 33 violations, and 236 excess | src | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| 10 | Constitution Principle I heading | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| 11 | Constitution requires Python 3.15 or newer | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 278 |
| 12 | Nested source package gate row names the ratchet test | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | partial | 259 |
| 13 | Move-module guard checks the nested ratchet guidance text | tests/guardrails/test_move_module_guidance.py | main | ae163b792b330285dba7a8c32cc957a78c3838d4 | present | 17 |
| 14 | Domain guard defines the five-child test | tests/guardrails/test_src_domain_structure.py | main | 8c1567e3b78c57a9a7a40578106d4a34659a977a | present | 99 |
| 15 | CI defines MYPY_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| 16 | Symbol map names the audit renderer and utility text paths | tests/guardrails/test_src_public_symbol_preservation.py | main | 08f978e755abdf643e7a6d826811401f710883f8 | present | 82 |
| 17 | Hot file MistHelper.py exists | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 0 |
| 18 | Hot file operation_registry.py exists | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 0 |
| 19 | Hot file endpoint_primary_key_strategies.py exists | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 0 |
| 20 | Reserved file zscaler_catalogue.py exists | src/foundation/support/utils/zscaler_catalogue.py | main | 4ca1d97e1e45ab59711f97988938e9c2162be0d6 | present | 0 |
| 21 | Open pull request 4208 changes initialize_mist_session.py | src/foundation/support/refactors/initialize_mist_session.py | pull/4208 | 843be63bc837 | present | 0 |
| 22 | Open pull request 4813 changes data_exporter.py | src/operations/exporting/export/data_exporter.py | pull/4813 | c00a85f8b3fe | present | 0 |
| 23 | Pull request 4552 merged at 0bd6d6d22ffa | pull/4552 | main | 0bd6d6d22ffac4d5e4322d2fb34b5416dd4ba085 | present | 0 |
| 24 | Pull request 4557 merged at e2e7413bba32 | pull/4557 | main | e2e7413bba32ce0f733e18dae903f031ff8102f6 | present | 0 |
| 25 | Audit renderer module exists at the rendering path | src/mist/access/audit/rendering/renderer.py | main | 1443aefcfd8098e3fac28fce1cfd425bef25782c | present | 0 |
| 26 | Old audit renderer path is absent | src/mist/access/audit/renderer.py | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | absent | 0 |
| 27 | Utility text module exists at the metadata path | src/mist/realtime/websocket_streams/catalog/utilities/metadata/utility_text.py | main | 535c724843b72230642f48158118ff727a6de9bf | present | 0 |
| 28 | Old utility text path is absent | src/mist/realtime/websocket_streams/catalog/utility_text.py | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | absent | 0 |
| 29 | Audit test is absent at the legacy path tests/unit/audit | tests/unit/audit/test_renderer_structure_issue_3824.py | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | absent | 0 |
| 30 | Audit test exists at the moved path | tests/unit/marvis/mist/access/audit/test_renderer_structure_issue_3824.py | main | 31bac05a99d745c4ad9a4a341d5e04ddf86a8812 | present | 0 |
| 31 | Audit changelog fragment exists | changelog.d/issue-3824-audit-renderer-structure.md | main | d8f9e39f12be2c9797eeb5afe6bea6f1b12a9f41 | present | 0 |
| 32 | WebSocket feature structure test exists | tests/unit/websocket_streams/live/transport/runtime/test_ws_feature_structure.py | main | d2a3569288f6443e3d06b19819f0daa0eaa4478b | present | 0 |
| 33 | Legacy audit plan states Python 3.13 | specs/numbered/0/0/1/1/0/2/4/4/3824-audit-renderer-structure/plan.md | main | 8033235fd1124c4d6bb3ff64aa442705a43c1cd6 | stale | 0 |
| 34 | Legacy audit spec states 34 violations and 237 excess | specs/numbered/0/0/1/1/0/2/4/4/3824-audit-renderer-structure/spec.md | main | 13ae2ddebe7ae86499d32f399600f861a852d17a | stale | 0 |
| 35 | Legacy DB writers plan states Python 3.13 | specs/3824-db-writers-package/plan.md | main | 22d934e19a0ac736e64c4d01279204b196cb60f4 | stale | 0 |
| 36 | Process baseline grandfathers the DB writers record | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 319 |
| 37 | DB package holds five counted children | src/foundation/persistence/db | main | 9b43737e18dedb66b53b2b2cf95a7c0b1f4b7730 | present | 0 |
| 38 | Writers package holds the ArangoDB writer | src/foundation/persistence/db/writers/arango_writer.py | main | 3db01f97a21de021213bb4d8a8f7300b530cc82a | present | 0 |
| 39 | Writers package holds the Redis writer | src/foundation/persistence/db/writers/redis_writer.py | main | 7b66735dab8091d32a98cd3d2040db8745c55229 | present | 0 |
| 40 | DB writers changelog fragment exists | changelog.d/issue-3824-db-writers-package.md | main | 3ba529cc5fa4c0e2e8e9d909d3c2a8f219018052 | present | 0 |
| 41 | DB writers base commit exists | commits/2a00e32745472f70764206b060dacc1c4dd13992 | main | 2a00e32745472f70764206b060dacc1c4dd13992 | present | 0 |
| 42 | Resources org folder holds four counted children | src/mist/resources/org | main | 094a9ac97e3e5ef51617a87ebc07a7bafb55fdd8 | present | 0 |
| 43 | Access folder holds three counted children | src/mist/access | main | 7e9b2c8135cead4c013a128c04d29a0bc2224093 | present | 0 |
| 44 | Destination is free for the access response_integrity module | src/mist/access/response_integrity.py | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | absent | 0 |
| 45 | Destination is free for the networking routing_support package | src/mist/networking/network/routing_support | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | absent | 0 |
| 46 | Destination is free for the websocket command_context package | src/mist/realtime/websocket/command_context | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | absent | 0 |
| 47 | Destination is free for the marvis alarm_actions package | src/mist/intelligence/marvis/actions/alarm_actions | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | absent | 0 |
| 48 | Issue 4168 is open and its title names the export folder | issues/4168 | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| 49 | Issue 4009 is open for the metrics gateway core modules | issues/4009 | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| 50 | Issue 1794 is open. Issue 3824 comment 10 reserves its file | issues/1794 | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| 51 | Violating directory with 15 counted children | src/foundation/models/dataclasses | main | 9c2b605abff021278f4bb13af24fd965784c58fe | present | 0 |
| 52 | Violating directory with 33 counted children | src/foundation/support/refactors | main | f84f2ce1bc5c0085873725fac9a4fe07df261d65 | present | 0 |
| 53 | Violating directory with 9 counted children | src/foundation/support/refactors/serial_cc | main | eaa97b65a848f23d4357f3eae31b641bc3c179b2 | present | 0 |
| 54 | Violating directory with 18 counted children | src/foundation/support/utils | main | e04ee3936345e05494bc53dc0c29bfd28a5145f1 | present | 0 |
| 55 | Violating directory with 8 counted children | src/interfaces/monitoring/metrics_gateway | main | 00b737f77c5d708d1ddb9288f3d7306baa04c8d2 | present | 0 |
| 56 | Violating directory with 11 counted children | src/interfaces/portals/upgrade_portal | main | 9f69e75110e889343b9a81f62c774f60fd1ebe33 | present | 0 |
| 57 | Violating directory with 7 counted children | src/interfaces/portals/upgrade_portal/app | main | 5050b006f776a8b4031cbc64293c4c52ddc646fa | present | 0 |
| 58 | Violating directory with 12 counted children | src/interfaces/portals/upgrade_portal/app/routes | main | 6c14ca92440a688b6e56687c4e8648b7e439b886 | present | 0 |
| 59 | Violating directory with 9 counted children | src/interfaces/portals/upgrade_portal/capture | main | 2767a3cd5c8cad30939290d2c04086f4f8c4e791 | present | 0 |
| 60 | Violating directory with 7 counted children | src/interfaces/portals/upgrade_portal/compare | main | d669f54e1ba4d49f4621b70d8f85c28ddf0628ff | present | 0 |
| 61 | Violating directory with 9 counted children | src/interfaces/portals/upgrade_portal/runtime | main | 6603e5cd07604509e51b07689609de824a4c2d91 | present | 0 |
| 62 | Violating directory with 21 counted children | src/interfaces/portals/upgrade_portal/upgrade | main | 4523cb1c518d4a6c85b719a956478a40384c076e | present | 0 |
| 63 | Violating directory with 6 counted children | src/interfaces/portals/upgrade_portal/upgrade/org_cascade | main | f4283272eaca0e8ba2c1910d6ce8390fd85dbd32 | present | 0 |
| 64 | Violating directory with 19 counted children | src/interfaces/visualization/maps | main | 1907b95a87c4da18d10084b23cfff9da49da4f8a | present | 0 |
| 65 | Violating directory with 8 counted children | src/interfaces/visualization/maps/launcher | main | 16bb6f33eadc253a3a5e48afdd40469a9bc71ce0 | present | 0 |
| 66 | Violating directory with 8 counted children | src/interfaces/visualization/ui | main | 44c636bfe1f4ec2300403e7e6ad92b86c5066acc | present | 0 |
| 67 | Violating directory with 7 counted children | src/mist/access/api | main | 4ec10e478f3b370be159b98442a1a72ad88f3b90 | present | 0 |
| 68 | Violating directory with 6 counted children | src/mist/intelligence/marvis/actions | main | ff3a77de4c303606a12d231897e598df812ea6af | present | 0 |
| 69 | Violating directory with 18 counted children | src/mist/intelligence/reports | main | 9d38aeec794436ee76012c6f5f741942cb3fc180 | present | 0 |
| 70 | Violating directory with 7 counted children | src/mist/intelligence/troubleshooting/rf_diagnostics | main | 40b00ca02e3e69270c8e1dff22b89366cdb98252 | present | 0 |
| 71 | Violating directory with 7 counted children | src/mist/networking/network | main | 3258506a121410a671c9585a537988be603bd1c5 | present | 0 |
| 72 | Violating directory with 7 counted children | src/mist/realtime/websocket | main | d2f8c321bf10b59a22dbac3068d86af9c1967607 | present | 0 |
| 73 | Violating directory with 14 counted children | src/mist/resources/device | main | 6a52b8637753458216ef6465f81dd8a60a755296 | present | 0 |
| 74 | Violating directory with 16 counted children | src/mist/resources/gateway | main | ceca608ac0b01f226e98d07e524547b90fc784a4 | present | 0 |
| 75 | Violating directory with 7 counted children | src/mist/resources/inventory | main | 800a2d492bebe33d095bf92891747c51de880f8a | present | 0 |
| 76 | Violating directory with 13 counted children | src/mist/resources/site/address_audit | main | 8cda7a2bde7a358b5228f0b68babb300ad5564df | present | 0 |
| 77 | Violating directory with 12 counted children | src/operations/execution/capture | main | 5a7ce7c37b0465d7e416d86b9bb3e68c2404b824 | present | 0 |
| 78 | Violating directory with 11 counted children | src/operations/execution/firmware | main | 414a7e58ca8202cb4d000c6900685bc484fb6810 | present | 0 |
| 79 | Violating directory with 8 counted children | src/operations/execution/ssh | main | 2cd0b2abaef31f41a151c6eb76008b227139517e | present | 0 |
| 80 | Violating directory with 7 counted children | src/operations/execution/ssid_consolidation | main | a80e0f5e420bcf9cc8438ab522f497aff882da07 | present | 0 |
| 81 | Violating directory with 48 counted children | src/operations/exporting/export | main | a0956c911946e08c84fee7a003099c7dc5f60a1e | present | 0 |
| 82 | Violating directory with 6 counted children, owned by issue 4168 | src/operations/exporting/juniper_rma/model | main | 36e849ddcfb4355c629dd7d27f4f964a5dfae334 | present | 0 |
| 83 | Violating directory with 7 counted children, owned by issue 4168 | src/operations/exporting/juniper_rma/workflows | main | f16f43c7aec6bd547af3ac984adf88f7a2ad1060 | present | 0 |

Note on rows 21 and 22: the blob column holds the short head SHA of the open pull request. The check reads the pull request file list, not the tree.

## Legacy Claim Review

The legacy records are the audit renderer record `specs\numbered\0\0\1\1\0\2\4\4\3824-audit-renderer-structure` and the DB writers record `specs\3824-db-writers-package`. Each claim below cites its remote check.

| ID | Legacy claim | Status | Check |
| - | - | - | - |
| L-01 | Audit renderer modules sit at the rendering path | verified | 25 |
| L-02 | Old audit renderer path is removed | verified | 26 |
| L-03 | Utility text sits at the metadata path | verified | 27 |
| L-04 | Old utility text path is removed | verified | 28 |
| L-05 | Audit test files sit at `tests/unit/audit/` | absent | 29 |
| L-06 | Audit changelog fragment exists | verified | 31 |
| L-07 | WebSocket feature structure test exists | verified | 32 |
| L-08 | Audit plan states Python 3.13 | stale | 33 |
| L-09 | Audit spec states 34 violations and 237 excess | stale | 34 |
| L-10 | DB writers plan states Python 3.13 | stale | 35 |
| L-11 | Writers package holds both writer modules | verified | 38, 39 |
| L-12 | Process baseline grandfathers the DB writers record | verified | 36 |
| L-13 | DB writers base commit exists | verified | 41 |
| L-14 | Pull requests 4552 and 4557 merged | verified | 23, 24 |

Totals for the legacy claims: 10 verified, 3 stale, and 1 absent. These counts appear in `existing_record` of the STATUS file.

## Sources

- GitHub issue 3824: body and 13 comments, read with `gh issue view`. Comment 1 lists the earlier inventory. Comments 2 and 3 correct the commit. Comment 4 proposes the total excess rule. Comment 6 records the automatic closure.
- Pull requests: the ten pull requests returned by `gh pr list --search 3824`, plus pull requests 4607, 4658, 4208, and 4813. The file lists came from `gh pr view`.
- Remote tree and files: `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1` and `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main`. Base64 content was decoded in PowerShell.
- Local files at HEAD `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, which equals remote main (C-01). Read in full: `AGENTS.md`, `.github\copilot-instructions.md`, `.specify\memory\constitution.md`, `.specify\templates\spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`. Read in full: the two legacy records. Searched by pattern only: the reference record `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv` (headings), and `documentation\quality-gates.md`, `architecture.md`, `development-setup.md`, `container-deployment.md`, and `operator-guide.md`.
- Gate commands: the Local gates table and the Move a module table in `.github\copilot-instructions.md`.
- Skills: none loaded. No Podman, Juniper, or Python refactor skill applies to this record.
- Mist API documentation and the mistapi SDK: not read. No slice changes a Mist call (U-9).

## Unverified

- **U-1**: The Move a module table names `source_dependency_resolver.py`. This check did not read that file on remote main.
- **U-2**: The import lines in `junk/diag_rbo.py`, a root file that pull request 4552 added. This check did not read the file body.
- **U-3**: Results of Ruff, Black, mypy, pytest, bandit, radon, pylint, vulture, pydocstyle, interrogate, ste-linter, and the test-quality analyzer. Rule 2 forbids running them, so no gate result is claimed.
- **U-4**: The `symbol-diff` command and the `misthelper-devtools` package named in `requirements-dev.txt`. This check did not read the package.
- **U-5**: CI results of open pull requests 4208 and 4813. This check read the file lists only.
- **U-6**: Line numbers in the legacy plans and specs. Their claims cite the whole file, so the line is 0.
- **U-7**: Coverage and complexity values. No measurement ran.
- **U-8**: The reason that the legacy audit tests moved from `tests/unit/audit/`. Pull requests 4358 and 4650 reorganized test paths. Their file lists were not read.
- **U-9**: Behavior of the Mist API and of the mistapi SDK. This record changes no Mist call, so the check did not read those sources.
