# Research: Organization Invites Export Handles a Missing mistapi Function

Facts come from GitHub main. The `gh api` reads return blob SHAs and file text, and each claim cites a path and a line range. A local file counts as evidence only when its Git blob SHA equals the GitHub main blob SHA (RV-45). Local Git history was read with read-only commands.

## Issue Facts

- Issue #4825 is OPEN. It was created and last updated on 2026-11-17T23:00:48Z. The author is `jmorrison-juniper`. The labels are `bug` and `MistHelper.py`. The issue has no comments.
- The issue names base commit `b7a18b7ead7b1de5882bcd288203c015b1eef792` and a locked mistapi 0.64.x environment. The base commit exists on GitHub (RV-03).
- The issue states that `OrgExportUtils._invites` accesses `mistapi.api.v1.orgs.invites.listOrgInvites`, and that the installed SDK has no such member. No production operation ran.
- The issue requires this: "Determine the supported invitation export endpoint before changing the implementation." Decision D-1 answers it.
- The issue reproduction steps are: bootstrap the locked environment, run the introspection command, and examine `_invites`. The quickstart repeats them in Step 1.
- The issue error text is `E1101: Module 'mistapi.api.v1.orgs.invites' has no 'listOrgInvites' member (no-member)`. The same log lists `listOrgInvites available: False` and the three SDK callables. The log line number is Unverified item U-2.
- The issue reports a changed-source Pylint score of 9.74 out of 10. This value is Unverified (U-1).
- Linked pull request #4829, titled `fix(export): skip org invites export when SDK call is missing`, is MERGED at 2026-11-19T05:14:25Z. Its merge commit is `0686430755be0025c8c78f764a4e471a29274803`. Its head is `a90ac84837602869eb4e54f37948cd925942d833` on branch `fix/4825-org-invites`. Its base is `b6347ec7374c2a3c1c8ba1f2482aed52cbc81fe6`.
- Pull request #4829 changed seven files. The list includes `src/operations/exporting/export/org_export_utils.py` (+15 -2) and `tests/unit/export/test_org_export_utils.py` (+19 -10).
- Pull request #4829 reports SUCCESS for its checks. Its auto-merge jobs report SKIPPED or SUCCESS.
- Related issue #4758, "Pylance: correct entry point type diagnostics", is CLOSED at 2026-11-19T23:49:00Z. It found this defect. It is related, not a dependency.
- Seven pull requests are open. None touches the target files (RV-44).

## Root Cause

- The string `listOrgInvites` first appears in the initial commit `1d00b0495` (2025-12-09). The `-S` search found it in that commit (read only).
- Commit `02c984253` (2026-07-08) moved the call out of `MistHelper.py` and into `org_export_utils.py` in the retired `export` package at the source root. Its diff shows both sides (read only).
- Commit `025ef82ee` (2026-10-04) renamed the file to `src/operations/exporting/export/org_export_utils.py` with similarity 98 percent.
- Commit `c3b97113a` (2026-03-07) added documentation that names `listOrgInvites`. Specification 009 keeps that mention at RV-37.
- No mistapi tag from v0.62.0 to v0.64.2 defines the function (RV-24). The call was never backed by a released SDK function.

## Decisions

### D-1. No supported endpoint or function lists organization admin invites

- **Decision**: Keep the guard. Do not call another resource for invites.
- **Rationale**: The four local OpenAPI files define POST only on the invites path (RV-25 to RV-28). The HTML reference lists no GET (RV-29). The installed invites module defines three callables (RV-22). Upstream tags v0.62.0 to v0.64.2 match (RV-24).
- **Alternatives considered**:
  - Raw HTTP GET to an undocumented path. Rejected. The constitution names mistapi the sole interface for Mist REST APIs. The WebSocket exception does not allow direct HTTP. No local source documents this path.
  - `listOrgAdmins`, installed `orgs/admins.py` lines 17 and 36 (RV-47). Rejected. Its description lists administrators with privileges, not pending invites (RV-25).
  - `listSdkInvites` and `listOrgMarvisClientInvites`. Rejected. They read SDK onboarding invites and Marvis client profiles (RV-30, RV-31).
- **Risk**: A later mistapi release adds the function. Mitigation: plan Risks table.

