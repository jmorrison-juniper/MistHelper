# Research: Laptop Branch Archive Verification

Each decision lists the choice, the rationale, and the alternatives. Facts come from GitHub GET responses on 2026-11-26 and from read-only local git commands. Each remote claim appears once in the remote verification table.

## D-1. Verification authority

- **Decision**: GitHub GET responses on origin decide whether a name exists. Local git reads serve as a cross-check.
- **Rationale**: Origin holds the archive. The repository truth order puts remote state first. The local checkout differs from the archive (F-6).
- **Alternatives considered**:
  - Local refs only. Rejected: the local refs show this checkout, not origin.
  - `git ls-remote`. Rejected: the request limits this work to GitHub GET requests and read-only local git commands.
  - Web pages. Rejected: they give no structured output for 497 names.
- **Risk**: GitHub rate limits. Mitigation: the retry rule in the spec edge cases.

## D-2. Count split

- **Decision**: Report 491 archive refs and 6 rescue branches. The listed total is 497.
- **Rationale**: The archive listing returns 491 names with the prefix `archive/laptop-20261121/`. The 6 rescue names exist as branches with their own prefix. The two counts sum to 497, the issue count.
- **Alternatives considered**:
  - Treat all 497 as archive refs. Rejected: the listing contradicts this.
  - Drop the rescue names. Rejected: the request asks for each listed name.
- **Risk**: A reader reads 497 as archive refs. Mitigation: F-1 and FR-006.

## D-3. Remote counterpart definition

- **Decision**: A remote counterpart is a branch named exactly like the original branch name, at `refs/heads/<name>`. An archive ref never counts.
- **Rationale**: The issue names each branch by its original name. A same-name branch on origin shows whether that name remains on origin.
- **Alternatives considered**:
  - Content containment for each name. Rejected: it needs 491 compare calls, and containment does not show a name. The compare ran once, for the one differing name (RC-37).
  - The archive ref as the counterpart. Rejected: the archive ref is the archive copy itself.
- **Risk**: A same-name branch can hold other content. Mitigation: compare the tips of every same-name branch. This run had one case.

## D-4. Record route and slug

- **Decision**: Use `specs/numbered/0/0/1/2/3/4/3/3/4868-laptop-branch-archive`. The slug is `laptop-branch-archive`.
- **Rationale**: The base-5 digits of 4868, padded to eight places, are 0 0 1 2 3 4 3 3. The route follows the rule of `Get-SpecRadixSegments` (RC-11 to RC-13). The slug names the subject. The issue title carries the date.
- **Alternatives considered**:
  - A timestamp route under `live/`. Rejected: an issue has a number, and numeric records follow the repository rule (RC-07).
  - The slug `laptop-archive-20261121`. Rejected: the date adds no meaning to the subject.
- **Risk**: The route helper was not run. Mitigation: T009 checks the child counts (RC-23 to RC-26).

## D-5. Contract file for the GET checks

- **Decision**: Add `design/contracts/archive-ref-verification.md`.
- **Rationale**: The checks read one remote interface. A contract fixes the requests and the response fields that the checks read.
- **Alternatives considered**:
  - Omit the folder. Rejected: the verification interface is the core of this record.
- **Risk**: The response shape may change. Mitigation: T014 reruns the checks.

## D-6. Changelog fragment

- **Decision**: Add `changelog.d/issue-4868-laptop-branch-archive.md` with one `Added` bullet.
- **Rationale**: The constitution requires one fragment for each change (RC-10). The file name follows the issue rule (RC-14).
- **Alternatives considered**:
  - Skip the fragment. The changelog README allows this for internal-only changes. Rejected: the constitution governs, and it does not exempt internal changes.
- **Risk**: The fragment adds one file to a folder with existing debt (RC-28).

## D-7. Notes in other repositories

- **Decision**: Do not read the two notes that the issue names in `jmorrison-juniper/vmm-topology-automation` (issues 351 and 352). List them as unverified references.
- **Rationale**: The notes describe the machine, not MistHelper files. This record needs no content from them. The notes name credential locations, and this record must not copy them.
- **Alternatives considered**:
  - Read and summarize the notes. Rejected: the content lies outside this repository and names credential locations.
- **Risk**: A reader misses context from the notes. Mitigation: the Unverified list names both references.

## D-8. Archive deletion deferred to a human

- **Decision**: HUMAN-DECISION-REQUIRED. This record deletes no archive ref. Any later deletion needs a human decision and a rerun of TC-01 to TC-05.
- **Rationale**: Deleting an archive ref can remove the only remote copy of its unique commits. This is a destruction of data decision.
- **Alternatives considered**:
  - Keep every archive ref. The issue allows this, and it is the safe default.
  - Delete the prefix after a fixed period. Rejected: it removes data without a review.
  - Delete the names one at a time after a human reviews each name. Recommended: a human reviews the content of each name on main, then approves its deletion.
- **Recommended option**: Keep the refs until a human reviews each name. Delete a name only after the approval and a passing rerun of TC-01 to TC-05.
- **Risk**: A human approves a deletion without a review. Mitigation: the Warning in the spec and the open item in the Unverified list.

