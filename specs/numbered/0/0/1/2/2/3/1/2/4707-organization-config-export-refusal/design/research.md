# Research: Organization Config Export Refusal

Each decision lists what the spec chose, why, and what else the team considered. Facts come from local source reads and from remote checks on `main`. The remote table lists each check. Each row cites a path, a ref, a blob SHA or commit SHA, a result, and a line.

## R0. Source conflicts

- **Decision**: The spec uses the enforced mistapi pin. `pyproject.toml` line 29 allows `>=0.64.1,<0.65`, and `requirements.txt` line 129 pins `mistapi==0.64.1` (RC-42, RC-43). The installed SDK reports `0.64.1` (RC-73).
- **Rationale**: The enforced pin controls the runtime. The repository rules state `>=0.64.0` (RC-03), and the constitution states `0.59+` (RC-05). Both texts drift from the enforced pin. Analysis F-07 records the drift.
- **Alternatives considered**:
  - Copy the rule text from the repository rules. It conflicts with the enforced pin.
  - Change the documentation in this change. It adds scope that the issue does not name.

## R1. Verification rule for a fetch

- **Decision**: A fetch is verified only when each response has an integer HTTP status from 200 through 299, and its payload is a list, or a dictionary whose `results` value is a list.
- **Rationale**: The SDK does not raise for an HTTP refusal. `_request_with_retry` returns an `APIResponse` built from the response (RC-63), and the status is stored on that object (RC-61). A payload check alone accepts a refusal body that carries a plausible structure. The organization name lookup already uses this status-first rule (RC-18).
- **Alternatives considered**:
  - Check for an error field only. It accepts a refused body that has no error field, and the issue reports such a body.
  - Accept any 2xx response. It accepts an unknown payload shape as verified.
  - Treat a missing status as success. It contradicts the rule in RC-18.
- **Risk**: An API change that alters the payload shape marks the type not verified. The export then stops. This is the safe direction.

## R2. Export writes nothing unless all six types verify

- **Decision**: The export writes no file when any configuration type is not verified. It logs one error for each type that is not verified and one stop message.
- **Rationale**: Menu 187 selects bundles by the name pattern `OrgConfig_Export_*.json` (manager file, `_select_import_file`). A partial file in `data/` looks like a complete bundle to an operator. Fail-closed output avoids a partial migration source.
- **Alternatives considered**:
  - Save a bundle with an incomplete marker. The import would reject it, but operators can still open or copy it.
  - Ask the operator whether to save a partial bundle. The prompt adds a risky default choice.
- **Risk**: One refused type blocks the whole export. The error names the type and the status, so the operator can repair access.

## R3. Pagination uses a verified page loop

- **Decision**: The reader calls `mistapi.get_next` for each follow-up page and verifies every page with the rule in R1.
- **Rationale**: `get_all` reads later pages without a status check (RC-20 at the manager call site, and the SDK loop at RC-58). The list branch adds the dictionary keys of an error body to the list (RC-58). The SDK helper returns an empty list when the body has no `results` (RC-57). The SDK's `get_next` returns the next response or `None` (RC-60), so the reader sees each page.
- **Alternatives considered**:
  - Keep `get_all` and verify page 1 only. Later pages stay unchecked.
  - Wrap `get_all` in a helper. A wrapper cannot see the status of each page.

## R4. Exception boundary per type

- **Decision**: Keep the broad `except Exception` at the boundary of each configuration type. Categorize the failure as `exception`. Log the exception class name only.
- **Rationale**: Each type is attempted in one run, so the operator sees every failed type in one report. A broad boundary still fails closed, because an exception never produces a verified outcome.
- **Alternatives considered**:
  - Narrow the boundary to `(OSError, RuntimeError)`, as the organization name lookup does. The narrower clause sits at manager line 155 on the blob that RC-17 verifies. A programming error would then stop the run after earlier types, and the operator would lose the per-type report.

## R5. Bundle schema 1.1 with a fetch status map

- **Decision**: Write schema version `1.1`. Add `metadata.fetch_status`, which maps each of the six keys to `verified`. Keep `object_counts` and the six lists.
- **Rationale**: A map proves the verification state of each type. The current schema is `1.0` (RC-22), which has no state.
- **Alternatives considered**:
  - Keep `1.0` and add one boolean. A boolean cannot identify the type that failed.
  - Add a free text reason. A free text value is hard to validate in import.

## R6. Import refuses legacy and unverified bundles before the prompt

