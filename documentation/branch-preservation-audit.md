# Branch preservation audit

Status note, 2026-09-25: this file is a historical audit report. The final
result is the tag archive described below. The branch table records the audit
evidence that existed before the archive tags replaced the branches.

Date: 2026-09-17.

This audit reviewed the remote branches under `preservation/*` and `recovery/*`.
The count before the audit was 119 branches.
The count after the audit was 0 branches.

Every one of those 119 commits still exists. A tag holds each one. Read
"The tag archive" below before you look for a branch that is no longer there.

## Result summary

The first pass of this audit deleted no branch, because its content comparison
did not finish. A second pass replaced that pass. This section records the
second pass.

A faster comparison finished the measurement. For each branch the comparison
read the merge base with `main`, listed the files the branch changed, and
compared the object identifier of each file against the `main` version.

| Group | Count | Meaning |
| - | -: | - |
| `DIFFERS` | 108 | At least one changed file does not match `main`. |
| `NO_BASE` | 7 | The branch shares no merge base with `main`. |
| `CONTAINED` | 2 | Every changed file matches `main` exactly. |
| `NO_CHANGE` | 2 | The branch changed no file against its merge base. |

Only 4 of the 119 branches proved safe to delete on content alone. A bulk delete
of the other 115 was not safe, and a branch-by-branch judgment needed a reader.

## The tag archive

The audit took a third path instead of a delete or a keep. It moved every
branch to a tag.

A tag holds a commit for as long as the repository lives, exactly as a branch
does. A tag does not appear in a branch list, so the branch list became short
without the loss of a single commit.

The steps ran in this order.

1. Read the commit identifier of each of the 119 branches.
2. Create one tag for each branch, named `archive/<the branch name>`.
3. Push every tag to `origin`.
4. Read the tags back from `origin` and compare each commit identifier against
   the branch it came from. The comparison reported 0 tags missing and 0 tags
   with a wrong commit identifier.
5. Confirm that no worktree and no open pull request used any of the branches.
   The check reported 0 blocked branches.
6. Delete the 119 branches. The delete reported 119 successes and 0 failures.

The tag push and the verification both finished before the first delete ran.

## Recover a branch from its tag

```powershell
git fetch origin --tags
git branch <the branch name> archive/<the branch name>
git push origin <the branch name>
```

For example, this command restores one rescued stash.

```powershell
git branch preservation/rescue-stash-main-1-20260912 archive/preservation/rescue-stash-main-1-20260912
```

Warning: do not delete a tag under `archive/`. Each tag is the only remaining
reference to its commit. A deleted tag lets the garbage collector remove the
commit, and no other copy exists.

## Why the easy tests give a wrong answer here

A reader who repeats this audit will meet two traps.

A difference against `main` reports every branch as different. The branches date
from 2026-09-11 through 2026-09-14, and `main` gained thousands of changes after
that date. The difference measures the growth of `main`, not the content of the
branch.

A count of unique commits also misleads. This repository squashes every merge,
so a branch whose work already reached `main` still shows its original commits
as unique. The measurement reported 55 branches with exactly one unique commit.

The comparison that works reads the merge base first, then compares only the
files that the branch itself changed.


## Repeat commands

Run these commands from the audit worktree.

```powershell
git fetch origin main
git fetch origin '+refs/heads/preservation/*:refs/remotes/origin/preservation/*' '+refs/heads/recovery/*:refs/remotes/origin/recovery/*'
git worktree list
gh pr list --repo jmorrison-juniper/MistHelper --state open --json number,headRefName,title --limit 200
git for-each-ref refs/remotes/origin/preservation refs/remotes/origin/recovery --format='%(refname:short)|%(objectname)'
git merge-base origin/main origin/<branch>
git diff --name-only <base> origin/<branch>
git diff <base> origin/<branch> -- <file>
git diff origin/<branch>:<file> origin/main:<file>
```

The audit used the repeat commands above.
The first audit pass also started a full file comparison script.
That first script did not complete before the first report deadline.
The second pass above replaced that incomplete pass.

## Branch table

