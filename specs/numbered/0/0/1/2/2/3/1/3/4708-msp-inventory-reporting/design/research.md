# Research: MSP inventory batch coverage

## Method

- The remote tree came from one call to `repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`. The response reported `truncated` as false and 11,404 entries.
- Step 3 search: no folder in the working tree `specs` starts with `4708-`. The legacy record exists only in local commit `eaae12d3`, and that commit does not reach `main` (R-03, R-04, R-06, R-11). All nine files of that legacy folder and its changelog fragment were read.
- Source bodies came from the contents endpoint with the ref set to main. Each body was decoded in memory. Each line number below comes from the decoded text.
- For each file that this record cites, the local index blob equals the remote blob. The local line numbers therefore equal the remote line numbers.
- The pinned mistapi files come from `.venv\Lib\site-packages\mistapi`. They are local evidence, and the table marks them as such.

## Decisions

### D-1 Count successful results as the processed count

- Chosen: Count the entries in `collected` after the per-organization runner returns. Recommended.
- Alternatives: (a) Count organization records, which is the defect at line 516. (b) Count runner calls, including failures. Rejected, because a failure would count as processed.
- Reason: The issue defines processed as processed successfully.
- Risk: A runner that returns empty lists counts as successful. Test T-F covers this case.

### D-2 Print a successful total and a skipped or failed total

- Chosen: Print two totals in the footer. Print the cause on each skipped record line. Recommended.
- Alternatives: (a) Print three totals, for successful, skipped, and failed. Rejected, because the issue asks for two groups, and a third total adds output.
- Reason: The operator sees the split by record, and the footer stays short.
- Risk: The footer does not separate skipped records from failed records. Each console line names the cause.

### D-3 Keep the complete footer unchanged

- Chosen: A complete batch keeps `MSP inventory summary complete. Processed N organizations.` A partial batch prints a new partial footer. Recommended.
- Alternatives: (a) Use one new footer for every batch, as the legacy repair does. Rejected, because the owner asks to preserve successful batch behavior (comment IC_kwDOQltU8c8AAAABkerCbA).
- Reason: The output of a complete batch stays the same.
- Risk: Two footer formats exist. The contract in `design/contracts/console.md` lists both.

### D-4 Use a precise partial heading label

- Chosen: A complete batch uses `All Orgs`. A partial batch uses `Partial: S successful, E skipped or failed`. Recommended.
- Alternatives: (a) Use `(S of T Orgs)`. Rejected, because the reader cannot see that records were excluded. (b) Use the legacy text. This choice matches the legacy wording, and the record adopts it.
- Reason: The label gives both counts and the excluded state.
- Risk: The heading is longer. The console width holds it on a standard terminal.

### D-5 Mark partial export names

- Chosen: A partial batch uses the prefix `MSP_{name}_Partial`. A complete batch keeps the prefix `MSP_{name}`. Recommended.
- Alternatives: (a) Change only the console label, as the legacy repair does. Rejected, because the CSV file on disk still names the full MSP report. (b) Skip the combined exports for a partial batch. Rejected, because it discards valid organization data, and the issue asks to preserve that processing.
- Reason: A partial export cannot pass as a complete report.
- Risk: A consumer that matches names exactly must match both forms. The export contract lists both forms.

### D-6 Keep the two-result threshold

- Chosen: Combined reports need at least two successful results, as before. Recommended.
- Alternatives: Change the threshold to one result. Rejected, because the change would alter complete-batch report behavior.
- Reason: The owner asks to preserve combined-report behavior.
- Risk: A batch with one successful result writes no combined report. This behavior exists today.

### D-7 Append tests and keep existing test lines

- Chosen: Append the fixture and eight tests at the end of `tests/unit/inventory/test_org_device_inventory_msp.py`. Add default arguments to the renderers, so the existing calls stay valid. Recommended.
- Alternatives: (a) Edit the existing tests. Rejected, because the baseline file holds 30 lines that name this module, and line shifts create false new findings. (b) Create a new test module. Rejected, because the owner reserves the existing file for this issue.
- Reason: The test-quality baseline keeps its positions.
- Risk: The default arguments hide a missed call site. The new tests call every renderer with an explicit label.

### D-8 Rebuild the repair from main, and keep the legacy record as reference

