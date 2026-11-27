# Research: SQLite schema context errors

This file holds the decisions, the remote verification table, the sources, and the unverified items for issue #4712. Each remote row cites GitHub `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, unless the row names another ref.

## Method

- The issue body and five owner comments were read with `gh issue view`. The comment links appear in the Sources section.
- PR #4358 was read with `gh pr view`. Open pull requests were checked for file overlap with `gh pr list`.
- The full `main` tree was read once with `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`. Paths were filtered in PowerShell from that one response.
- Each file body was read with `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main`, then decoded from base64. The OpenAPI file was read as raw text.
- Candidate commits were read with read-only git commands. Each commit was confirmed with `gh api repos/jmorrison-juniper/MistHelper/commits/<sha>`.
- No build, test, linter, container, or repository script ran. No GitHub write action ran.

## Decisions

### D-1 Local failures propagate

- **Decision**: The detector raises the original error for a local failure. It returns `unknown` only after a completed walk with no matching frame.
- **Alternatives considered**:
  - Keep the `unknown` fallback and log the failure. The schema still changes without a stop. Rejected.
  - Return a sentinel value from the detector. Each caller must check it. The writer already reports failure through its boolean result. Rejected.
  - Raise a new typed exception class. The module already holds five top-level names, which is the five-item limit. The exporter boundary catches every exception. Rejected.
- **Rationale**: The issue requires that a local programming or logging failure not select a different schema. Constitution Principle III, Safety-First, requires validation before use. A failed detection gives no valid name.
- **Risk**: A SQLite write with no API function name stops on a local failure. The operator sees one error line. Mitigation: D-7 and D-8.

### D-2 Remove the broad handler

- **Decision**: Delete the `except Exception` clause and its log call. In the remote file these are lines 62 and 63.
- **Alternatives considered**:
  - Narrow the clause to `AttributeError` and `RuntimeError`, then log and re-raise. The logger call at line 59 stays inside the protected block. A narrowed clause would log the same failure a second time. Rejected.
  - Keep the clause and re-raise. The boundary already logs the failure. The clause adds no information. Rejected.
- **Rationale**: The `finally` clause stays. The exporter boundary gives one error line (row 11). The blind handler baseline has no entry for this file (row 16). The handler binds `error` and uses it, so the ratchet guard does not count it as blind (row 17). Removal lowers the broad handler count only.
- **Risk**: Exceptions outside the two expected classes also propagate. This behavior is intended.

### D-3 No writer change

- **Decision**: `src/foundation/support/refactors/sqlite_database_writer.py` does not change.
- **Alternatives considered**:
  - Catch the detector error in `_resolve_api_function_name` and return `False` from `write()`. The exporter boundary already gives the same result. This choice duplicates that handling and widens the change. Rejected.
- **Rationale**: `DataExporter._dispatch_format_write` catches every writer exception, logs the table and format, and returns `False` (rows 10 and 11). The writer calls the detector only when the API function name is empty (row 7). Writes with a named function never reach the detector.
- **Risk**: None for named writes. Unnamed writes follow D-1 and D-7.

### D-4 Test placement

- **Decision**: Add the regression tests under `tests/unit/config/foundation/persistence/storage/db/`. Update the legacy test in place at `tests/unit/db/test_database_schema_utils.py`.
- **Alternatives considered**:
  - Put the new file beside the legacy test under `tests/unit/db/`. That folder is the one open issue #4142 retires. Rejected.
  - Move the legacy test into the storage package now. The move is tracked by issue #4142, and PR #4358 did not perform it (rows 13, 79, 69). Rejected.
- **Rationale**: The storage package exists with sibling tests (row 14). The rename target is absent (row 79). The open pull request check found no other open change to the legacy file.
- **Risk**: The later move must carry the updated assertion. See analysis item A-03.

### D-5 Focused test set

- **Decision**: Add three new tests and update one legacy test. Do not carry forward the 19 candidate cases.
- **Alternatives considered**:
  - Carry forward all 19 candidate cases. The name-pattern and nearest-match cases test behavior that this change does not touch. The cleanup-observer case restates the implementation. Rejected.