### D-2. The absent path logs one ERROR and writes no file

- **Decision**: Log one ERROR record. Write no `OrgInvites.csv`. Raise no exception.
- **Rationale**: An empty file reads as zero invites. The module docstring states this at GitHub main lines 719 to 724. The shared export writes a file only on success.
- **Alternatives considered**:
  - Write an empty `OrgInvites.csv`. Rejected. Caution: The file would report a false zero of invites.
  - Raise an exception. Rejected. It stops the other organization exports.
  - Write a marker file. Rejected. It creates a new output contract.
- **Risk**: An operator misses the error. Mitigation: the ERROR level and the fixed text that names the file.

### D-3. Keep `_invites` and its tests

- **Decision**: Keep the method and its two tests. Record that no caller exists on main.
- **Rationale**: Code search and local search find no caller (RV-35, RV-36). Removal widens the change and removes a documented method. A separate issue decides on removal.
- **Alternatives considered**: Delete the method and its tests now. Rejected. It changes scope beyond the runtime defect.
- **Risk**: Dead code remains. Mitigation: a follow-up issue, listed in analysis item A-19.

### D-4. Use `getattr` with a default of `None` for the guard

- **Decision**: Keep `getattr(mistapi.api.v1.orgs.invites, "listOrgInvites", None)` (RV-01).
- **Rationale**: The lookup runs once. It returns `None` for a missing name. The export never reaches a direct attribute read.
- **Alternatives considered**:
  - `try` with `except AttributeError`. Rejected. It catches more than the one lookup.
  - `hasattr`, then a direct read. Rejected. It performs two lookups for one name.
- **Risk**: A renamed function is skipped, not followed. The ERROR record makes the skip visible.

### D-5. Keep the mistapi pin. Do not move to v0.64.2

- **Decision**: Keep `mistapi>=0.64.1,<0.65` in `pyproject.toml` and `mistapi==0.64.1` in `requirements.txt` (RV-15, RV-17).
- **Rationale**: The v0.64.2 invites module has the same blob as v0.64.1 (RV-24). A pin move adds no function.
- **Alternatives considered**: Move to v0.64.2. Rejected. It adds nothing for this defect. Widen the upper bound. Rejected. It is outside this issue.
- **Risk**: None for this change.

### D-6. Add the logs, the comments, and the return type to `_invites`

- **Decision**: Add an INFO record before the shared export call and a DEBUG record after it. Add inline comments to changed and adjacent uncommented lines. Declare `-> None`.
- **Rationale**: The constitution applies these rules to each touched function (constitution Principles VI and VII). Pull request #4829 touched `_invites` and left the gaps (RV-41 to RV-43).
- **Alternatives considered**:
  - Leave the function as it is. Rejected. The constitution says such code must not merge.
  - Add the logs to `export_data`. Rejected. About 20 call sites in `org_export_utils.py` would change behavior.
- **Risk**: The new INFO line repeats the start message of `export_data` (line 61). The text names the invites export, so the two messages differ.

### D-7. Keep the existing `# type: ignore[no-untyped-call]` on the shared export call

- **Decision**: Keep the suppression on line 733. Track the module-wide pattern in a follow-up issue.
- **Rationale**: The same comment appears on about 20 calls in the module. Removal needs a typed shared export and a mypy run. This change adds no suppression.
- **Alternatives considered**: Remove the suppression now. Rejected. Mypy was not run for this record, and the cause is unverified (Unverified item U-5).
- **Risk**: The suppression hides a real typing issue. Mitigation: the follow-up issue.

### D-8. Remove the wrong list-endpoint entries from three invites pages

- **Decision**: Remove the wrong Related Endpoints entry from three pages. The entry names `GET_orgs_org_id_invites.md`. The pages are the DELETE page (line 68), the POST page (line 296), and the PUT page (line 295).
- **Rationale**: The file `GET_orgs_org_id_invites.md` does not exist in `documentation/api/orgs/`. The link target is the POST page (RV-08 to RV-10). No list endpoint exists (D-1). The generator writes a placeholder in that section (`scripts/generate_api_docs.py` lines 372 and 373, and 607 and 608, local), so the list came from manual enrichment. The generator skips enriched pages (RV-32).
- **Alternatives considered**:
  - Add a GET page. Rejected. No endpoint exists.
  - Change the generator. Rejected. The generator writes only placeholder text.
  - Leave the entries. Rejected. They name an endpoint that does not exist.