- **Decision**: `_validate_bundle_structure` rejects a bundle whose schema is not `1.1` or whose fetch status is not `verified` for each key. The check runs before the preview and before the prompts.
- **Rationale**: A legacy bundle has no provenance proof. A migration source must be complete. The check after the key check keeps the existing key error text for a missing type (test `test_a_missing_type_key_fails`).
- **Alternatives considered**:
  - Accept legacy bundles with a warning. The warning does not prove that the contents are complete.
  - Accept a dry run with an unverified bundle. The preview would show an incomplete plan.

## R7. Destination inventory gate after confirmation

- **Decision**: `_fetch_existing_objects` returns `False` when a destination type is not verified. `import_config` returns before `_execute_import`. The gate applies to dry-run and live modes.
- **Rationale**: The current order fetches the destination after the IMPORT confirmation (RC-25). Keeping the order keeps the operator flow and the prompt tests. A dry run without conflict data hides real conflicts, so the dry run uses the same gate.
- **Alternatives considered**:
  - Fetch the destination before the prompt. It changes the prompt order and the existing tests.
  - Continue a dry run with a warning. The preview can then show objects that the live import would skip.

## R8. Module placement and the five-item rule

- **Decision**: Keep the new classes in `src/mist/resources/org/org_config_migration_manager.py`. The module holds five top-level names: `logger`, `ConfigFetchOutcome`, `ConfigFetchReader`, `BundleVerification`, and `OrgConfigMigrationManager`.
- **Rationale**: The directory already holds five tracked children (RC-49). A new file or folder adds a child to a full directory. The manager loses two methods, from 49 to 47.
- **Alternatives considered**:
  - A new module in `src/mist/resources/org/`. It adds a child to a full directory.
  - A new package under `src/mist/resources/`. It changes the module path and adds a child to another parent.

## R9. Route for the record

- **Decision**: Use `specs/numbered/0/0/1/2/2/3/1/2/4707-organization-config-export-refusal`.
- **Rationale**: The route uses the eight-digit base-5 value of the number. The spec route script uses base 5 (RC-10). The value of 4707 in base 5 is `122312`, which pads to `00122312`, and that matches the route in the brief. The same rule gives `00114110` for issue 4280 and `00124140` for issue 4920. Both folders exist on main (RC-47, RC-48).

## R10. Holds, labels, and merge

- **Decision**: Keep precondition P-1, the `needs-human-review` label, and the disabled automatic merge. Implementation waits for an explicit handover.
- **Rationale**: The owner comment on issue #4707 says to keep the file-handover and human-review holds. The handoff file holds no entry for this issue (RC-44). AGENTS.md git flow (RC-01) requires human review for a change to a destructive path. Menu 187 is a destructive operation (RC-28).
- **Alternatives considered**:
  - Start after PR #4404 merged. The merge happened on 2026-11-13 (RC-55), but the owner comment still keeps the holds.
  - Enable automatic merge after CI passes. The label `needs-human-review` blocks that path.

## R11. Documentation scope

- **Decision**: Update the module docstring, the inline comments, and the changelog fragment. Do not edit `README.md`, `documentation/operator-guide.md`, or the menu API pages.
- **Rationale**: `README.md` and `documentation/operator-guide.md` hold no menu 58 or 187 text and no bundle text (RC-12, RC-13). The menu API pages list endpoints and handler names (RC-14, RC-15), and this change keeps both. The changelog rule (RC-45) and the precedent fragment (RC-46) set the format.

## R12. Skills

- **Decision**: No skill is loaded.
- **Rationale**: The issue concerns Mist cloud configuration export. It does not concern Podman, storage, networking, or Juniper device behavior. The brief limits skill use to those topics.

## Remote verification