| Branch | Commit SHA | Group | Reason |
| - | - | - | - |
| `preservation/1375-branch-head-20260911` | `9b04d1ee44410c3c4522ab501e57cc6061cf5828` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/1375-recovery-dirty-20260911` | `0c01313020f792f38ab357a7948a73ee53b1dad0` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/1376-dirty-20260911` | `cf1c51b7474ce78f7492c8dd82fcfb0ffe4b6dde` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/1376-recovery-commit-20260911` | `bba37590b3a67c33d2109986532ea6bef3d365ed` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/1380-dirty-20260911` | `4a9de16ff5c8b2dac1283a9807b3e5bd62044e63` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/1381-branch-head-20260911` | `5ea0968e46ee1a3f74fed76079d016221fc3a941` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/1384-branch-head-20260911` | `c8808e42ca220fec3fe049506b1e263baa6f1d8f` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/1395-dirty-20260911` | `dfdbac04d59328207313e729d4c9b02d2bdb36e4` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/1400-branch-head-20260911` | `4ee5b83fb07b6bdc9202a43442991780bf75e7d1` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/1402-branch-head-20260911` | `a16e4f22dfe372203ed60b682926eeecb112e17b` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/1980-fix-1840-thread-scan-20260912` | `66d0a4367d0ee072e36d07d472b7b3f623a18b5d` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/1980-jmorrison-jnpr-ci-pytest-gate-failure-20260912` | `d5471cefe028892f81bdd0e68acea4d80190accc` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/1980-jmorrison-jnpr-production-readiness-sweep-20260912` | `93d60517d566fe12e9b7839e4fb6dd7c1520d5e3` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/1980-ops-gate-fix-20260912` | `99cdca8ecd981986551394f3d4cc9b94470a070a` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/2447-active-work-20260912` | `228dd7ced9d2eb89ec984b92e3c758cf5ade78a9` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/2447-active-work-20260913` | `9ebc8ea7c87add09bcac87737b9bae25644ee4e6` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/2447-original-branch-20260912` | `c85264218969faf9d55c8f9925b862c32e01f72e` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/2447-site-lock-branch-20260913` | `2f21084ccea125eeddb596885dcbf9215d926d45` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/2482-delivery-wip-20260912` | `46fec6c44f06df6bf88280e9ef20dd4ac159abf8` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/2482-performance-hook-catalog-20260912` | `e7cd9c3c92f2095f0f770756b8325a0ee552449c` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/2488-superseded-pr2504-20260912` | `b37e4d57e64cdcf2f7aabfa4fde14237cee78afe` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/2488-superseded-pr2504-final-20260912` | `a81d6b4e3dd167c17a6965a67ac504487a5d110c` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/2495-superseded-pr2502-20260912` | `5fadb32b32c65f53a952ae8e380afc10a7468765` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/2530-remote-tip-20260912` | `0d6e521b65a94e111376ed60a6afc15145c10460` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/2564-superseded-pr2603-20260913` | `b51072413ce266bbbe00fa522f38570499b641af` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/2651-remote-tip-20260914` | `63da786b3c73bf94f605576e661d26689b3f2139` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/2651-remote-tip-b-20260914` | `d842f46de95191539fcb741f82cc796263a6e8f6` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/868-branch-head-20260911` | `ee8171842d95286e49791fc4094e126bad5770f6` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/audit-pr-2280-closed-unmerged-20260913` | `c35debc68e1430ae286c1df54d5fda4df531f314` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/audit-pr-2374-closed-unmerged-20260913` | `7e5036a5c89b11e0b5cbd23b1138618c514ed182` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/audit-pr-2382-closed-unmerged-20260913` | `a0fe246018e76291d82a598c69e48eece3ab000e` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/audit-pr-2391-closed-unmerged-20260913` | `a0fe246018e76291d82a598c69e48eece3ab000e` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/audit-pr-2453-closed-unmerged-20260913` | `7d1a7f5ba0f02873033d8284eb25359f90d9d3b3` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/audit-pr-2454-closed-unmerged-20260913` | `1a0532da3e6de3e08828795e453e816fb1608992` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/audit-pr-2457-closed-unmerged-20260913` | `4ff8c4667b7fe51f8a10f6367bd509467f655285` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/audit-pr-2464-closed-unmerged-20260913` | `930f0a5b029dde8799a49d19898f07414326efd6` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/audit-pr-2534-closed-unmerged-20260913` | `d158d7107d901c0f7e43624cb3b696567269fe84` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/audit-rescue-mh-1741-20260913` | `da6a994465ff9371cab92cfe4d34c57f505c4b06` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/audit-rescue-mh-2596-nogit-20260913` | `6a0a57382a55c22e2424b0ec4b30f64dab1aa511` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/audit-rescue-mh-2624-20260913` | `1b4511eefa3f52f91adcca852ecb1578eca1889c` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/audit-rescue-mh-2624-final-20260913` | `bfeed9c955cf6cfaac9b7db74e014f41facf2cd4` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/audit-rescue-mh-2624-latest-20260913` | `f6ad266dd518b6cf8077e2e4dbb9c825bcad8449` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/audit-rescue-mh-entry-20260913` | `e241850fa4f8f2d163cc24bf02e839282ba57668` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/audit-rescue-mh-fix-2563-head-20260913` | `6787db5c23dcf45cd829030e4fac5bf1f4446556` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/bot-claim-integration-20260912` | `80843bdbed31a75f7d03b86aa65da8b93ad181dc` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-coord-1371-dirty-20260912` | `b156eecc7a33c1c0e783dd87e19e4ce215294ec3` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-head-mh-1789-20260912` | `3ecace748805b9eb41580edf70eb0b4f7475d966` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-head-mh-1897-20260912` | `6d89d404915ff59ebb7746d80a056ab6fb9964f9` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-head-mh-1948-wt-20260912` | `b208e6344d3b41ba0e14cc4dbbaf697fa449dd50` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-head-mh-2383-20260912` | `ff9dc2b6fd798c06bf44ea506e952caa28517061` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-head-mh-2384-log-rotation-20260912` | `012f9a422145ec942e13e6d32ac2d6f8ee50cf7f` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-head-mh-2395-recent-files-20260912` | `c89f01be2a27fc9169facc114f89007e20bf51f2` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-head-mh-2396-20260912` | `b03d6f12fc86d153545236d4b690a730203e2971` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-head-mh-2398-favicon-20260912` | `cb1d0c3387892d5e4b9df8561f306577b8cc9ada` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-head-mh-2399-operations-counts-20260912` | `3a54b368e3c9e4346dca234ed6308724c008804a` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-head-mh-coord-1372-20260912` | `6cd96503e1fa809a95ad698a45aa5f31fe08d309` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-head-mh-coord-1375-20260912` | `e68da39ccc13ca45fac960a2725bce786cd2dde6` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-head-mh-coord-1380-20260912` | `95e524cb9f869a59f0fd9b96268244f720137724` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-head-mh-coord-1384-20260912` | `e9be4bfb534bd1e95b41a6c5afb7bcd4c00b81e4` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-head-mh-coord-1402-20260912` | `8b1da2e7c440cba416353d15f774862f0ed42a4f` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-head-mh-wt-2397-20260912` | `51f80e92a0c23914b78c6b776e7a1b17cc435c44` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-mh-1375-dirty-20260912` | `dc6c19188da916e7bc2e0a4048df95dbb078de0e` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-mh-1376-dirty-20260912` | `d77faed53786c446175547ce3402440d5838f5b8` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-mh-1380-dirty-20260912` | `47f0076b73967b9d6cdc6dc7c320f97e83f23012` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-mh-2436-dirty-20260912` | `784049d25de823a456110808a51480c5045adfee` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/final-mh-wt-dirty-20260912` | `dbcb134bce803e0c95cd60ccc69bef06a5b1f6aa` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/fix-2495-favicon-before-rebase-20260912-0039` | `f1d12d02f1a47479817f3e48bb20ccb653d07839` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/orphan-2378-snapshot-20260911` | `24adb04d9964e18150c2c1680073f29b0b9d4aac` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/orphan-coord-1377-snapshot-20260912` | `e349bb5c9cd2309ce62d8bedfe9e65ff5b10f133` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/orphan-perfdeliver-snapshot-20260913` | `2ff0114efd63fc9c2e97ab595b3ce65d50fa6273` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-1771-complexity-20260912` | `b8fe20a0d241087460456c9ba8f1fbbbe0f62c14` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-code-misthelper-dirty-20260912` | `a01406abe642023f26340627713c84c3edf9b6ec` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-dependabot-hypothesis-20260912` | `0e87d15be593f08ad8c293e37588ce0f716a9e00` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-dependabot-openai-gte-20260912` | `0949c1c439b64e0c3e97d15e7dccf0a5d55c893e` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-dependabot-pylint-20260912` | `7b79a4724b00d875bdd3bb93c1a180e3f729dd15` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-dependabot-ruff-20260912` | `f8f8cc08a2eddd72a94e0c974052985445f9a26b` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-docs-1757-spec-module-paths-20260912` | `23552f77efb9903835b15777cf597d50790c177a` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-entry-offline-20260913` | `0759ceb1c09c99593b2a7447026e8dba8ca139b2` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-fix-1763-mermaid-lint-20260912` | `3cfd6d89cb0f64ee025f1152d3a97e5a501d0978` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-lint-1795-commit-20260912` | `01e1073237f912287c0dfa23eeed9505e1c57743` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-lint-1795-handoff-20260912` | `8f387929a3de25563bf6fd414dc5840a59d1664a` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-mh-2443-dirty-20260912` | `b034eb403df32971fd48d8ab561cfe9ad0748939` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-mh-bytes-head-20260913` | `d80b2f381e895e7e0f97af01a7b05578aaf856f8` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-mh-entry-2-20260913` | `8d451725847c118d073f2bfc80e182bc64d48387` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-mh-entry-3-20260913` | `f1f926c0bb47253408f66bfa8bca4c3bdbaed51e` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-mh-entry-4-20260913` | `bbe04b446888c806d4fd9708e70c3d29efc8f9ab` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-mh-entry-final-20260913` | `672c11d010eefcffb8ee08d2c20f453670e7ab73` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-mh-f2-1708-20260913` | `0e0607ffb1a7b10a56feb775ab671a806be04928` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-mh-f2-1899-dirty-20260913` | `55f6576bf0940162887fe78c1c6d417085dac511` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-mh-f2-2550-dirty-20260913` | `1d6239e0a08a5d2994aa770543053a85888b9ac2` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-mh-f2-2564-20260913` | `6d0ed7ef07d3d487f461f8ba30eb5d875ecb6d36` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-mh-f2-2564-b-20260913` | `67270651c735aeb7504c850cf84c46bb3ea47fcc` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-mh-f2-2564-dirty-20260913` | `c53bba56dbefa16a6647ab16f945f2eb9b79aa37` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-mh-f2-2605-20260913` | `46e25939df4b811970f092ff224d946174e80988` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-mh-f2-2605-dirty-20260913` | `2685c11db4a9f4ee617e7e2364537fc6c72b9ad0` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-mh-fix-2581-head-20260913` | `3f17a2d2fa110de956eb0e41b27586bb08110f5c` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-misthelper-checkout-20260912` | `5397f9fb1867204ebaee4b804fa7fa833c42c60b` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-misthelper-root-dirty-20260912` | `c49dd8bc1f7fdcc3afbbe3b457832f4a3430ff16` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-musical-guide-20260912` | `3df52783e4d6c6bf7ba14e8a3be1e249cefb6ee8` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-onedrive-misthelper-dirty-20260912` | `28557bd47c9dc76349e258199d071414b71d149d` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-orphan-automatic-guide-20260912` | `4c7dad3a2ef1111b78b5a4a6946a52d5e96ed675` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-orphan-crispy-spork-20260912` | `41fd3cc559f0f54472efd6426ad4093757c30635` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-perf-byte-bound-20260913` | `4db817c5a3132c9a4e5c1461b3f474fda188c00d` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-perf-modules-20260912` | `d6416765a60d1901fdcad5fbbaebf46d29c01566` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-perf-modules-full-20260912` | `0cb2b6561adda7b4df858dc837cc0a4da9b31ea3` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-resolve-overhead-20260913` | `d19de945c076e3cc67476666b36a16be6d1c97f8` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-stash-1395-0-20260912` | `dfdbac04d59328207313e729d4c9b02d2bdb36e4` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-stash-code-misthelper-0-20260912` | `32ddc995e3cc6e72dd881ad0045786d7c96836df` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-stash-code-misthelper-1-20260912` | `e31c1467e846867ae9a1484e3a90d903ada3ebc3` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-stash-code-misthelper-2-20260912` | `eb7cb61842e42a20910f4244a4c24eccf7685427` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-stash-code-misthelper-3-20260912` | `15b2f82ac5a044661b4564b70c95397d212f947c` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-stash-fresh-1376-0-20260912` | `cf1c51b7474ce78f7492c8dd82fcfb0ffe4b6dde` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-stash-main-0-20260912` | `0c01313020f792f38ab357a7948a73ee53b1dad0` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-stash-main-1-20260912` | `4a9de16ff5c8b2dac1283a9807b3e5bd62044e63` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-stash-main-2-20260912` | `f9f2e1af509c2024879645cde5ab910668e75ded` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `preservation/rescue-urban-eureka-20260912` | `89f23dd6c69b9b136cb382c7c83ed71a77ad0bb0` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `recovery/1793-module-logger-wip` | `bb635a476b11d98d98ea48fe0a39391a45fcef48` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `recovery/2645-structural-wip` | `cd0c445b0e31923217aa07d5ade4aaaeb3bf400d` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |
| `recovery/2689-sdk-guard-wip` | `60c3bd8035fad92ebb865d45060a02647ff29eb3` | `UNIQUE` | The audit did not prove that `main` contains this branch change. The safety rule keeps it. |