## D-9. Claimed unpushed counts

- **Decision**: Record the claimed unpushed commit counts as claims. This record does not verify them.
- **Rationale**: A count of commits that no remote branch holds needs a full history walk for each archive tip. A local recount started and did not finish within five minutes, so the run stopped. The local remote-tracking refs also reflect the fetch time, not the state on 2026-11-21.
- **Alternatives considered**:
  - Recount in full with `git rev-list`. Rejected: the run exceeded the time limit.
- **Risk**: A reader takes a claimed count as fact. Mitigation: the Unverified list.

## D-10. Labels and size

- **Decision**: Add the labels `chore` and `docs`. Use size `S`.
- **Rationale**: The change adds Markdown files and one fragment. It changes no code. The label `in-progress` belongs to the orchestrator, which claims the issue before branching.
- **Alternatives considered**:
  - Size `M`. Rejected: the change has ten Markdown files and no code.
- **Risk**: None found.

## Issue Facts

- Issue 4868 is open. It was created and last updated on 2026-11-21 at 19:28:28 UTC, by `jmorrison-juniper`.
- The issue has no labels and no comments.
- The issue names no repository file, symbol, or test. It names the notes in `jmorrison-juniper/vmm-topology-automation`, issues 352 and 351.
- The issue gives recovery commands with `git fetch` and `git branch`. This record does not run them.
- The issue gives no reproduction steps and no error text.

## Remote Verification

Each row is one remote check. The table holds 39 rows, and the status file lists the same 39 checks in the same order. A line value of 0 means the claim has no file line. An `n/a` value means the check covers an aggregate or an absent item. The Claim column gives the cause.

