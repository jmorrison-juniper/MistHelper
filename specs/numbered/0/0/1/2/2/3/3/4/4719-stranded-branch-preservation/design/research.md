# Research: Stranded Branch Preservation

## Method

- The inventory uses the remote head SHA from the GitHub git refs API. Local counts use the same SHA. A commit SHA identifies its content, so a local object with that SHA shows the remote content.
- Local commands were read-only. No branch was checked out, fetched, pulled, rebased, or changed.
- Line numbers come from the remote blob content split on LF. A line number is the first line that contains the cited text.
- For a ref row, the blob SHA field holds the commit SHA. For a path row, the blob SHA field holds the blob SHA.
- The privacy-held branch shows only its head SHA, its commit count, and its path count.
- The Mist API and the `mistapi` SDK were not consulted. No claim depends on either source.
- No web source was fetched. No local skill applied, because the task concerns GitHub refs and pull requests.

## Decisions

### D-1 Scope

- **Decision**: The record covers the 51 branches named in issue #4719.
- **Alternatives considered**: All 505 rows of issue #4911. The 51 branches plus the two local-only branches.
- **Rationale**: The owner assessed these 51 branches in the issue comments. Issue #4911 adds 454 rows without an owner assessment. Its 434 archive rows may hold private content.
- **Risk**: The 454 rows stay stranded until task T015 completes.
- **Human decision**: No.

### D-2 Preservation method

- **Decision**: Each stranded branch gets one draft preservation pull request.
- **Alternatives considered**: Tag each head. Copy each head to an archive branch. Keep the branches as they are.
- **Rationale**: The report counts only pull requests that keep a head. The documentation requires a pull request before any cleanup. Tags and archive branches do not clear a report row.
- **Risk**: Publication exposes unreviewed content. Decision D-3 and decision D-5 control that risk.
- **Human decision**: No.

### D-3 Publication gate

- **Decision**: No preservation pull request opens until the owner releases the publication hold on issue #4719.
- **Alternatives considered**: Open pull requests now. Release each batch by a separate owner comment.
- **Rationale**: The owner comment of 2026-11-09T17:25:15Z states that no publication is authorized. The comment of 2026-11-09T18:03:52Z states that the publication hold stays in force.
- **Risk**: The stranded state continues until the owner releases the hold.
- **Human decision**: No. The owner made this decision in the issue comments, and this record keeps it.

### D-4 No deletion, rename, rebase, or force-push

- **Decision**: No branch is deleted, renamed, rebased, or force-pushed in this record.
- **Alternatives considered**: Delete each branch after its pull request exists, as step 3 of the documentation allows. Delete the branches now.
- **Rationale**: The owner comment of 2026-11-09T19:12:57Z states that no deletion is authorized. The owner comparisons used an older `main`, so content equivalence is unverified (unverified item U-2).
- **Risk**: The branches stay in the clone and on GitHub until a later record decides on deletion.
- **Human decision**: No.

### D-5 Privacy hold

- **Decision**: Branch `recovery/2977-handoff-20261004` keeps metadata only until the owner completes a privacy review.
- **Alternatives considered**: Read the source and publish it now. Remove the branch from the inventory.
- **Rationale**: The owner comment of 2026-11-09T19:06:03Z states that the branch has a privacy hold. Removing the branch would hide a stranded branch from the inventory.
- **Risk**: The branch stays unpreserved until the review completes.
- **Human decision**: No.

### D-6 Overlap deferral

- **Decision**: Four branches wait for owner reconciliation of draft pull requests #4208 and #4813.
- **Alternatives considered**: Open the preservation pull requests now. Close pull requests #4208 and #4813.
- **Rationale**: The owner comment of 2026-11-09T17:25:15Z states that overlapping work needs ownership reconciliation before any publication. A preservation pull request does not change those open pull requests, so the wait limits merge conflicts only.
- **Risk**: Four branches stay unpreserved longer than the other 46.
- **Human decision**: No.

### D-7 Upstream fix

- **Decision**: The title search defect is fixed in `misthelper-devtools`. This repository moves its pins after a released fix.
- **Alternatives considered**: Copy the reusable workflow into this repository. Disable the weekly job until the fix lands.
- **Rationale**: One source owns the workflow. The pin `79a5e45970e876f1656d69520d9635cea1aa25ef` is the latest tag, and the `main` branch holds the same blob. A local copy duplicates the defect and the logic.
- **Risk**: The weekly job keeps creating one issue per run until the fix ships.
- **Human decision**: No.

