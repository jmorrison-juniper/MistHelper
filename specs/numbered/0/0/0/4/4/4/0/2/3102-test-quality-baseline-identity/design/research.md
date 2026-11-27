# Research: Test-quality baseline identity by content

**Issue**: 3102, "The test-quality ratchet baseline drifts on any line move, failing unrelated pull requests".
**Route**: `specs\numbered\0\0\0\4\4\4\0\2`.
**Spec record**: `specs\numbered\0\0\0\4\4\4\0\2\3102-test-quality-baseline-identity`.

## Method

This research read the issue, its comments, the linked pull requests, and the remote tree of `jmorrison-juniper/MistHelper` at `main`. It also read `jmorrison-juniper/misthelper-devtools` at the pinned commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.

Remote evidence outranks local files. Every cited line was read through the GitHub API. Local files supplied the measured counts in the measured facts table. No build, test, linter, formatter, install, or analyzer run occurred.

The remote tree query returned 11404 entries with `truncated` set to false. The misthelper-devtools pinned tree returned 411 entries with `truncated` set to false.

## Decisions

### D-1. Repair the identity key in misthelper-devtools and bump the pin

- **Decision**: Change the comparator in misthelper-devtools, release it, and bump the pin in `requirements-dev.txt`.
- **Alternatives**: (a) A MistHelper wrapper that re-anchors baseline lines before the gate. (b) A vendored copy of `baseline.py` in MistHelper. (c) The upstream repair and a pin bump.
- **Chosen**: (c).
- **Reason**: The comparator is in the shared package at `baseline.py` lines 48-57 and 85-126 (R-31 to R-34). The owner comments on 2026-10-20 require an upstream repair. A wrapper or copy would duplicate the gate contract.
- **Risk**: The release delays implementation. Tasks T001 to T009 run first, and this record stays complete while they wait.
- **Human decision**: No.

### D-2. Key each finding by a content anchor, not by the test function name

- **Decision**: The identity key uses the SHA-256 digest of the whitespace-normalized flagged line.
- **Alternatives**: (a) The test function name proposed in the issue. (b) The qualified name of the enclosing function from the syntax tree. (c) The content anchor.
- **Chosen**: (c).
- **Reason**: 176 of 733 baseline entries name no test in their explanation (84 `weak_is_not_none` and 92 `missing_fm_*`). The anchor works for every rule. It matches the content anchor that issue 3069 proposed for the CodeQL register.
- **Risk**: A reworded flagged statement counts as a new finding. Reviewers see that change, which matches issue 3069 acceptance 3.
- **Human decision**: No.

### D-3. Give file-level findings the sentinel anchor `file-level`

- **Decision**: The `_finding` helper in `missing_failure_mode.py` sets `content_anchor` to `file-level`.
- **Alternatives**: (a) Hash the text of line 1. (b) Leave the anchor empty. (c) Use the sentinel.
- **Chosen**: (c).
- **Reason**: The helper sets `line_number=1` (R-45). Its 92 baseline entries flag docstring or header text. A hash of line 1 would change when a header line is inserted, which breaks issue acceptance 1.
- **Risk**: A future detector that reports file-level findings must set the sentinel. Task T002 adds a test for the constant anchor.
- **Human decision**: No.

### D-4. Compare identity keys as occurrence counts

- **Decision**: Compare identity keys as multisets. Each key carries an occurrence count.
- **Alternatives**: (a) Sets, as the pinned comparator uses (R-33, R-34). (b) An ordinal suffix for each repeated key. (c) Multisets.
- **Chosen**: (c).
- **Reason**: Two identical flagged statements in one file share a key after the change. A set collapses them, so a second identical finding passes. 104 of 275 rule and file groups hold more than one baseline entry.
- **Risk**: Caution: an identical statement that replaces a removed statement in the same file nets to zero. Position cannot reveal that case. The `gate_removed` count shows the removal.
- **Human decision**: No.

### D-5. Keep line_number as information only