- **Rationale**: AGENTS.md says to add tests only for behavior that a change introduces or fixes. The existing detection tests in the legacy file keep covering the unchanged patterns and the absent-frame result.
- **Risk**: A later change to name matching depends on the existing tests. Those tests stay in place.

### D-6 Record slug and route

- **Decision**: Use the record folder `4712-schema-context-errors` under the route `0\0\1\2\2\3\2\2`. Confirm the route with `Resolve-SpecFeaturePath` in task T003.
- **Alternatives considered**:
  - Slug `sqlite-schema-context-errors`. The longer slug differs from the candidate record name without a benefit. Rejected.
  - Compute the route by hand only. The candidate did this because PowerShell was unavailable. PowerShell now runs in this environment (row 77). Rejected.
- **Rationale**: The route is base five with eight digits (rows 21 and 22). Arithmetic check: 1 times 3125, plus 2 times 625, plus 2 times 125, plus 3 times 25, plus 2 times 5, plus 2 times 1 equals 4712. The digits `1 2 2 3 2 2` pad to `0 0 1 2 2 3 2 2`. The parent folder `0\0\1\2\2\3\2` holds two children and gains one (row 36). The local listing shows five children at `0\0\1\2`. The route reuses its child `2`, so it adds none there.
- **Risk**: The record path depends on the route. Task T003 verifies it.

### D-7 README text

- **Decision**: Add two sentences after "It writes each output file to `data/`." in the paragraph at README line 30.
- **Alternatives considered**:
  - A new README section. The README has no output section. Rejected.
  - No README change. The constitution requires a README update for each behavior change (row 49). Rejected.
- **Rationale**: Row 49 and row 51. The owner comment of 2026-11-10 names the missing README update (Sources).
- **Risk**: The new text must pass the STE linter. Task T009 checks it.

### D-8 Operator guide text

- **Decision**: Add one paragraph after the SQLite row at `documentation/operator-guide.md` line 752, in the section Find your output.
- **Alternatives considered**:
  - A new troubleshooting section. The operator guide has no output troubleshooting section. Rejected.
  - Put the full policy in README only. AGENTS.md says to keep each technical fact in one location. Rejected.
- **Rationale**: The SQLite row names `data/mist_data.db` (row 53). The runtime log is `data/script.log` (row 46).
- **Risk**: The paragraph quotes the log text from `DataExporter._dispatch_format_write` (row 11). A later change to that text needs a matching update.

### D-9 Changelog fragment name

- **Decision**: Name the fragment `changelog.d/issue-4712-schema-context-errors.md`. Write one `###` heading and one Fixed bullet that names the issue.
- **Alternatives considered**:
  - `pr-<number>.md`. The pull request does not exist yet. The naming rule keeps the first name after the pull request opens (row 19). Rejected.
  - A date-based name. The issue exists, so the issue-number form applies (row 19). Rejected.
- **Rationale**: The name rule (row 19) and the guard pattern (row 18) both accept the issue-number form. The fragment is user visible, so the internal-only exception does not apply (row 50).

### D-10 Branch and candidate reuse

- **Decision**: Create `fix/4712-schema-context-errors` from current `main`. Reuse the candidate design only. Do not cherry-pick or rebase commit `b4b81164`.
- **Alternatives considered**:
  - Rebase the candidate branch. Its base is 84 commits behind `main` (row 75). Its validation used Python 3.14.7, but the repository requires 3.15 (rows 25 and 76). Rejected.
  - Publish the candidate as it stands. The owner holds publication (Sources). Rejected.
- **Rationale**: AGENTS.md, Git flow, Branch, requires a branch from `main` only. The candidate design already removes the broad handler and lets failures propagate (commit `052c16ab1`, read locally).
- **Risk**: The design work repeats. The change is small, so the cost is low.

### D-11 Publication gate