### D-8 Closing keyword

- **Decision**: The record pull request uses `Closes #4719`, because the constitution requires it.
- **Alternatives considered**: Use `Refs #4719`, the form that the quality gates guide uses for a preparation pull request.
- **Rationale**: The constitution governs conflicts between practice documents. Its governance section names it as the authoritative source.
- **Risk**: Merging the record closes issue #4719. The next report then opens a new tracking issue until task T021 lands.
- **Human decision**: No.

### D-9 Changelog fragment

- **Decision**: The record adds one fragment named `changelog.d/issue-4719-stranded-branch-preservation.md`.
- **Alternatives considered**: Add no fragment, under the internal-only exemption in the changelog README.
- **Rationale**: The constitution requires one unique fragment for each change. The constitution governs conflicts.
- **Risk**: A non-user-visible change adds one changelog entry.
- **Human decision**: No.

### D-10 Constitution steps 10 to 12

- **Decision**: The constitution check reports steps 10 to 12 as fail, with the reason. The pull request body reports the same result.
- **Alternatives considered**: Amend the constitution in this record. Change the container build trigger in this record. Add a product file to trigger a build.
- **Rationale**: The container build workflow runs only for a product file change. Amending the constitution or the trigger is a separate change. Adding a product file would change behavior that this record does not own.
- **Risk**: The owner must accept the failed rule or amend it.
- **Human decision**: No.

### D-11 Record path

- **Decision**: The record path is `specs\numbered\0\0\1\2\2\3\3\4\4719-stranded-branch-preservation`. The route `0/0/1/2/2/3/3/4` is the base-5 form of 4719 with eight levels.
- **Alternatives considered**: A shorter slug. A timestamp route.
- **Rationale**: The route script `.specify/scripts/powershell/spec-route.ps1` defines the numeric route. The slug names the work.
- **Risk**: None known. The route leaf is absent on `main`.
- **Human decision**: No.

### D-12 Duplicate tracking issues

- **Decision**: The duplicate tracking issues close only after the owner approves one canonical open issue and task T021 lands.
- **Alternatives considered**: Close the duplicates now. Keep all five open.
- **Rationale**: Closing before the fix loses the thread of the owner assessment. Keeping all five open leaves five copies of the same report.
- **Risk**: Four duplicates stay open for a period.
- **Human decision**: No.

### D-13 Local-only branches

- **Decision**: The two local-only branches stay local until the owner verifies them in their own clone.
- **Alternatives considered**: Push both branches now. Delete both branches.
- **Rationale**: Neither branch exists in this clone or on GitHub. The owner comments state that publication and deletion are not authorized.
- **Risk**: A local loss on the workstation removes the only copy until the owner verifies the branches.
- **Human decision**: No.

## Remote verification

Each row is one check. Rows 1 to 2 describe `main`. Rows 3 to 33 describe documents, rules, and workflows. Rows 34 to 36 describe the upstream workflow and its tag. Rows 37 to 38 describe the route. Row 39 describes the archive namespace. Rows 40 to 43 describe overlaps. Rows 44 to 45 describe the local-only branches. Rows 46 to 96 describe the 51 branches.