- **Decision**: Keep `line_number` in each baseline entry and in each `gate_new` line. Exclude it from the identity key.
- **Alternatives**: (a) Keep it in the key, as the pinned comparator does (R-32). (b) Remove the field. (c) Keep it as information.
- **Chosen**: (c).
- **Reason**: Issue acceptance criteria keep the line for readers. Excluding it removes the drift defect.
- **Risk**: The stored line goes stale after edits. The next write refreshes it, and the gate does not read it.
- **Human decision**: No.

### D-6. Remove unmatched occurrences in analyzed files, and report removals without failing

- **Decision**: `--prune-baseline` removes unmatched occurrences in files that the run parsed without a parse error. It keeps entries of other files. It drops entries of unscanned files, as it does today. The gate reports removals and never fails on them.
- **Alternatives**: (a) Keep the file-level prune (R-35, R-36). (b) Count-based prune for analyzed files. (c) Fail the gate on removals.
- **Chosen**: (b).
- **Reason**: Issue acceptance 3 requires that prune drops a stale entry. The file-level rule never drops a removed finding in a scanned file. Under multiset counts, a stale occurrence lets one later identical finding pass. Parse-error files are missing from the scanned set (R-39, R-40), so the current prune drops their entries.
- **Risk**: A detector regression can remove entries during prune. The prune refuses entries of files with parse errors, and the pull request lists each dropped entry.
- **Human decision**: No.

### D-7. Fail closed on a missing content anchor

- **Decision**: The loader rejects any baseline entry without a valid `content_anchor`. The gate exits 2. The loader does not read the old format.
- **Alternatives**: (a) Derive anchors at load time from line numbers. (b) A reader that accepts both formats. (c) Fail closed.
- **Chosen**: (c).
- **Reason**: Load-time derivation depends on line numbers, which drift. A dual reader keeps a compatibility path. AGENTS.md section "Code quality" (line 73, R-52) rejects compatibility shims and fallback paths.
- **Risk**: A pin bump without the migration fails the gate. Tasks T013 and T014 merge in one pull request.
- **Human decision**: No.

### D-8. Migrate by regenerating from current findings

- **Decision**: Run `--write-baseline` with the new release on a branch from `main`. Confirm the old gate exits 0 first. List every dropped entry in the pull request.
- **Alternatives**: (a) Add anchors to all 733 entries by script. (b) Edit the JSON by hand. (c) Regenerate.
- **Chosen**: (c).
- **Reason**: Twelve entries name a missing file (R-24), so no anchor exists for them. 34 entries name blank lines, and no syntax node starts on a blank line. Issue 3069 recorded 88 rows for its own migration. An earlier `--write-baseline` run removed 335 unmatched entries (R-30).
- **Risk**: Caution: the dropped count exceeds 46 when more entries do not match. Task T014 records the exact count and every dropped entry.
- **Human decision**: No.

### D-9. Print a `gate_removed` count and a second prune count

- **Decision**: Keep the existing `gate_scope`, `gate_new`, and `gate` lines. Add `gate_removed` for analyzed files. Add a second prune count line.
- **Alternatives**: (a) Remove silently. (b) Write a separate report file only. (c) Add stdout lines.
- **Chosen**: (c).
- **Reason**: Principles V and VII require visible evidence. Issue acceptance 4 asks that the gate report counts. The job step runs the command, and the job result depends on the exit code (R-04).
- **Risk**: A consumer that parses these lines breaks. Other consumers are unverified (Unverified item 6).
- **Human decision**: No.

### D-10. Keep a changed-scope pull request with no test file green

- **Decision**: A pull request that changes no test file exits 0 and prints `gate_scope: 0 files checked`.
- **Alternatives**: (a) Fail the gate. (b) Omit the scope line. (c) Keep it green and print the counts.
- **Chosen**: (c).
- **Reason**: The empty-scope path already prints the zero counts (R-51). Push runs scan every file (R-04, lines 623-632). A failure would block every non-test pull request.
- **Risk**: Caution: a pull request can add untested source code and pass until the push run. This gap exists today, and this change does not close it.
- **Human decision**: No.

