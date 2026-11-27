# Research: Operator Guide Operation Count

## Summary of Findings

- The operator guide states `303 operations` and `numbered 1 to 304` (R-01).
- The generated menu reference states 308 actionable menu operations, numbered 1 to 309 (R-03).
- The operator guide still holds the stale count on `main`. Pull request #4918 changed the guide and left the count in place.
- No test reads the guide count. The destructive menu guard reads no operator guide (R-72).
- Continuous integration does not grade the guide with the STE gate (R-47). Pre-commit does (R-49).
- The route `specs\numbered\0\0\1\2\4\1\3\0` equals the base-5 digits of 4915, padded to eight digits. The route helper computes it that way (R-91).
- Affected path: the operator guide (`documentation/operator-guide.md`) links to the menu reference (`documentation/menu_reference.md`). The menu reference names its generator inputs: `menu_actions` in `MistHelper.py` and `src/foundation/support/utils/operation_registry.py` (R-06). The generator writes that page (R-07). This change edits neither input (FR-004).

## Decisions

### D-1 Delete the count and keep the menu reference link

- Decision: Delete the sentence that states the count and the numbering range. Keep the link to the menu reference.
- Alternatives: (a) Update the count to 308 and the range to 1 to 309. Rejected, because the count drifted after issue #4155 closed (R-01, R-03). (b) Generate the count into the guide. Rejected, because it adds generator scope to a text fix. (c) Delete the count and keep the link. Chosen.
- Rationale: The menu reference is generated, and it states the total (R-03, R-06). The issue asks for the link instead of the count.
- Risk: Caution: operators lose the total at a glance. Mitigation: the menu reference states the total in its first section (R-03).
- Human decision required: no.

### D-2 Guard the guide with an absence check

- Decision: The guard test fails when the guide contains a count phrase. The test does not compare the count with the registry.
- Alternatives: (a) Compare the guide count with the registry total, as `test_instruction_table_counts_match_the_registry` does (R-74). Rejected, because the guide would state a count again, which D-1 removes. (b) Absence check. Chosen.
- Rationale: An absence check needs no update when the registry changes. It stops the drift that issue #4155 recorded.
- Risk: A sentence that counts the operations of one menu matches the pattern. Mitigation: the author rewords the sentence, as the spec edge case states.
- Human decision required: no.

### D-3 Place the guard test in the existing destructive menu module

- Decision: Add the class and the test function to `tests/guardrails/test_destructive_menu_docs.py`.
- Alternatives: (a) A new module in `tests/guardrails`. Rejected, because the folder holds 79 direct children (R-81), and Principle I forbids a new direct child in a noncompliant parent (R-15). (b) A new nested package for one test. Rejected, because it adds structure for one test. (c) The existing module. Chosen.
- Rationale: The module already guards menu documents against the registry (R-73, R-74).
- Risk: The module name names destructive docs, while the new test names the operator guide. Mitigation: the module docstring gains one paragraph about the guide.
- Human decision required: no.

### D-4 Add one fragment with the Fixed type

- Decision: Add `changelog.d/issue-4915-operator-guide-count.md` with one `###` heading and one Fixed bullet.
- Alternatives: (a) No fragment, because the change is text only. Rejected, because the no-fragment rule covers internal-only changes (R-90), and the guide is operator-facing (R-71). (b) The Changed type. Rejected, because the guide held a wrong fact, and the Fixed type names that kind of change (R-77). (c) One Fixed fragment. Chosen.
- Rationale: Each change adds one fragment (R-17). The release note reaches operators through the changelog.
- Risk: None identified.
- Human decision required: no.

### D-5 Limit scope to the operator guide

- Decision: Limit this change to the operator guide. Track the wiki count, the README-count instructions, the continuous integration STE gap, and the quality gates text in follow-up issues.
- Alternatives: (a) Fix the wiki count and the instructions in the same pull request. Rejected, because one issue holds one subject (R-33). (b) Add the operator guide to the STE workflow files list. Rejected, because the workflow change needs its own issue. The workflow lists five files (R-47). (c) Limit the scope. Chosen.
- Rationale: The issue acceptance uses a local STE check. Pre-commit already grades the guide (R-49).
- Risk: The stale text remains until the follow-up issues close (R-11, R-12, R-14, R-60).
- Human decision required: no.