- **Risk**: None for the links. The markdown link guard still passes, because the remaining links resolve.

### D-9. No primary key strategy for `listOrgInvites` now

- **Decision**: Add no entry to `ENDPOINT_PRIMARY_KEY_STRATEGIES` for `listOrgInvites`.
- **Rationale**: The local OpenAPI files define no list response for organization invites. The invite schemas are `admin_invite` for registration, `sdk_invite_sms`, `sdkinvite`, and `sdkinvite_list` (RV-25). No natural key can be cited. The absent path writes no row. The default strategy applies to unknown endpoints (RV-34).
- **Alternatives considered**:
  - Key the rows on `email`. Rejected. No cited schema supports this key.
  - Use the default strategy only. Accepted for now. It applies without an entry.
- **Risk**: A future write path uses the default key. Mitigation: plan Risks table, and analysis item A-3.

### D-10. Use a new branch from GitHub main, and keep issue #4825 as the subject

- **Decision**: Create `fix/4825-org-invites-followup` from GitHub main. Keep issue #4825 open as the subject.
- **Rationale**: The branch `fix/4825-org-invites` belongs to pull request #4829, which squash merged (RV-20). AGENTS.md warns that a commit pushed after a squash merge becomes an orphan. Issue #4825 stayed open because the pull request used `Refs`. The defects belong to the same function and the same contract.
- **Alternatives considered**:
  - Reuse `fix/4825-org-invites`. Rejected. Warning: A push after a squash merge creates an orphan pull request that nobody merges.
  - Open a new issue first. The AGENTS.md post-merge rule suggests this. Rejected for this record. The orchestrator can open one before T-PR and change the branch name.
- **Risk**: A reviewer asks for a new issue. Mitigation: the branch name change in T-PR.

### D-11. Add no new changelog fragment

- **Decision**: Keep `changelog.d/issue-4825-org-invites.md` unchanged (RV-11).
- **Rationale**: The changelog README (rule 4) says to add no fragment for an internal-only change. The existing fragment states the user-visible fix.
- **Alternatives considered**: Add `issue-4825-followup.md`. Rejected. It duplicates an entry for a change that users do not see.
- **Risk**: None.

### D-12. Replace the legacy record files in place

- **Decision**: Write this record into `specs/numbered/0/0/1/2/3/3/0/0/4825-org-invites/`, with slug `org-invites`.
- **Rationale**: The slug matches the legacy folder. Two folders for one issue would break the `<ISSUE>-` discovery rule in the brief.
- **Alternatives considered**: Use a new slug. Rejected. It creates a second record for one issue.
- **Risk**: The legacy files remain in git history at commit `0686430`. That history stays available.

### D-13. Strengthen the absent-path test and add a log-order test

- **Decision**: Replace the `any` check with an exact count of one ERROR record. Assert that `export_data` is not called. Add one log-order test (T007 and T008).
- **Rationale**: The current assertion passes with two ERROR records. It does not check the shared export. FR-002 and FR-004 need both checks.
- **Alternatives considered**:
  - Keep the current assertion. Rejected. It does not prove FR-002 or FR-004.
  - Add a new test file. Rejected. The existing test module holds all tests for this method.
- **Risk**: The tests depend on log levels. Mitigation: the tests check levels and the record count only, not the full text.

## Remote Verification Table

