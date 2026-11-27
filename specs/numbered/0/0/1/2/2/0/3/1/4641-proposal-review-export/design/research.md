# Research: Versioned Proposal Review and Safe Export

**Date**: 2026-11-26
**Feature**: [Versioned Proposal Review and Safe Export](../spec.md)

## R1. Issue Facts

Issue #4641 is open. Its title is "[Spec]: Add versioned proposal review and safe export". It carries the labels `feature` and `web-portal`. It has no comments. The author is `jmorrison-juniper`. The issue was created and last updated on 2026-11-07.

- Problem: Engineers need the exact proposal before export. A source or target change must invalidate a prior review.
- Scope: Complete tasks T017 and T018 of the full-parity task map. Add structured review and versioned offline operations.
- Constraints: Keep preview available without Mist credentials. Use the existing exporter only where its contract applies. Do not introduce cloud writes.
- Security: Use synthetic input and mocked responses. Exports omit credentials and secret values. Do not log source configuration.
- Test plan: Test export identity, omission reporting, unavailable-state handling, changed-scope invalidation, version integrity, and secret absence.
- Migration: Preserve the existing DNS preview, review, and export clients. Do not register shared portal routes.
- Acceptance: Show target object changes, omissions, unresolved mappings, and verification state. Bind export to the current proposal. Invalidate review after each relevant change. Prove that exports hold no credentials. Keep the work offline and non-writing.
- Prerequisites named in the issue: #4637 structured input, #4638 hardware selection, #4640 network conversion, and #4639 management and security review. Full task map: PR #4596.

Source: `https://github.com/jmorrison-juniper/MistHelper/issues/4641`

## R2. Linked and Referenced PRs

A PR search for `4641` returned no pull request. The referenced PRs below carry the program history.

| PR | State | Facts | Relevance |
| - | - | - | - |
| #4596 | MERGED on 2026-11-13 | Ten files under the full-parity record. | Task map that the issue names. |
| #4208 | OPEN | 82 files. It changes `web_portal/app.py` (+64, -0) and `web_portal/templates/base.html` (+7, -0). | Owns the shared portal files. This change edits neither file. |

Open PR scan on 2026-11-26: seven open PRs were scanned. Two touch planned paths. PR #4208 touches the shared portal files and `changelog.d/pr-4208.md`. PR #4813 touches `changelog.d/issue-4776-csv-carriage-returns.md`. The planned fragment name is unique, so the two changelog entries do not collide.

Sources: `https://github.com/jmorrison-juniper/MistHelper/pull/4596`, `https://github.com/jmorrison-juniper/MistHelper/pull/4208`

## R3. Existing Record

No folder whose name starts with `4641-` exists under `specs/` on the local checkout. No record exists under the route `specs/numbered/0/0/1/2/2/0/3/1` on `main` (row 72). The draft folder for issue #4641 in `spec-drafts` was empty before this drafting pass. The steps 3 and 4 of the brief do not apply, because no legacy record exists.

Route check: 4641 equals `122031` in base 5. Padded to eight levels, the route is `0/0/1/2/2/0/3/1`. Issue #4224 uses the same rule with `0/0/1/1/3/3/4/4`, and issue #4920 uses `0/0/1/2/4/1/4/0`.

## R4. Remote Verification Table