### D-6 Record steps 10 to 12 of Principle IV as not triggered

- Decision: Record steps 10 to 12 of Principle IV as not triggered for this change. After the merge, check the runs of `container-build.yml`, and record that no run matches the merge commit. Do not dispatch a build by hand.
- Alternatives: (a) Dispatch `container-build.yml` by hand. Rejected, because the image content does not change. The image excludes the documentation folder (R-57, R-58). (b) Hold the merge until the owner changes Principle IV. Rejected, because the rule does not block a documentation change, and the orchestrator can confirm the exception. (c) Record the evidence and the exception. Chosen.
- Rationale: The build paths exclude the guide and the tests (R-56). Principle IV says that no step may be skipped (R-20). The exception is written, so it is not silent.
- Risk: A strict reader counts steps 10 to 12 as skipped. Mitigation: the orchestrator confirms D-6 in the summary, and analysis item A-7 tracks the conflict.
- Human decision required: no.

### D-7 Run the menu reference drift check as proof

- Decision: Run the menu reference generator and the drift check as proof for FR-004.
- Alternatives: (a) Skip the check, because the gate does not cover the changed files. Rejected, because the check is inexpensive and proves that the generated pages stay unchanged. (b) Run the check. Chosen.
- Rationale: The continuous integration job compares the regenerated pages with git diff (R-40).
- Risk: Caution: the generator rewrites a page on the workstation. Mitigation: stop, report the page, and do not commit a generated change for this issue.
- Human decision required: no.

### D-8 Ship the record in the same pull request, at the route

- Decision: Put the record in the same pull request as the guide, the test, and the fragment. Place it at the route.
- Alternatives: (a) A separate record pull request. Rejected, because each change adds its own unique record (R-16), and two pull requests for one issue add merge ordering. (b) Session files only. Rejected, because the route guards check committed records (R-79, R-80). (c) The same pull request. Chosen.
- Rationale: The structure and route guards run on the committed record (R-79, R-80).
- Risk: The pull request adds eight Markdown files. Mitigation: ste-linter runs on each record file by name (T-LOCAL-GATES).
- Human decision required: no.

## Remote Verification Table

Each row is a check on remote `main`, read through the GitHub contents or tree API. The blob or tree SHA is the value that the API returns. Line is the line number in the decoded file, or 0 for a whole-file or folder claim.