| # | Claim | Path | Ref | Blob SHA or commit SHA | Result | Line |
| - | - | - | - | - | - | - |
| 1 | Current main commit is f03c6c9b. | refs/heads/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| 2 | Owner comments measured main 3964d21d, which is no longer current. | refs/heads/main | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | stale | 0 |
| 3 | AGENTS.md sets an instruction limit of 20 words. | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 48 |
| 4 | AGENTS.md requires a Warning or Caution opening for a safety statement. | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 52 |
| 5 | AGENTS.md forbids a semicolon in prose. | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 50 |
| 6 | AGENTS.md requires preservation proof before closing an unmerged pull request. | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 271 |
| 7 | Copilot instructions list the stranded branch report workflow row. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 475 |
| 8 | Copilot instructions name each changelog fragment by pull request or issue. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| 9 | Copilot instructions list the STE lint workflow row. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 470 |
| 10 | The constitution requires one changelog fragment for each change. | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| 11 | The constitution requires Closes with the issue number in each pull request description. | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 519 |
| 12 | The constitution governs conflicts with other practice documents. | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 529 |
| 13 | The constitution requires the deployment pipeline after each release-note fragment. | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 175 |
| 14 | The numeric route base is 5. | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| 15 | The numeric route width is 8 levels. | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| 16 | The stranded branch report runs on a Monday schedule at 07:00 UTC. | .github/workflows/stranded-branch-report.yml | main | 0fde8b4e98edcc111425e3a385e42075cf43595f | present | 20 |
| 17 | The stranded branch report job pins the reusable workflow at tag v0.6.4. | .github/workflows/stranded-branch-report.yml | main | 0fde8b4e98edcc111425e3a385e42075cf43595f | present | 47 |
| 18 | The close-linked issues workflow runs on closed pull requests and on a schedule. | .github/workflows/close-linked-issues.yml | main | 42a085ac6240518b028862c290ec9502a5b13b2a | present | 21 |
| 19 | The close-linked issues job pins the reusable workflow at tag v0.6.4. | .github/workflows/close-linked-issues.yml | main | 42a085ac6240518b028862c290ec9502a5b13b2a | present | 50 |
| 20 | The changelog README exempts an internal-only change from a fragment. | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| 21 | The stranded branch review requires a pull request before any cleanup. | documentation/stranded-branch-review.md | main | 8091539c31ff8648d0426f4a8a92e01e0eb902b4 | present | 46 |
| 22 | The contributing guide requires a pull request for every branch the report names. | documentation/contributing.md | main | 3b455b6d6730e16972540f14f7f654462b1c27bd | present | 76 |
| 23 | The quality gates guide uses Refs for a preparation pull request. | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 118 |
| 24 | The pull request template requires one changelog fragment. | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 36 |
| 25 | The pull request title workflow checks Conventional Commits titles. | .github/workflows/pull-request-title.yml | main | 6b161b5a7dd71a0f0c9c0f38b750a7322ae8704e | present | 17 |
| 26 | The container build workflow declares path filters for product files. | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 6 |
| 27 | The CI workflow defines its jobs. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 136 |
| 28 | The auto-merge workflow reads the auto-merge label. | .github/workflows/auto-merge.yml | main | 9d26134dd84cf50008a17fd878772102ce355983 | present | 14 |
| 29 | The reference record spec exists on main. | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| 30 | The spec template defines the User Scenarios and Testing section. | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 11 |
| 31 | The plan template defines the Constitution Check section. | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 44 |
| 32 | The tasks template defines the Format section. | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 20 |
| 33 | The checklist template defines the Notes section. | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 35 |
| 34 | The pinned devtools report workflow searches for the tracking title with a colon and parentheses. | misthelper-devtools:.github/workflows/reusable-stranded-branch-report.yml | 79a5e45970e876f1656d69520d9635cea1aa25ef | b8ca235c93beddef9307d797da87223a920df729 | present | 156 |
| 35 | The devtools main branch holds the same report workflow. | misthelper-devtools:.github/workflows/reusable-stranded-branch-report.yml | main | b8ca235c93beddef9307d797da87223a920df729 | present | 156 |
| 36 | The latest devtools tag is v0.6.4 at the pin. | misthelper-devtools:refs/tags/v0.6.4 | v0.6.4 | 79a5e45970e876f1656d69520d9635cea1aa25ef | present | 0 |
| 37 | Parent node 0/0/1/2/2/3/3 holds 4 children on main, so one new child is allowed. | specs/numbered/0/0/1/2/2/3/3/ | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| 38 | Route leaf 0/0/1/2/2/3/3/4 is absent on main. | specs/numbered/0/0/1/2/2/3/3/4/ | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | absent | 0 |
| 39 | The archive namespace holds 491 remote branches. | refs/heads/archive/ | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| 40 | Branch recovery/3213-handoff-20261004 shares deploy/.env.example with draft pull request 4208. | deploy/.env.example | recovery/3213-handoff-20261004 | 8090bc7d195407ecafe62fd16f38847ae18b5170 | partial | 0 |
| 41 | Branch jmorrison-juniper-issue-2746 shares tests/unit/refactors/test_wlanradius_timer_manager_paths.py with draft pull request 4208. | tests/unit/refactors/test_wlanradius_timer_manager_paths.py | jmorrison-juniper-issue-2746 | 4ebe402c19de77a546960896ef70bb3286860f13 | partial | 0 |
| 42 | Branch jmorrison-juniper-local-build-revision shares deploy/.env.example with draft pull request 4208. | deploy/.env.example | jmorrison-juniper-local-build-revision | c80f23510a679985f9892ee59f0c181a8cdaa953 | partial | 0 |
| 43 | Branch recovery/3699-handoff-20261004 shares tests/unit/export/test_endpoint_family_exporter.py with draft pull request 4813. | tests/unit/export/test_endpoint_family_exporter.py | recovery/3699-handoff-20261004 | c0261d9fba897fb6339c46d26e465bcc3703ac1d | partial | 0 |
| 44 | Local-only branch jmorrison-juniper-issue-triage-overlap-analysis has no remote copy. | refs/heads/jmorrison-juniper-issue-triage-overlap-analysis | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | absent | 0 |
| 45 | Local-only branch jmorrison-juniper-ssh-telemetry-test-repair has no remote copy. | refs/heads/jmorrison-juniper-ssh-telemetry-test-repair | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | absent | 0 |
| 46 | Branch fix/3158-wip-controls exists at head 0f6b375e and no pull request holds that head. | refs/heads/fix/3158-wip-controls | fix/3158-wip-controls | 0f6b375e71243311b5cf5856fe9f220842a14e3b | present | 0 |
| 47 | Branch fix/3168-structured-signals exists at head 69d19411 and no pull request holds that head. | refs/heads/fix/3168-structured-signals | fix/3168-structured-signals | 69d19411fbc13c0b0ab55b10d49ae7ec177024c0 | present | 0 |
| 48 | Branch fix/3183-status-fallback exists at head 0c46332a and no pull request holds that head. | refs/heads/fix/3183-status-fallback | fix/3183-status-fallback | 0c46332ad00b2c9131f29fba218400ba7ece8f51 | present | 0 |
| 49 | Branch fix/3222-confirm-details exists at head 18138f9b and no pull request holds that head. | refs/heads/fix/3222-confirm-details | fix/3222-confirm-details | 18138f9b28173c969a57d447291ffebcd6daa029 | present | 0 |
| 50 | Branch jmorrison-jnpr-snmp-fallback-delivery exists at head 73a1edaa and no pull request holds that head. | refs/heads/jmorrison-jnpr-snmp-fallback-delivery | jmorrison-jnpr-snmp-fallback-delivery | 73a1edaa973b4fb5110d9d3607377e42773d8445 | present | 0 |
| 51 | Branch fix/3506-site-lock-logs exists at head 8c8fc28d and no pull request holds that head. | refs/heads/fix/3506-site-lock-logs | fix/3506-site-lock-logs | 8c8fc28d452126a0e42c98040f8edf56d11a412f | present | 0 |
| 52 | Branch recovery/2863-handoff-20261004 exists at head 188956f9 and no pull request holds that head. | refs/heads/recovery/2863-handoff-20261004 | recovery/2863-handoff-20261004 | 188956f937019a0e07cab73919ebd289179c5def | present | 0 |
| 53 | Branch recovery/2711-handoff-20261004 exists at head 9e943bfe and no pull request holds that head. | refs/heads/recovery/2711-handoff-20261004 | recovery/2711-handoff-20261004 | 9e943bfe30d9ab4513ba1d595e844fd8c1c080d0 | present | 0 |
| 54 | Branch recovery/3575-handoff-20261004 exists at head 5746418f and no pull request holds that head. | refs/heads/recovery/3575-handoff-20261004 | recovery/3575-handoff-20261004 | 5746418f8cd77fa1ccd6cc004fd5f07a20ddaffb | present | 0 |
| 55 | Branch recovery/3700-handoff-20261004 exists at head f253dd3b and no pull request holds that head. | refs/heads/recovery/3700-handoff-20261004 | recovery/3700-handoff-20261004 | f253dd3b5533b63f0e75047e3fb918d976311b58 | present | 0 |
| 56 | Branch recovery/3701-handoff-20261004 exists at head d2d2421d and no pull request holds that head. | refs/heads/recovery/3701-handoff-20261004 | recovery/3701-handoff-20261004 | d2d2421da64d7884f7988321197dec066accb9f7 | present | 0 |
| 57 | Branch recovery/2752-handoff-20261004 exists at head 024d42ff and no pull request holds that head. | refs/heads/recovery/2752-handoff-20261004 | recovery/2752-handoff-20261004 | 024d42ff7f840becd7583433d502fbdf453594a3 | present | 0 |
| 58 | Branch recovery/2861-handoff-20261004 exists at head 6cea98a9 and no pull request holds that head. The owner recorded no head. | refs/heads/recovery/2861-handoff-20261004 | recovery/2861-handoff-20261004 | 6cea98a9794d87e0ed3738bf331afff51280f76c | present | 0 |
| 59 | Branch recovery/2977-handoff-20261004 exists at head d6e8eb86 and no pull request holds that head. Metadata only under the privacy hold. | refs/heads/recovery/2977-handoff-20261004 | recovery/2977-handoff-20261004 | d6e8eb8672edfa1c5123df03294ecd8daa98a051 | present | 0 |
| 60 | Branch recovery/3213-handoff-20261004 exists at head 8090bc7d and no pull request holds that head. | refs/heads/recovery/3213-handoff-20261004 | recovery/3213-handoff-20261004 | 8090bc7d195407ecafe62fd16f38847ae18b5170 | present | 0 |
| 61 | Branch recovery/3326-handoff-20261004 exists at head fa25a39c and no pull request holds that head. | refs/heads/recovery/3326-handoff-20261004 | recovery/3326-handoff-20261004 | fa25a39cd3d77a9a9fc4c5d5327ba9c2e6c1c499 | present | 0 |
| 62 | Branch recovery/3329-handoff-20261004 exists at head 7332749c and no pull request holds that head. | refs/heads/recovery/3329-handoff-20261004 | recovery/3329-handoff-20261004 | 7332749c6cf0344a2e7fdcbe02e1948f450d6b2c | present | 0 |
| 63 | Branch recovery/3295-handoff-20261004 exists at head b1fe853f and no pull request holds that head. | refs/heads/recovery/3295-handoff-20261004 | recovery/3295-handoff-20261004 | b1fe853fb26f4f4c7efd82148e5af14084a313ae | present | 0 |
| 64 | Branch recovery/3728-handoff-20261004 exists at head 533ced96 and no pull request holds that head. | refs/heads/recovery/3728-handoff-20261004 | recovery/3728-handoff-20261004 | 533ced96928dd51dc68a139d20c9476d08e87eb8 | present | 0 |
| 65 | Branch recovery/3436-handoff-20261004 exists at head 0a032e83 and no pull request holds that head. | refs/heads/recovery/3436-handoff-20261004 | recovery/3436-handoff-20261004 | 0a032e83ab7cde0faec752258971df7b6b657d0c | present | 0 |
| 66 | Branch recovery/3699-handoff-20261004 exists at head c0261d9f and no pull request holds that head. | refs/heads/recovery/3699-handoff-20261004 | recovery/3699-handoff-20261004 | c0261d9fba897fb6339c46d26e465bcc3703ac1d | present | 0 |
| 67 | Branch recovery/3375-handoff-20261004 exists at head 499b764f and no pull request holds that head. | refs/heads/recovery/3375-handoff-20261004 | recovery/3375-handoff-20261004 | 499b764f16fee9a465c9c789f3806ad9c0cdae1c | present | 0 |
| 68 | Branch recovery/3158-handoff-20261004 exists at head ecb0bc87 and no pull request holds that head. | refs/heads/recovery/3158-handoff-20261004 | recovery/3158-handoff-20261004 | ecb0bc87ceafe3f5024d678bdc99ad4b159fad7c | present | 0 |
| 69 | Branch recovery/3743-handoff-20261004 exists at head 4ecd16c7 and no pull request holds that head. | refs/heads/recovery/3743-handoff-20261004 | recovery/3743-handoff-20261004 | 4ecd16c7e409e88899e46b105e5ec0b3e67b875c | present | 0 |
| 70 | Branch recovery/3491-handoff-20261004 exists at head 97139eb2 and no pull request holds that head. | refs/heads/recovery/3491-handoff-20261004 | recovery/3491-handoff-20261004 | 97139eb2c6dc667d456c2fce420f8c57f6c67025 | present | 0 |
| 71 | Branch recovery/2747-handoff-20261004 exists at head 2d5695fb and no pull request holds that head. | refs/heads/recovery/2747-handoff-20261004 | recovery/2747-handoff-20261004 | 2d5695fb4ed00411e5dbaf0d2b03539e3aff4863 | present | 0 |
| 72 | Branch recovery/3745-handoff-20261004 exists at head 50e3d841 and no pull request holds that head. | refs/heads/recovery/3745-handoff-20261004 | recovery/3745-handoff-20261004 | 50e3d841dfbbcfb89fd0b419ce5631c5bd1068bd | present | 0 |
| 73 | Branch recovery/3749-handoff-20261004 exists at head 9f930182 and no pull request holds that head. | refs/heads/recovery/3749-handoff-20261004 | recovery/3749-handoff-20261004 | 9f930182fa5349ebf59fac3e8c9830327f4116b4 | present | 0 |
| 74 | Branch recovery/3161-handoff-20261004 exists at head 33141f05 and no pull request holds that head. | refs/heads/recovery/3161-handoff-20261004 | recovery/3161-handoff-20261004 | 33141f05cd19c509f723c57534edd2900b4ecde3 | present | 0 |
| 75 | Branch recovery/3388-handoff-20261004 exists at head ea0a7467 and no pull request holds that head. | refs/heads/recovery/3388-handoff-20261004 | recovery/3388-handoff-20261004 | ea0a7467b81b297580f7a264658bd15fbf442c1e | present | 0 |
| 76 | Branch recovery/3380-handoff-20261004 exists at head a3af99af and no pull request holds that head. | refs/heads/recovery/3380-handoff-20261004 | recovery/3380-handoff-20261004 | a3af99af23ba29e31725673a87e0f771293ba985 | present | 0 |
| 77 | Branch recovery/3761-handoff-20261004 exists at head ebc40dac and no pull request holds that head. | refs/heads/recovery/3761-handoff-20261004 | recovery/3761-handoff-20261004 | ebc40dac8dcb47b0c835bf45b7474dde1732669f | present | 0 |
| 78 | Branch recovery/3760-handoff-20261004 exists at head 12f10ece and no pull request holds that head. | refs/heads/recovery/3760-handoff-20261004 | recovery/3760-handoff-20261004 | 12f10ece0901452bd71eb1baa563ee77de5687db | present | 0 |
| 79 | Branch recovery/3769-handoff-20261004 exists at head 54188ffc and no pull request holds that head. | refs/heads/recovery/3769-handoff-20261004 | recovery/3769-handoff-20261004 | 54188ffcaffc18e3d5ced162fc64ef1762a90b70 | present | 0 |
| 80 | Branch recovery/2708-handoff-20261004 exists at head f195788a and no pull request holds that head. | refs/heads/recovery/2708-handoff-20261004 | recovery/2708-handoff-20261004 | f195788a090d6ace8f2f320dc1f96a413876e2c4 | present | 0 |
| 81 | Branch recovery/3818-handoff-20261004 exists at head 0bb31494 and no pull request holds that head. | refs/heads/recovery/3818-handoff-20261004 | recovery/3818-handoff-20261004 | 0bb3149476b5658f8dc9ce44661d4c90dadc3669 | present | 0 |
| 82 | Branch recovery/3738-handoff-20261004 exists at head c70007d4 and no pull request holds that head. | refs/heads/recovery/3738-handoff-20261004 | recovery/3738-handoff-20261004 | c70007d407c5cd58ef08901832806120175d49b3 | present | 0 |
| 83 | Branch docs/3818-campaign-stop-20261004 exists at head 8c3e6cac and no pull request holds that head. | refs/heads/docs/3818-campaign-stop-20261004 | docs/3818-campaign-stop-20261004 | 8c3e6cacc6d101c3b4356369f94b2f50039f987b | present | 0 |
| 84 | Branch fix/3292-isolate-retry-e2e-sites exists at head f706902a and no pull request holds that head. | refs/heads/fix/3292-isolate-retry-e2e-sites | fix/3292-isolate-retry-e2e-sites | f706902a5af34e272583b45686fd60b4e1225fed | present | 0 |
| 85 | Branch jmorrison-juniper-startup-dependency-reassessment exists at head e849f3fe and no pull request holds that head. | refs/heads/jmorrison-juniper-startup-dependency-reassessment | jmorrison-juniper-startup-dependency-reassessment | e849f3fe4e0734f54de76a0b171390674555ca2b | present | 0 |
| 86 | Branch jmorrison-juniper-fix-2863-identifier-defaults-batch-1 exists at head 6eec0e4b and no pull request holds that head. | refs/heads/jmorrison-juniper-fix-2863-identifier-defaults-batch-1 | jmorrison-juniper-fix-2863-identifier-defaults-batch-1 | 6eec0e4bf09a6ca5deb1bb78c008337bab6e7464 | present | 0 |
| 87 | Branch jmorrison-juniper-assessment-4026 exists at head 83d197e3 and no pull request holds that head. | refs/heads/jmorrison-juniper-assessment-4026 | jmorrison-juniper-assessment-4026 | 83d197e30fd9519521697154036eadf4e52a2850 | present | 0 |
| 88 | Branch jmorrison-juniper-issue-3416-lint-pattern exists at head 3d51242e and no pull request holds that head. | refs/heads/jmorrison-juniper-issue-3416-lint-pattern | jmorrison-juniper-issue-3416-lint-pattern | 3d51242e41f2815bbcaeaa076a2c1e60b2fd9550 | present | 0 |
| 89 | Branch jmorrison-juniper-false-success-family-4028 exists at head 4be5f321 and no pull request holds that head. | refs/heads/jmorrison-juniper-false-success-family-4028 | jmorrison-juniper-false-success-family-4028 | 4be5f321a3ba26c136c541e062c7aa4e7442aae9 | present | 0 |
| 90 | Branch jmorrison-jnpr-test-4035-menu-92-selection-result exists at head 9851ed28 and no pull request holds that head. | refs/heads/jmorrison-jnpr-test-4035-menu-92-selection-result | jmorrison-jnpr-test-4035-menu-92-selection-result | 9851ed28ced6f6d0909fe529e0a8f43c1a412bed | present | 0 |
| 91 | Branch jmorrison-juniper-issue-2746 exists at head 4ebe402c and no pull request holds that head. | refs/heads/jmorrison-juniper-issue-2746 | jmorrison-juniper-issue-2746 | 4ebe402c19de77a546960896ef70bb3286860f13 | present | 0 |
| 92 | Branch jmorrison-juniper-coordinate-issue-work exists at head 29c54897 and no pull request holds that head. | refs/heads/jmorrison-juniper-coordinate-issue-work | jmorrison-juniper-coordinate-issue-work | 29c5489751ed84a8595cefe85f0e2aa7716b8608 | present | 0 |
| 93 | Branch jmorrison-juniper-issue-4269-runtime-nested-feature-identity-in-speck-4a6090 exists at head d8a7b9c7 and no pull request holds that head. | refs/heads/jmorrison-juniper-issue-4269-runtime-nested-feature-identity-in-speck-4a6090 | jmorrison-juniper-issue-4269-runtime-nested-feature-identity-in-speck-4a6090 | d8a7b9c71583668b7284c81ab69cc9f1a5dbba78 | present | 0 |
| 94 | Branch jmorrison-juniper-issue-2747-wan-probe-test-quality exists at head db030903 and no pull request holds that head. | refs/heads/jmorrison-juniper-issue-2747-wan-probe-test-quality | jmorrison-juniper-issue-2747-wan-probe-test-quality | db030903fb77beca6c57d7bb10f356cbc290bd58 | present | 0 |
| 95 | Branch jmorrison-juniper-fix-4494-csrf-warning-prefix exists at head 862f1a8c and no pull request holds that head. | refs/heads/jmorrison-juniper-fix-4494-csrf-warning-prefix | jmorrison-juniper-fix-4494-csrf-warning-prefix | 862f1a8ce6254fa836a780623b462d3140c35292 | present | 0 |
| 96 | Branch jmorrison-juniper-local-build-revision exists at head c80f2351 and no pull request holds that head. | refs/heads/jmorrison-juniper-local-build-revision | jmorrison-juniper-local-build-revision | c80f23510a679985f9892ee59f0c181a8cdaa953 | present | 0 |