Each row is one check. The blob SHA column holds the commit SHA for a commit row. The `local-venv` ref marks an installed package in `.venv`. Its SHA is the value of `git hash-object` on that file. No package file is in the repository tree.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| RC-01 | AGENTS.md defines STE, gates, and git flow | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| RC-02 | Repository rules hold the Local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RC-03 | Repository rules state mistapi>=0.64.0,<0.65 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | stale | 21 |
| RC-04 | Constitution defines the Five-Item Rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-05 | Constitution states mistapi 0.59 or newer | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | stale | 279 |
| RC-06 | Spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| RC-07 | Plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| RC-08 | Tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| RC-09 | Checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| RC-10 | Spec route script uses base 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-11 | Quality gate page lists CI jobs and thresholds | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 0 |
| RC-12 | README holds no menu 58 or 187 row and no bundle text | README.md | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | present | 0 |
| RC-13 | Operator guide holds no menu 58 or 187 text | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 0 |
| RC-14 | Menu API page documents menu 58 | documentation/menu-api/safe.md | main | c4c10e2ed30aeb6617716a6d0a90de7f36ed7ad1 | present | 847 |
| RC-15 | Menu API page documents menu 187 | documentation/menu-api/destructive.md | main | 643ff157e818944a0e4d7fbd208b282c4a1c0113 | present | 754 |
| RC-16 | Endpoint coverage page lists listOrgNetworks | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 730 |
| RC-17 | Manager defines six configuration types | src/mist/resources/org/org_config_migration_manager.py | main | 358a2cc226d550a0d838b10ae0738944894f5655 | present | 42 |
| RC-18 | Manager validates HTTP status in the organization name lookup | src/mist/resources/org/org_config_migration_manager.py | main | 358a2cc226d550a0d838b10ae0738944894f5655 | present | 159 |
| RC-19 | Manager returns an empty list after a fetch exception | src/mist/resources/org/org_config_migration_manager.py | main | 358a2cc226d550a0d838b10ae0738944894f5655 | present | 202 |
| RC-20 | Manager sends replies to mistapi.get_all without a status check | src/mist/resources/org/org_config_migration_manager.py | main | 358a2cc226d550a0d838b10ae0738944894f5655 | present | 208 |
| RC-21 | Export logs completion without a verification gate | src/mist/resources/org/org_config_migration_manager.py | main | 358a2cc226d550a0d838b10ae0738944894f5655 | present | 114 |
| RC-22 | Bundle schema version is 1.0 | src/mist/resources/org/org_config_migration_manager.py | main | 358a2cc226d550a0d838b10ae0738944894f5655 | present | 218 |
| RC-23 | Bundle structure check validates keys only | src/mist/resources/org/org_config_migration_manager.py | main | 358a2cc226d550a0d838b10ae0738944894f5655 | present | 309 |
| RC-24 | Import conflict cache reuses the fetch that returns an empty list | src/mist/resources/org/org_config_migration_manager.py | main | 358a2cc226d550a0d838b10ae0738944894f5655 | present | 377 |
| RC-25 | Import fetches destination inventory after confirmation | src/mist/resources/org/org_config_migration_manager.py | main | 358a2cc226d550a0d838b10ae0738944894f5655 | present | 141 |
| RC-26 | Issue body says draft #4404 owns the manager file | src/mist/resources/org/org_config_migration_manager.py | main | 358a2cc226d550a0d838b10ae0738944894f5655 | stale | 0 |
| RC-27 | Menu 58 is category safe | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 645 |
| RC-28 | Menu 187 is category destructive | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 646 |
| RC-29 | Menu 58 handler calls export_config | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6298 |
| RC-30 | Menu 187 handler calls import_config | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6308 |
| RC-31 | Conflicts test asserts a failed fetch returns an empty list | tests/unit/org/test_org_config_migration_conflicts.py | main | d236dbe09d02028d2400235697e251a4d9acc784 | present | 637 |
| RC-32 | Conflicts test asserts a None paging result becomes an empty list | tests/unit/org/test_org_config_migration_conflicts.py | main | d236dbe09d02028d2400235697e251a4d9acc784 | present | 602 |
| RC-33 | Workflow test asserts a saved bundle after fetch failures | tests/unit/org/test_org_config_migration_workflow.py | main | 6d169157ff1e507919793aac210fd15db29e2856 | present | 379 |
| RC-34 | Workflow helper builds six keys without fetch status | tests/unit/org/test_org_config_migration_workflow.py | main | 6d169157ff1e507919793aac210fd15db29e2856 | present | 40 |
| RC-35 | Workflow test names the schema version stamp | tests/unit/org/test_org_config_migration_workflow.py | main | 6d169157ff1e507919793aac210fd15db29e2856 | present | 225 |
| RC-36 | SDK guard baseline holds 10 unresolved call sites | tests/integration/test_mistapi_sdk_compatibility.py | main | cab2d602113012729f6c392dff43197d05913a38 | present | 16 |
| RC-37 | SDK guard baseline holds 366 unverifiable call sites | tests/integration/test_mistapi_sdk_compatibility.py | main | cab2d602113012729f6c392dff43197d05913a38 | present | 17 |
| RC-38 | CI defines MYPY_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-39 | CI defines VULTURE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RC-40 | CI defines PYDOCSTYLE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| RC-41 | CI defines INTERROGATE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RC-42 | pyproject pins mistapi at or above 0.64.1 and below 0.65 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| RC-43 | requirements.txt pins mistapi 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| RC-44 | Handoff file holds no entry for issue 4707 | .github/copilot-handoff.md | main | 17acc1af13e4615c763cc2bd8c7d239ff1709b61 | absent | 0 |
| RC-45 | Changelog rule names the issue form for an issue without a pull request | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| RC-46 | Precedent fragment for issue 4280 holds a Fixed bullet | changelog.d/issue-4280-organization-metadata-refusal.md | main | b951b4eb1e0e645ef690212c6f7bec4901f17f2a | present | 3 |
| RC-47 | Precedent record for issue 4280 exists | specs/numbered/0/0/1/1/4/1/1/0/4280-organization-metadata-refusal/spec.md | main | d169ecd85531d526bcc1d02a3a265786a5dff2c2 | present | 0 |
| RC-48 | Reference record for issue 4920 exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-49 | Manager directory holds five tracked children | src/mist/resources/org/__init__.py | main | 6b7946945cb2505923fd975eac684a1d6aa2ff0a | present | 0 |
| RC-50 | No record for issue 4707 exists under the route | specs/numbered/0/0/1/2/2/3/1/2 | main | not applicable | absent | 0 |
| RC-51 | Local HEAD equals remote main | git rev-parse HEAD (local) | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-52 | Remote main is the commit at authoring | repos/jmorrison-juniper/MistHelper/commits/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-53 | Issue body cites main 3964d21d | repos/jmorrison-juniper/MistHelper/commits/3964d21d03f9f5717cb8eafb7272ecff21f5362a | main | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | stale | 0 |
| RC-54 | Issue comment cites main b7a18b7e | repos/jmorrison-juniper/MistHelper/commits/b7a18b7ead7b1de5882bcd288203c015b1eef792 | main | b7a18b7ead7b1de5882bcd288203c015b1eef792 | stale | 0 |
| RC-55 | PR 4404 merge commit is on main | repos/jmorrison-juniper/MistHelper/commits/31b752f060d4d10cbe87b5880b071b6570d0b3c9 | main | 31b752f060d4d10cbe87b5880b071b6570d0b3c9 | present | 0 |
| RC-56 | PR 4310 create-id commit is on main | repos/jmorrison-juniper/MistHelper/commits/531bfe42cb5cf7a9cdf9621cd4e93ab22b5e1ede | main | 531bfe42cb5cf7a9cdf9621cd4e93ab22b5e1ede | present | 0 |
| RC-57 | mistapi get_all returns an empty list when no branch matches | .venv\Lib\site-packages\mistapi\__pagination.py | local-venv | 795dd0400f9db69d1ee67aa96e3ddfca405e6f1a | present | 74 |
| RC-58 | mistapi list branch extends later pages with response data | .venv\Lib\site-packages\mistapi\__pagination.py | local-venv | 795dd0400f9db69d1ee67aa96e3ddfca405e6f1a | present | 62 |
| RC-59 | mistapi get_next is exported | .venv\Lib\site-packages\mistapi\__init__.py | local-venv | f6fca30f4088d763e76f3072d02a3095d46852b9 | present | 16 |
| RC-60 | mistapi get_next returns the next response or None | .venv\Lib\site-packages\mistapi\__pagination.py | local-venv | 795dd0400f9db69d1ee67aa96e3ddfca405e6f1a | present | 17 |
| RC-61 | APIResponse stores the HTTP status code | .venv\Lib\site-packages\mistapi\__api_response.py | local-venv | 2d878d79295fec79e6409f6243132c53280f15ab | present | 48 |
| RC-62 | APIResponse defaults data to an empty dictionary | .venv\Lib\site-packages\mistapi\__api_response.py | local-venv | 2d878d79295fec79e6409f6243132c53280f15ab | present | 39 |
| RC-63 | Request layer returns a response for HTTP errors without raising | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 258 |
| RC-64 | Request layer starts with no response before a connection failure | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 207 |
| RC-65 | listOrgNetworks builds the documented path | .venv\Lib\site-packages\mistapi\api\v1\orgs\networks.py | local-venv | 13c142d7fd215700217c96559cdfedf068647d70 | present | 48 |
| RC-66 | listOrgNetworks takes the org identifier and the limit | .venv\Lib\site-packages\mistapi\api\v1\orgs\networks.py | local-venv | 13c142d7fd215700217c96559cdfedf068647d70 | present | 17 |
| RC-67 | listOrgDeviceProfiles accepts a type filter | .venv\Lib\site-packages\mistapi\api\v1\orgs\deviceprofiles.py | local-venv | b603220c8e11b8c64b523b4c9e683d3408eff299 | present | 20 |
| RC-68 | listOrgServices is defined | .venv\Lib\site-packages\mistapi\api\v1\orgs\services.py | local-venv | 20e034e490c137209f284fc69b95b43e6f33eb24 | present | 17 |
| RC-69 | listOrgVpns is defined | .venv\Lib\site-packages\mistapi\api\v1\orgs\vpns.py | local-venv | fb72b5dadf4a5e46578b3c0c381a2884d61320ad | present | 17 |
| RC-70 | listOrgGatewayTemplates is defined | .venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py | local-venv | 6b82963804738f1a6a85af80dab4b3c7d9b67735 | present | 17 |
| RC-71 | listOrgServicePolicies is defined | .venv\Lib\site-packages\mistapi\api\v1\orgs\servicepolicies.py | local-venv | b1c6ab1bc13c6925db80dfd30105f6b7166f1a74 | present | 17 |
| RC-72 | getOrg takes the org identifier | .venv\Lib\site-packages\mistapi\api\v1\orgs\orgs.py | local-venv | e08585784e20246bdfb509e3e1e85e4d0528764c | present | 42 |
| RC-73 | Installed mistapi version is 0.64.1 | .venv\Lib\site-packages\mistapi\__version.py | local-venv | cb8f30ff14092ff9d6ddfafaeef41dac5e425f38 | present | 1 |
| RC-74 | OpenAPI getOrg operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 4898 |
| RC-75 | OpenAPI listOrgDeviceProfiles operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 7957 |
| RC-76 | OpenAPI listOrgGatewayTemplates operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9731 |
| RC-77 | OpenAPI listOrgNetworks operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 15122 |
| RC-78 | OpenAPI listOrgNetworks responses hold no 503 | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 15126 |
| RC-79 | OpenAPI listOrgServicePolicies operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 18345 |
| RC-80 | OpenAPI listOrgServices operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 18494 |
| RC-81 | OpenAPI listOrgVpns operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 23524 |
| RC-82 | Changelog guard checks each fragment name | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 151 |
| RC-83 | Pull request template exists | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 0 |