| ID | Claim | Path | Blob or tree SHA | Result | Line |
| - | - | - | - | - | - |
| R-01 | Operator guide states 303 operations and numbering 1 to 304 | documentation/operator-guide.md | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | stale | 13 |
| R-02 | Operator guide links to the menu reference | documentation/operator-guide.md | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 14 |
| R-03 | Menu reference states 308 actionable menu entries numbered 1 to 309 | documentation/menu_reference.md | 2bd972183c64302e76442d30669bb9e7362856f1 | present | 6 |
| R-04 | Menu reference states menu 0 is Exit and 309 entries in total | documentation/menu_reference.md | 2bd972183c64302e76442d30669bb9e7362856f1 | present | 8 |
| R-05 | Menu reference table lists menu 309 | documentation/menu_reference.md | 2bd972183c64302e76442d30669bb9e7362856f1 | present | 345 |
| R-06 | Menu reference states that the code generates the page | documentation/menu_reference.md | 2bd972183c64302e76442d30669bb9e7362856f1 | present | 3 |
| R-07 | Generator writes documentation/menu_reference.md | scripts/generate_menu_wiki.py | f959225275536743e93bc95d37cb015865a73d53 | present | 66 |
| R-08 | Generator writes documentation/wiki/Menu-Reference.md | scripts/generate_menu_wiki.py | f959225275536743e93bc95d37cb015865a73d53 | present | 65 |
| R-09 | Wiki copy of the menu reference has the same blob as the menu reference | documentation/wiki/Menu-Reference.md | 2bd972183c64302e76442d30669bb9e7362856f1 | present | 1 |
| R-10 | Copilot instructions state 308 registered operations numbered 1 through 309 | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 11 |
| R-11 | Copilot instructions tell authors to update the README operation count | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | stale | 242 |
| R-12 | Wiki home states 269 actionable menu operations | documentation/wiki/Home.md | e5b10c30d3e4f7d87290156d5a69e0fa18c6347c | stale | 7 |
| R-13 | README states an operation count | README.md | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | absent | 0 |
| R-14 | Constitution tells authors to update the README operation count | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | stale | 352 |
| R-15 | Constitution limits each hierarchy level to five children | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 40 |
| R-16 | Constitution allows changelog.d direct children and requires a folder debt record | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 46 |
| R-17 | Constitution requires one release-note fragment for each change | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| R-18 | Constitution Principle IV step 10 waits for the main build | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 166 |
| R-19 | Constitution Principle IV step 11 verifies the image revision | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 168 |
| R-20 | Constitution requires the full pipeline after any code change and forbids skipped steps | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 145 |
| R-21 | Constitution Principle II requires class-based architecture | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 91 |
| R-22 | Constitution Principle III requires safety-first input handling | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| R-23 | Constitution Principle IV defines the full deployment pipeline | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| R-24 | Constitution requires specs records under managed roots | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 57 |
| R-25 | Constitution Principle V requires ASCII-only log output | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 184 |
| R-26 | Constitution Principle VI requires inline comments on AI-generated code | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 206 |
| R-27 | Constitution Principle VII requires action logging | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 237 |
| R-28 | Constitution names mistapi as the sole Mist REST interface | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 279 |
| R-29 | Constitution names Podman as the container runtime | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 300 |
| R-30 | Constitution requires os.path or pathlib for file paths | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 310 |
| R-31 | AGENTS requires the STE gate for each Markdown file | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 340 |
| R-32 | AGENTS requires each change to carry tests, and a test must be able to fail | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 135 |
| R-33 | AGENTS states that one issue holds one subject | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 185 |
| R-34 | AGENTS requires the in-progress label before the branch | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 187 |
| R-35 | AGENTS names the branch pattern type/issue-slug | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 194 |
| R-36 | AGENTS requires a worktree for each branch | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 198 |
| R-37 | AGENTS requires staging by explicit path | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 251 |
| R-38 | AGENTS requires Closes issue in the pull request body | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| R-39 | CI defines the menu reference drift job | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 704 |
| R-40 | CI regenerates the menu reference and compares it with git diff | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 722 |
| R-41 | CI pytest shards include tests/guardrails | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 255 |
| R-42 | CI runs the changelog fragment guard | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 298 |
| R-43 | CI MYPY_PATHS excludes tests | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-44 | CI VULTURE_PATHS excludes tests | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R-45 | CI PYDOCSTYLE_PATHS excludes tests | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| R-46 | CI INTERROGATE_PATHS excludes tests | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R-47 | CI STE workflow grades the operator guide | .github/workflows/ste-lint.yml | abaeff6d5e299bfa7de4dc15d04f4ef31cf13b5f | absent | 44 |
| R-48 | Repository STE threshold is 80 | .ste-linter.toml | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 15 |
| R-49 | Pre-commit ste-linter grades Markdown and Python files and excludes specs | .pre-commit-config.yaml | 1f0e25544b2f347d8791dec74b7a233c681488ac | present | 34 |
| R-50 | Pre-commit runs markdown-link-check | .pre-commit-config.yaml | 1f0e25544b2f347d8791dec74b7a233c681488ac | present | 37 |
| R-51 | Pre-commit runs ruff on Python files | .pre-commit-config.yaml | 1f0e25544b2f347d8791dec74b7a233c681488ac | present | 7 |
| R-52 | Copilot instructions describe the auto-merge workflow | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 471 |
| R-53 | Copilot instructions describe the close-linked-issues workflow | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 472 |
| R-54 | Copilot instructions give the worktree bootstrap command | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 29 |
| R-55 | Worktree bootstrap script exists | scripts/bootstrap_worktree.py | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 1 |
| R-56 | Container build paths include the operator guide or tests | .github/workflows/container-build.yml | 737325976de75e90aa4526ab1cf2978782e648ce | absent | 6 |
| R-57 | Docker ignore excludes the documentation folder | .dockerignore | 4fc430ad7046ec61f6f64d9658bda2567f84c09d | present | 83 |
| R-58 | Containerfile copies only the OpenAPI JSON from documentation | Containerfile | bc9249a19f6f181e7ea0e2c4b565a139d16d9253 | present | 139 |
| R-59 | Pull request template exists | .github/PULL_REQUEST_TEMPLATE.md | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 1 |
| R-60 | Quality gates page says ste-lint grades this guide (documentation/quality-gates.md) | documentation/quality-gates.md | 6776d334cca5d9b43273473a06da367a65605c6d | stale | 286 |
| R-61 | Quality gates page defines the menu reference drift job | documentation/quality-gates.md | 6776d334cca5d9b43273473a06da367a65605c6d | present | 67 |
| R-62 | Copilot instructions Lint row runs ruff check | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 58 |
| R-63 | Copilot instructions Format row runs black check | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 59 |
| R-64 | Copilot instructions Tests row runs the changed test file | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| R-65 | Copilot instructions state Python 3.15 or newer | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 20 |
| R-66 | Copilot instructions menu reference gate row | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 72 |
| R-67 | Copilot instructions symbols gate row | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 73 |
| R-68 | Copilot instructions STE gate row includes the operator guide | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | absent | 74 |
| R-69 | Copilot instructions define the test quality ratchet | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 95 |
| R-70 | Copilot instructions Security lint row runs bandit | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 67 |
| R-71 | Copilot instructions require one fragment for each user-visible change | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| R-72 | Destructive menu guard reads the operator guide | tests/guardrails/test_destructive_menu_docs.py | 7acb28a5879b6634850f3558e636d6b798695fe8 | absent | 0 |
| R-73 | Destructive menu guard defines test_documents_match_the_registry | tests/guardrails/test_destructive_menu_docs.py | 7acb28a5879b6634850f3558e636d6b798695fe8 | present | 88 |
| R-74 | Destructive menu guard defines test_instruction_table_counts_match_the_registry | tests/guardrails/test_destructive_menu_docs.py | 7acb28a5879b6634850f3558e636d6b798695fe8 | present | 109 |
| R-75 | Hardware shell lock guard reads the operator guide | tests/guardrails/test_hardware_shell_lock_docs.py | 83926b3fbc870c5b69ba48dd5a0a2591ae183ed6 | present | 28 |
| R-76 | Metrics gateway guard reads the operator guide | tests/guardrails/test_metrics_gateway_container_contract.py | d658b1f21c553cb1930e63a9bd2011fd1340da05 | present | 17 |
| R-77 | Changelog guard allows five change types | tests/guardrails/test_changelog_fragment_policy.py | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 45 |
| R-78 | Changelog guard defines the issue name form | tests/guardrails/test_changelog_fragment_policy.py | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 39 |
| R-79 | Specs structure guard test exists | tests/guardrails/test_process_folder_structure.py | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 133 |
| R-80 | Spec route contract guard test exists | tests/guardrails/test_spec_route_contract.py | b174399ad5f23f4844dc442954bf203be07342f3 | present | 45 |
| R-81 | tests/guardrails holds 79 direct children | tests/guardrails | 17c7b7f3c0ec8acc4c4d338ea27a8eb1fa2203da | present | 0 |
| R-82 | changelog.d holds 335 direct children | changelog.d | ece56396f47d31dfed7bebe6c69f6dda39f53d83 | present | 0 |
| R-83 | Route level specs/numbered/0/0/1/2/4/1 holds one child | specs/numbered/0/0/1/2/4/1 | b86cdb8134240596ecab84c015df8b79670b31b7 | present | 0 |
| R-84 | Route target folder specs/numbered/0/0/1/2/4/1/3 exists before the change | specs/numbered/0/0/1/2/4/1/3 | none | absent | 0 |
| R-85 | Route level specs/numbered/0/0/1/2 holds five children | specs/numbered/0/0/1/2 | 6fe73b539f8c9f60287ac92b27ae521e59c73503 | present | 0 |
| R-86 | Reference record spec exists for shape | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| R-87 | Precedent changelog fragment exists for an operator-facing docs change | changelog.d/issue-4916-readme-lean.md | 7a8043d62fde4da4b4079aa5bff3693ec68ea60e | present | 3 |
| R-88 | Changelog README defines the pull request name form | changelog.d/README.md | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 26 |
| R-89 | Changelog README requires one bullet for each change type | changelog.d/README.md | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 38 |
| R-90 | Changelog README adds no fragment for internal-only changes | changelog.d/README.md | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| R-91 | Spec route helper computes numbered routes with base five digits | .specify/scripts/powershell/spec-route.ps1 | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 4 |
| R-92 | Spec route helper resolves numbered paths under specs/numbered | .specify/scripts/powershell/spec-route.ps1 | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 34 |