All rows read GitHub `main` through `gh api` on 2026-11-26, unless the row names a local path. The commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` on `main` equals the local HEAD. Seven local files were hashed with the git blob method. Each hash equals its remote blob SHA. A line of `0` means that the claim applies to the whole file, the directory, or the absence of a path. The table holds 78 rows, and `4641-STATUS.json` holds the same 78 entries in the same order.

| # | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| 1 | Remote `main` points at the baseline commit | `refs/heads/main` | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| 2 | The converter package root holds five direct children | `src/interfaces/portals/cisco_config_converter/` | main | not-a-blob | present | 0 |
| 3 | The converter presentation folder holds two children | `src/interfaces/portals/cisco_config_converter/presentation/` | main | not-a-blob | present | 0 |
| 4 | The converter `state/` package is absent | `src/interfaces/portals/cisco_config_converter/state/` | main | not-a-blob | absent | 0 |
| 5 | The version 1 route `/export` is registered | `src/interfaces/portals/cisco_config_converter/routes.py` | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 64 |
| 6 | The converter request class limits the converter path prefix | `src/interfaces/portals/cisco_config_converter/routes.py` | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 28 |
| 7 | `verify_host` requires `ConverterRequest` and CSRF protection | `src/interfaces/portals/cisco_config_converter/routes.py` | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 103 |
| 8 | The action binds review through `ReviewState.verify` | `src/interfaces/portals/cisco_config_converter/routes.py` | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 137 |
| 9 | Export sends the attachment name `cisco-proposal.json` | `src/interfaces/portals/cisco_config_converter/routes.py` | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 148 |
| 10 | `routes.py` holds three top-level classes | `src/interfaces/portals/cisco_config_converter/routes.py` | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 17 |
| 11 | The converter sources hold no mistapi import | `src/interfaces/portals/cisco_config_converter/` | main | not-a-blob | absent | 0 |
| 12 | `routes.py` holds no inline `#` comment | `src/interfaces/portals/cisco_config_converter/routes.py` | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | absent | 0 |
| 13 | `models.py` holds five top-level classes at lines 13, 21, 29, 38, and 84 | `src/interfaces/portals/cisco_config_converter/models.py` | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 13 |
| 14 | `ReviewState` holds the session digest methods | `src/interfaces/portals/cisco_config_converter/models.py` | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 84 |
| 15 | The digest uses sorted, compact canonical JSON and rejects NaN | `src/interfaces/portals/cisco_config_converter/models.py` | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 90 |
| 16 | The source kind accepts `standalone` and `spoke` only | `src/interfaces/portals/cisco_config_converter/models.py` | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 51 |
| 17 | `conversion.py` holds one top-level class | `src/interfaces/portals/cisco_config_converter/conversion.py` | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 11 |
| 18 | The known gap names the global IPv4 DNS subset | `src/interfaces/portals/cisco_config_converter/conversion.py` | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 26 |
| 19 | The browser script sends `X-CSRFToken` on JSON POST | `src/interfaces/portals/cisco_config_converter/presentation/converter.js` | main | 9c7ad354600aade5b3a37bbd536ac49486edfd6e | present | 56 |
| 20 | The export button carries the test ID `cisco-export` | `src/interfaces/portals/cisco_config_converter/presentation/converter.html` | main | 270c3e40e226c026a54aef846f9b341d6a76eee9 | present | 24 |
| 21 | The isolated host fixture mounts only the feature blueprint | `tests/integration/web_portal/cisco_config_converter/test_routes.py` | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 19 |
| 22 | The route test rejects review after an edit | `tests/integration/web_portal/cisco_config_converter/test_routes.py` | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 80 |
| 23 | The converter integration folder holds two children | `tests/integration/web_portal/cisco_config_converter/` | main | not-a-blob | present | 0 |
| 24 | The browser class `TestCiscoOfflinePreview` exists | `tests/e2e/web_portal/test_portal_smoke.py` | main | 56e87d332700603c9925aa061c4594f864e7ac49 | present | 23 |
| 25 | The `tests/e2e/web_portal/` folder holds 32 direct children against a limit of five | `tests/e2e/web_portal/` | main | not-a-blob | present | 0 |
| 26 | `web_portal/app.py` references no converter | `web_portal/app.py` | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | absent | 0 |
| 27 | The navigation template holds no converter entry | `web_portal/templates/base.html` | main | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | absent | 0 |
| 28 | The navigation template exposes the `csrf-token` meta value | `web_portal/templates/base.html` | main | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | present | 6 |
| 29 | The portal service enables `CSRFProtect` | `web_portal/services/config.py` | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 301 |
| 30 | The portal secret falls back to a random `uuid4` value | `web_portal/services/config.py` | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 113 |
| 31 | `compose.yml` holds no converter service | `compose.yml` | main | b3944fc9f994ca149974072b1a9c8f13797d7924 | absent | 0 |
| 32 | `README.md` names no converter | `README.md` | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | absent | 0 |
| 33 | The operator guide holds no converter section | `documentation/operator-guide.md` | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | absent | 0 |
| 34 | The nested package guard sets `MAX_CHILDREN` to 5 | `tests/guardrails/test_nested_package_structure.py` | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 17 |
| 35 | The changelog fragment policy guard exists | `tests/guardrails/test_changelog_fragment_policy.py` | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| 36 | `DataExporter` is the multi-backend export facade | `src/operations/exporting/export/data_exporter.py` | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 81 |
| 37 | `DataExporter.write_with_format_selection` is the public entry point | `src/operations/exporting/export/data_exporter.py` | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 153 |
| 38 | The constitution limits each hierarchy level to five children | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 40 |
| 39 | The constitution scopes the output backend rule to API export and data collection | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 312 |
| 40 | The constitution requires Python 3.15 or newer | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 278 |
| 41 | The repository rules limit each structural directory to five children | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 167 |
| 42 | The local gates table starts at its header row | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 55 |
| 43 | The STE gate lists named Markdown files, not spec records | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| 44 | Changelog fragments are named for a pull request or an issue | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| 45 | The CI type-check scope is `MYPY_PATHS` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| 46 | The CI source scope is `SRC_PATH` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 78 |
| 47 | The CI dead-code scope is `VULTURE_PATHS` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| 48 | The CI docstring scope is `PYDOCSTYLE_PATHS` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| 49 | The CI docstring coverage scope is `INTERROGATE_PATHS` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| 50 | The OpenAPI file defines the gateway templates path | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9727 |
| 51 | The OpenAPI operation is `createOrgGatewayTemplate` | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9764 |
| 52 | The OpenAPI request body references `gateway_template` | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9887 |
| 53 | The OpenAPI `gateway_template` schema starts at line 80654 | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80654 |
| 54 | The `gateway_template` schema holds a `dns_servers` property | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80678 |
| 55 | The `dns_servers` component holds an array of strings | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 78042 |
| 56 | The `gateway_template` schema requires `name` | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80783 |
| 57 | The `gateway_template_type` enum holds `spoke` and `standalone` | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80788 |
| 58 | The installed mistapi SDK defines `createOrgGatewayTemplate` | `.venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py` | local-venv | 6b82963804738f1a6a85af80dab4b3c7d9b67735 | present | 58 |
| 59 | The installed mistapi version is 0.64.1 | `.venv\Lib\site-packages\mistapi-0.64.1.dist-info` | local-venv | not-a-blob | present | 0 |
| 60 | Full-parity T017 names proposal and export tests | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md` | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 63 |
| 61 | Full-parity T018 names structured review and versioned operations | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md` | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 64 |
| 62 | Full-parity dependency: T017 depends on T006 | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md` | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 141 |
| 63 | Full-parity dependency: T018 depends on T010, T014, T016, and T017 | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md` | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 142 |
| 64 | Full-parity FR-005 uses role for Branch, Hub, or Standalone | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md` | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 111 |
| 65 | Full-parity FR-009 lists proposal contents | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md` | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 115 |
| 66 | The full-parity portal contract requires an explicit version contract | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/portal.md` | main | 56e3b23b9ac04e4a733c62970811ca0ead4df83c | present | 15 |
| 67 | Full-parity comparison row C18 covers proposal inspection and export | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md` | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 102 |
| 68 | The parent record reuses T017 for export tests | `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/tasks.md` | main | fcdff941b5dfd214ae882be77d26c17ec903e8d5 | present | 65 |
| 69 | The parent record blocks T015 on shared portal ownership | `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/tasks.md` | main | fcdff941b5dfd214ae882be77d26c17ec903e8d5 | present | 51 |
| 70 | The parent plan states Python 3.13 | `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/plan.md` | main | 9c3fdacc929850e1ed923b248f1dc6520aa01fdd | present | 15 |
| 71 | The unit test path named by the parent record is absent | `tests/unit/gateway/overrides/test_cisco_config_converter.py` | main | not-a-blob | absent | 0 |
| 72 | Route `0/0/1/2/2/0/3/1` holds no record | `specs/numbered/0/0/1/2/2/0/3/1/` | main | not-a-blob | absent | 0 |
| 73 | Route `0/0/1/2/2/0/2/1` holds no record, because issue #4636 is not merged | `specs/numbered/0/0/1/2/2/0/2/1/` | main | not-a-blob | absent | 0 |
| 74 | The known gap says unsupported values are omitted to protect credentials | `src/interfaces/portals/cisco_config_converter/conversion.py` | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 28 |
| 75 | The unsupported label replaces the value with `[values omitted]` | `src/interfaces/portals/cisco_config_converter/conversion.py` | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 82 |
| 76 | The upload read stops one byte beyond the 16 MiB limit | `src/interfaces/portals/cisco_config_converter/routes.py` | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 124 |
| 77 | The constitution requires a README update for each behavior change | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 400 |
| 78 | Full-parity T006 sets a 15-minute review lifetime until the owner approves another value | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md` | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 36 |

Counts: 78 rows in total. Rows 58 and 59 use the local `.venv` path. The other 76 rows use GitHub `main`.

## R5. Converter Source Facts (Version 1 Contract)

- The version 1 page, script, and routes exist on `main` (rows 5 to 9, 19, and 20).
- The version 1 response holds `gateway_template`, `unsupported_items`, and `known_gaps` (`models.py` TypedDict classes at rows 13 and 14).
- The session stores one proposal digest and one reviewed digest (rows 14 and 15). Preview clears both values before it publishes a new digest (`routes.py` row 8 and `models.py` row 14).
- Unsupported items keep a line number and a label only (rows 74 and 75). The known gaps say that values are omitted (row 74).
- The request bound is 16 MiB plus 16 KiB for the converter prefix (rows 6 and 76).
- The version 1 tests use an isolated host and no Mist credential (rows 21 and 22). The browser journey uses the same host (row 24).

## R6. Five-Item Capacity

| Directory or module | Children or names now | After this change | Limit | Rows |
| - | - | - | - | - |
| Converter root | 5 | 5 | 5 | 2 |
| Converter presentation folder | 2 | 3 | 5 | 3 |
| `state/` package | Absent on `main`. Issue #4636 creates five children. | 5 | 5 | 4 and the issue #4636 draft plan |
| Converter integration test folder | 2 | 4 after issues #4636 and #4641 | 5 | 23 |
| `proposals/` test package | Absent | 3 | 5 | New |
| `tests/e2e/web_portal/` | 32 | 32, with no new child | 5 | 25 |
| `routes.py` top-level classes | 3 | 4 | 5 | 10 |
| `conversion.py` top-level classes | 1 | 2 | 5 | 17 |
| `models.py` top-level classes | 5 | Removed by issue #4636 | 5 | 13 |
| `state/proposal.py` top-level names | Four planned by issue #4636 | 5 | 5 | Issue #4636 draft plan |

Caution: Issue #4648 plans two more direct files in the integration folder (`test_parity.py` and `test_portal_browser.py`, from its draft spec). With issues #4636 and #4641, the folder then holds six children. Analysis item A-1 records the conflict.

## R7. Mist API and SDK Facts

- The gateway templates path and its POST operation exist in the OpenAPI file (rows 50 and 51).
- The POST request body references `gateway_template` (row 52). The schema requires `name` (row 56) and has a `type` enum with `spoke` and `standalone` (row 57). It holds a `dns_servers` property (row 54) that references an array of strings (row 55).
- The installed mistapi SDK defines `createOrgGatewayTemplate(mist_session, org_id, body)` at line 58 (row 58). The installed version is 0.64.1 (row 59). The brief names the pin `mistapi>=0.64.0,<0.65`, and 0.64.1 lies inside that range.
- This feature calls none of these methods. The rows support the object change shape only (FR-002).
- The blob SHA in row 58 is a git-style hash of a local file outside the repository. It was computed with the git blob method, so it is not a repository blob.

## R8. Persistence, Session, and Secret Facts

- The browser session stores digests only (rows 14 and 15). No source text enters the session.
- The portal enables `CSRFProtect` in its service configuration (row 29). The converter registration requires it (row 7).
- The portal secret falls back to a random `uuid4` value when `PORTAL_SECRET_KEY` is unset (row 30). A restart then clears every review, and the operator must review again (Caution in the spec).
- The program default for a review is a 15-minute lifetime (row 78). Issue #4636 draft decision D-6 applies the same lifetime to stored records. Version 2 applies it to session values (decision D-20).
- Issue #4636 draft decision D-15 marks the fallback as a human decision. This record keeps that owner decision open (decision D-15 below).

## R9. Exporter Facts

- `DataExporter` is the multi-backend export facade (row 36). Its public entry point is `write_with_format_selection` (row 37).
- The constitution scopes the output backend rule to API export and data collection (row 39). The version 2 proposal holds no Mist API response data.
- The issue asks to use the existing exporter only where its contract applies. Decision D-5 explains the choice.

## R10. Test Layout Facts

- The isolated host fixture mounts only the feature blueprint (row 21). The review invalidation test sits at line 80 (row 22).
- The browser class `TestCiscoOfflinePreview` sits at line 23 of the smoke file (row 24). Its existing journey uses the isolated host.
- The converter integration folder holds two children (row 23). The e2e web portal folder holds 32 children (row 25). The version 2 tests use a nested `proposals/` package, and the browser method goes in the existing class.
- The nested package guard limits each directory to five children (row 34).
- The changelog fragment policy guard exists (row 35).

## R11. Gates and Tooling Facts

- The local gates table starts at line 55 (row 42). Each command in `tasks.md` comes from that table.
- The CI scope values for mypy, source, dead code, docstrings, and docstring coverage are in rows 45 to 49.
- The STE gate lists named files only (row 43). This record is not one of them.
- The changelog fragment naming rule is in lines 451 and 452 (row 44).
- Pylint, bandit, radon, and test-quality commands come from the local gates table (row 42). Their CI copies are in `ci.yml` rows 45 to 49.

## R12. Program and Authorization Facts

- Full-parity T017 and T018 define the proposal and export scope (rows 60 and 61). Their dependency rows name T006 for T017 and T010, T014, T016, and T017 for T018 (rows 62 and 63).
- The full-parity spec uses the word role for Branch, Hub, or Standalone (row 64). This record uses template type for the DNS values standalone and spoke, and it reserves hardware role for issue #4638 (decision D-10).
- Issue #4224 uses T017 for export tests in its own task list (row 68). Its T015 waits for shared portal ownership (row 69).
- The coordinator decision on issue #4633 authorizes offline work for the converter (GitHub comment, 2026-11-08T23:37:56Z). Issue #4633 and issue #4632 are closed. The other program issues are open.
- The issue #4636 coordinator comment of 2026-11-09T16:55:13Z states that offline decisions do not authorize a cloud write or release.
- Draft records in `spec-drafts` are local files, not remote evidence. This record reads them for context only. The draft records are issue #4636 (spec, plan, research, state records contract, and STATUS), issue #4648 (spec), and issue #4649 (spec).

## R13. Decisions

Each decision names the alternatives, the choice, the reason, and the risk. The `human_decision_required` flag in `status.json` marks only D-15.

### D-1. Add version 2 routes beside the version 1 routes

- Alternatives: (a) Change the version 1 routes in place. (b) Add a `version` query parameter to the version 1 routes.
- Chosen: Three routes under `/cisco-config-converter/v2/`: preview, review, and export.
- Reason: The full-parity portal contract requires an explicit version contract (row 66). Version 1 tests and the browser journey stay valid (rows 21 and 24).
- Risk: Two response shapes exist. Mitigation: The routes share one upload validator and one review state.
- Human decision: No.

### D-2. Keep review state as digests in the signed browser session

- Alternatives: (a) The private file store from issue #4636. (b) Browser storage. (c) Server memory.
- Chosen: Digests in the signed session, as version 1 already uses (rows 14 and 15).
- Reason: FR-014 forbids a file write. Issue #4636 defines the store for later approvals, so this record does not need it for review.
- Risk: A restart or a second process clears review, and the route fails closed. Mitigation: The Caution in the spec and decision D-15.
- Human decision: No.

### D-3. Bind the proposal digest to the full object, including the scope digest

- Alternatives: (a) A digest of the scope only. (b) A keyed HMAC of the proposal.
- Chosen: `ReviewState.digest` over the full object. The object holds `scope_digest`, which is `ReviewState.digest` over the scope (row 15).
- Reason: Any field change changes the proposal digest. Issue #4636 draft decision D-4 also uses a legacy review digest and a scope digest.
- Risk: A serialization change breaks review. Mitigation: The canonical JSON rule (row 15) and test 10.
- Human decision: No.

### D-4. Omit a source content digest from responses

- Alternatives: (a) A SHA-256 digest of the source bytes. (b) An HMAC of the source bytes with the portal secret.
- Chosen: Byte count and suffix only.
- Reason: A content digest lets an attacker confirm a guessed configuration. Each preview clears review (D-18), so the source needs no digest in the binding.
- Risk: Two sources with equal byte counts and equal suffixes look alike in the scope. Mitigation: Each new preview clears review, and the proposal digest changes when the converted content changes.
- Human decision: No.

### D-5. Export version 2 as a JSON attachment, not through DataExporter

- Alternatives: (a) `DataExporter.write_with_format_selection` to CSV, SQLite, ArangoDB, and Redis (rows 36 and 37). (b) A new export backend.
- Chosen: The JSON attachment pattern from version 1 (row 9), with `Cache-Control: no-store` (FR-019).
- Reason: The constitution scopes the rule to API data (row 39). The proposal holds no Mist response data. A backend write would break FR-014.
- Risk: A reviewer may expect `DataExporter`. Mitigation: FR-015 and test 16.
- Human decision: No.

### D-6. Use action `propose_create` and existing state `not_checked`

- Alternatives: (a) Action `create`. (b) Existing state `unknown`.
- Chosen: `propose_create` and `not_checked`.
- Reason: Offline work cannot know whether the object exists. `create` would state an unverified fact. `not_checked` names the check that did not run.
- Risk: Operators may read `propose_create` as approval. Mitigation: `cloud_state` is `unavailable` (D-8).
- Human decision: No.

### D-7. Keep `unresolved_mappings` as an empty list for the DNS subset

- Alternatives: (a) Omit the key until issue #4638 needs it. (b) Add a placeholder entry.
- Chosen: An empty list.
- Reason: FR-012 fixes the key set. A placeholder entry would invent a mapping.
- Risk: An empty list can look complete. Mitigation: The UI shows "None" next to the scope fields that read "Not selected" (`design/contracts/ui-v2.md`).
- Human decision: No.

### D-8. Report `local_schema` as passed and `cloud_state` as unavailable

- Alternatives: (a) Omit `cloud_state`. (b) Use the value `not_checked`.
- Chosen: `unavailable`, with the reason "Offline preview. No Mist request is made."
- Reason: The issue test plan requires unavailable-state handling. The reason tells the operator why the check did not run.
- Risk: Low. The reason text must stay short.
- Human decision: No.

### D-9. Require exact keys and `proposal_version` 2

- Alternatives: (a) Accept extra keys. (b) Accept version 1 bodies on version 2 routes.
- Chosen: Strict checks. Missing keys, extra keys, and any other version return HTTP 400.
- Reason: The contract must detect drift when issues #4637 to #4640 add fields.
- Risk: Strict checks block a legitimate addition until the contract revision. Mitigation: Assumption A-1.
- Human decision: No.

### D-10. Reserve hardware role, hardware model, and target as null scope fields

- Alternatives: (a) Add these fields later with a new version. (b) Fill them with default values.
- Chosen: Null values now. A later value changes the scope digest, so review invalidates (FR-011).
- Reason: The issue requires invalidation after role, model, and target changes. Null fields keep the key set stable.
- Risk: A null value can read as "none selected." Mitigation: The UI shows "Not selected."
- Human decision: No.

### D-11. Place code in existing modules, with one new class for each module

- Alternatives: (a) A new `proposal/` package under the converter root. (b) New classes in `models.py`.
- Chosen: `ProposalAssembler` in `conversion.py`, `StructuredProposal` in `state/proposal.py`, `ProposalRoutes` in `routes.py`, and `proposal_review.js` in `presentation/`.
- Reason: The converter root already holds five children (row 2). `models.py` already holds five classes (row 13).
- Risk: `routes.py` grows. Mitigation: T007 keeps each method within the limits.
- Human decision: No.

### D-12. Place the version 2 tests in a nested `proposals/` package

- Alternatives: (a) A direct file named `test_proposals.py`, which is the full-parity path (row 60). (b) A new file in the unit folder.
- Chosen: A nested `proposals/` package.
- Reason: The integration folder holds two children now (row 23). A direct file would add a child. The unit path that issue #4224 names is absent on `main` (row 71), so the unit folder is not an option.
- Risk: The full-parity map names a different path. Mitigation: Analysis item A-5.
- Human decision: No.

### D-13. Add the browser test to `TestCiscoOfflinePreview`

- Alternatives: (a) A new file under `tests/e2e/web_portal/`. That adds a child to an overfull folder (row 25). (b) A new browser file under the integration folder.
- Chosen: One method in the existing converter class (row 24).
- Reason: The Playwright CI job runs tests under `tests/e2e/`. `documentation/quality-gates.md` describes that job. The file was read locally, so the claim is listed under Unverified U-9.
- Risk: A reviewer may question an edit to a shared test file. Mitigation: The edit stays in the converter class and changes no shared fixture. Analysis item A-11.
- Human decision: No.

### D-14. Start after issue #4636 merges

- Alternatives: (a) Edit `models.py` now. (b) Edit `state/` paths before issue #4636 merges.
- Chosen: Wait for the merge.
- Reason: `models.py` holds five classes (row 13). Issue #4636 moves that module. A new class there would break the five-name limit.
- Risk: The schedule waits for another issue. Mitigation: T004 and T005 can begin after T002.
- Human decision: No.

### D-15. Make no change to the portal secret policy

- Alternatives: (a) Remove the random fallback now. (b) Require `PORTAL_SECRET_KEY` now.
- Chosen: No change. Review fails closed after a restart (row 30).
- Reason: The credential policy is an owner decision. Issue #4636 draft decision D-15 already marks it as such.
- Risk: Reviews clear after a restart that uses a random secret. Mitigation: The Caution in the spec and the owner decision.
- Human decision: HUMAN-DECISION-REQUIRED. The question is credential policy. Issue #4636 owns the question.

### D-16. Add one changelog fragment and leave the README unchanged

- Alternatives: (a) Add a README section. (b) Add no fragment.
- Chosen: One fragment (FR-022). The README stays unchanged (row 32).
- Reason: The repository rule requires a fragment for each user-visible change (row 44). The README names no converter, so a section would start a new documentation scope.
- Risk: The constitution asks for a README update on each behavior change (row 77). Mitigation: Analysis item A-7 asks the owner to decide the README scope.
- Human decision: No.

### D-17. Reuse version 1 error messages and status codes

- Alternatives: (a) A new error schema with error codes.
- Chosen: The same `error` key in each failed response, and the same status codes 400, 409, and 413.
- Reason: The version 1 browser script reads the `error` key of each failed response (row 19 names the same file). Clients already handle this shape.
- Risk: None significant.
- Human decision: No.

### D-18. Share one session digest slot between the versions

- Alternatives: (a) Separate slots for version 1 and version 2.
- Chosen: One slot, the existing `cisco_proposal` and `cisco_reviewed` keys (rows 8 and 14).
- Reason: Any preview replaces the slot and clears the review (FR-010). A version 1 export then cannot approve a version 2 object.
- Risk: Two browser tabs share the slot. Mitigation: The spec records this behavior as an edge case.
- Human decision: No.

### D-19. Accept the ten-key StructuredProposal as a justified exception

- Alternatives: (a) Nested TypedDict types. (b) A plain dictionary with no TypedDict.
- Chosen: One TypedDict with ten keys.
- Reason: Nested types add names to `state/proposal.py`, which the five-name limit blocks. A plain dictionary removes the static type check.
- Risk: A reviewer may reject the class size. Mitigation: Complexity Tracking in `plan.md`.
- Human decision: No.

### D-20. Enforce a 15-minute lifetime on version 2 previews and reviews

- Alternatives: (a) No time limit. The browser session lifetime would bound approvals. (b) A 15-minute lifetime, inclusive at 15 minutes. (c) Store-based expiry from issue #4636, which waits for the store.
- Chosen: Option (b). A preview cannot be reviewed 15 minutes or more after it is recorded. A review cannot be exported 15 minutes or more after it is recorded.
- Reason: Full-parity T006 uses a 15-minute review lifetime (row 78). Issue #4636 draft decision D-6 uses the same value and inclusive expiry. The session values carry the same rule until the store exists.
- Risk: Operators preview again more often. Mitigation: The response text names the required step, and the owner can change the value through issue #4636 decision D-6.
- Human decision: No.

## Sources

- Repository files read locally: `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, and the converter, test, portal, and deployment files named in R4. Each claim that uses a file cites its row in R4.
- Local reads of the documentation files `documentation/quality-gates.md`, `documentation/architecture.md`, `documentation/development-setup.md`, and `documentation/container-deployment.md` provide context only. No claim in this record depends on them, except U-9.
- Reference record: `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`. Its spec, plan, tasks, analysis, design, and checklist files set the shape of this record.
- Full-parity record: `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/`.
- Parent record: `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/`.
- SDK and API: `.venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py` and `.venv\Lib\site-packages\mistapi-0.64.1.dist-info`. OpenAPI: `documentation/mist-api-openapi31yaml.yaml`, read through the blob API on `main`.
- Draft records (local only): `spec-drafts/4636` (spec, plan, research, state records contract, and STATUS), `spec-drafts/4648/spec.md`, and `spec-drafts/4649/spec.md`.
- Issues: `https://github.com/jmorrison-juniper/MistHelper/issues/4641`, `https://github.com/jmorrison-juniper/MistHelper/issues/4633` (coordinator decision of 2026-11-08T23:37:56Z), `https://github.com/jmorrison-juniper/MistHelper/issues/4636` (coordinator comment of 2026-11-09T16:55:13Z), and issues #4224 and #4634 to #4649 (state read on 2026-11-26).
- Pull requests: `https://github.com/jmorrison-juniper/MistHelper/pull/4596`, `https://github.com/jmorrison-juniper/MistHelper/pull/4208`.

