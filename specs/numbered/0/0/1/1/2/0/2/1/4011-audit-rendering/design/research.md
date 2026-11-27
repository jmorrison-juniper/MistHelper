# Research: Refactor: isolate audit renderer modules

Each decision lists the chosen option, the reason, the alternatives, and the risk. GitHub `main` is the truth source. Its commit is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The local HEAD has the same commit. Five unrelated local files are modified. None is in the audit package.

## Summary of findings

- Issue #4011 is open. Its body describes the flat audit layout from 2026-10-06.
- PR #4552 merged on 2026-10-31. It moved the renderer under `rendering/` and created `rendering/clusters/`. This is the 3824 layout.
- On main, the audit root holds five children. The rendering package holds five children. No helpers package exists.
- The issue target still applies. The rendering package must hold two children. The helpers package must hold five modules.
- The local commit `5b665c48` is diverged from main by 401 commits. This record rebuilds the change from main and does not reuse that commit.

## Linked work and PR state

| Item | State | Evidence |
|---|---|---|
| Issue #4011 | OPEN | Labels `refactor`, `complexity`, `src`. Five comments from 2026-10-06 to 2026-11-08. |
| Parent issue #3824 | OPEN | Title "Refactor: reduce nested source package child counts". |
| PR #4552 | MERGED 2026-10-31T09:27:15Z | Head `jmorrison-juniper-3824-audit-renderer-structure`. Closes #3824. Created the `rendering/clusters/` layout. Rows RC-01 to RC-09. |
| PR #4122 | MERGED 2026-10-10T05:06:30Z | Changed the hook guard file. The issue comments named it as a conflict. Now merged. |
| PR #4125 | MERGED 2026-10-10T20:34:56Z | Added the nested package guard and its baseline file. Row RC-31. |
| PR #4557 | MERGED 2026-11-05T10:57:12Z | Changed the symbol guard file. |
| PR #4607 | MERGED 2026-11-13T07:14:03Z | Changed the symbol guard file and the hook catalog CSV. |
| PR #4208 | OPEN | Changes `tests/guardrails/test_src_public_symbol_preservation.py`. The only open pull request with file overlap. |
| PR #3873 | MERGED 2026-10-06T01:14:24Z | Search hit for "4011". One file, a dependency update. Not a linked change. |
| Issue #4116 | CLOSED | Hook catalog move map. Related to PR #4122. |
| Issue #4118 | CLOSED | Nested package guard. Related to PR #4125. |
| Commit `5b665c48` | Exists on GitHub. Diverged from main. | Ahead 1, behind 401 (row RC-60). |
| Commit `63f5ad94` | Exists on GitHub. Diverged from main. | Final local tip named in the issue comments (row RC-61). |

## D-1. Target layout

- Chosen: Build the layout from the issue. Move the five helper modules into `rendering/helpers/`. Remove `rendering/clusters/`.
- Reason: The issue sets exact counts. Root holds 5, rendering holds 2, helpers holds 5. Only this layout meets rendering 2 and helpers 5. Main holds rendering at 5 and has no helpers package (rows RC-01 to RC-10).
- Alternatives:
  - Keep the #3824 `clusters/` layout and close #4011 as superseded.
  - Move only the delta, format, and time helpers, and keep `clusters/`.
- Risk: This change reverses the #3824 layout. The #3824 contract still names `clusters/` (row RC-40). A reviewer may ask to close the issue instead.

## D-2. Symbol guard rows

- Chosen: Replace the six flat-keyed rows in `MODULE_PATHS` with six rows keyed by baseline paths. The renderer row maps to itself.
- Reason: The symbol guard reads the baseline archive. It maps each baseline module to its current path (rows RC-25 and RC-26). Flat keys match no baseline path. Six rows keep the count from the issue.
- Alternatives:
  - Keep the flat rows and add six baseline rows. This duplicates the concept and leaves stale values.
  - Add five helper rows and drop the renderer row. This breaks the six-row count in the issue.
- Risk: The renderer row is not a move. It documents the canonical location and keeps the renderer under the symbol check.

## D-3. Hook catalog

- Chosen: Update the file path of seven active rows in `hook-catalog.csv`. Update the expected rows in the hook guard. Leave `python-inventory.csv` unchanged.
- Reason: The hook guard resolves each active row against current AST symbols (row RC-27). The inventory test pins a historical source revision, so the inventory must not follow moves (row RC-29). PR #4552 changed the same CSV. The summary tests count rows and distinct paths, and a one-to-one rename keeps those counts.
- Alternatives:
  - Keep the CSV and add a six-path map in the hook guard. The local commit used this approach. It does not match main practice.
  - Regenerate every catalog artifact. This changes historical evidence and adds scope.
