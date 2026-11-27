# Research: Gated Converter Administration and Unassignment

## Evidence Boundary

Observation date: 2026-11-26. This record ran no build, no test, no linter, and no repository script.
No live Mist request ran. No web source was fetched. No skill was loaded, because no Podman or Juniper device question applies.

| Evidence | Revision or state |
| --- | --- |
| Local `HEAD` in the read-only checkout | `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, committed 2026-11-26T07:15:01Z |
| Remote `main` tree | Fetched with `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`. The response holds 11,404 entries and is not truncated. |
| Remote file bodies | Decoded from `gh api repos/jmorrison-juniper/MistHelper/contents/{file-path}?ref=main`, one file at a time. Nothing was written to disk. |
| Mist OpenAPI | `documentation/mist-api-openapi31yaml.yaml`. Its local hash equals the remote blob (RC-22), so local line numbers apply to `main`. |
| Installed SDK | `.venv\Lib\site-packages\mistapi`, package version 0.64.1 (`mistapi-0.64.1.dist-info`). This is a local file. The record does not claim a remote copy. |
| Issue 4645 | GitHub issue, read with `gh issue view`. Labels: `feature`, `web-portal`, `needs-human-review`. State: open. |
| Linked pull requests | None found for issue 4645 (`gh pr list --search 4645`). |
| Related pull requests | PR 4596 merged 2026-11-13. PR 4208 is open. |
| Related issues | 4224 (open), 4633 (closed), 4634 (open), 4635 (open), 4636 (open), 4637 to 4649 (open). Issue 4634 has three comments. Issue 4633 has three comments. |
| Local draft for issue 4636 | `C:\Users\jmorrison\.copilot\session-state\30878eb1-80d0-451d-bd0c-0b3624089852\files\spec-drafts\4636`. It is a local draft and is not committed. Its names are cited here as dependencies. |

Truth order: the remote tree and the remote file bodies outrank the local search. Local copies match the remote copies where a row says so.

## Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk.
Decisions D-1, D-2, and D-3 need a human owner. Each of the other decisions has a recommended option that the research supports.

### D-1. Operator identity and authorization policy for administrative writes HUMAN-DECISION-REQUIRED

- Alternatives: (a) An IP allowlist. Rejected, because an allowlist does not identify an operator (live `research.md`, readiness decisions). (b) A shared password. Rejected, because a shared secret cannot name one operator. (c) A named identity provider with role checks. Recommended. (d) Keep every identity refused until the owner chooses (c) or another named design.
- Chosen: (d) now. The production verifier refuses every identity (FR-003). The owner decides option (c) or another named design.
- Reason: Issue 4636 decision D-10 refuses write-capable approvals without a verified operator. Issue 4636 records that no operator identity provider exists in the repository (F-07).
- Risk: No run can start until the owner decides. Refusal keeps production safe in the meantime.

### D-2. Owner enablement of each family, scope limit, recovery limit, and retention HUMAN-DECISION-REQUIRED

- Alternatives: (a) Enable all five families now. Rejected, because no family has complete evidence. (b) Never enable a family. Rejected, because the issue requires the function. (c) Enable one family at a time after issue 4634 evidence and an owner decision. Chosen. (d) Enable a list for each run. Rejected, because a list for each run adds a second configuration path.
- Chosen: Option (c). The owner records each family decision in issue 4645 with its scope limit and recovery limit.
- Reason: Gate G4 requires owner approval for each family (plan.md, Approval Gates). Issue 4645 states that no production operation is authorized.
- Risk: Enablement takes longer. The disabled default protects production during that time.

### D-3. Site-template unassignment semantics HUMAN-DECISION-REQUIRED

- Alternatives: (a) Send `sitetemplate_id` as null through `updateSiteInfo`. This is the candidate in RC-29 and RC-32. Its null semantics are unverified (UV-05). (b) Update the site template object. No verified field exists for this path. (c) Keep the path refused and record an unsupported disposition in issue 4649. Recommended until evidence exists.
- Chosen: The path stays refused under FR-015. The owner chooses option (a) after issue 4634 verifies it, or option (c).
- Reason: The OpenAPI assigns a site template through the Update Site endpoint (RC-31). The `site` schema names no unassignment value (RC-30). The live contract has no site-template row (RC-34).
- Risk: The C30 row stays partial. Issue 4649 records the disposition.

### D-4. Template deletion covers gateway templates only

- Alternatives: (a) Delete every template family. Rejected, because no evidence exists for the other families and the issue says not to broaden scope. (b) Delete gateway templates only. Chosen. (c) Delete no template. Rejected, because the issue requires template deletion.
- Reason: The live contract maps template deletion to `deleteOrgGatewayTemplate` (RC-36). The 4224 converter creates gateway templates (4224 spec, User Story 1).
- Risk: Operators may expect other families. Issue 4649 records the disposition for each family.

### D-5. Test location

- Alternatives: (a) `tests/contract/cisco_config_converter/`. Rejected, because `tests/contract/` already holds 17 children (RC-13). (b) `tests/e2e/cisco_config_converter/`. Rejected, because `tests/e2e/` already holds five children (RC-14). (c) `tests/integration/web_portal/cisco_config_converter/administration/`. Chosen.
- Reason: Constitution Principle I (RC-50). Issue 4636 decision D-2 chose the same tree for its state tests.
- Risk: The T025 path in the live task list differs from this path. The pull request body records the difference.

### D-6. Source location and capacity

- Alternatives: (a) A sixth root child `administration/`. Rejected, because the root holds five children (RC-07). (b) More methods on `ConverterRoutes`. Rejected, because the class holds five members (RC-05). (c) A new folder inside `state/`. Rejected, because `state/` holds five children after issue 4636. (d) Move `conversion.py` into `engine/` and add `engine/administration/`. Chosen.
- Reason: Findings F-01, F-11, and F-14. Option (d) keeps every folder at five children or fewer.
- Risk: Import paths change. The move guard, the symbol gate, and a grep for the old path cover the change (`design/quickstart.md`, Scenario 6).

### D-7. Live references block a scope. No automatic detachment

- Alternatives: (a) Detach each reference automatically. Rejected, because the change touches unrelated objects. (b) Allow an override with a second confirmation. Rejected, because the operator cannot judge a live site from the review alone. (c) Block the scope. Chosen.
- Reason: Issue 4645 and the live research row C30 require preservation of unrelated references (RC-44).
- Risk: Some valid deletions need manual cleanup first. The review lists each reference, so the operator can plan that cleanup.

### D-8. Run order, stop rule, and retry rule

- Alternatives: (a) Parallel writes. Rejected, because the stop rule cannot work with parallel writes. (b) Deletions before unassignments. Rejected, because a deletion can leave a reference in a device profile. (c) Fixed order with a stop at the first failed or indeterminate object. Chosen.
- Order: device profile MAC unassignments, then gateway template deletions, then network deletions, then service deletions. A template might reference a network or a service (UV-01). Deleting the template first avoids a dangling reference.
- Stop rule: The first `failed` or `indeterminate` object stops the run. Each later object becomes `not_attempted` (FR-017).
- Retry rule: No write repeats automatically (FR-017). A 429 response is read back before any decision (UV-07).
- Risk: Long runs stop early. Operators repeat a review after the stop.

### D-9. Two environment variables and no new documentation file

- Alternatives: (a) A database flag. Rejected, because it adds a store. (b) A separate configuration file. Rejected, because it adds a file. (c) Two environment variables with comments in `deploy/.env.example`. Chosen. (d) A new file under `documentation/`. Rejected, because `documentation/` is a grandfathered noncompliant parent (plan.md, Complexity Tracking).
- Reason: A new variable enters `deploy/.env.example` (RC-53, copilot-instructions). The README rule covers menu operations, and this change adds no menu row.
- Risk: Operators miss the flags. The page stays hidden until enabled, and the changelog fragment names both variables.

### D-10. Two confirmations and the approval lifetime

- Alternatives: (a) One typed word. Rejected, because the issue requires two confirmations. (b) Two typed words. Rejected, because a second typed word does not prove that the operator reviewed the scope. (c) A scope confirmation that echoes the digest, then the typed `CONFIRM`. Chosen. (d) A longer approval lifetime. Rejected, because a long lifetime allows a stale scope.
- Lifetime: 15 minutes, inclusive. Issue 4636 decision D-6 uses the same lifetime.
- Reason: The live spec requires two confirmations and the typed `CONFIRM` (RC-41). Issue 4636 decision D-7 makes each approval one use.
- Risk: Operators repeat the review after 15 minutes. That repetition is intended.

### D-11. A verified backup manifest for each family

- Alternatives: (a) No backup check. Rejected, because the issue requires verified backup evidence. (b) A warning only. Rejected, because the issue requires a refusal on backup failure. (c) A verified manifest for each family that covers each selected object. Chosen.
- Reason: The issue test plan requires a refusal on backup failure. The restore guide in `documentation/backup-restoration.md` requires an exact typed word before a restore runs (RC-51).
- Risk: This record depends on issue 4643. Task T001 confirms that dependency.

### D-12. Read-back decides each outcome

- Alternatives: (a) Trust the HTTP status. Rejected, because a timeout leaves the result unknown. (b) Repeat the write after an error. Rejected, because a repeated delete can act on a changed object. (c) Read back each object and mark an unknown result as `indeterminate`. Chosen.
- Reason: Issue 4636 decision D-8 marks unknown write outcomes as indeterminate.
- Risk: Each object adds one read. The 25-object limit bounds the extra reads.

### D-13. Exclude service policy deletion, device profile deletion, site deletion, inventory unassignment, and restore

- Alternatives: (a) Include service policy deletion. Rejected, because the issue does not name it and no owner approved it (F-05). (b) Include device profile deletion. Rejected, because the issue names unassignment only. (c) Exclude each operation from this issue. Chosen. Issue 4649 records the owner disposition.
- Reason: The issue scope (RC-39, RC-40). Issue 4634 asks whether the converter needs `deleteOrgServicePolicy` (RC-33).
- Risk: Parity gaps remain until issue 4649 closes them.

### D-14. No auto-merge label for this pull request

- Alternatives: (a) Add `auto-merge` after CI passes. Rejected, because AGENTS.md forbids it for a destructive-operation change (RC-48). (b) Add `auto-merge` after orchestrator approval. Rejected, because the same rule applies. (c) Keep human review. Chosen.
- Reason: AGENTS.md lines 230 and 231 (RC-48).
- Risk: The merge takes longer. The change is reviewed by a person.

### D-15. Administration UI in new presentation files

- Alternatives: (a) Edit `presentation/converter.html` and `presentation/converter.js`. Rejected, because issue 4647 owns the visual work in those files (live tasks T029 and T030). (b) Add `presentation/administration.html` and `presentation/administration.js`. Chosen.
- Reason: The presentation folder holds two children (RC-10). Two new files give four children, which stays within the limit.
- Risk: Two presentation sources exist. Both use the host theme services.

### D-16. No shared portal registration in this issue

- Alternatives: (a) Register the routes in `web_portal/app.py` now. Rejected, because PR 4208 owns that file (RC-57). (b) Register the routes in a later integration change. Chosen, after issue 4648.
- Reason: The current portal has no converter registration (RC-15). Gate G3 requires a handover first.
- Risk: The feature stays unreachable in the deployed portal until issue 4648 completes. The isolated test host still exercises the routes.

## Remote Verification

Each row records one check. The table holds 72 rows. The STATUS file repeats the same 72 checks in the same order.
Blob SHA `none` marks an absent path, a pull request, or a local SDK file.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| RC-01 | Target routes module holds the converter blueprint | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 0 |
| RC-02 | ConverterRoutes.blueprint registers the converter URL rules | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 49 |
| RC-03 | Registration fails when CSRFProtect is absent | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 107 |
| RC-04 | No administrative route or refusal path exists | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | absent | 0 |
| RC-05 | Class ConverterRoutes holds five members | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 45 |
| RC-06 | ReviewState holds the session-based approval | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 84 |
| RC-07 | Converter root holds five direct children | src/interfaces/portals/cisco_config_converter | main | 363cf44f8bad5dfdcd344a76852a8a34146b9190 | present | 0 |
| RC-08 | State package from issue 4636 is absent | src/interfaces/portals/cisco_config_converter/state | main | none | absent | 0 |
| RC-09 | Engine package for this change is absent | src/interfaces/portals/cisco_config_converter/engine | main | none | absent | 0 |
| RC-10 | Presentation folder holds two direct children | src/interfaces/portals/cisco_config_converter/presentation | main | bc5adba315c0ff6fbbb7d2b4b6e1a7680d15dce6 | present | 0 |
| RC-11 | Feature integration test folder holds two direct children | tests/integration/web_portal/cisco_config_converter | main | 6538f20cdb454342a96e079a0e7678fb6baa7a42 | present | 0 |
| RC-12 | Planned contract test file is absent | tests/contract/cisco_config_converter/test_administration.py | main | none | absent | 0 |
| RC-13 | Folder tests/contract holds 17 direct children | tests/contract | main | 3e544ef7c55adf7c8a8010e6da3afc345b27d57e | present | 0 |
| RC-14 | Folder tests/e2e holds five direct children | tests/e2e | main | 828f24a6106147d9263b550da13acfaa4866b3bf | present | 0 |
| RC-15 | web_portal/app.py has no converter registration | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | absent | 0 |
| RC-16 | PORTAL_SECRET_KEY falls back to a random UUID | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 113 |
| RC-17 | MYPY_PATHS gate value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-18 | VULTURE_PATHS gate value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RC-19 | PYDOCSTYLE_PATHS gate value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| RC-20 | INTERROGATE_PATHS gate value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RC-21 | Test quality gate row in the quality gates guide | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 63 |
| RC-22 | Mist OpenAPI YAML on main equals the local copy | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 0 |
| RC-23 | Operation deleteOrgNetwork at path DELETE networks network_id | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 15275 |
| RC-24 | Operation deleteOrgService at path DELETE services service_id | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 18562 |
| RC-25 | Operation deleteOrgGatewayTemplate at path DELETE gatewaytemplates | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9905 |
| RC-26 | Operation deleteOrgDeviceProfile (out of scope) | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 8140 |
| RC-27 | Operation unassignOrgDeviceProfile at path POST unassign with mac_addresses body | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 8399 |
| RC-28 | Schema mac_addresses_macs requires one item and unique items | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 84079 |
| RC-29 | Operation updateSiteInfo request body uses the site schema | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 26026 |
| RC-30 | Schema site declares sitetemplate_id in UUID format | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 100596 |
| RC-31 | Update Site assigns a site template through sitetemplate_id | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 20349 |
| RC-32 | Site example shows sitetemplate_id null | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 56559 |
| RC-33 | Operation deleteOrgServicePolicy exists (out of scope) | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 18413 |
| RC-34 | Live contract has no site template operation | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | absent | 0 |
| RC-35 | Live contract has no network template operation | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | absent | 0 |
| RC-36 | Live contract lists deleteOrgGatewayTemplate | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 63 |
| RC-37 | Live contract lists unassignOrgDeviceProfile | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 68 |
| RC-38 | Live contract warns against automatic site template clearing | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 105 |
| RC-39 | Live T025 names the contract test path | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 90 |
| RC-40 | Live T026 names routes.py | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 91 |
| RC-41 | Live FR-024 requires two confirmations and the typed CONFIRM word | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 130 |
| RC-42 | Live research row C25 for administrative visibility | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 109 |
| RC-43 | Live research row C29 for template and service deletion | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 113 |
| RC-44 | Live research row C30 for site template and device unassignment | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 114 |
| RC-45 | Parent numbered record 4224 exists | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter | main | 2324c91a3e3067c6e0912b76807755fce992e8c1 | present | 0 |
| RC-46 | Route record folder for issue 4645 is absent | specs/numbered/0/0/1/2/2/0/4/0/4645-cisco-converter-administration | main | none | absent | 0 |
| RC-47 | Route ancestor holds three children before this change | specs/numbered/0/0/1/2/2 | main | 69448521ad293f85e5b4fb0703815880f0bcd1a8 | present | 0 |
| RC-48 | AGENTS.md forbids auto-merge for a destructive-operation change | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 230 |
| RC-49 | Copilot instructions require a typed word for destructive operations | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 327 |
| RC-50 | Constitution forbids a direct child in a noncompliant parent | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 43 |
| RC-51 | Backup restoration uses an exact typed word | documentation/backup-restoration.md | main | f256e296c2e24a39f062627efbc531f9bcb0ebd5 | present | 62 |
| RC-52 | data/ is git-ignored | .gitignore | main | 17eadfadb35a59e191a61c78877569ad747ddcc7 | present | 95 |
| RC-53 | Environment template exists for new variables | deploy/.env.example | main | 7137364423308485be734a391798d85c6a37eaf4 | present | 0 |
| RC-54 | Changelog fragment rule exists | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 0 |
| RC-55 | SDK compatibility guard exists | tests/integration/test_mistapi_sdk_compatibility.py | main | cab2d602113012729f6c392dff43197d05913a38 | present | 0 |
| RC-56 | Process folder structure guard exists | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 0 |
| RC-57 | PR 4208 is open and owns the shared portal files | PR 4208 for web_portal/app.py and web_portal/templates/base.html | main | none | present | 0 |
| RC-58 | PR 4596 merged the 33-task map | PR 4596 for specs/live tasks.md | main | none | present | 0 |
| RC-59 | Function deleteOrgNetwork in installed SDK | .venv\Lib\site-packages\mistapi\api\v1\orgs\networks.py | mistapi 0.64.1 installed | none | present | 117 |
| RC-60 | Function deleteOrgService in installed SDK | .venv\Lib\site-packages\mistapi\api\v1\orgs\services.py | mistapi 0.64.1 installed | none | present | 117 |
| RC-61 | Function deleteOrgGatewayTemplate in installed SDK | .venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py | mistapi 0.64.1 installed | none | present | 117 |
| RC-62 | Function deleteOrgDeviceProfile in installed SDK | .venv\Lib\site-packages\mistapi\api\v1\orgs\deviceprofiles.py | mistapi 0.64.1 installed | none | present | 122 |
| RC-63 | Function unassignOrgDeviceProfile in installed SDK | .venv\Lib\site-packages\mistapi\api\v1\orgs\deviceprofiles.py | mistapi 0.64.1 installed | none | present | 214 |
| RC-64 | Function updateSiteInfo in installed SDK | .venv\Lib\site-packages\mistapi\api\v1\sites\sites.py | mistapi 0.64.1 installed | none | present | 67 |
| RC-65 | Function deleteOrgServicePolicy in installed SDK (out of scope) | .venv\Lib\site-packages\mistapi\api\v1\orgs\servicepolicies.py | mistapi 0.64.1 installed | none | present | 117 |
| RC-66 | Function getOrgNetwork for read-back in installed SDK | .venv\Lib\site-packages\mistapi\api\v1\orgs\networks.py | mistapi 0.64.1 installed | none | present | 89 |
| RC-67 | Function getOrgService for read-back in installed SDK | .venv\Lib\site-packages\mistapi\api\v1\orgs\services.py | mistapi 0.64.1 installed | none | present | 89 |
| RC-68 | Function getOrgGatewayTemplate for read-back in installed SDK | .venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py | mistapi 0.64.1 installed | none | present | 89 |
| RC-69 | Function getOrgDeviceProfile for read-back in installed SDK | .venv\Lib\site-packages\mistapi\api\v1\orgs\deviceprofiles.py | mistapi 0.64.1 installed | none | present | 94 |
| RC-70 | Function listOrgNetworkTemplates for reference reads in installed SDK | .venv\Lib\site-packages\mistapi\api\v1\orgs\networktemplates.py | mistapi 0.64.1 installed | none | present | 17 |
| RC-71 | Live contract has no site information read | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | absent | 0 |
| RC-72 | Changelog fragment policy guard exists | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |

Notes on the table:

- RC-01 to RC-05 read the remote file body. The line numbers come from that body.
- RC-22 compares the local OpenAPI hash with the remote blob. Both equal `b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14`. Lines RC-23 to RC-33 come from the local copy and apply to `main`.
- RC-34 to RC-44 read the remote file bodies of the live record. RC-34 and RC-35 are absence checks. Their search terms return no match in the remote contract body.
- RC-57 and RC-58 record pull request state from `gh pr view`.
- RC-59 to RC-70 read the installed SDK. The SDK is not in the repository tree, so the record cites the local path only.

## Sources

| Source | Local path or URL | Used for |
| --- | --- | --- |
| Repository agent rules | `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md` | Rules for gates, safety, structure, and records |
| Spec Kit templates | `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md` | Section headings for the record |
| Parent record | `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter` (RC-45) | Program context and the 4224 converter scope |
| Reference record | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv` (local copy only, not a remote claim) | Shape and depth of the record only. No content was copied. |
| Full-parity record | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity` (RC-34 to RC-44) | Tasks T025, T026, comparison rows C25, C29, C30, and the live contract |
| Mist OpenAPI | `documentation/mist-api-openapi31yaml.yaml` (RC-22 to RC-33) | Endpoint behavior and schema text |
| Installed SDK | `.venv\Lib\site-packages\mistapi` (RC-59 to RC-70) | Function names, signatures, and line numbers |
| Portal source | `src/interfaces/portals/cisco_config_converter/routes.py`, `models.py` (RC-01 to RC-06) | Current blueprint, CSRF guard, and session approval |
| Portal shared code | `web_portal/app.py`, `web_portal/services/config.py` (RC-15, RC-16) | Registration absence and the secret-key fallback |
| Gate configuration | `.github/workflows/ci.yml` (RC-17 to RC-20) | Gate path values for the local gate commands |
| Gate guide | `documentation/quality-gates.md` (RC-21) | Test quality gate definition |
| Destructive pattern | `documentation/backup-restoration.md` (RC-51) | Exact typed word and verified backup pattern |
| Operator guide | `documentation/operator-guide.md` | Context only. No claim in this record depends on it. |
| Architecture guide | `documentation/architecture.md` | Context only. No claim in this record depends on it. |
| Container guide | `documentation/container-deployment.md` | Context only. No container starts in this record. |
| Issue 4645 | `gh issue view 4645 -R jmorrison-juniper/MistHelper`, https://github.com/jmorrison-juniper/MistHelper/issues/4645 | Requirements, labels, and the comment dated 2026-11-10 |
| Issue 4634 | https://github.com/jmorrison-juniper/MistHelper/issues/4634 (three comments, read with `gh issue view`) | API evidence status and the `deleteOrgServicePolicy` question |
| Issue 4633 | https://github.com/jmorrison-juniper/MistHelper/issues/4633 (three comments, read with `gh issue view`) | Coordinator decision on offline scope and shared-file owners |
| Issue 4636 draft | `C:\Users\jmorrison\.copilot\session-state\30878eb1-80d0-451d-bd0c-0b3624089852\files\spec-drafts\4636\design\research.md` (local draft, not committed) | Decisions D-2, D-6, D-7, D-8, D-9, D-10, and the state type names |
| PR 4208 | https://github.com/jmorrison-juniper/MistHelper/pull/4208 (state read with `gh pr view`) | Shared file ownership |
| PR 4596 | https://github.com/jmorrison-juniper/MistHelper/pull/4596 (merged 2026-11-13, read with `gh pr view`) | Source of the 33-task map |

No web source was fetched for this record. No upstream check is recorded.

## Unverified

Each item below remains unverified. Each item names the reason. A task in `tasks.md` or an open item in `analysis.md` owns it.

| ID | Unverified item | Reason | Owner |
| --- | --- | --- | --- |
| UV-01 | Reference fields that link a gateway template, a network, or a service to a site or a device | No contract row names them. | Issue 4634, task T003 |
| UV-02 | Mist behavior when a referenced network or service is deleted | The OpenAPI descriptions in RC-23 and RC-25 do not state it. | Issue 4634, task T003 |
| UV-03 | Response bodies and 5xx behavior for each delete and unassign call | The OpenAPI lists 200 to 429 only (issue 4634 comment dated 2026-11-10). | Issue 4634, task T003 |
| UV-04 | Whether `unassignOrgDeviceProfile` accepts a subset of assigned MAC addresses without side effects on other devices | No fixture exists. | Issue 4634, task T003 |
| UV-05 | Whether `updateSiteInfo` accepts a null `sitetemplate_id` and changes no other field | The site schema in RC-30 defines no null value. The example in RC-32 shows null for a site with no template. | Owner decision D-3 and issue 4634 |
| UV-06 | A read that maps each MAC address to a device identifier for read-back | The live inventory has no MAC lookup row. | Issue 4634, task T003 |
| UV-07 | Whether a 429 response proves that no change occurred | The OpenAPI describes no write semantics for 429. The design uses read-back instead (D-12). | Issue 4634, task T003 |
| UV-08 | Availability of an operator identity provider | The repository holds no provider (issue 4636 decision D-10). | Owner decision D-1 |
| UV-09 | Pagination completeness of reference lists | No fixture exists. | Issue 4634, task T003 |
| UV-10 | Deployed values of `CISCO_CONVERTER_ADMIN_MODE` and `CISCO_CONVERTER_ADMIN_FAMILIES` | No deployment data was read. The record does not claim any value. | Owner, outside this record |
| UV-11 | Whether issue 4643 stores the complete prior state in each backup manifest | Issue 4643 has no draft record yet. | Issue 4643 owner |
| UV-12 | Whether `symbol-diff` reports an added class as a change | The tool was not run. | Task T-LOCAL-GATES |
| UV-13 | The image revision label key for constitution step 11 | The label key was not verified in a repository file. | Task T-MERGE |