## Deleted branches

No branch was deleted in this batch.

## Kept branches

- `preservation/1375-branch-head-20260911` at `9b04d1ee44410c3c4522ab501e57cc6061cf5828`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/1375-recovery-dirty-20260911` at `0c01313020f792f38ab357a7948a73ee53b1dad0`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/1376-dirty-20260911` at `cf1c51b7474ce78f7492c8dd82fcfb0ffe4b6dde`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/1376-recovery-commit-20260911` at `bba37590b3a67c33d2109986532ea6bef3d365ed`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/1380-dirty-20260911` at `4a9de16ff5c8b2dac1283a9807b3e5bd62044e63`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/1381-branch-head-20260911` at `5ea0968e46ee1a3f74fed76079d016221fc3a941`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/1384-branch-head-20260911` at `c8808e42ca220fec3fe049506b1e263baa6f1d8f`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/1395-dirty-20260911` at `dfdbac04d59328207313e729d4c9b02d2bdb36e4`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/1400-branch-head-20260911` at `4ee5b83fb07b6bdc9202a43442991780bf75e7d1`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/1402-branch-head-20260911` at `a16e4f22dfe372203ed60b682926eeecb112e17b`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/1980-fix-1840-thread-scan-20260912` at `66d0a4367d0ee072e36d07d472b7b3f623a18b5d`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/1980-jmorrison-jnpr-ci-pytest-gate-failure-20260912` at `d5471cefe028892f81bdd0e68acea4d80190accc`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/1980-jmorrison-jnpr-production-readiness-sweep-20260912` at `93d60517d566fe12e9b7839e4fb6dd7c1520d5e3`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/1980-ops-gate-fix-20260912` at `99cdca8ecd981986551394f3d4cc9b94470a070a`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/2447-active-work-20260912` at `228dd7ced9d2eb89ec984b92e3c758cf5ade78a9`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/2447-active-work-20260913` at `9ebc8ea7c87add09bcac87737b9bae25644ee4e6`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/2447-original-branch-20260912` at `c85264218969faf9d55c8f9925b862c32e01f72e`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/2447-site-lock-branch-20260913` at `2f21084ccea125eeddb596885dcbf9215d926d45`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/2482-delivery-wip-20260912` at `46fec6c44f06df6bf88280e9ef20dd4ac159abf8`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/2482-performance-hook-catalog-20260912` at `e7cd9c3c92f2095f0f770756b8325a0ee552449c`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/2488-superseded-pr2504-20260912` at `b37e4d57e64cdcf2f7aabfa4fde14237cee78afe`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/2488-superseded-pr2504-final-20260912` at `a81d6b4e3dd167c17a6965a67ac504487a5d110c`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/2495-superseded-pr2502-20260912` at `5fadb32b32c65f53a952ae8e380afc10a7468765`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/2530-remote-tip-20260912` at `0d6e521b65a94e111376ed60a6afc15145c10460`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/2564-superseded-pr2603-20260913` at `b51072413ce266bbbe00fa522f38570499b641af`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/2651-remote-tip-20260914` at `63da786b3c73bf94f605576e661d26689b3f2139`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/2651-remote-tip-b-20260914` at `d842f46de95191539fcb741f82cc796263a6e8f6`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/868-branch-head-20260911` at `ee8171842d95286e49791fc4094e126bad5770f6`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/audit-pr-2280-closed-unmerged-20260913` at `c35debc68e1430ae286c1df54d5fda4df531f314`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/audit-pr-2374-closed-unmerged-20260913` at `7e5036a5c89b11e0b5cbd23b1138618c514ed182`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/audit-pr-2382-closed-unmerged-20260913` at `a0fe246018e76291d82a598c69e48eece3ab000e`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/audit-pr-2391-closed-unmerged-20260913` at `a0fe246018e76291d82a598c69e48eece3ab000e`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/audit-pr-2453-closed-unmerged-20260913` at `7d1a7f5ba0f02873033d8284eb25359f90d9d3b3`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/audit-pr-2454-closed-unmerged-20260913` at `1a0532da3e6de3e08828795e453e816fb1608992`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/audit-pr-2457-closed-unmerged-20260913` at `4ff8c4667b7fe51f8a10f6367bd509467f655285`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/audit-pr-2464-closed-unmerged-20260913` at `930f0a5b029dde8799a49d19898f07414326efd6`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/audit-pr-2534-closed-unmerged-20260913` at `d158d7107d901c0f7e43624cb3b696567269fe84`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/audit-rescue-mh-1741-20260913` at `da6a994465ff9371cab92cfe4d34c57f505c4b06`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/audit-rescue-mh-2596-nogit-20260913` at `6a0a57382a55c22e2424b0ec4b30f64dab1aa511`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/audit-rescue-mh-2624-20260913` at `1b4511eefa3f52f91adcca852ecb1578eca1889c`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/audit-rescue-mh-2624-final-20260913` at `bfeed9c955cf6cfaac9b7db74e014f41facf2cd4`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/audit-rescue-mh-2624-latest-20260913` at `f6ad266dd518b6cf8077e2e4dbb9c825bcad8449`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/audit-rescue-mh-entry-20260913` at `e241850fa4f8f2d163cc24bf02e839282ba57668`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/audit-rescue-mh-fix-2563-head-20260913` at `6787db5c23dcf45cd829030e4fac5bf1f4446556`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/bot-claim-integration-20260912` at `80843bdbed31a75f7d03b86aa65da8b93ad181dc`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-coord-1371-dirty-20260912` at `b156eecc7a33c1c0e783dd87e19e4ce215294ec3`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-head-mh-1789-20260912` at `3ecace748805b9eb41580edf70eb0b4f7475d966`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-head-mh-1897-20260912` at `6d89d404915ff59ebb7746d80a056ab6fb9964f9`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-head-mh-1948-wt-20260912` at `b208e6344d3b41ba0e14cc4dbbaf697fa449dd50`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-head-mh-2383-20260912` at `ff9dc2b6fd798c06bf44ea506e952caa28517061`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-head-mh-2384-log-rotation-20260912` at `012f9a422145ec942e13e6d32ac2d6f8ee50cf7f`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-head-mh-2395-recent-files-20260912` at `c89f01be2a27fc9169facc114f89007e20bf51f2`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-head-mh-2396-20260912` at `b03d6f12fc86d153545236d4b690a730203e2971`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-head-mh-2398-favicon-20260912` at `cb1d0c3387892d5e4b9df8561f306577b8cc9ada`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-head-mh-2399-operations-counts-20260912` at `3a54b368e3c9e4346dca234ed6308724c008804a`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-head-mh-coord-1372-20260912` at `6cd96503e1fa809a95ad698a45aa5f31fe08d309`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-head-mh-coord-1375-20260912` at `e68da39ccc13ca45fac960a2725bce786cd2dde6`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-head-mh-coord-1380-20260912` at `95e524cb9f869a59f0fd9b96268244f720137724`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-head-mh-coord-1384-20260912` at `e9be4bfb534bd1e95b41a6c5afb7bcd4c00b81e4`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-head-mh-coord-1402-20260912` at `8b1da2e7c440cba416353d15f774862f0ed42a4f`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-head-mh-wt-2397-20260912` at `51f80e92a0c23914b78c6b776e7a1b17cc435c44`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-mh-1375-dirty-20260912` at `dc6c19188da916e7bc2e0a4048df95dbb078de0e`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-mh-1376-dirty-20260912` at `d77faed53786c446175547ce3402440d5838f5b8`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-mh-1380-dirty-20260912` at `47f0076b73967b9d6cdc6dc7c320f97e83f23012`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-mh-2436-dirty-20260912` at `784049d25de823a456110808a51480c5045adfee`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/final-mh-wt-dirty-20260912` at `dbcb134bce803e0c95cd60ccc69bef06a5b1f6aa`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/fix-2495-favicon-before-rebase-20260912-0039` at `f1d12d02f1a47479817f3e48bb20ccb653d07839`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/orphan-2378-snapshot-20260911` at `24adb04d9964e18150c2c1680073f29b0b9d4aac`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/orphan-coord-1377-snapshot-20260912` at `e349bb5c9cd2309ce62d8bedfe9e65ff5b10f133`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/orphan-perfdeliver-snapshot-20260913` at `2ff0114efd63fc9c2e97ab595b3ce65d50fa6273`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-1771-complexity-20260912` at `b8fe20a0d241087460456c9ba8f1fbbbe0f62c14`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-code-misthelper-dirty-20260912` at `a01406abe642023f26340627713c84c3edf9b6ec`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-dependabot-hypothesis-20260912` at `0e87d15be593f08ad8c293e37588ce0f716a9e00`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-dependabot-openai-gte-20260912` at `0949c1c439b64e0c3e97d15e7dccf0a5d55c893e`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-dependabot-pylint-20260912` at `7b79a4724b00d875bdd3bb93c1a180e3f729dd15`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-dependabot-ruff-20260912` at `f8f8cc08a2eddd72a94e0c974052985445f9a26b`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-docs-1757-spec-module-paths-20260912` at `23552f77efb9903835b15777cf597d50790c177a`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-entry-offline-20260913` at `0759ceb1c09c99593b2a7447026e8dba8ca139b2`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-fix-1763-mermaid-lint-20260912` at `3cfd6d89cb0f64ee025f1152d3a97e5a501d0978`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-lint-1795-commit-20260912` at `01e1073237f912287c0dfa23eeed9505e1c57743`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-lint-1795-handoff-20260912` at `8f387929a3de25563bf6fd414dc5840a59d1664a`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-mh-2443-dirty-20260912` at `b034eb403df32971fd48d8ab561cfe9ad0748939`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-mh-bytes-head-20260913` at `d80b2f381e895e7e0f97af01a7b05578aaf856f8`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-mh-entry-2-20260913` at `8d451725847c118d073f2bfc80e182bc64d48387`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-mh-entry-3-20260913` at `f1f926c0bb47253408f66bfa8bca4c3bdbaed51e`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-mh-entry-4-20260913` at `bbe04b446888c806d4fd9708e70c3d29efc8f9ab`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-mh-entry-final-20260913` at `672c11d010eefcffb8ee08d2c20f453670e7ab73`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-mh-f2-1708-20260913` at `0e0607ffb1a7b10a56feb775ab671a806be04928`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-mh-f2-1899-dirty-20260913` at `55f6576bf0940162887fe78c1c6d417085dac511`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-mh-f2-2550-dirty-20260913` at `1d6239e0a08a5d2994aa770543053a85888b9ac2`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-mh-f2-2564-20260913` at `6d0ed7ef07d3d487f461f8ba30eb5d875ecb6d36`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-mh-f2-2564-b-20260913` at `67270651c735aeb7504c850cf84c46bb3ea47fcc`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-mh-f2-2564-dirty-20260913` at `c53bba56dbefa16a6647ab16f945f2eb9b79aa37`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-mh-f2-2605-20260913` at `46e25939df4b811970f092ff224d946174e80988`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-mh-f2-2605-dirty-20260913` at `2685c11db4a9f4ee617e7e2364537fc6c72b9ad0`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-mh-fix-2581-head-20260913` at `3f17a2d2fa110de956eb0e41b27586bb08110f5c`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-misthelper-checkout-20260912` at `5397f9fb1867204ebaee4b804fa7fa833c42c60b`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-misthelper-root-dirty-20260912` at `c49dd8bc1f7fdcc3afbbe3b457832f4a3430ff16`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-musical-guide-20260912` at `3df52783e4d6c6bf7ba14e8a3be1e249cefb6ee8`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-onedrive-misthelper-dirty-20260912` at `28557bd47c9dc76349e258199d071414b71d149d`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-orphan-automatic-guide-20260912` at `4c7dad3a2ef1111b78b5a4a6946a52d5e96ed675`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-orphan-crispy-spork-20260912` at `41fd3cc559f0f54472efd6426ad4093757c30635`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-perf-byte-bound-20260913` at `4db817c5a3132c9a4e5c1461b3f474fda188c00d`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-perf-modules-20260912` at `d6416765a60d1901fdcad5fbbaebf46d29c01566`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-perf-modules-full-20260912` at `0cb2b6561adda7b4df858dc837cc0a4da9b31ea3`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-resolve-overhead-20260913` at `d19de945c076e3cc67476666b36a16be6d1c97f8`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-stash-1395-0-20260912` at `dfdbac04d59328207313e729d4c9b02d2bdb36e4`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-stash-code-misthelper-0-20260912` at `32ddc995e3cc6e72dd881ad0045786d7c96836df`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-stash-code-misthelper-1-20260912` at `e31c1467e846867ae9a1484e3a90d903ada3ebc3`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-stash-code-misthelper-2-20260912` at `eb7cb61842e42a20910f4244a4c24eccf7685427`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-stash-code-misthelper-3-20260912` at `15b2f82ac5a044661b4564b70c95397d212f947c`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-stash-fresh-1376-0-20260912` at `cf1c51b7474ce78f7492c8dd82fcfb0ffe4b6dde`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-stash-main-0-20260912` at `0c01313020f792f38ab357a7948a73ee53b1dad0`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-stash-main-1-20260912` at `4a9de16ff5c8b2dac1283a9807b3e5bd62044e63`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-stash-main-2-20260912` at `f9f2e1af509c2024879645cde5ab910668e75ded`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `preservation/rescue-urban-eureka-20260912` at `89f23dd6c69b9b136cb382c7c83ed71a77ad0bb0`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `recovery/1793-module-logger-wip` at `bb635a476b11d98d98ea48fe0a39391a45fcef48`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `recovery/2645-structural-wip` at `cd0c445b0e31923217aa07d5ade4aaaeb3bf400d`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
- `recovery/2689-sdk-guard-wip` at `60c3bd8035fad92ebb865d45060a02647ff29eb3`: The audit did not prove that `main` contains this branch change. The safety rule keeps it.