- **Decision**: Tasks T-PR and T-MERGE wait for the owner to lift the publication hold and for the orchestrator to authorize the merge. Tasks T001 to T012 and T-LOCAL-GATES do not wait.
- **Alternatives considered**:
  - Open the pull request now. The owner hold blocks publication. Rejected.
- **Rationale**: The hold is an owner instruction in the issue comments (Sources). It is not one of the four categories that section 6 of the brief names. This decision is not marked human-required.
- **Risk**: The hold can last longer than the implementation. The branch can stay local. Check the base again before opening the pull request.

## Document applicability

- `documentation/quality-gates.md`: The heading search found no section that changes this design. The gate commands come from the Local gates table in `.github/copilot-instructions.md` (rows 42 and 43).
- `documentation/architecture.md`: A term search for SQLite, schema, and primary key found the data folder row. It names `mist_data.db`. No design change follows from it.
- `documentation/development-setup.md`: A search for pytest commands found only upgrade portal examples. No design change follows from it.
- `documentation/container-deployment.md`: Not applicable. This change starts no container and changes no port.
- `documentation/operator-guide.md`: Applicable. Its Find your output section gets the new paragraph (rows 52 and 53).

## Remote verification table

Each row is one check. The table holds 85 rows. The `Line` value 0 means a presence check with no line claim. A `Blob SHA` value starting with `tree` names a directory. A `Blob SHA` value of `none` names a path absent from `main`.

