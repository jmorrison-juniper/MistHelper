# Research: Virtual Chassis Menu Guidance

**Record date**: 2026-11-26. **Issue**: #4747. **Remote truth**: GitHub `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

## Method

- Issue facts came from `gh issue view 4747`. The issue is open. Its labels are `bug`, `MistHelper.py`, and `needs-human-review`. It has no comments. Its body cites commit `0d881744310dc2c1b1be8b47b5b5402504029062` and names issues #2863 and #4358.
- Linked pull requests: `gh pr list --search 4747` returned an empty list.
- Legacy record: no folder that starts with `4747-` exists in the local `specs` tree or in the remote tree (RC-52). The reuse steps do not apply.
- Remote reads used `gh api` only. Each cited body was decoded from base64 and searched line by line. The table below records each check.
- Local `git hash-object` gave blob SHAs for the three `.venv` mistapi files, which sit outside the repository tree. It also gave the local checkout blob for the module (RC-03).
- No build, test, linter, or package step ran. No repository file was changed. No URL was fetched. No skill was loaded, because no Podman or Juniper device question appears in the issue.

## Decisions

### D-1 Replace stale numbers with the registered menus

- **Chosen**: Use menu 161 for the single conversion, menu 162 for the bulk conversion, and menu 14 for the status check.
- **Alternatives**: Renumber the menus to match the old text. Or remove the numbers and name each operation.
- **Reason**: The menu table and the registry assign these numbers (RC-25 to RC-27, RC-34 to RC-36). The change is the smallest one that matches them.
- **Risk**: Operators with saved reports still see the old numbers. The changelog names both sets.
- **Human decision**: no.

### D-2 Use the term menu in all touched text

- **Chosen**: Write `menu` in each touched message, comment, and docstring.
- **Alternatives**: Keep `option`, which the printed messages used. Or write `operation`.
- **Reason**: The CLI flag `--menu` and the menu table use the term `menu`. One term names one concept (STE rule).
- **Risk**: None measurable.
- **Human decision**: no.

### D-3 Place the four tests in existing classes

- **Chosen**: Add three methods to `TestCheckStatus` (RC-39) and one method to `TestHandleConversionResponse` (RC-40). The classes then hold five and four methods.
- **Alternatives**: Add a new test module under `tests/unit`. Add a new class to the existing module. Add a file under `tests/guardrails`.
- **Reason**: Each alternative adds a child to a parent that already holds more than five children (RC-43), and Principle I forbids that (RC-66).
- **Risk**: The test placement reads less naturally. Each docstring states the purpose of its test.
- **Human decision**: no.

### D-4 Import the registry inside the registry test

- **Chosen**: Import `MistHelper` and `OperationRegistry` inside the registry test method.
- **Alternatives**: Parse `MistHelper.py` with `ast`. Hard-code the expected titles. Import at module level.
- **Reason**: The guard test reads the same source (RC-46, RC-47). A method-level import keeps the order of the mistapi stub that the module uses (RC-38).
- **Risk**: The import loads more modules during the test. The guard test already loads them offline.
- **Human decision**: no.

### D-5 Replace all stale lines in both files

- **Chosen**: Replace the 16 stale lines in the module (RC-05) and the two stale lines in the root test (RC-44, RC-45).
- **Alternatives**: Change only the three printed lines that the issue cites. Or rename the line-numbered test names too.
- **Reason**: The issue asks for stale comments and docstrings. The root test repeats the same wrong mapping. The test names cite lines, and changing them is outside the defect (RC-42).
- **Risk**: The text diff is larger. Each change replaces one line.
- **Human decision**: no.

### D-6 Keep the module line count

- **Chosen**: Replace each line in place. Add no line above line 184.
- **Alternatives**: Add logging or helper functions above line 184.
- **Reason**: The test names cite lines 102 to 184 (RC-42). A line insertion above 184 makes those names misleading.
- **Risk**: None for behavior. A later logging change can add lines below line 184.
- **Human decision**: no.

### D-7 Keep the confirmations and the API calls

- **Chosen**: Keep the typed `CONVERT` checks (RC-16, RC-17) and the convert calls (RC-14, RC-15) unchanged.
- **Alternatives**: Change the prompt text or the calls.
- **Reason**: Principle III requires typed confirmation (RC-67). The issue asks to preserve the confirmations.
- **Risk**: None.
- **Human decision**: no.

### D-8 Proceed despite the stale rename and the partial queue claim