| # | Claim | Path | Ref | Blob or object SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | AGENTS.md has the writing style section | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RC-02 | AGENTS.md limits an instruction to 20 words | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 48 |
| RC-03 | AGENTS.md requires a Warning or Caution opening for a safety statement | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 52 |
| RC-04 | AGENTS.md gives the branch name rule | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 194 |
| RC-05 | The repository rules list the STE gate in the local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| RC-06 | The repository rules require managed spec roots | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159 |
| RC-07 | The repository rules require the eight-level base-5 route for numeric records | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 160 |
| RC-08 | The repository rules limit each structural directory to five children | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 167 |
| RC-09 | Constitution principle I limits each hierarchy level to five children | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 40 |
| RC-10 | The constitution requires one changelog fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| RC-11 | The route helper defines the function Get-SpecRadixSegments | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 4 |
| RC-12 | The route helper uses base five | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-13 | The route helper default width is eight | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| RC-14 | The changelog README names issue fragments with the pattern issue-number-slug | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| RC-15 | The STE minimum score is 80 | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 15 |
| RC-16 | The quality gates document the STE command | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 283 |
| RC-17 | CI runs speckit-task-audit as an advisory step | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 750 |
| RC-18 | The spec template has the user scenarios heading | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 11 |
| RC-19 | The plan template has the summary heading | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 14 |
| RC-20 | The tasks template has the format heading | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 20 |
| RC-21 | The checklist template has the notes heading | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 35 |
| RC-22 | The reference record has a spec file of the same shape | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 26 |
| RC-23 | No path under specs contains 4868 on main | specs | main | n/a: no tree entry matches | absent | 0 |
| RC-24 | The route folder specs/numbered/0/0/1/2/3/4/3/3 does not exist on main | specs/numbered/0/0/1/2/3/4/3/3 | main | n/a: no tree entry exists | absent | 0 |
| RC-25 | The folder specs/numbered/0/0/1/2/3/4/3 holds two children on main | specs/numbered/0/0/1/2/3/4/3 | main | adeb0e014a78c2b2751f414e663db95cc7e475ea | present | 0 |
| RC-26 | The folder specs/numbered/0/0/1/2/3 holds five children on main | specs/numbered/0/0/1/2/3 | main | a1c84837ea062a10365e2afd44ac19a2f2356dd7 | present | 0 |
| RC-27 | The recursive tree on main lists 11,404 entries and is not truncated | repository root tree | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-28 | The folder changelog.d holds 335 direct children on main | changelog.d | main | ece56396f47d31dfed7bebe6c69f6dda39f53d83 | present | 0 |
| RC-29 | 491 archive refs exist under archive/laptop-20261121 on origin | refs/heads/archive/laptop-20261121/* | origin | n/a: aggregate of 491 tips in data-model.md | present | 0 |
| RC-30 | The stash ref exists on origin | refs/heads/archive/laptop-20261121/stash-0 | origin | 9d96feb696df742bcda242ee4b439060168b873d | present | 0 |
| RC-31 | 6 rescue branches exist on origin | refs/heads/rescue/uncommitted-20261121-* | origin | n/a: aggregate of 6 tips in data-model.md | present | 0 |
| RC-32 | Each rescue branch commit has one parent | refs/heads/rescue/uncommitted-20261121-* | origin | n/a: aggregate of 6 commits | present | 0 |
| RC-33 | The issue count of 497 archive refs matches origin | refs/heads/archive/laptop-20261121/* | origin | n/a: 491 of 497 names match | partial | 0 |
| RC-34 | One archived name has a same-name branch on origin | refs/heads/ plus each archived name, 491 names | origin | n/a: 1 of 491 names | partial | 0 |
| RC-35 | 489 archived names have no same-name branch on origin | refs/heads/ plus each archived name, 491 names | origin | n/a: 489 names | absent | 0 |
| RC-36 | The same-name branch of jmorrison-juniper-4200-migrate-mistwanperformance sits at another tip | refs/heads/jmorrison-juniper-4200-migrate-mistwanperformance | origin | 843be63bc837513b4442dae69da9f0db922e0ed1 | partial | 0 |
| RC-37 | The archive tip of jmorrison-juniper-4200-migrate-mistwanperformance diverges from that branch (48 ahead, 85 behind) | compare of 843be63bc837513b4442dae69da9f0db922e0ed1 and d77a900f9ec4db7149f90f324f1ade7772a6243d | origin | d77a900f9ec4db7149f90f324f1ade7772a6243d | partial | 0 |
| RC-38 | The source branch of the stash does not exist on origin | refs/heads/jmorrison-juniper-documented-trend-object-export | origin | n/a: HTTP 404 Not Found | absent | 0 |
| RC-39 | No pull request links issue 4868 | pull requests and search hits #2583 and #976 | origin | n/a: no link found | absent | 0 |

## Local Cross-Check

These values come from read-only commands: `git for-each-ref` and `git rev-parse --abbrev-ref HEAD` on the local checkout. The current branch of the local checkout is `main`.

- Local heads: 330. Local archive heads: 0. Local rescue heads: 1.
- Remote-tracking refs: 599. Remote-tracking archive refs under `refs/remotes/origin/archive/laptop-20261121/`: 491.
- Each remote-tracking archive tip equals the origin tip: 491 of 491.
- Archived names with a local branch: 10.
  - Same tip as the archive: `fix/2746-fm-http-status`, `fix/4766-msp-inventory-pagination`, `jmorrison-juniper-fix-4042-msp-selector`, and `refactor/2926-portal-handlers-c`.
  - Different tip from the archive: `chore/3400-dependency-bounds`, `jmorrison-jnpr-feat-4020-ordered-single-site-firmware-p`, `jmorrison-jnpr-fix-4051-rrm-dry-run-precedence`, `jmorrison-juniper-assess-4118`, `jmorrison-juniper-fix/3846-orphan-src-cleanup`, and `jmorrison-juniper-refactor-4007-troubleshooting-core`.

## Count Arithmetic

- Listed names: 497 = 491 archived names + 6 rescue branches.
- Counterpart states: 489 none + 1 differs + 6 self + 1 not applicable = 497.
- Claimed unpushed commits: 2,087 in total. The 6 rescue names claim 49. The 491 archived names claim 2,038.

## Not Applicable Checks

- Mist API and mistapi: the issue names no Mist request. No Mist document was read.
- Podman and containers: the issue names no container. The container documents were searched only.
- Juniper device behavior: the issue names no device. No juniper skill was loaded.
- Skills: no skill was loaded, because no listed skill matches a branch archive.

## Unverified

Each item states the claim and the reason it stays unverified.

1. The claim that each local-only branch held commits that no remote branch held at archive time. Reason: the local checkout cannot show the laptop state, and the recount in D-9 did not finish.
2. The claimed unpushed commit counts. Reason: D-9.
3. The claim that no secret exists in the archived commits. Reason: no secret scan ran in this work. The issue names the scan result only.
4. The claim that nothing was force-pushed, merged, or deleted. Reason: origin reads show the current state, not the push history.
5. The claim that each rescue commit sits on its worktree HEAD. Reason: the worktree is not in this checkout. RC-32 proves one parent for each rescue commit, but it does not prove the parent.
6. The base commit of the stash. Reason: the source branch is absent on origin, and no local copy was read.
7. The two notes in `jmorrison-juniper/vmm-topology-automation`, issues 351 and 352. Reason: D-7.
8. The absence of an archive procedure in `documentation/architecture.md`, `documentation/development-setup.md`, `documentation/container-deployment.md`, and `documentation/operator-guide.md`. Reason: the search used the local checkout, not the remote tree. The search found worktree and branch-name rules in `development-setup.md`, which this record does not change.

## Sources

Local paths read in full or in part:

- `AGENTS.md`
- `.github/copilot-instructions.md`
- `.specify/memory/constitution.md`
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`
- `.specify/scripts/powershell/spec-route.ps1` (read, not run)
- `changelog.d/README.md`
- `.ste-linter.toml`
- `documentation/quality-gates.md`
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv` (shape only)

Local paths searched only:

- `documentation/architecture.md`, `documentation/development-setup.md`, `documentation/container-deployment.md`, and `documentation/operator-guide.md`
- `tests/guardrails/test_spec_route_contract.py` and `tests/guardrails/test_process_folder_structure.py` (names and assertions)

Remote sources: origin GET responses in the remote table. No URL was fetched.