| # | Kind | Claim | Path | Ref | Blob SHA | Result | Line |
|---|---|---|---|---|---|---|---|
| 1 | code | Detector function is defined | src/foundation/persistence/db/database_schema_utils.py | main | 5374c1b1ffc90e756e15dd19d2ddc4a859c3a6fc | present | 49 |
| 2 | code | Detector logs the detected name inside its try block | src/foundation/persistence/db/database_schema_utils.py | main | 5374c1b1ffc90e756e15dd19d2ddc4a859c3a6fc | present | 59 |
| 3 | code | Detector broad handler binds the caught exception | src/foundation/persistence/db/database_schema_utils.py | main | 5374c1b1ffc90e756e15dd19d2ddc4a859c3a6fc | present | 62 |
| 4 | code | Detector returns unknown after the frame walk | src/foundation/persistence/db/database_schema_utils.py | main | 5374c1b1ffc90e756e15dd19d2ddc4a859c3a6fc | present | 66 |
| 5 | code | get_endpoint_strategy selects the strategy for an API name | src/foundation/persistence/db/database_schema_utils.py | main | 5374c1b1ffc90e756e15dd19d2ddc4a859c3a6fc | present | 69 |
| 6 | code | SQLite writer write pipeline resolves the API name | src/foundation/support/refactors/sqlite_database_writer.py | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 93 |
| 7 | code | SQLite writer calls the detector only when the API name is unset | src/foundation/support/refactors/sqlite_database_writer.py | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 145 |
| 8 | code | SQLite writer calls the detector to set the API name | src/foundation/support/refactors/sqlite_database_writer.py | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 147 |
| 9 | code | SQLite writer selects the strategy with get_endpoint_strategy | src/foundation/support/refactors/sqlite_database_writer.py | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 221 |
| 10 | code | Exporter dispatch catches writer exceptions | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 148 |
| 11 | code | Exporter dispatch logs the table and output format on failure | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 149 |
| 12 | code | Exporter SQLite writer call returns the write result | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 386 |
| 13 | code | Legacy unit test defines the stack inspection test | tests/unit/db/test_database_schema_utils.py | main | 5b6fa81817179472ff7ef448d813355c304cf3db | present | 55 |
| 14 | code | Sibling persistence storage test directory exists | tests/unit/config/foundation/persistence/storage/db/test_sqlite_database_writer_logging.py | main | 1187733345339971518dd7636ee86700251044fd | present | 0 |
| 15 | code | Strategy entry getOrgInventory is natural_pk | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 144 |
| 16 | config | Blind handler baseline has no entry for database_schema_utils | .github/blind-exception-handler-baseline.json | main | f3a2ee54395a205b422bcbdb0bea9d489a06d951 | absent | 0 |
| 17 | config | Blind handler ratchet guard reads the baseline path | tests/guardrails/test_blind_exception_handler_ratchet.py | main | 3cab97e42178b7b978bcc78eab73d8a0fb3eae27 | present | 155 |
| 18 | config | Changelog fragment policy accepts issue-number file names | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 39 |
| 19 | config | Changelog README defines the issue-number file name rule | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| 20 | config | Changelog README defines the fragment body rule | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 35 |
| 21 | config | Route algorithm uses base five | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| 22 | config | Route width is eight segments | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| 23 | config | Resolve-SpecFeaturePath calculates the numbered route | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 34 |
| 24 | config | Process folder baseline exists for the specs guard | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| 25 | config | Python requirement is 3.15 or newer | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| 26 | config | mypy strict mode is enabled | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 279 |
| 27 | config | Ruff line length is 120 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 202 |
| 28 | config | CI MYPY_PATHS variable is defined | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| 29 | config | CI VULTURE_PATHS variable is defined | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| 30 | config | CI PYDOCSTYLE_PATHS variable is defined | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| 31 | config | CI INTERROGATE_PATHS variable is defined | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| 32 | config | STE linter config file exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| 33 | config | Bootstrap script exists | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 0 |
| 34 | config | Test quality configuration file exists | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 0 |
| 35 | config | Pull request template has no Closes line | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | absent | 0 |
| 36 | config | Route parent directory holds two children | specs/numbered/0/0/1/2/2/3/2 | main | tree 45fc14f0bef9b7afd401d1510c39ba73506f6a58 | present | 0 |
| 37 | config | Reference record spec exists at its route | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| 38 | doc | AGENTS writing style section exists | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| 39 | doc | AGENTS specifications section exists | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 345 |
| 40 | doc | AGENTS pull request section exists | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 221 |
| 41 | doc | Repository instructions require Python 3.15 or newer | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 20 |
| 42 | doc | Local gates Tests row defines the pytest command | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| 43 | doc | Local gates STE row defines the ste-linter command | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| 44 | doc | Test quality ratchet section exists | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 95 |
| 45 | doc | Test quality row bans a bare assert result | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 253 |
| 46 | doc | Runtime log is data/script.log | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 337 |
| 47 | doc | Constitution defines the five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| 48 | doc | Constitution defines inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| 49 | doc | Constitution requires README update for behavior changes | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 400 |
| 50 | doc | Constitution requires one release note fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| 51 | doc | README output sentence names data as the output folder | README.md | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | present | 30 |
| 52 | doc | Operator guide Find your output section exists | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 744 |
| 53 | doc | Operator guide SQLite row names data/mist_data.db | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 752 |
| 54 | doc | Spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| 55 | doc | Plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| 56 | doc | Tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| 57 | doc | Checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| 58 | doc | Mist API GET table lists getOrgInventory | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 607 |
| 59 | doc | Mist API missing table does not list getOrgInventory | documentation/MIST_API_MISSING_ENDPOINTS.md | main | e4949ef2ab2ed1d86e6309bd919401d65b2c0ae0 | absent | 0 |
| 60 | sdk | OpenAPI defines operationId getOrgInventory | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 10660 |
| 61 | sdk | OpenAPI defines the path /api/v1/orgs/{org_id}/inventory | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 10639 |
| 62 | sdk | Installed mistapi defines getOrgInventory | .venv\Lib\site-packages\mistapi\api\v1\orgs\inventory.py | mistapi 0.64.1 installed | 4632461c7eef0317f7c7810f018a6cc7b305f4a2 | present | 17 |
| 63 | sdk | Python currentframe returns None without frame support | C:\Users\jmorrison\AppData\Local\Python\pythoncore-3.15-64\Lib\inspect.py | Python 3.15.2 installed | 945f696bf0abe177a6a598c5fdf7e5a5be2a673d | present | 1690 |
| 64 | commit | Issue cited commit 3964d21d is an ancestor of main | commit 3964d21d03f9f5717cb8eafb7272ecff21f5362a | main | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | present | 0 |
| 65 | commit | Current main head commit is f03c6c9b | commit f03c6c9b36d612a48d7b9652998c2fd87dd777ca | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| 66 | commit | Local candidate commit b4b81164 exists on GitHub | commit b4b81164da5de46b3f010671008d82dd3ff315e0 | archive branch | b4b81164da5de46b3f010671008d82dd3ff315e0 | present | 0 |
| 67 | commit | Local candidate commit b4b81164 is not on main | commit b4b81164da5de46b3f010671008d82dd3ff315e0 | main | b4b81164da5de46b3f010671008d82dd3ff315e0 | absent | 0 |
| 68 | commit | Archive branch head is the candidate commit | branch archive/laptop-20261121/jmorrison-juniper-sqlite-context-failures | archive branch | b4b81164da5de46b3f010671008d82dd3ff315e0 | present | 0 |
| 69 | issue | Issue 4142 is open and owns the test domain move | issue 4142 | GitHub | none | present | 0 |
| 70 | legacy | Legacy plan says the handler catches inspection and logging errors | src/foundation/persistence/db/database_schema_utils.py | main | 5374c1b1ffc90e756e15dd19d2ddc4a859c3a6fc | present | 62 |
| 71 | legacy | Legacy plan says the legacy test expects the defective fallback | tests/unit/db/test_database_schema_utils.py | main | 5b6fa81817179472ff7ef448d813355c304cf3db | present | 67 |
| 72 | legacy | Legacy plan says the utility class exceeds five members | src/foundation/persistence/db/database_schema_utils.py | main | 5374c1b1ffc90e756e15dd19d2ddc4a859c3a6fc | present | 41 |
| 73 | legacy | Legacy plan route 0/0/1/2/2/3/2/2 matches the base five algorithm | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| 74 | legacy | Legacy record commit b4b81164 exists | commit b4b81164da5de46b3f010671008d82dd3ff315e0 | archive branch | b4b81164da5de46b3f010671008d82dd3ff315e0 | present | 0 |
| 75 | legacy | Legacy validation base commit 343461229 is current origin main | commit 343461229b9cfbeec93d0dd61ee8a17fb24c6814 | main | 343461229b9cfbeec93d0dd61ee8a17fb24c6814 | stale | 0 |
| 76 | legacy | Legacy validation interpreter is Python 3.14.7 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | stale | 23 |
| 77 | legacy | Legacy plan says PowerShell is unavailable | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | stale | 4 |
| 78 | legacy | Legacy spec says draft 4358 still owns the rename | pull request 4358 | GitHub | none | stale | 0 |
| 79 | legacy | Legacy spec says the rename target exists | tests/unit/config/foundation/persistence/storage/db/test_database_schema_utils.py | main | none | absent | 0 |
| 80 | legacy | Legacy tasks say the regression test file exists | tests/unit/config/foundation/persistence/storage/db/test_database_schema_context_errors.py | main | none | absent | 0 |
| 81 | legacy | Legacy record folder exists on main | specs/numbered/0/0/1/2/2/3/2/2/4712-schema-context-errors | main | none | absent | 0 |
| 82 | legacy | Legacy tasks say the changelog fragment exists | changelog.d/issue-4712-schema-context-errors.md | main | none | absent | 0 |
| 83 | code | DataProcessingUtils class defines the escape and key helpers the writer calls | src/foundation/models/data/data_processing_utils.py | main | f0e53336717eefbbe0bf7b4136b3e0d4f11f3847 | present | 27 |
| 84 | config | STE command input CLAUDE.md exists | CLAUDE.md | main | 9821a79a4481e754bc34052ace0daffa0f8ec088 | present | 0 |
| 85 | config | STE command input ASD writing guide exists | documentation/ASD-STE100_writing-guide.md | main | b464165aae116a17bb3031d3cef9b84a95589c0a | present | 0 |