### D-11. Place consumer tests in the existing scope test file

- **Decision**: Add a class `TestBaselineIdentity` to `tests/guardrails/local_test_quality_loop/test_scope.py`.
- **Alternatives**: (a) A new file in that folder. (b) A new folder. (c) The existing file.
- **Chosen**: (c).
- **Reason**: The folder holds five children (R-15). A sixth child breaks the Five-Item Rule (R-17). `test_scope.py` already runs the installed analyzer through `AnalyzerFixture` (R-14).
- **Risk**: The file grows past 700 lines (R-13 shows line 696 as the current end of file). Accepted.
- **Human decision**: No.

### D-12. Place upstream tests in existing test files and add no package module

- **Decision**: Update `test_baseline_differ.py`, `test_gate_decision.py`, and `test_cli.py`. Add no module to the package.
- **Alternatives**: (a) A new module in `src/misthelper_devtools/test_quality_analyzer/`. (b) The existing files.
- **Chosen**: (b).
- **Reason**: The package root holds 12 direct children at the pinned commit (R-55). A new module adds a child to a noncompliant parent. The identity resolver class goes in `baseline.py`.
- **Risk**: Edits to shared fixtures affect unrelated cases. Each file runs on its own.
- **Human decision**: No.

### D-13. Release misthelper-devtools 0.7.0

- **Decision**: Release version 0.7.0. The current version is 0.6.4 (R-49).
- **Alternatives**: (a) Version 0.6.5 as a patch. (b) Version 0.7.0 as the minor step for a breaking change in a 0.x release.
- **Chosen**: (b).
- **Reason**: The loader rejects baseline files without `content_anchor`. Older baselines fail after the upgrade.
- **Risk**: Readers that expect 0.6.x see a larger step. Accepted.
- **Human decision**: No.

### D-14. Change only the pip pin in MistHelper

- **Decision**: Change the pip pin in `requirements-dev.txt` line 197. Keep the reusable workflow pins at `79a5e459` (v0.6.4).
- **Alternatives**: (a) Move every pin to the new release. (b) Keep the workflow pins.
- **Chosen**: (b).
- **Reason**: The change alters the analyzer, not the reusable workflows. The reusable workflow pin appears at ci.yml line 1317 (R-53). AGENTS.md section "GitHub governance" assigns pin updates to Dependabot.
- **Risk**: Two misthelper-devtools versions run in one pipeline. The split already exists (R-06 and R-53), so this change adds no new split.
- **Human decision**: No.

### D-15. Choose reproduction entries from a live report file

- **Decision**: Select reproduction entries from `test_quality_analyzer_output/report.json` after a live run. Do not use the issue example rows.
- **Alternatives**: (a) The issue example rows. (b) A live report file.
- **Chosen**: (b).
- **Reason**: No explanation on main names `test_write_function_handles_empty`. Line 153 on main is blank (R-21). The report file names the findings that the current analyzer produces (R-50).
- **Risk**: The report file location depends on the analyzer default (R-50). The quickstart names that default.
- **Human decision**: No.

## Remote verification

Each row records one remote check. The table has 56 rows. The `remote_checks` array in `META_DIR\3102-STATUS.json` has the same 56 rows. The summary states the same count.

Result values: `present` means the path and line exist at the ref. `absent` means the path does not exist at the ref.