Count: 83 remote checks. Results: 76 present, 5 stale, 2 absent.

## Sources

- Local source, identical to the remote blob that RC-17 verifies: `src/mist/resources/org/org_config_migration_manager.py`. Lines 42, 114, 141, 150-161, 183-218, 258, 293-330, and 372-377 were read.
- Local tests, identical to the remote blobs in RC-31 through RC-35: `tests/unit/org/test_org_config_migration_conflicts.py` and `tests/unit/org/test_org_config_migration_workflow.py`.
- Local SDK, `.venv\Lib\site-packages\mistapi`: the pagination module, the response module, the request module, the orgs API modules, and the version module. Each file has a `git hash-object` value in the table above. The file is read only.
- Mist OpenAPI file, `documentation/mist-api-openapi31yaml.yaml`. Its blob SHA `b7fc2bfb` matches the remote tree. Line numbers come from a decode of the remote blob.
- Local git history, read only: `git log --oneline -6 -- src/mist/resources/org/org_config_migration_manager.py` from the repository root lists `31b752f06` (PR 4404), `531bfe42c` (PR 4310), and `025ef82ee`.
- GitHub reads through `gh`, with the authentication preamble of the brief: `gh issue view 4707`, `gh issue view 4280`, `gh issue view 4277`, `gh pr list --search 4707`, `gh pr view 4404`, `gh pr list --state open` (no open pull request touches the manager file), `gh api` on the tree, the contents, the blobs, and the commits.
- No `web_fetch` call was made. No upstream source was needed, because the installed SDK and the repository hold the answers.

## Unverified

- The live Mist response to HTTP 503 on the six list endpoints. No live call was made, because the authoring run does not call production systems.
- Whether operator `data/` folders hold legacy bundles. The repository does not hold operator data.
- Whether a Mist organization returns HTTP 403 or an empty list for a feature that is disabled. No live data was read.
- The symbol gate behavior for added top-level names. The tool source sits in the `misthelper-devtools` package, which is not in the repository tree.
- The advisory `speckit_task_audit` acceptance of this task format. The audit rules were not read.
- The SDK guard counts after the change. No test ran during authoring.
- The pylint score and the coverage after the change. No gate ran during authoring.
- The GitHub required checks and CodeQL result for a pull request. No pull request exists yet.
- The auto-merge workflow behavior with the `needs-human-review` label. The workflow file was not read, and no decision depends on it.