## Sources

- S-01 Issue #4719: `gh issue view 4719`. Title "chore(git): a branch holds work with no pull request". State OPEN. Labels `ci` and `chore`. Created 2026-11-09T16:59:18Z. Updated 2026-11-09T22:14:30Z. The body lists 51 branch rows. The record holds 25 owner comments.
- S-02 Owner hold comments on issue #4719. Node IDs and times: IC_kwDOQltU8c8AAAABkiKwBw (2026-11-09T17:25:15Z) states that no publication, merge, or cleanup is authorized. IC_kwDOQltU8c8AAAABkjAo-w (2026-11-09T18:03:52Z) states that the publication hold stays in force. IC_kwDOQltU8c8AAAABkkMgnw (2026-11-09T19:06:03Z) states that the privacy hold covers one branch.
- S-03 Tracking issues: `gh issue list --state all --search "holds work with no pull request in:title"`. Open: 4911, 4818, 4719, 4583, and 4302. Closed: 4486, 4184, 3921, 3529, and 3490.
- S-04 Report runs: `gh run list --workflow stranded-branch-report.yml --limit 10`. Ten runs, all with conclusion success. Dates: 2026-09-27 (manual), 2026-09-28, 2026-10-05, 2026-10-12, 2026-10-19, 2026-10-26, 2026-11-02, 2026-11-09, 2026-11-16, and 2026-11-23. Each run created one tracking issue a few minutes after it started.
- S-05 Issue #4911 body, created 2026-11-23: 505 table rows. The rows hold 1616 commits ahead in total. 434 rows start with `archive/`, and they hold 1123 commits ahead. Issue #4818 holds 54 rows. Issue #4583 holds 52 rows. Issue #4302 holds 48 rows.
- S-06 Title search test, 2026-11-26. The workflow query `chore(git): a branch holds work with no pull request in:title` returns no issue. The plain query `holds work with no pull request in:title` returns issues 4911, 4818, 4719, 4583, and 4302.
- S-07 Remote heads: `gh api` on the `git/ref/heads` path of each of the 51 branches. The heads list holds 598 refs in total.
- S-08 Open pull requests: `gh pr list --state open`. Seven open pull requests: #4890, #4889, #4888, #4887, #4886, #4813 (draft), and #4208 (draft). Their file lists come from `gh pr view` with the `--json files` option.
- S-09 Pull request holders: `gh pr list --state all --limit 5000` returned 2396 pull requests. No pull request has a head name that matches one of the 51 branches.
- S-10 Local commit data: `git -C` on the clone, with `rev-list --count`, `diff --name-only`, and `log --format` for the range from the main SHA to the head SHA. The main SHA is f03c6c9b. The head SHA is the remote head of each branch.
- S-11 Git tree on `main`: `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`. 11404 entries. The response is not truncated. The tree gives the blob SHAs in rows 3 to 33 and rows 37 and 38.
- S-12 Blob content: the git data blob endpoint for each blob SHA, decoded from base64. Line numbers come from the decoded text.
- S-13 Devtools repository: the tag list shows `v0.6.4` at `79a5e45970e876f1656d69520d9635cea1aa25ef` as the newest tag. The `main` head is `2239e7bd468fd27e40c43f2b87fcd35a2e49672b`. The reusable report workflow has blob `b8ca235c93beddef9307d797da87223a920df729` on both the pin and `main`.
- S-14 Local documents read in the repository working copy: `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, the four templates in `.specify/templates/`, `.specify/scripts/powershell/spec-route.ps1`, `documentation/quality-gates.md`, `documentation/stranded-branch-review.md`, `documentation/contributing.md`, `documentation/development-setup.md`, `changelog.d/README.md`, and the two workflow files `.github/workflows/stranded-branch-report.yml` and `.github/workflows/close-linked-issues.yml`.
- S-15 Reference record: `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`. Its spec, plan, tasks, analysis, design files, contracts, and checklists set the shape of this record.
- S-16 Documents not applicable: `documentation/operator-guide.md` and `documentation/container-deployment.md` name a branch or a pull request only in container naming rules. No claim in this record depends on them.
- S-17 Linked pull requests: `gh pr list --state all --search 4719` returned no pull request. No pull request is linked to issue #4719 by its number.

## Unverified

- U-1 Local existence of `jmorrison-juniper-issue-triage-overlap-analysis`, with the reported head `a4c7aa10`, and `jmorrison-juniper-ssh-telemetry-test-repair`, with the reported head `fd7f20a2`. Reason: neither ref exists in this clone or on GitHub. The owner comments report both in another worktree.
- U-2 Content equivalence of each branch with `main` or with a merged pull request. Reason: the owner comparisons used `main` at `3964d21d`. This record did not repeat them.
- U-3 Source content of `recovery/2977-handoff-20261004`. Reason: the owner privacy hold forbids the read.
- U-4 Content of the 454 extra rows of issue #4911. Reason: the rows are outside the scope in decision D-1.
- U-5 Reasons for the closure of tracking issues 3490, 3529, 3921, 4184, and 4486. Reason: no closure record was read in this session.
- U-6 Effect of the closing keyword on issue #4719 at merge. Reason: GitHub documents the behavior, but this session did not test it.
- U-7 Whether `misthelper-devtools` holds a branch or a pull request for the title search fix. Reason: this session did not search that repository for one.