## Unverified

- U-1: This drafting pass ran no build, test, linter, formatter, or container. The brief forbids those commands.
- U-2: The STE score of this record was not measured. The brief forbids linters, and the gate lists named files only (row 43).
- U-3: The browser test was not executed. Chromium behavior in the isolated host is unverified.
- U-4: The final route set of issue #4648 was not read from GitHub. The draft spec in `spec-drafts/4648/spec.md` was read, and it is local.
- U-5: Issues #4637 to #4640 have no records on `main` or in `spec-drafts`. Their output shape is unknown.
- U-6: Deployments were not checked for a set `PORTAL_SECRET_KEY`. No deployment data was read. Issue #4636 draft item U-11 records the same gap.
- U-7: The container worker count was not verified. The issue #4636 draft cites `container/scripts/start.sh` line 225, and this record did not read that file.
- U-8: No tool gate checks inline comments on new lines. A reviewer checks them.
- U-9: `documentation/quality-gates.md` describes the Playwright CI job. The file was read locally, and its blob was not compared with `main`.
- U-10: The constitution does not say whether module constants count toward the five-name limit. This record counts classes only.
- U-11: The browser session size with the digest values was not measured. Each digest adds 64 hexadecimal characters.
- U-12: The mistapi runtime behavior was not executed. The signature comes from the installed source (row 58).