- **Chosen**: Proceed. Record the contradiction. T001 repeats the overlap check before any edit.
- **Alternatives**: Stop until a human confirms ownership with #2863 and #4358.
- **Reason**: PR #4358 merged and changes no virtual chassis path (RC-49). No open pull request touches a target file (RC-51). The inventory cited by #2863 lists the module (RC-50).
- **Risk**: A pull request can touch a target file after this research. T001 and the pull request step check again.
- **Human decision**: no.

### D-9 Expect no change to generated menu pages

- **Chosen**: Run the generators in T-LOCAL-GATES and expect no changed file.
- **Alternatives**: Hand-edit the generated pages. Or regenerate and commit them by default.
- **Reason**: The generator reads `MistHelper.py` and the registry (RC-80). The scanner parses no comments or docstrings (RC-81).
- **Risk**: A page can change anyway. The fix is then to regenerate and commit only that page.
- **Human decision**: no.

### D-10 Keep the issue-based changelog name

- **Chosen**: Name the fragment `issue-4747-virtual-chassis-menu-options.md` and keep the name after the pull request opens.
- **Alternatives**: Use `pr-<number>.md` after the pull request opens. Or use a date-based name.
- **Reason**: The changelog rule names the issue form when no pull request exists (RC-57). It says to keep the first name, because a rename looks like a conflict (RC-58).
- **Risk**: A reviewer can ask for the pull request form. The rule rejects that request.
- **Human decision**: no.

### D-11 Keep the auto-merge label off

- **Chosen**: Do not add `auto-merge`. A human reviews the pull request, and the orchestrator authorizes the merge.
- **Alternatives**: Add `auto-merge` after the checks pass.
- **Reason**: The issue states that human review remains required. The label `needs-human-review` is set on the issue.
- **Risk**: The merge takes longer.
- **Human decision**: no. This is a merge gate, not a licensing, legal, data, credential, or priority decision.

### D-12 Write the tests before the text change

- **Chosen**: Add the four tests, run them, and confirm the failures. Then change the text.
- **Alternatives**: Change the text first, then add the tests.
- **Reason**: A test must be able to fail (AGENTS.md, RC-59). The red run proves that the new tests detect the stale text.
- **Risk**: One extra red run.
- **Human decision**: no.

### D-13 Add a static guard for the stale text

- **Chosen**: Add the static test `test_virtual_chassis_sources_name_no_stale_menus`. It reads the module and the root test.
- **Alternatives**: Rely on review only.
- **Reason**: FR-005 and FR-006 need a test. AGENTS.md requires guards that prove they can fail (RC-59).
- **Risk**: The regex can give a false result. The test runs red before the fix and green after it.
- **Human decision**: no.

### D-14 Leave the bulk path without rollback guidance

- **Chosen**: The bulk path keeps its current output. It gets no rollback guidance.
- **Alternatives**: Add the success guidance to the bulk path.
- **Reason**: Adding guidance is new behavior, and the issue asks only for correct numbers. The bulk path does not call the success helper (RC-15).
- **Risk**: Operators can expect verification guidance after a bulk run. The gap is recorded for a separate issue.
- **Human decision**: no.

## Remote verification table