Result values: `present`, `absent`, `partial`, or `stale`. `main` means GitHub main at commit `f03c6c9`.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RV-01 | Guard present (`getattr` default `None`, one ERROR, return) | `src/operations/exporting/export/org_export_utils.py` | main | cfe85d09447ec3be6271f2a4cb8e5ea2dac5fb81 | present | 726-732 |
| RV-02 | Shared export keeps `data_type` and `sort_key` | `src/operations/exporting/export/org_export_utils.py` | main | cfe85d09447ec3be6271f2a4cb8e5ea2dac5fb81 | present | 733-734 |
| RV-03 | Base commit calls `listOrgInvites` directly | `src/operations/exporting/export/org_export_utils.py` | b7a18b7ead7b1de5882bcd288203c015b1eef792 | bceef6a0d63449231f75c1323347d37b2d1822cb | present | 714 |
| RV-04 | Absent-path test exists | `tests/unit/export/test_org_export_utils.py` | main | 6ac423a110058e72cbbf6e500c966660da6f3c61 | present | 976-986 |
| RV-05 | Absent-path test asserts one error and no export call | `tests/unit/export/test_org_export_utils.py` | main | 6ac423a110058e72cbbf6e500c966660da6f3c61 | partial | 985-986 |
| RV-06 | Supported-path test exists | `tests/unit/export/test_org_export_utils.py` | main | 6ac423a110058e72cbbf6e500c966660da6f3c61 | present | 963-974 |
| RV-07 | DELETE page cites issue #4825 in MistHelper Notes | `documentation/api/orgs/DELETE_orgs_org_id_invites_invite_id.md` | main | c4823388571abbf21c937f40c3a35edcc1921e52 | present | 71-73 |
| RV-08 | DELETE page names a GET invites list | `documentation/api/orgs/DELETE_orgs_org_id_invites_invite_id.md` | main | c4823388571abbf21c937f40c3a35edcc1921e52 | stale | 68 |
| RV-09 | POST page names a GET invites list | `documentation/api/orgs/POST_orgs_org_id_invites.md` | main | 7024d05f5c7d3808d37357ee04be5e6fe211c589 | stale | 296 |
| RV-10 | PUT page names a GET invites list | `documentation/api/orgs/PUT_orgs_org_id_invites_invite_id.md` | main | 87c932415bf553300652b3ed0bb91cdc22d279b4 | stale | 295 |
| RV-11 | Changelog fragment has one heading and one Fixed bullet | `changelog.d/issue-4825-org-invites.md` | main | 7092b318e80f92fb240ba69ef1bb98c507cd9e6c | present | 1-3 |
| RV-12 | Legacy spec status reads "Local commit ready" | `specs/numbered/0/0/1/2/3/3/0/0/4825-org-invites/spec.md` | main | 16b81350ae9d13fe72183d97e6d09f0b3c284c1c | stale | 7 |
| RV-13 | Legacy tasks leave T015 and T016 open | `specs/numbered/0/0/1/2/3/3/0/0/4825-org-invites/tasks.md` | main | de555112597209234fcbc04f4604040ee718a980 | stale | 43-44 |
| RV-14 | Legacy plan says Python 3.13 or newer | `specs/numbered/0/0/1/2/3/3/0/0/4825-org-invites/plan.md` | main | 2a15320cce1693a0660a021ef4eaf9cde5c083ba | stale | 13 |
| RV-15 | pyproject requires Python 3.15 | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| RV-16 | Legacy lines name `>=0.64.0,<0.65`. The pyproject floor is 0.64.1 | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | stale | 29 |
| RV-17 | requirements.txt pins mistapi 0.64.1 | `requirements.txt` | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| RV-18 | Instruction file names `mistapi>=0.64.0,<0.65` | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | stale | 21 |
| RV-19 | Commit `b2249e25`, which the legacy spec cites | commit `b2249e25` | b2249e25 | none (HTTP 422, no local object) | absent | 0 |
| RV-20 | Pull request #4829 merged as a squash commit | merge commit `0686430755be0025c8c78f764a4e471a29274803` | main | none | present | 0 |
| RV-21 | Pull request #4829 says `Refs #4825`, and issue #4825 stayed open | pull request #4829 and issue #4825 | main | none | present | 0 |
| RV-22 | Installed invites module defines three callables | `src/mistapi/api/v1/orgs/invites.py` upstream, equal to `.venv/Lib/site-packages/mistapi/api/v1/orgs/invites.py` locally | v0.64.2 | 1d30b6661959258973d841ed97de1220a6fb6bd7 | present | 17, 48, 76 |
| RV-23 | Upstream code search finds no `listOrgInvites` | `tmunzer/mistapi_python` code search | default branch | none | absent | 0 |
| RV-24 | Six tags share the invites module with no list function | `src/mistapi/api/v1/orgs/invites.py` | v0.62.0, v0.63.0, v0.63.3, v0.64.0, v0.64.1, v0.64.2 | 1d30b6661959258973d841ed97de1220a6fb6bd7 for each tag | absent | 0 |
| RV-25 | OpenAPI 3.1 JSON defines POST only on the invites path, and GET sdkinvites exists | `documentation/mist-api-openapi31json.json` | main | 5f9f4ce94f812f0e818ee65f99f032118a28f56c | present | 1 (minified JSON) |
| RV-26 | OpenAPI 3.0 JSON defines POST only on the invites path | `documentation/mist-api-openapi3json.json` | main | 8efb60f30b65b8044f86120e5a3ce8f6c306e5d4 | present | 1 (minified JSON) |
| RV-27 | OpenAPI 3.1 YAML defines POST only on the invites path | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 11202-11249 |
| RV-28 | OpenAPI 3.0 YAML defines POST only on the invites path | `documentation/mist-api-openapi3yaml.yaml` | main | f5096e59431c530962887ff501b425146e8ace00 | present | 21777-21950 |
| RV-29 | HTML reference lists POST, PUT, and DELETE for invites and no GET for invites. Line 1333 is the admins GET | `documentation/Org _ API _ Mist.html` | main | 9e1cddd271d3f696e6fab4fc182e2722681d3ba5 | present | 1333, 1514, 1612, 1615 |
| RV-30 | `listSdkInvites` is GET sdkinvites for SDK onboarding | `documentation/api/orgs/GET_orgs_org_id_sdkinvites.md` | main | 1f77d7759f132b820cdcafdc45626b5b759de53d | present | 7, 11 |
| RV-31 | `listOrgMarvisClientInvites` lists Marvis client invites | `documentation/api/orgs/GET_orgs_org_id_marvisinvites.md` | main | 06cbfa9138199c372c0900797f36f5615d048dbf | present | 7, 11 |
| RV-32 | Generator skips a page that has no placeholder text | `scripts/generate_api_docs.py` | main | 444df852b47769047e9e38beb266de93951a05d4 | present | 863-870 |
| RV-33 | No primary key strategy for `listOrgInvites` | `src/foundation/support/refactors/endpoint_primary_key_strategies.py` | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | absent | 0 (`listSdkInvites` at 1326) |
| RV-34 | Unknown endpoints fall back to the default strategy | `src/foundation/persistence/db/database_schema_utils.py` | main | 5374c1b1ffc90e756e15dd19d2ddc4a859c3a6fc | present | 79-85 |
| RV-35 | Code search for `listOrgInvites` finds `src` only in `org_export_utils.py` | GitHub code search, `jmorrison-juniper/MistHelper` | main | none | present | 0 |
| RV-36 | Code search for `_invites` finds no `src` caller besides the definition | GitHub code search, `jmorrison-juniper/MistHelper` | main | none | present | 0 |
| RV-37 | Specification 009 names `listOrgInvites` under `orgs.invites` | `specs/009-api-docs-enrichment/research.md` | main | e7437f8915de79590020274dac84d9de9dc072f4 | stale | 93 |
| RV-38 | CI names the gate paths and the pylint threshold | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93, 101, 104, 107, 122 |
| RV-39 | Markdown link guard exists | `tests/guardrails/test_markdown_links.py` | main | cafefdac69006ddf7544e5a57a101f0f63fbcc38 | present | 1-17 |
| RV-40 | Process folder guard finds `spec.md` and rejects a nested record | `tests/guardrails/test_process_folder_structure.py` | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 39, 58 |
| RV-41 | `_invites` declares no return type | `src/operations/exporting/export/org_export_utils.py` | main | cfe85d09447ec3be6271f2a4cb8e5ea2dac5fb81 | absent | 718 |
| RV-42 | Lines 727, 728, 729, 730, and 734 have no inline comment | `src/operations/exporting/export/org_export_utils.py` | main | cfe85d09447ec3be6271f2a4cb8e5ea2dac5fb81 | absent | 727-734 |
| RV-43 | No INFO record before and no DEBUG record after the shared export call | `src/operations/exporting/export/org_export_utils.py` | main | cfe85d09447ec3be6271f2a4cb8e5ea2dac5fb81 | absent | 733-735 |
| RV-44 | No open pull request touches the target files | GitHub pull request list, open state | main | none | present | 0 |
| RV-45 | Local working tree equals GitHub main for the two changed code files | `git hash-object` locally, compared with RV-01 and RV-04 | main | cfe85d09447ec3be6271f2a4cb8e5ea2dac5fb81 and 6ac423a110058e72cbbf6e500c966660da6f3c61 | present | 0 |
| RV-46 | Installed `sdkinvites` module equals upstream v0.64.2 | `.venv/Lib/site-packages/mistapi/api/v1/orgs/sdkinvites.py` | v0.64.2 | 03f0cd063ad9fc347e940f1a7aa6874f922e79c6 | present | 17, 36 |
| RV-47 | Installed `admins` module equals upstream v0.64.2 | `.venv/Lib/site-packages/mistapi/api/v1/orgs/admins.py` | v0.64.2 | 59d6f2d6cda7cc744e3674d43085c40f93700c96 | present | 17, 36 |