Counts: 85 rows. Result values: 73 present, 8 absent, 4 stale, 0 partial. Legacy rows 70 to 82 hold 5 present, 4 stale, and 4 absent.

## Legacy record verification

The legacy record sits in commit `b4b81164` on branch `archive/laptop-20261121/jmorrison-juniper-sqlite-context-failures` (rows 66 and 68). It holds `spec.md`, `plan.md`, `tasks.md`, `design/validation.md`, and `design/checklists/requirements.md` under the route folder. Commit `052c16ab1` holds the candidate source change. Commit `d9d75e00c` holds the candidate test file. The record is a draft. It is not proof.

- Verified: rows 70 to 74. The handler, the defective test expectation, the five-member class, the route algorithm, and the candidate commit all match the remote state.
- Stale: rows 75 to 78. The base commit is 84 commits behind `main`. The interpreter was 3.14.7, and the repository requires 3.15. PowerShell runs in this environment. PR #4358 merged on 2026-11-13.
- Absent: rows 79 to 82. The rename target, the regression test file, the record folder, and the changelog fragment are absent from `main`.

## Sources

- Issue #4712 body and comments were read with `gh issue view 4712 -R jmorrison-juniper/MistHelper`. Owner comments: `https://github.com/jmorrison-juniper/MistHelper/issues/4712#issuecomment-6744283900` (2026-11-09), `#issuecomment-6744351494`, `#issuecomment-6744372936`, `#issuecomment-6744551359`, and `#issuecomment-6764708023` (2026-11-10, publication hold and README gap).
- PR #4358 `https://github.com/jmorrison-juniper/MistHelper/pull/4358` (MERGED 2026-11-13T19:33:49Z). Its status rollup holds 52 entries: 43 success, 9 skipped, and 0 failure. PR #4740 (MERGED 2026-11-10T09:19:42Z). PR #4813 is open and changes `src/operations/exporting/export/data_exporter.py` and `tests/unit/export/test_data_exporter.py`.
- Issue #1794 (open, blind exception handlers) and issue #4142 (open, test domain packages).
- Repository rules: `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, `.specify/templates/*.md`, and the reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`. Each read through the remote contents API.
- Candidate commits on the archive branch: `052c16ab1` (source fix), `d9d75e00c` (test file), and `b4b81164` (test assertion). Read with `git show` in read-only mode. Each commit confirmed through the commits API.
- Local environment: `.venv\pyvenv.cfg` names Python 3.15.2. `.venv\Lib\site-packages\mistapi\api\v1\orgs\inventory.py` defines `getOrgInventory`. Its blob SHA came from `git hash-object`, read only.
- Standard library: `inspect.currentframe` at line 1688 returns `sys._getframe(1)` or `None` at line 1690 of the installed `inspect.py`.
- Skills: none loaded. No Podman, container, or Juniper device question exists in this issue.
- No `web_fetch` call ran.

## Unverified

- U-1: The candidate test counts (8 failed and 11 passed, then 131 passed) and the coverage value (100 percent) come from the legacy validation. No test ran in this session.
- U-2: The STE scores of 86 to 98 come from the legacy validation. No STE run ran in this session.
- U-3: The issue reproduction output (`natural_pk` and `unknown` with `auto_increment_with_unique`) is author-reported. No reproduction ran in this session.
- U-4: The legacy route check of 12 directories is not repeated. This session checked the route parents only.
- U-5: The effect on production `data/mist_data.db` is not known. This session opened no database.
- U-6: `Resolve-SpecFeaturePath` did not run. The route rests on the function source (row 23) and the arithmetic in D-6. Task T003 runs the function.
- U-7: The new tests did not run under Python 3.15.2. Task T-LOCAL-GATES runs them.
- U-8: Remote CI for a future pull request is not known. No pull request exists for this branch.
- U-9: The candidate commit content beyond the source and test diffs was not read. Only the five record files and the two diffs were read.
- U-10: The root logger configuration decides whether the boundary error line reaches `data/script.log`. This session did not read the logging setup. The operator paragraph names the runtime log from the copilot-instructions table (row 46).