| ID | Claim checked | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | Baseline file exists and holds 733 entries | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 1 |
| R-02 | Ratchet settings file exists | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 1 |
| R-03 | Test quality ratchet job exists | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 602 |
| R-04 | Ratchet step comments and command for the gate scope | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 623-632 |
| R-05 | Type gate paths name src and product files, not tests | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-06 | Analyzer pin names commit 2239e7bd | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 197 |
| R-07 | Prune command is documented | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 33 |
| R-08 | Write-baseline removal of unmatched entries is documented | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 36 |
| R-09 | Guide says the gate_scope line counts files and findings | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 148 |
| R-10 | Guide forbids a baseline rewrite that hides a new finding | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 150 |
| R-11 | Known pitfall for the issue 2689 guard rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 560 |
| R-12 | Preflight test for live guides exists | tests/guardrails/local_test_quality_loop/test_guidance.py | main | 1f49b5fe3deea64d8e3bf3f5a49635f457d0819b | present | 774 |
| R-13 | Scope test class for analyzer runs exists | tests/guardrails/local_test_quality_loop/test_scope.py | main | 2c3645416c5c96cd6d1a788221a1ce04376ef447 | present | 456 |
| R-14 | Fixture runs the installed analyzer module | tests/guardrails/local_test_quality_loop/fixtures.py | main | 9c3228edb6070ade70ae4a1702927f81d3821c13 | present | 370 |
| R-15 | Folder holds five children and receives no new file | tests/guardrails/local_test_quality_loop | main | af80444b5b898c60d2a958025a7cdc6334b3a28f | present | 0 |
| R-16 | Writing rule for Simplified Technical English | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 42 |
| R-17 | Five-Item Rule in the constitution | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R-18 | Spec route uses base five with eight levels | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R-19 | Changelog name for a pull request | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 26 |
| R-20 | STE configuration file exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 1 |
| R-21 | Line 153 of the named test file is blank on main | tests/test_upgrade_portal_audit.py | main | 4d36aa4faf0d366b2ebadb70900344e6d37037c2 | present | 153 |
| R-22 | Line 26 holds the assert statement of the example entry | mist-ops-platform/tests/integration/test_e2e_smoke.py | main | c6b3946b56eb16667ad836710d60c623ec847080 | present | 26 |
| R-23 | Line 631 holds a call line, not a test definition | tests/unit/org/test_org_config_migration_conflicts.py | main | d236dbe09d02028d2400235697e251a4d9acc784 | present | 631 |
| R-24 | Missing test file named by 12 baseline entries | tests/unit/test_bulk_switch_upgrader.py | main | none | absent | 0 |
| R-25 | Path named in the issue body for the baseline | tools/test_quality_analyzer/baseline.json | main | none | absent | 0 |
| R-26 | Route folder for this issue | specs/numbered/0/0/0/4/4/4/0/2 | main | none | absent | 0 |
| R-27 | Earlier spec record folder for issue 3102 | specs/**/3102-* | main | none | absent | 0 |
| R-28 | CodeQL register script changed by pull request 3090 | scripts/codeql_verdict_register.py | main | none | absent | 0 |
| R-29 | CodeQL register test changed by pull request 3090 | tests/unit/test_codeql_verdict_register.py | main | none | absent | 0 |
| R-30 | Earlier removal of 335 unmatched entries | documentation/development-tooling-migration.md | main | 7a512059a87c07345728032ac684843d04005e9c | present | 121 |
| R-31 | Comparator identity function exists | src/misthelper_devtools/test_quality_analyzer/baseline.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | a5b505cd19a5f7cab6f017c43e35b6eab2cd9c5f | present | 48 |
| R-32 | Identity includes line_number | src/misthelper_devtools/test_quality_analyzer/baseline.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | a5b505cd19a5f7cab6f017c43e35b6eab2cd9c5f | present | 55 |
| R-33 | Diff builds dictionaries keyed by identity | src/misthelper_devtools/test_quality_analyzer/baseline.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | a5b505cd19a5f7cab6f017c43e35b6eab2cd9c5f | present | 96 |
| R-34 | Diff uses set differences | src/misthelper_devtools/test_quality_analyzer/baseline.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | a5b505cd19a5f7cab6f017c43e35b6eab2cd9c5f | present | 99 |
| R-35 | Prune keeps findings by file path | src/misthelper_devtools/test_quality_analyzer/baseline.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | a5b505cd19a5f7cab6f017c43e35b6eab2cd9c5f | present | 175 |
| R-36 | Stale advisory uses file paths only | src/misthelper_devtools/test_quality_analyzer/baseline.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | a5b505cd19a5f7cab6f017c43e35b6eab2cd9c5f | present | 160 |
| R-37 | Gate scope printer exists | src/misthelper_devtools/test_quality_analyzer/__main__.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | c0686f691c8acbdd1d05ea5a7a52c17eaefd5296 | present | 848 |
| R-38 | Gate path prints the gate_scope line | src/misthelper_devtools/test_quality_analyzer/__main__.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | c0686f691c8acbdd1d05ea5a7a52c17eaefd5296 | present | 377 |
| R-39 | Scanned set excludes parse-error files | src/misthelper_devtools/test_quality_analyzer/__main__.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | c0686f691c8acbdd1d05ea5a7a52c17eaefd5296 | present | 347 |
| R-40 | Parse errors are appended without a skipped record | src/misthelper_devtools/test_quality_analyzer/__main__.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | c0686f691c8acbdd1d05ea5a7a52c17eaefd5296 | present | 638 |
| R-41 | Prune message counts stale paths | src/misthelper_devtools/test_quality_analyzer/__main__.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | c0686f691c8acbdd1d05ea5a7a52c17eaefd5296 | present | 534 |
| R-42 | New finding output format | src/misthelper_devtools/test_quality_analyzer/__main__.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | c0686f691c8acbdd1d05ea5a7a52c17eaefd5296 | present | 858 |
| R-43 | Finding dataclass starts at line 53 | src/misthelper_devtools/test_quality_analyzer/detection/types.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 89ad1fbc1767be4076d8e3c6ac830c75ee00803e | present | 53 |
| R-44 | Zero-assertion finding uses the function line | src/misthelper_devtools/test_quality_analyzer/detection/weak_assertion.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 954ff75110492c221efba929f200225ac6415f54 | present | 248 |
| R-45 | File-level finding uses line 1 | src/misthelper_devtools/test_quality_analyzer/detection/missing_failure_mode.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 6e1da59538ea9df663d17d72d54f6d870f74a234 | present | 760 |
| R-46 | Untested finding names the analyzed source module | src/misthelper_devtools/test_quality_analyzer/detection/untested.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 9d351a0b4e4f277b72b48fbfe544cb86fa58dd0e | present | 151 |
| R-47 | Differ test builds keys with line numbers | tests/tools/test_quality_analyzer/test_baseline_differ.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | c9f22a5433b1bb8cc973370c6fad9ae23db7e497 | present | 62 |
| R-48 | Gate decision test helper takes a line number | tests/tools/test_quality_analyzer/test_gate_decision.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 113773068b27fd9d8ddd04cc6ad4373354ab010a | present | 20 |
| R-49 | Package version is 0.6.4 | pyproject.toml | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 0f52f10c8308a883314489e20970883c62d0943d | present | 3 |
| R-50 | Analyzer writes report.json and summary.md into test_quality_analyzer_output | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 45 |
| R-51 | Empty-scope path prints gate_scope with zero counts | src/misthelper_devtools/test_quality_analyzer/__main__.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | c0686f691c8acbdd1d05ea5a7a52c17eaefd5296 | present | 513 |
| R-52 | Code quality section rejects compatibility shims | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 73 |
| R-53 | Reusable quality gate issues workflow is pinned at v0.6.4 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1317 |
| R-54 | Weak assertion rule names an assert node line | src/misthelper_devtools/test_quality_analyzer/detection/weak_assertion.py | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 954ff75110492c221efba929f200225ac6415f54 | present | 207 |
| R-55 | Package root holds 12 direct children | src/misthelper_devtools/test_quality_analyzer | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 52d413dac4d93050f0d30d807afbf94a5905abf5 | present | 0 |
| R-56 | Report contract file exists and stays unchanged | src/misthelper_devtools/test_quality_analyzer/report.schema.json | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | d739b18c025dc7b73e340b3cdc8c8fa5900fdcd9 | present | 1 |