## Legacy Claim Checks

The legacy record has three files: `spec.md`, `plan.md`, and `tasks.md`. Their blob SHAs on main are RV-12, RV-14, and RV-13. Each row names the legacy line.

| ID | Legacy location | Claim | Result | Evidence |
| - | - | - | - | - |
| LC-01 | `spec.md` line 13 | `_invites` reads `listOrgInvites` directly | verified | RV-03 |
| LC-02 | `spec.md` line 13 | The installed mistapi has no such function | verified | RV-22, RV-24 |
| LC-03 | `spec.md` line 13 | The export raises `AttributeError` | verified | RV-03. A module attribute read raises this error in Python. The run is not reproduced (U-1). |
| LC-04 | `spec.md` line 13 | "The work is already committed in commit b2249e25." | absent | RV-19 |
| LC-05 | `spec.md` line 7 | Status reads "Local commit ready. Publication pending." | stale | RV-20, RV-21 |
| LC-06 | `spec.md` FR-001 to FR-006 | Guard and export behavior | verified | RV-01, RV-02 |
| LC-07 | `spec.md` Mist section | SDK has three callables only | verified | RV-22 |
| LC-08 | `spec.md` Mist section | OpenAPI defines POST only | verified | RV-25 to RV-28 |
| LC-09 | `spec.md` Mist section | `listSdkInvites` calls GET `/sdkinvites` | verified | RV-30, RV-46 |
| LC-10 | `spec.md` Mist section | `listSdkInvites` is a different resource | verified | RV-25, RV-30 |
| LC-11 | `spec.md` line 88 | Locked line is `>=0.64.0,<0.65` | stale | RV-16, RV-18 |
| LC-12 | `spec.md` line 88 | Installed version is 0.64.1 | verified | RV-17, RV-22 |
| LC-13 | `spec.md` Assumptions | No menu route runs `_invites` | verified | RV-35, RV-36 |
| LC-14 | `plan.md` line 14 | Locked line is `>=0.64.0,<0.65` | stale | RV-16 |
| LC-15 | `plan.md` line 13 | Python 3.13 or newer is required | stale | RV-14, RV-15 |
| LC-16 | `plan.md` Constitution Check | Title uses Conventional Commits form | verified | RV-20 |
| LC-17 | `plan.md` Constitution Check | Contract tests exist | verified | RV-04, RV-06 |
| LC-18 | `plan.md` Design Decision 1 | Guard uses a default lookup | verified | RV-01 |
| LC-19 | `plan.md` Design Decision 4 | Function returns `None` | verified | RV-01. The return annotation is absent (RV-41), tracked in analysis item A-6. |
| LC-20 | `plan.md` Risks | "The guard handles both cases", add or rename | stale | RV-01. A renamed function is skipped, not followed. |
| LC-21 | `tasks.md` line 14 | T001 evidence is an investigation artifact | stale | RV-13. The cited file is `spec.md`. |
| LC-22 | `tasks.md` T003 to T008 | Delivered code, tests, note, and fragment | verified | RV-01, RV-04, RV-07, RV-11 |
| LC-23 | `tasks.md` lines 43 and 44 | T015 and T016 are open | stale | RV-13, RV-21 |
| LC-24 | `spec.md` SC-001 and `tasks.md` T009 | 96 tests pass | unverified, not counted | U-1 |
| LC-25 | `tasks.md` T011 | 2490 passed and 4 skipped | unverified, not counted | U-1 |
| LC-26 | `tasks.md` T010, T012, T013 | Gate results and STE scores | unverified, not counted | U-1 |