Each row is one check. The count of rows equals the `remote_checks` count in `META_DIR\4747-STATUS.json`.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Issue 4747 cites commit 0d881744 and it exists on GitHub | commit 0d881744310dc2c1b1be8b47b5b5402504029062 | 0d881744310dc2c1b1be8b47b5b5402504029062 | none (commit object) | present | 0 |
| RC-02 | Main head commit is the base of this record | commit main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-03 | Local checkout copy of the module equals the main blob | src/mist/resources/device/virtual_chassis.py | local checkout | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 0 |
| RC-04 | Module docstring names menus 92, 93, and 94 | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 7 |
| RC-05 | Module holds 16 stale menu lines at 7, 81-84, 96, 111, 116, 135, 153, 182, 206, 231, 420, 421, and 540 | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 7 |
| RC-06 | Single conversion usage note names option 92 | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 420 |
| RC-07 | Bulk usage note names option 93 | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 421 |
| RC-08 | Rollback note names Menu 94 for verification | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 540 |
| RC-09 | Rollback note warns that a revert can need a factory reset and re-adoption | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 539 |
| RC-10 | Usage-note helper is defined | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 417 |
| RC-11 | Conversion success helper is defined | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 533 |
| RC-12 | Status check calls the usage-note helper | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 250 |
| RC-13 | Single conversion calls the response handler after the convert call | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 480 |
| RC-14 | Single conversion calls the convert endpoint in the execute helper | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 477 |
| RC-15 | Bulk convert call in the API helper does not call the success helper | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 588 |
| RC-16 | Bulk confirmation accepts only the literal CONVERT | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 380 |
| RC-17 | Single confirmation accepts only the literal CONVERT | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 868 |
| RC-18 | Class VCIODeps is the first top-level class of the module | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 38 |
| RC-19 | Class VirtualChassisManager starts at line 102 | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 102 |
| RC-20 | Menu table dictionary menu_actions is defined | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 3658 |
| RC-21 | GlobalImportManager.MenuEntry resolves to the menu_entry dataclass | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 1254 |
| RC-22 | Menu 92 entry is titled Select a site (used by other functions) | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 5255 |
| RC-23 | Menu 93 entry is titled View device inventory for a selected site | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 5263 |
| RC-24 | Menu 94 entry is titled View statistics for a selected device at a site | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 5271 |
| RC-25 | Menu 161 entry is destructive and launches the single conversion | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 5369 |
| RC-26 | Menu 162 entry is destructive and launches the bulk conversion | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 5377 |
| RC-27 | Menu 14 entry launches the conversion status check | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 5387 |
| RC-28 | Issue anchor lines 5426 to 5444 held menus 92 to 94 at commit 0d88 | MistHelper.py | 0d881744310dc2c1b1be8b47b5b5402504029062 | c6df4393483ef7b5c25e945f73dd8126ce0fa8b4 | present | 5426 |
| RC-29 | Issue anchor lines 5426 to 5444 hold other menus on main | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | stale | 5426 |
| RC-30 | Class OperationRegistry holds the category map | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 48 |
| RC-31 | Registry lists menu 92 as interactive_safe | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 121 |
| RC-32 | Registry lists menu 93 as interactive_safe | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 122 |
| RC-33 | Registry lists menu 94 as interactive_safe | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 123 |
| RC-34 | Registry lists menu 161 as destructive | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 184 |
| RC-35 | Registry lists menu 162 as destructive | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 185 |
| RC-36 | Registry lists menu 14 as resource_intensive | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 731 |
| RC-37 | MenuEntry dataclass holds menu_id, title, and category fields | src/foundation/support/utils/menu_entry.py | main | 97fb40fdd99ed40d3554a98dccc5634e96e261ca | present | 11 |
| RC-38 | Unit test module imports VirtualChassisManager under a mistapi stub | tests/unit/test_virtual_chassis.py | main | 530fda76b86af6234154d0faf5771c3b3398176f | present | 21 |
| RC-39 | Class TestCheckStatus holds two methods before the change | tests/unit/test_virtual_chassis.py | main | 530fda76b86af6234154d0faf5771c3b3398176f | present | 937 |
| RC-40 | Class TestHandleConversionResponse holds three methods before the change | tests/unit/test_virtual_chassis.py | main | 530fda76b86af6234154d0faf5771c3b3398176f | present | 640 |
| RC-41 | No unit test asserts the usage-note or rollback text | tests/unit/test_virtual_chassis.py | main | 530fda76b86af6234154d0faf5771c3b3398176f | absent | 0 |
| RC-42 | Cited test name refers to module line 102 | tests/unit/test_virtual_chassis.py | main | 530fda76b86af6234154d0faf5771c3b3398176f | present | 1027 |
| RC-43 | First test class in the unit test module starts at line 116 | tests/unit/test_virtual_chassis.py | main | 530fda76b86af6234154d0faf5771c3b3398176f | present | 116 |
| RC-44 | Root test docstring names option 92 | tests/test_virtual_chassis.py | main | 45f1a45a5f500cc2aa1f2d6c8b1159971d43aecf | present | 1 |
| RC-45 | Root test comment names option 92 | tests/test_virtual_chassis.py | main | 45f1a45a5f500cc2aa1f2d6c8b1159971d43aecf | present | 9 |
| RC-46 | Guard test imports MistHelper | tests/guardrails/test_operation_registry_menu_coverage.py | main | 626c6ccc7b1c72069256c6fa57e891695b93358e | present | 13 |
| RC-47 | Guard test reads MistHelper.menu_actions as the runtime mapping | tests/guardrails/test_operation_registry_menu_coverage.py | main | 626c6ccc7b1c72069256c6fa57e891695b93358e | present | 39 |
| RC-48 | Changelog fragment policy guard exists | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| RC-49 | Draft PR 4358 renames the unit test module, but PR 4358 merged on 2026-11-13 and changes no virtual chassis path | tests/unit/test_virtual_chassis.py | main | 530fda76b86af6234154d0faf5771c3b3398176f | stale | 0 |
| RC-50 | Issue 2863 queue includes the module, through the inventory that its body cites | specs/1924-failure-evidence/inventory.md | main | 9d5724dbdf6811d9458e60937e7afcb8d9d28e36 | partial | 442 |
| RC-51 | No open pull request changes the four target files, across seven open pull requests | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | absent | 0 |
| RC-52 | No record folder for issue 4747 exists on main | specs/numbered/0/0/1/2/2/4/4/2 | main | none (path absent) | absent | 0 |
| RC-53 | Route digits equal base-5 digits of 4747, padded to eight digits | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-54 | Route parent specs/numbered/0/0/1/2 holds five children and receives no new child | specs/numbered/0/0/1/2 | main | not applicable (directory) | present | 0 |
| RC-55 | Route parent specs/numbered/0/0/1/2/2/4 holds three children and receives one more | specs/numbered/0/0/1/2/2/4 | main | not applicable (directory) | present | 0 |
| RC-56 | Reference record 4920 spec exists as the shape reference | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-57 | Changelog naming table names issue-number-slug for issue-only fragments | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| RC-58 | Changelog rule keeps the first fragment name after the pull request opens | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 32 |
| RC-59 | AGENTS.md exists with the writing and git-flow rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| RC-60 | Local gates table has the Tests row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| RC-61 | Local gates table has the Menu reference row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 72 |
| RC-62 | Local gates table has the Symbols row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 73 |
| RC-63 | Local gates table has the STE row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| RC-64 | Repository states that Python 3.15 or newer is required | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 20 |
| RC-65 | Repository states that the tool runs on Windows 11, macOS, and Linux | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 15 |
| RC-66 | Constitution Principle I is the five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-67 | Constitution Principle III is safety-first with typed confirmation | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| RC-68 | Constitution Principle IV is the full deployment pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| RC-69 | Constitution Principle V is observability with ASCII logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 182 |
| RC-70 | Constitution Principle VI is inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| RC-71 | Constitution Principle VII is action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| RC-72 | Constitution technology constraints state Python 3.15 | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 278 |
| RC-73 | Quality gates list the menu_reference_drift job | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 67 |
| RC-74 | Quality gates include the section for local venv commands | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 241 |
| RC-75 | Architecture menu map lists Virtual Chassis 161-162 as destructive | documentation/architecture.md | main | b4cab54be36d223b7eba879ca99b838f508938ce | present | 141 |
| RC-76 | Container rule covers test and debug containers | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 141 |
| RC-77 | Operator guide has no virtual chassis conversion text | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | absent | 0 |
| RC-78 | README has no virtual chassis menu text | README.md | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | absent | 0 |
| RC-79 | Test-quality baseline has no entry for the virtual chassis test modules | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | absent | 0 |
| RC-80 | Menu generator reads MistHelper.py as the menu source | scripts/generate_menu_wiki.py | main | f959225275536743e93bc95d37cb015865a73d53 | present | 62 |
| RC-81 | Menu API scanner parses no comments or docstrings | scripts/menu_api_map/analysis/scanner.py | main | 8a90431fe64be7a23ab3c4a0145efd8d5aeffeb0 | absent | 0 |
| RC-82 | GET coverage document lists getSiteDeviceVirtualChassis | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 1223 |
| RC-83 | GET coverage document lists no convert endpoint | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | absent | 0 |
| RC-84 | OpenAPI defines operation convertSiteVirtualChassisToVirtualMac | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 31698 |
| RC-85 | OpenAPI defines path /vc/convert_to_virtualmac | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 31687 |
| RC-86 | Pinned mistapi 0.64.1 defines convertSiteVirtualChassisToVirtualMac | .venv\Lib\site-packages\mistapi\api\v1\sites\devices.py | local .venv | fd3faa0988e688c1cac4e21f22ebe22693f77409 | present | 3649 |
| RC-87 | Pinned mistapi 0.64.1 defines getSiteInfo | .venv\Lib\site-packages\mistapi\api\v1\sites\sites.py | local .venv | 3b110ec432906c3b9ef438712816a3faf960817a | present | 17 |
| RC-88 | Installed mistapi version is 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | local .venv | not applicable (metadata file) | present | 0 |
| RC-89 | Response handler returns before the success helper on an HTTP or detail error | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 496 |
| RC-90 | ci.yml sets MYPY_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-91 | ci.yml sets VULTURE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RC-92 | ci.yml sets PYDOCSTYLE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| RC-93 | ci.yml sets INTERROGATE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RC-94 | Destructive menu docs guard exists | tests/guardrails/test_destructive_menu_docs.py | main | 7acb28a5879b6634850f3558e636d6b798695fe8 | present | 0 |
| RC-95 | Quality gates list the test_quality_gate command | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 63 |
| RC-96 | Local gates table has the compile, lint, format, and types rows | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 57 |
| RC-97 | Local gates table has the complexity to docstrings rows | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 66 |
| RC-98 | The --test sweep runs only the safe category | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 227 |
| RC-99 | Missing-endpoint document lists no convert endpoint | documentation/MIST_API_MISSING_ENDPOINTS.md | main | e4949ef2ab2ed1d86e6309bd919401d65b2c0ae0 | absent | 0 |
| RC-100 | Converted-prefix constant is 020003 | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 34 |
| RC-101 | Usage-note block prints its header and three notes at lines 419 to 424 | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 419 |
| RC-102 | Rollback block prints its six lines at lines 535 to 540 | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 535 |
| RC-103 | Response handler takes no API session, only the response and identifiers | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 488 |
| RC-104 | Existing confirmation tests cover the typed-confirmation helper | tests/unit/test_virtual_chassis.py | main | 530fda76b86af6234154d0faf5771c3b3398176f | present | 297 |
| RC-105 | Existing API call tests cover the execute helper | tests/unit/test_virtual_chassis.py | main | 530fda76b86af6234154d0faf5771c3b3398176f | present | 669 |
| RC-106 | Dry run returns before the convert call and prints no rollback guidance | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 309 |