## Linked issues and pull requests

| Item | State | Relation to issue 3102 | Evidence |
| - | - | - | - |
| Issue 3102 | OPEN | Subject. Labels: ci, quality-gates, chore, in-progress, priority:P1, severity:high. | `gh issue view 3102`, comments of 2026-10-02, 2026-10-07, 2026-10-19, and 2026-10-20 |
| Issue 3069 | CLOSED 2026-09-20 | Precedent. Proposed a hash of the flagged line for the CodeQL register. | `gh issue view 3069` |
| Pull request 3090 | MERGED 2026-09-20 | Precedent pull request with three files. Two of those files are absent on main (R-28, R-29). | `gh pr view 3090` |
| Pull request 3101 | MERGED 2026-09-20 | Named in the issue as the reproduction. The historical CI output was not read. | `gh pr view 3101` |
| Pull request 3234 | MERGED 2026-09-23 | Search hit only. The body does not mention 3102. Not linked. | `gh pr view 3234` |
| Pull request 3268 | MERGED 2026-09-24 | Cites issue 3102. Edited two assertions in `tests/contract/upgrade_portal/test_org_upgrade_routes.py` to clear the ratchet. | `gh pr view 3268` |
| Pull request 4358 | MERGED 2026-11-13 | Changed the baseline file by 586 additions and 586 deletions. The 2026-10-20 reservation is no longer active. | `gh pr view 4358` |
| Issue 2689 | CLOSED 2026-09-16 | Source of the guard rule that prints counts and fails on unreadable input. | `gh issue view 2689`, R-11 |
| Issue 4142 | OPEN | Splits `tests/unit` into domain packages. Future file moves change baseline file paths. | `gh issue view 4142`, pull request 4358 file list |
| misthelper-devtools issue 42 | CLOSED 2026-10-03 | Earlier upstream report. The pinned code still keys on line numbers. | `gh issue view 42 -R jmorrison-juniper/misthelper-devtools` |
| misthelper-devtools commit 2239e7bd | Pinned | Equal to upstream `main`. The compare API reports the pin as five commits ahead of tag v0.6.4. | commits and compare API |
| misthelper-devtools commit e8e093d | Release 0.6.3 | Named in the 2026-10-19 comment as the pin. The current pin is different. | commits API and tags API |
| misthelper-devtools tag v0.6.4 at 79a5e459 | Tagged | The reusable workflow pin in ci.yml line 1317 names this commit (R-53). | tags API and R-53 |
| CI run 45774119357 | success | Head `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` on main. The job `Test quality ratchet (gate)` succeeded. | `gh run view 45774119357` |