- Risk: The change edits a file under `specs/2448`. Any later regeneration must keep the seven rows.

## D-4. No compatibility shims

- Chosen: Remove each old path. Add no alias module, wrapper, re-export, or fallback import.
- Reason: `AGENTS.md` says not to add or keep a compatibility shim (row RC-53). The issue says not to leave aliases at old paths.
- Alternatives: Keep import shims for one release. This conflicts with the repository rule.
- Risk: An unseen caller breaks at import time. The retired-path scan and the import checks detect each caller in tracked files.

## D-5. Consumers without an edit

- Chosen: Make no edit in `audit_analysis_ops.py`, `junk/diag_rbo.py`, `tests/run_audit_integration.py`, or `tests/unit/marvis/mist/access/audit/test_audit_analysis_ops.py`.
- Reason: Each file already imports the canonical renderer path (rows RC-14, RC-16, RC-17, RC-23). An edit would be a no-op. The consumer test still runs and still passes as an acceptance check.
- Alternatives: Edit the four files to match the issue text. This creates churn with no behavior change.
- Risk: A reviewer may expect a diff in these files. The record names the verified state.

## D-6. Structure guard with exact counts

- Chosen: Add `tests/guardrails/test_audit_rendering_structure.py`. It has one exact-count test, one retired-path scan test, and three failure proofs.
- Reason: The issue requires exact counts (acceptance criteria 3 to 5). The nested guard enforces only the limit of five (row RC-31). Guards belong under `tests/guardrails/`. `AGENTS.md` requires each guard to prove that it can fail.
- Alternatives:
  - Rely only on the nested guard. This cannot enforce exact counts.
  - Add the checks to the #3824 unit test. This puts a guard in the wrong folder.
- Risk: The guard uses `git ls-files`. It needs a git checkout. The nested guard already has the same need.

## D-7. Nested package guard unchanged

- Chosen: Keep `tests/guardrails/nested_package_baseline.json` and the expected message unchanged.
- Reason: No audit directory exceeds five children on main (row RC-30). The change removes one directory (`clusters`) and adds one directory (`helpers`). The examined count stays the same (row RC-31). The guard counts directories that hold tracked Python files, so a leftover cache folder does not count.
- Alternatives: Update the baseline or the expected message. This adds churn and hides a real count change.
- Risk: If the examined count changes, the guard fails. Task T024 checks this.

## D-8. Changelog fragment

- Chosen: Add `changelog.d/issue-4011-audit-rendering.md` with one `### Changed` heading and one bullet.
- Reason: The constitution requires one fragment for each change (row RC-56). The changelog rule in the repository instructions limits fragments to user-visible changes (row RC-58). The fragment satisfies both rules. The #3824 fragment is the model (row RC-37).
- Alternatives: Skip the fragment for an internal refactor. This breaks the constitution rule.
- Risk: Low. The bullet must name issue #4011.

## D-9. Record layout

- Chosen: Use the record layout of the brief. The folder holds `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`.
- Reason: The brief governs this record. The issue needs a routed specification, which this layout satisfies. The three-file layout of the local commit cannot hold the analysis and the design files that the brief requires.
- Alternatives: Use the three-file layout of commit `5b665c48`. This record rejects it because its paths and counts are stale (see analysis.md).
- Risk: The local commit record and this record differ. The implementation must use this record.

## D-10. Delivery and naming

- Chosen: Use branch `chore/4011-audit-rendering`. Use the commit type `refactor`. Keep the work local until the coordinator assigns the serial slot.
- Reason: `AGENTS.md` lists `feat`, `fix`, `chore`, and `docs` as branch types, and it allows a more precise commit type (row RC-53). The issue requires local work until the slot.
- Alternatives:
  - Open a pull request now. This breaks the serial slot rule.
  - Use branch `refactor/4011-audit-rendering`. This branch type is not in the list.
- Risk: Pull request #4208 changes the symbol guard file. The rebase must resolve only the `MODULE_PATHS` block.

## D-11. Gate scope