## Sources

Local files read (repository root is `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`):

- `AGENTS.md`, read in full. Remote blob `44a9afffb5bd6f774973a845d27343e4e528b6ad` (RC-59).
- `.github\copilot-instructions.md`, read in full, 601 lines. Remote blob `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` (RC-60 to RC-65, RC-96 to RC-98).
- `.specify\memory\constitution.md`, read in full, 563 lines. Remote blob `4584997a264c5a7ade2ca7441246e1f067083aa1` (RC-66 to RC-72).
- `.specify\templates\spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`, read in full. Remote blobs `083ef123c7a2e56e21f3062173fb003258f927e2`, `1a54553bd85cbef2178aa55efbeeb0c1942ffdde`, `7e5170324d41a6736c498d6b9fc83651f31d0778`, and `806657da09d1058823923e346a323b633114971a`.
- `.specify\scripts\powershell\spec-route.ps1`, read in full. Remote blob `37293a255f9b5de20ccb2b3ef0ad15717bab2826` (RC-53).
- `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`. The headings and child layout served as the shape reference (RC-56). Its content was not copied.
- `documentation\quality-gates.md`, `architecture.md`, and `container-deployment.md`, and `operator-guide.md` (grep only). Remote rows RC-73 to RC-77 and RC-95.
- `documentation\MIST_API_GET_ENDPOINTS.md` and `MIST_API_MISSING_ENDPOINTS.md`. Coverage checks in RC-82, RC-83, and RC-99.
- `documentation\mist-api-openapi31yaml.yaml`. Read through the blob API, 125048 lines (RC-84, RC-85).
- `.venv\Lib\site-packages\mistapi\api\v1\sites\devices.py` and `sites.py`, and `.venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA`. Read with `Select-String` and `git hash-object` (RC-86 to RC-88).
- The module, the unit test, the root test, the guard tests, the registry, the menu entry dataclass, `MistHelper.py`, and `ci.yml`, all read from remote blobs.