Totals for the STATUS file: 15 verified, 7 stale, and 1 absent. Three claims are unverified and not counted.

## Sources

Local files read, relative to the repository root:

- `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, and the four Spec Kit templates.
- `changelog.d/README.md`, `scripts/generate_api_docs.py`, and `tests/guardrails/test_process_folder_structure.py`.
- `documentation/mist-api-openapi31json.json`, `documentation/mist-api-openapi3json.json`, `documentation/mist-api-openapi31yaml.yaml`, `documentation/mist-api-openapi3yaml.yaml`, and `documentation/Org _ API _ Mist.html`.
- `documentation/api/orgs/DELETE_orgs_org_id_invites_invite_id.md`, `POST_orgs_org_id_invites.md`, `PUT_orgs_org_id_invites_invite_id.md`, `GET_orgs_org_id_sdkinvites.md`, and `GET_orgs_org_id_marvisinvites.md`.
- `src/operations/exporting/export/org_export_utils.py` lines 52 to 80 and 717 to 735.
- `tests/unit/export/test_org_export_utils.py` lines 963 to 986.
- `.venv/Lib/site-packages/mistapi/api/v1/orgs/invites.py`, `sdkinvites.py`, `admins.py`, and `marvisinvites.py`, plus `mistapi-0.64.1.dist-info`.
- `src/foundation/persistence/db/database_schema_utils.py` lines 79 to 94.

GitHub reads, all read only:

- `gh issue view 4825`, `gh issue view 4758`, `gh pr list`, and `gh pr view 4829`.
- `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main` for each path in the table.
- `gh api repos/jmorrison-juniper/MistHelper/commits/<sha>` for each commit in the table.
- `gh api repos/tmunzer/mistapi_python/git/trees/<tag>` and `contents/src/mistapi/api/v1/orgs/invites.py?ref=<tag>` for tags v0.62.0 to v0.64.2. Source repository: https://github.com/tmunzer/mistapi_python.
- Code search with `gh api search/code` for `listOrgInvites` and `_invites`.

Local Git history, read only: `git log -S`, `git log --follow`, `git show --stat`, and `git hash-object`.

No `web_fetch` call was made. No skill was loaded, because the issue concerns the Mist API SDK, not Podman or Juniper device behavior.

Documents read for applicability:

- `documentation/quality-gates.md`: applies. Its section "Run a gate on your own machine" gives the Windows interpreter form.
- `documentation/development-setup.md`: applies. It requires Python 3.15 or newer and gives the `.venv` paths.
- `documentation/architecture.md`, `documentation/container-deployment.md`, and `documentation/operator-guide.md`: not applicable. A text search found no mention of the invites export.
- `documentation/MIST_API_GET_ENDPOINTS.md` and `documentation/MIST_API_MISSING_ENDPOINTS.md`: they list Marvis invite endpoints (lines 654 and 632) and SDK invite endpoints (lines 775 and 748). They list no organization admin invite GET endpoint.
- Reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`: read for shape only. No content was copied.

## Unverified

- U-1. The test runs and gate results in the legacy record. The brief forbids test and gate runs for this task. The 96-pass, 2490-pass, STE-score, and pylint-score values are not reproduced.
- U-2. The issue log line 721. The base commit `b7a18b7` places the call at line 714 (RV-03). The working tree that produced the log is not available.
- U-3. Live Mist cloud behavior for an invites GET request. No live request was made. The local sources define no such endpoint.
- U-4. mistapi releases after v0.64.2. Only tags up to v0.64.2 were read.
- U-5. Whether the `# type: ignore[no-untyped-call]` comments are still needed. Mypy was not run.
- U-6. The output path inside the shared export for the supported path. The backend path was not traced.
- U-7. The author's reason for the first `listOrgInvites` call in commit `1d00b0495`. Git history records the change, not the reason.