- Chosen: Reuse the route and the slug `msp-inventory-reporting`. Start the branch from `main`. Do not cherry-pick the legacy commits. Recommended.
- Alternatives: (a) Cherry-pick `5b25a48e` and `eaae12d3`. Rejected, because the legacy record carries the Python 3.13 claim, a stale baseline, a changed complete footer, and unverified evidence. (b) Use a new slug. Rejected, because two records under one route create an ambiguous path.
- Reason: The legacy record and this record share one route and one slug, so the final record replaces the legacy path.
- Risk: The owner may publish the legacy branch later. Both branches would then touch the same path. Decision D-9 keeps publication on hold.

### D-9 Hold publication and merge for owner authorization

- HUMAN-DECISION-REQUIRED. Category: product priority (release timing).
- Chosen: Hold each push, pull request, and merge until the owner authorizes it. Recommended.
- Alternatives: (a) Publish now. Rejected, because comments IC_kwDOQltU8c8AAAABkerCbA and IC_kwDOQltU8c8AAAABkfIWFg say not to push, open a pull request, or merge without authorization. (b) Publish the legacy branch instead. Rejected, because it carries the defects in D-8.
- Reason: The owner keeps control of the release timing and names the outstanding decision.
- Risk: The fix waits. The owner must name the outstanding decision in comment IC_kwDOQltU8c8AAAABkfIWFg before authorization.

### D-10 Keep the existing labels

- Chosen: Keep `bug`, `tests`, and `in-progress` on issue #4708. Add no label. Recommended.
- Alternatives: Add `docs` for this record. Rejected, because this record is not user documentation, and the scope label set names no spec label.
- Reason: The issue already carries one type label and one scope label.
- Risk: None identified.

### D-11 Keep the adjacent findings out of scope

- Chosen: Keep the paging question (AN-10), the error path (AN-11), and the five-item debt (AN-13) out of this change. Name separate issues for each. Recommended.
- Alternatives: Include one of the three in this change. Rejected, because each finding needs its own live or structural evidence, and the rules require one concern for each issue.
- Reason: The change stays small, and each finding gets its own review.
- Risk: The paging gap remains open until its issue closes.

## Remote Verification