- Chosen: Run every applicable gate from the local gates table before the push. Run both `pytest-chunks` shards locally.
- Reason: The repository rule requires every applicable gate (row RC-54). The gates table lists both shards as local gates.
- Alternatives: Run the shards only in CI. This skips a gate that the table lists as local.
- Risk: The two shards need a long local run. The run must finish before the push.

## Remote verification

Ref `main` is commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` unless a row names another ref. Blob SHAs come from the recursive tree of `main`. A local file hash matched the tree SHA when a row names a local path. Line numbers come from a decoded remote body or from a local file that matches the tree SHA.

| Row | Claim | Path | Ref | Blob SHA | Result | Line |
|---|---|---|---|---|---|---|
| RC-01 | Renderer defines AuditReportRenderer | src/mist/access/audit/rendering/renderer.py | main | 1443aefcfd8098e3fac28fce1cfd425bef25782c | present | 54 |
| RC-02 | Renderer imports helper and cluster modules from retired paths | src/mist/access/audit/rendering/renderer.py | main | 1443aefcfd8098e3fac28fce1cfd425bef25782c | present | 22 |
| RC-03 | Delta helper defines DiffKeyContext | src/mist/access/audit/rendering/_renderer_delta.py | main | 19e344f5a71aad4dcec1f5c9695154f85d39761b | present | 22 |
| RC-04 | Format helper defines format_delta_html | src/mist/access/audit/rendering/_renderer_format.py | main | d4947e5b82299a1cb09849b501055f877a0b2b79 | present | 28 |
| RC-05 | Time helper defines epoch_to_readable | src/mist/access/audit/rendering/_renderer_time.py | main | a9e9a1cca4203af96562710f86af6130a82bd7fb | present | 14 |
| RC-06 | HTML cluster defines _HtmlCluster and imports three helpers from retired paths | src/mist/access/audit/rendering/clusters/_renderer_html.py | main | 169502dd7c48bbbf8836746e9a93c6f2adb4f82a | present | 43 |
| RC-07 | Mermaid cluster defines _MermaidCluster and imports two helpers from retired paths | src/mist/access/audit/rendering/clusters/_renderer_mermaid.py | main | 49e04be850afaf7f8ac9f6fce12df567b9249d3d | present | 27 |
| RC-08 | Rendering package init holds one docstring | src/mist/access/audit/rendering/__init__.py | main | 13ab42ce050296f0482a9305297ab8b563c53b94 | present | 1 |
| RC-09 | Clusters package init holds one docstring and this change removes it | src/mist/access/audit/rendering/clusters/__init__.py | main | b60bec2081415798262781b08e2a8f7001e80b6f | present | 1 |
| RC-10 | Helpers package is absent on main | src/mist/access/audit/rendering/helpers | main | none | absent | 0 |
| RC-11 | Audit root holds the analyzer module | src/mist/access/audit/analyzer.py | main | f74802fbb3e0aa99e01003a1ed7de76f451f9852 | present | 0 |
| RC-12 | Audit root holds the filter module | src/mist/access/audit/filter.py | main | 4f3754fa618b6a7ad08aa35127f80f294abfce30 | present | 0 |
| RC-13 | Audit root holds the time parser module | src/mist/access/audit/time_parser.py | main | 5820b92c646e138533c5b0070088a7095d0c0a85 | present | 0 |
| RC-14 | Audit operations module imports the canonical renderer path | src/mist/access/audit/audit_analysis_ops.py | main | dbd8f92a3779e1ef1abef6be90e5f3c5940cdaeb | present | 20 |
| RC-15 | Audit operations module passes api_kwargs into the SDK call (pre-existing, out of scope) | src/mist/access/audit/audit_analysis_ops.py | main | dbd8f92a3779e1ef1abef6be90e5f3c5940cdaeb | present | 55 |
| RC-16 | Diagnostic script imports the canonical renderer path (no edit) | junk/diag_rbo.py | main | bb919a6e6c5f4cde417ddd6f5cae88cedcfa2e2f | present | 5 |
| RC-17 | Integration runner imports the canonical renderer path (no edit) | tests/run_audit_integration.py | main | 92f5ca5e59ce132856d474373abdf3099a4a850e | present | 11 |
| RC-18 | Renderer test imports the delta helper from a retired path | tests/test_audit_renderer.py | main | 76d4aa1f3d47e03825598e59ae91745dccb7215e | present | 15 |
| RC-19 | Format wave test imports the format helper from a retired path | tests/unit/marvis/mist/access/audit/test_renderer_format_wave9.py | main | 0a704c33e54a2d791d5d6409f7f12fb3b6c5296f | present | 10 |
| RC-20 | Time wave test imports the time helper from a retired path | tests/unit/marvis/mist/access/audit/test_renderer_time_wave9.py | main | f5e56e59d09954402a2a7376563f36ba7421a2e4 | present | 11 |
| RC-21 | Structure test lists six canonical renderer modules | tests/unit/marvis/mist/access/audit/test_renderer_structure_issue_3824.py | main | 31bac05a99d745c4ad9a4a341d5e04ddf86a8812 | present | 8 |
| RC-22 | Structure test lists six retired flat renderer paths | tests/unit/marvis/mist/access/audit/test_renderer_structure_issue_3824.py | main | 31bac05a99d745c4ad9a4a341d5e04ddf86a8812 | present | 17 |
| RC-23 | Audit operation consumer test imports the audit operations class (no edit) | tests/unit/marvis/mist/access/audit/test_audit_analysis_ops.py | main | cb99ba3ac76d5eafb99e05f1afd218d257294302 | present | 24 |
| RC-24 | Legacy test folder tests/unit/audit is absent | tests/unit/audit | main | none | absent | 0 |
| RC-25 | Symbol guard maps six flat renderer keys that no baseline path matches | tests/guardrails/test_src_public_symbol_preservation.py | main | 08f978e755abdf643e7a6d826811401f710883f8 | stale | 82 |
| RC-26 | Symbol guard checks each baseline module against its mapped path | tests/guardrails/test_src_public_symbol_preservation.py | main | 08f978e755abdf643e7a6d826811401f710883f8 | present | 348 |
| RC-27 | Hook guard expects the renderer rows at 3824 paths | tests/guardrails/test_performance_hook_catalog.py | main | 36593fd74460c1023614fb84e8523303c94ea507 | present | 277 |
| RC-28 | Hook catalog holds seven renderer rows at the 3824 paths | specs/2448-misthelper-performance-monitoring/artifacts/hook-catalog.csv | main | ee7a997df2dba3086122086f16a21d4807b23509 | present | 80 |
| RC-29 | Inventory CSV is historical and must not change | specs/2448-misthelper-performance-monitoring/artifacts/python-inventory.csv | main | 96a433783013ac8c97f6bcb01bcebdb0a067a140 | present | 0 |
| RC-30 | Nested baseline holds no entry for an audit directory | tests/guardrails/nested_package_baseline.json | main | 0d6c5ca933d83a4721c0bcc7220f69905fcf81f5 | absent | 0 |
| RC-31 | Nested guard pins the examined-count message | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 176 |
| RC-32 | Structure guard file is absent (planned new file) | tests/guardrails/test_audit_rendering_structure.py | main | none | absent | 0 |
| RC-33 | Changelog policy guard exists | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| RC-34 | Test quality preflight guard exists | tests/guardrails/local_test_quality_loop/test_guidance.py | main | 1f49b5fe3deea64d8e3bf3f5a49635f457d0819b | present | 0 |
| RC-35 | Test quality baseline holds no finding for the touched renderer tests | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | absent | 0 |
| RC-36 | Changelog fragment for issue 4011 is absent (planned new file) | changelog.d/issue-4011-audit-rendering.md | main | none | absent | 0 |
| RC-37 | Changelog model fragment for issue 3824 exists | changelog.d/issue-3824-audit-renderer-structure.md | main | d8f9e39f12be2c9797eeb5afe6bea6f1b12a9f41 | present | 3 |
| RC-38 | Route folder for issue 4011 is absent | specs/numbered/0/0/1/1/2/0/2/1 | main | none | absent | 0 |
| RC-39 | Route script sets base 5 and width 8 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-40 | Historical #3824 import contract names the clusters layout (not edited) | specs/numbered/0/0/1/1/0/2/4/4/3824-audit-renderer-structure/design/contracts/python-imports.md | main | 6d939294a7dc005a8a1098ae275e90b904f052d5 | present | 0 |
| RC-41 | CI path variables for mypy, vulture, pydocstyle, and interrogate | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-42 | Bootstrap script exists for a new worktree | scripts/bootstrap_worktree.py | main | e16515ffa789cca7d0bdd7e9789898588e5f1312 | present | 0 |
| RC-43 | Menu reference generator exists | scripts/generate_menu_wiki.py | main | f959225275536743e93bc95d37cb015865a73d53 | present | 0 |
| RC-44 | Line length limit is 120 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 202 |
| RC-45 | Resolver holds no audit module string | src/foundation/runtime/config/source_dependency_resolver.py | main | 18c0e2b88560614a4c987510032fea4946b0fc7c | absent | 0 |
| RC-46 | Historical plan 1008 (not edited) | specs/1008-top20-violations-remediation/plan.md | main | 37995bba59a22009b5aa852a7b87b1e8025925be | present | 0 |
| RC-47 | Historical plan 1013 (not edited) | specs/1013-misthelper-refactor-hot-classes/plan.md | main | 9fb00e5871f5e921974651ab2c1d12c7bc63b1db | present | 0 |
| RC-48 | Historical plan 1924 (not edited) | specs/1924-failure-evidence/plan.md | main | d03c912c1e929346704a36833b5ffe2d9568484f | present | 0 |
| RC-49 | Historical test map for issue 4142 names audit renderer test paths (not edited) | specs/numbered/0/0/1/1/3/0/3/2/4142-unit-test-domain-packages/design/standalone-test-map.md | main | fbff5ed89e54aa1519e247afdb23f8b800378908 | present | 0 |
| RC-50 | OpenAPI file names the logs search operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 12141 |
| RC-51 | Menu API doc names the audit endpoint and the audit operations class | documentation/menu-api/safe.md | main | c4c10e2ed30aeb6617716a6d0a90de7f36ed7ad1 | present | 335 |
| RC-52 | Pinned mistapi 0.64.1 defines listOrgAuditLogs (installed SDK file) | .venv\Lib\site-packages\mistapi\api\v1\orgs\logs.py | local-venv | 049f0f99642ac23b96ce59d9946aca4320d53f0e | present | 93 |
| RC-53 | Generic rule file names the compatibility shim ban and branch types | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| RC-54 | Repository instructions hold the local gates table (lines 50-76) and the move gates table (lines 261-273) | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RC-55 | Constitution Principle I states the five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-56 | Constitution requires one release-note fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| RC-57 | Repository requires Python 3.15 or newer | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 20 |
| RC-58 | Repository changelog rule limits fragments to user-visible changes | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| RC-59 | Repository rule limits each structural directory to five children | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 167 |
| RC-60 | Legacy implementation commit 5b665c48 exists on GitHub and diverges from main | commit 5b665c48f2cc92e69505a443f9895de8271d2031 | main | none | stale | 0 |
| RC-61 | Final local tip commit 63f5ad94 exists on GitHub and diverges from main | commit 63f5ad9477b0c39363263b5e759bf30f67471048 | main | none | stale | 0 |

## Sources

- Repository files in the working tree matched their remote blob SHAs by `git hash-object`.
- Files checked: `AGENTS.md`, the repository instructions, the constitution, the audit files, the guards, and the CSV artifacts.
- GitHub reads used `gh issue view`, `gh pr list`, `gh pr view`, and `gh api` for the tree, contents, commits, and compare endpoints.
- Read-only git commands ran: `git hash-object`, `git show`, `git status --porcelain`, `git rev-parse`, and `git ls-tree`. No checkout, fetch, branch, commit, or push ran.
- Local SDK file: `.venv\Lib\site-packages\mistapi\api\v1\orgs\logs.py` (mistapi 0.64.1, row RC-52).
- No URL was fetched. No `web_fetch` call ran. No skill was loaded because this change does not touch container, Juniper device, or Podman behavior.

## Unverified

- U-1: Collected test counts. Reason: this task does not run tests (brief rule 2). The implementation records the counts in task T003.
- U-2: Gate results for ruff, black, mypy, pylint, bandit, radon, vulture, pydocstyle, interrogate, ste-linter, markdown-link-check, symbol-diff, and test-quality-analyzer. Reason: this task does not run gates.
- U-3: The remote branch that holds commit `5b665c48`. Reason: the commit lookup returns the commit. The branch lookup did not run.
- U-4: CI status on `main` at commit `f03c6c9b`. Reason: the check-run reads did not run.
- U-5: Branch protection and required checks. Reason: the settings were not read. The repository says the protection applies where the plan permits.
- U-6: The safe sweep result. Reason: the sweep needs a runtime and a credential policy check. It did not run.
- U-7: Whether the symbol guard passes after the rebase onto a newer `main`. Reason: the baseline changes after each merge. The rebase must rerun the guard.