## Measured facts

| Measure | Value | How it was measured |
| - | - | - |
| Baseline entries on main | 733 | Parsed the baseline blob 512da22b (R-01) through the contents API. |
| Baseline entries at the base of pull request 4358 | 733 | Parsed the same file at commit 816f42ba. |
| Entries named in the issue | 1,097 | No state on main or at the base of pull request 4358 holds 1,097 entries. The origin is unverified. |
| Distinct file paths | 202 | Counted in the parsed baseline. |
| Entries whose file is missing on main | 12 | All 12 name `tests/unit/test_bulk_switch_upgrader.py` (R-24). |
| Entries by rule | weak_zero_assertions 557, weak_is_not_none 84, missing_fm_http_5xx 42, missing_fm_http_4xx 38, missing_fm_empty_body 5, missing_fm_malformed_json 5, missing_fm_connection_error 1, missing_fm_connection_timeout 1 | Grouped by `rule_id`. |
| Entries whose explanation names a test | 557 | Matched the text `test_`. All 557 are weak_zero_assertions. |
| Entries whose explanation names no test | 176 | 84 weak_is_not_none and 92 missing_fm rules. |
| Rule and file groups | 275 groups, 104 with more than one entry | Grouped by `rule_id` and `file_path`. |
| Flagged lines by class | weak_zero_assertions: def 457, assert 11, other 45, blank 32, missing file 12. weak_is_not_none: assert 69, other 12, blank 2, def 1. missing_fm rules: line 1 for 92. | Read each flagged line in the local clone at HEAD `f03c6c9b`. The sampled blank line matched R-21. |
| Entries on blank lines | 34 | No syntax node starts on a blank line. The analyzer names node start lines (R-44 and R-54). |
| Pull request 4358 baseline diff | 586 additions, 586 deletions | Pull request files API. |
| Pull request 4358 entry match | 440 entries match exactly. 293 entries differ in file path or related source. Each entry keeps its line number. | Compared base and head entries by key with and without file path. |
| Example rows in the issue | No explanation names `test_write_function_handles_empty`. Line 631 names `test_a_clean_object_reaches_the_create_call`. Line 153 is blank. | Parsed the baseline and read R-21 and R-23. |
| Content anchor example | `assert app is not None` at line 26 gives `5201feb70a5f94ce6321d47d0e892442c87998aa1545b37e5f4950734bfcdcfb` | Normalized the line and computed SHA-256 over the UTF-8 bytes. R-22 names the blob. |
| Untested finding file path | The analyzer uses the source module path, not a test file path | `untested.py` line 151 uses the analyzed module path as `file_path` (R-46). |