Result values are `present`, `absent`, `partial`, or `stale`. A legacy row is a claim that the legacy record makes. A partial result means that the object exists, but main does not contain it. A stale result means that the claim matches an old revision or an old text.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| R-01 | Legacy: baseline commit 3964d21d is the current main | commits/3964d21d03f9f5717cb8eafb7272ecff21f5362a | main | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | stale | 0 |
| R-02 | Current main ref is f03c6c9b | git/ref/heads/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R-03 | Legacy: commit 5b25a48e exists on GitHub | commits/5b25a48e6b1aef2529e3b68204fd7948fe8656ab | main | 5b25a48e6b1aef2529e3b68204fd7948fe8656ab | present | 0 |
| R-04 | Legacy: commit eaae12d3 exists on GitHub | commits/eaae12d3bc3d869cef710489625f8901f7c7e866 | main | eaae12d3bc3d869cef710489625f8901f7c7e866 | present | 0 |
| R-05 | Legacy: commit 5b25a48e is in main history | compare endpoint, base main, head 5b25a48e6b1aef2529e3b68204fd7948fe8656ab | main | 5b25a48e6b1aef2529e3b68204fd7948fe8656ab | absent | 0 |
| R-06 | Legacy: commit eaae12d3 is in main history | compare endpoint, base main, head eaae12d3bc3d869cef710489625f8901f7c7e866 | main | eaae12d3bc3d869cef710489625f8901f7c7e866 | absent | 0 |
| R-07 | Legacy: repair source blob 03f47053 is the main source file | src/mist/resources/inventory/org_device_inventory_msp.py | main | 36523c13a48d17580310ac4fc3d69efbe88a2dad | absent | 0 |
| R-08 | Owner comment: repair source blob 03f47053 exists on GitHub | git/blobs/03f47053dd847f5f3c1f8836dfd6dd43cd422654 | main | 03f47053dd847f5f3c1f8836dfd6dd43cd422654 | partial | 0 |
| R-09 | Legacy: follow-up test blob 841d9397 exists on GitHub | git/blobs/841d9397b48a13138dea65278a6f76ced8e904d1 | main | 841d9397b48a13138dea65278a6f76ced8e904d1 | absent | 0 |
| R-10 | Legacy: follow-up test blob 841d9397 exists in the local object store | local git object store | local-object-store | 841d9397b48a13138dea65278a6f76ced8e904d1 | absent | 0 |
| R-11 | Legacy: record folder exists on main | specs/numbered/0/0/1/2/2/3/1/3/4708-msp-inventory-reporting | main | none | absent | 0 |
| R-12 | Legacy: changelog fragment exists on main | changelog.d/issue-4708-msp-inventory-reporting.md | main | none | absent | 0 |
| R-13 | Legacy: plan requires Python 3.13 or newer, but the repository requires 3.15 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | stale | 23 |
| R-14 | Footer prints the organization record count on main | src/mist/resources/inventory/org_device_inventory_msp.py | main | 36523c13a48d17580310ac4fc3d69efbe88a2dad | present | 516 |
| R-15 | Skipped-record warning exists on main | src/mist/resources/inventory/org_device_inventory_msp.py | main | 36523c13a48d17580310ac4fc3d69efbe88a2dad | present | 480 |
| R-16 | Runner failure log exists on main | src/mist/resources/inventory/org_device_inventory_msp.py | main | 36523c13a48d17580310ac4fc3d69efbe88a2dad | present | 466 |
| R-17 | Combined model heading is fixed to All Orgs on main | src/mist/resources/inventory/org_device_inventory_msp.py | main | 36523c13a48d17580310ac4fc3d69efbe88a2dad | present | 190 |
| R-18 | Batch calls listMspOrgs once on main | src/mist/resources/inventory/org_device_inventory_msp.py | main | 36523c13a48d17580310ac4fc3d69efbe88a2dad | present | 135 |
| R-19 | Batch entry execute_msp exists on main | src/mist/resources/inventory/org_device_inventory_msp.py | main | 36523c13a48d17580310ac4fc3d69efbe88a2dad | present | 502 |
| R-20 | Test module exists on main | tests/unit/inventory/test_org_device_inventory_msp.py | main | 44475247c7b7182468ecad7cc69ab2fdd611a677 | present | 0 |
| R-21 | Existing batch test starts at line 135 on main | tests/unit/inventory/test_org_device_inventory_msp.py | main | 44475247c7b7182468ecad7cc69ab2fdd611a677 | present | 135 |
| R-22 | Facade binds execute_msp for the batch on main | src/mist/resources/inventory/org_device_inventory_summary_facade.py | main | 9f3549a47a941287968a9f9fff5cb163a62c75a9 | present | 82 |
| R-23 | Menu 13 registers the dispatch handler on main | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6391 |
| R-24 | Per-organization runner run_for_org exists on main | src/mist/resources/inventory/org_device_inventory_summary.py | main | 420fea3ba9b44bf3ead90da400be2c0ac003f2ed | present | 425 |
| R-25 | Changelog rule names issue-number fragments on main | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 26 |
| R-26 | Route algorithm uses base 5 on main | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R-27 | Destination check rejects a parent with five children on main | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 93 |
| R-28 | MYPY_PATHS includes src/ and MistHelper.py on main | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-29 | Pylint threshold is 9.5 on main | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 122 |
| R-30 | Task audit is advisory on main | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 750 |
| R-31 | Local gates table exists on main | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R-32 | Constitution requires action logging on main | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R-33 | Operator guide says msp grants follow each page | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | stale | 606 |
| R-34 | OpenAPI lists GET /api/v1/msps/{msp_id}/orgs as listMspOrgs | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 4081 |
| R-35 | OpenAPI org_list is an array of org objects | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 89182 |
| R-36 | Reference record 4920 spec exists on main | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| R-37 | Pinned mistapi listMspOrgs signature (local file) | .venv\Lib\site-packages\mistapi\api\v1\msps\orgs.py | local-venv | not applicable | present | 17 |
| R-38 | Pinned mistapi mist_get fetches every page (local file) | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | not applicable | absent | 260 |
| R-39 | Final record folder exists on main | specs/numbered/0/0/1/2/2/3/1/3/4708-msp-inventory-reporting | main | none | absent | 0 |

Summary of legacy rows: R-01, R-03, R-04, R-05, R-06, R-07, R-09, R-10, R-11, R-12, and R-13 are legacy claims. Eleven legacy claims give two verified, two stale, and seven absent results.

## Sources

Local paths, sections, and line ranges:

- `AGENTS.md`, section Writing style, at line 40.
- `AGENTS.md`, section Structure, at line 77.
- `AGENTS.md`, section Action logging, at line 104.
- `AGENTS.md`, section Input and data, at line 117.
- `AGENTS.md`, section Tests, at line 133.
- `AGENTS.md`, section Git flow, at line 179.
- `AGENTS.md`, section Pull request, at line 221.
- `AGENTS.md`, section Specifications, at line 345.
- `.github/copilot-instructions.md`, section Local gates, at line 50.
- `.github/copilot-instructions.md`, section Test quality ratchet, at line 95.
- `.github/copilot-instructions.md`, the rule for new Spec Kit records, at line 159.
- `.github/copilot-instructions.md`, section Safety in this repository, at line 309.
- `.github/copilot-instructions.md`, section Containers and ports, at line 354.
- `.github/copilot-instructions.md`, the changelog rule, at line 451.
- `.github/copilot-instructions.md`, the menu categories table, which lists menu 13 in the `safe` category.
- `.specify/memory/constitution.md`, Principle I, at line 38.
- `.specify/memory/constitution.md`, Principle II, at line 91.
- `.specify/memory/constitution.md`, Principle III, at line 113.
- `.specify/memory/constitution.md`, Principle IV, at line 143.
- `.specify/memory/constitution.md`, Principle V, at line 182.
- `.specify/memory/constitution.md`, Principle VI, at line 204.
- `.specify/memory/constitution.md`, Principle VII, at line 235.
- `.specify/memory/constitution.md`, section Testing, at line 361.
- `.specify/memory/constitution.md`, section Documentation, at line 398.
- `.specify/memory/constitution.md`, section SpecKit escalation, at line 420.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`: followed for headings and layout.
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`: read for the shape of the headings, which appear in spec, plan, tasks, analysis, research, data model, quickstart, contracts, and checklists. No text was copied.
- `documentation/quality-gates.md`, `documentation/architecture.md`, `documentation/development-setup.md`, and `documentation/container-deployment.md`: read. The container page applies only when a test starts a container, and this change starts none.
- `documentation/operator-guide.md` lines 428-452 and 560-622: read for the MSP scope lines and the grant table (line 606).
- `documentation/mist-api-openapi31yaml.yaml` line 4081 (path `/api/v1/msps/{msp_id}/orgs`), line 64453 (response `OrgsArray`), line 88841 (`org` field `id`), line 88865 (`org` field `name`), and lines 89182-89186 (`org_list`).
- `documentation/menu-api/safe.md` line 215: maps the GET operation to `msps.orgs.listMspOrgs` and `_call_list_msp_orgs`.
- `.venv\Lib\site-packages\mistapi\api\v1\msps\orgs.py` lines 17, 36, and 38: `listMspOrgs` and the single `mist_get` call.
- `.venv\Lib\site-packages\mistapi\__api_request.py` lines 203-258 and 260-277: the retry loop covers HTTP 429 only. `mist_get` makes one request.
- `.venv\Lib\site-packages\mistapi\__api_response.py` lines 39-41 and 72-95: `data` and `next` fields. `next` records a value, and no code follows it.
- `.venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA` lines 3 and 18: version 0.64.1 and `Requires-Python >=3.10`.
- Git history, local commit `5b25a48e6`. Its subject is `fix(inventory): report accurate MSP batch coverage`.
- Git history, local commit `eaae12d3b`. Its subject is `test(inventory): preserve existing test baseline locations`.
- Git history, the legacy record stored in commit `eaae12d3`.

Remote sources: the issue body and comments from `gh issue view 4708`, and the `main` checks in the table above.

No URL was fetched. No `web_fetch` call was made.

## Unverified

- U-01: The legacy record states local test counts, including 55 passing tests and a 1,124-test snapshot. The reason is that these runs occurred outside this repository, and the author rules forbid running tests.
- U-02: The content of the follow-up test blob `841d9397`. The reason is that GitHub returns HTTP 404 (R-09), and the local object store lacks the blob (R-10).
- U-03: The owner claim that 27 pull request head IDs were rechecked. The reason is that `gh pr list --search 4708` returns no pull request, and no tracked file lists the IDs.
- U-04: The outstanding decision named in comment IC_kwDOQltU8c8AAAABkfIWFg. The reason is that the issue does not state its text.
- U-05: The live paging behavior of `listMspOrgs`. The reason is that the author rules forbid live calls. The OpenAPI operation lists no page or limit parameter (R-34), and the tool makes one call (R-18).
- U-06: The legacy claim of a Python 3.14 local environment. The reason is that the claim cannot be checked, and the repository requires 3.15 (R-13).
- U-07: Hosted CI results for `5b25a48e` and `eaae12d3`. The reason is that no pull request exists for either commit.
- U-08: The legacy claim that the branch-creation hook was not run. The reason is that the claim describes a session event, and the repository holds no record of it.

## Skills

No skill was loaded. The issue touches no Podman behavior and no Juniper device behavior. The skill domains in the catalog do not cover MSP inventory batch code.