Row count: 92. This count equals the `remote_checks` count in the STATUS file.

## Sources

- Brief: `C:\Users\jmorrison\.copilot\session-state\30878eb1-80d0-451d-bd0c-0b3624089852\files\spec-brief.md`.
- Local repository, read only: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`. Local HEAD is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, the same commit as remote `main` (`gh api repos/jmorrison-juniper/MistHelper/commits/main`).
- GitHub reads, `gh` only:
  - `gh issue view 4915` (open, labels `chore` and `docs`, no comments).
  - `gh issue view 4155` (closed on 2026-10-09 with the same stale count).
  - `gh issue view 4917` (open, title "Test failure: 23 guardrail tests fail on a Windows workstation").
  - `gh pr list --search 4915` (one result: pull request #4918, merged on 2026-11-24).
  - `gh pr view 4918` (state MERGED on 2026-11-24, head branch `docs/4916-readme-lean`, three changed files, 49 status check entries). The body begins "Closes #4916" and states that issue #4915 tracks the count. Changed files are `README.md`, `changelog.d/issue-4916-readme-lean.md`, and `documentation/operator-guide.md`.
  - `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1` (11,404 entries, not truncated).
  - `gh api repos/jmorrison-juniper/MistHelper/contents/` followed by the repository path and `?ref=main` (blob SHA and decoded text for each row that cites a line).
  - `gh api repos/jmorrison-juniper/MistHelper/commits/0788b975ea45df840d003dd997c684dbe847c448` (merge commit of pull request #4918 exists on `main`).
- Skills: none loaded. The issue touches Markdown and one Python guard test. No Podman, container, or Juniper device behavior applies.
- Mist API and mistapi: not applicable. The change calls no endpoint and no SDK method. This record makes no Mist claim. `documentation/MIST_API_GET_ENDPOINTS.md` and `documentation/MIST_API_MISSING_ENDPOINTS.md` were not used, because the issue concerns menu count text.
- Web: `web_fetch` was not used. No web source supports a claim in this record.

## Unverified

- U-1: The STE score of the operator guide on `main` was not measured, because this run does not run linters (rule 2). Pull request #4918 reports 97 in both modes for its branch version of the guide. The score on `main` is unverified.
- U-2: The ASD-STE100 dictionary mode was not checked. The user-level dictionary of this workstation was not inspected.
- U-3: The names of the 23 failing Windows guardrail tests were not checked. Issue #4917 verifies the title and the open state. Pull request #4918 reports the failure count.
- U-4: The pre-commit hooks were not run (rule 2). The hook configuration was read from the remote file.
- U-5: The remote content of `documentation/architecture.md`, `documentation/development-setup.md`, and `documentation/container-deployment.md` was not decoded. A local search found no operation count and no operator guide reference in those files. Local HEAD equals remote `main`, so the committed content matches.
- U-6: The working tree of the local repository was not checked with `git status`. Every claim in this record uses remote evidence.