Remote reads used GitHub `main` in read-only mode. They covered the git tree (11404 entries, not truncated), commit records, PR 4358 files, issue 2863, and issue 4747.

URLs: none. No web fetch ran. The mistapi upstream repository was not checked.

## Unverified

- Live behavior of the convert endpoint. No conversion ran, and the issue forbids that test. The OpenAPI text describes the behavior (RC-84).
- The ste-linter score for the new changelog fragment. The brief forbids linter runs in this task. T006 checks it.
- The result of the four new tests. They do not exist yet. T002 runs them.
- The behavior of the `misthelper-devtools` tools (`symbol-diff`, `ste-linter`, and `test-quality-analyzer`) on the changed files. T-LOCAL-GATES runs them.
- The sandbox claims in the issue body, which describe an isolated macOS probe. The repository cannot confirm them.
- Upstream mistapi source for version 0.64.1. Only the installed `.venv` copy was read (RC-86, RC-87).
- Whether the inventory cited by issue #2863 is current. RC-50 shows that the file is listed, not that it is still a priority.
- The open pull request scan (RC-51) is a point-in-time check. T001 repeats it.
- Whether each `GlobalImportManager.MenuEntry` row has a `title` field. RC-21 and RC-37 verify the class and its fields, not each row.
- CI results for the future pull request. Tasks T-REMOTE-CI and T-MERGE decide these.