## Sources

Local sources read in full or in ranges:

- `AGENTS.md` at the repository root.
- `.github\copilot-instructions.md`, sections for local gates, test quality ratchet, and known pitfalls.
- `.specify\memory\constitution.md`, Principle I and the governance section.
- `.specify\templates\spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`.
- `.venv\Lib\site-packages\misthelper_devtools-0.6.4.dist-info\direct_url.json`, which names commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.
- `.venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\baseline.py`. Its LF-normalized git blob is `a5b505cd19a5f7cab6f017c43e35b6eab2cd9c5f`, which equals the pinned blob.
- `.venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\__main__.py` and `detection\types.py`, read for line numbers that the remote reads confirm.
- Reference record shape. Remote tree listing of `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv` holds `analysis.md`, `plan.md`, `spec.md`, `tasks.md`, and `design` with `checklists`, `contracts`, `data-model.md`, `quickstart.md`, and `research.md`.

Remote sources read through the GitHub API with `gh`, read-only:

- `https://api.github.com/repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`
- `https://api.github.com/repos/jmorrison-juniper/MistHelper/contents/.github/test-quality-baseline.json?ref=main`
- `https://api.github.com/repos/jmorrison-juniper/misthelper-devtools/contents/src/misthelper_devtools/test_quality_analyzer/baseline.py?ref=2239e7bd468fd27e40c43f2b87fcd35a2e49672b`
- `https://api.github.com/repos/jmorrison-juniper/misthelper-devtools/git/trees/2239e7bd468fd27e40c43f2b87fcd35a2e49672b?recursive=1`
- The compare endpoint for tag `v0.6.4` against commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` (read-only, through gh).
- The compare endpoint for commit `2239e7bd468fd27e40c43f2b87fcd35a2e49672b` against `main` (read-only, through gh).
- Issue and comment URLs in the issue JSON, for example `https://github.com/jmorrison-juniper/MistHelper/issues/3102#issuecomment-6303386240`.

Web source attempt: a `web_fetch` of a raw GitHub file URL returned `WebFetchBlockedUrlError`. No web source supports any claim in this record.

## Unverified

1. The historical CI output of pull request 3101, including the 12 new findings and the six drifted rows in the issue. The CI logs were not read.
2. The origin of the 1,097 entry count in the issue. Neither main nor the base of pull request 4358 holds that count.
3. The number of live findings on main and the number of stale entries beyond the 46 provable entries. Only an analyzer run measures them, and rule 2 forbids that run in this step.
4. The stale status of the 57 entries whose flagged line is neither a definition nor an assert. The classes do not prove stale status.
5. Whether misthelper-devtools CI passes at `2239e7bd`. The upstream workflow runs were not read.
6. Whether any external consumer parses the gate output lines. The repository search found only the local job.
7. Whether issue 4142 will move the files named by current baseline entries before this change merges. Pull request 4142 was not read.
8. The detectors `tautological.py` and `missing_edge_case.py` in misthelper-devtools were not read. Their flagged-line semantics are unknown, and task T002 checks them.

## Skills

No local skill was loaded. The issue concerns a Python test gate and a JSON baseline. It does not involve Podman or Juniper device behavior.
