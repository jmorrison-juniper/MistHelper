# Research: Release Publication

Each decision lists the choice, the alternatives, the reason, and the risk. Remote checks read `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` unless the row names another ref. The line numbers come from the remote blob named in the row.

## Sources

| ID | Source | Location | Used for |
| - | - | - | - |
| S-01 | `AGENTS.md` | Local: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\AGENTS.md`. Remote blob 44a9afffb5bd6f774973a845d27343e4e528b6ad. | Branch, worktree, commit, squash, and label rules (RC-49). |
| S-02 | `.github/copilot-instructions.md` | Local path in the repository. Remote blob f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179. | Bootstrap (RC-67), the Tests row (RC-68), the test-artifacts row (RC-46), and the serial merge slot (RC-45). |
| S-03 | `.specify/memory/constitution.md` | Local path in the repository. Remote blob 4584997a264c5a7ade2ca7441246e1f067083aa1. | Principles (RC-62, RC-63), Zscaler (RC-48), version format (RC-47), and Windows testing (RC-65). |
| S-04 | `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md` | Local paths in the repository. | Heading shape only. No claim cites them. |
| S-05 | Reference record `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv` | Local folder. Remote blob 83b950279e45704943ad6942d23c8fc99cced492 for `spec.md`. | Shape and depth of the record (RC-57). |
| S-06 | `documentation/container-deployment.md` | Remote blob f06228bc6bbe77cc009f956403872a06462466ea. | Revision label check (RC-50) and documented pull command (RC-66). |
| S-07 | `documentation/quality-gates.md` | Remote blob 6776d334cca5d9b43273473a06da367a65605c6d. | Queue settings owner approval (RC-51). |
| S-08 | `documentation/development-setup.md` | Local path in the repository. | Worktree bootstrap context. No claim cites it. |
| S-09 | `documentation/operator-guide.md` | Local path, searched for pull and restart text. | Context only. No claim cites it. |
| S-10 | `documentation/architecture.md` | Not read. | Not applicable: this release changes no architecture. |
| S-11 | Mist API OpenAPI file and mistapi source | Not read. | Not applicable: this release makes no Mist API or mistapi call. |
| S-12 | `changelog.d/README.md` | Remote blob fcbde10e0c293390bd9df8d62a5d61f158eca384. | Fragment shape and coordinator role (RC-44). |
| S-13 | `CHANGELOG.md` | Remote blob 2ddb493c8be66eddba8aa5825794c4f7b89f8048. | Heading, sentences, and layout (RC-06 to RC-14). |
| S-14 | `.github/workflows/release.yml` | Remote blob e81c05798c7609344d2d59b94114d7d9f76263be. | Tag trigger, build, container, notes, and release creation (RC-23 to RC-28). |
| S-15 | `.github/workflows/container-build.yml`, `auto-merge.yml`, `close-linked-issues.yml`, `ci.yml` | Remote blobs 737325976de75e90aa4526ab1cf2978782e648ce, 9d26134dd84cf50008a17fd878772102ce355983, 42a085ac6240518b028862c290ec9502a5b13b2a, and d51efbc13c0f0a2076680030ed8be7ef7cf64523. | Build, dispatch, close, and CI shards (RC-29 to RC-34). |
| S-16 | `scripts/release_body.py` | Remote blob 714052b2a0f3f0aa4a59d0f09c9dbefb343fb274. | Footer link, size limit, and summary form (RC-38, RC-39). |
| S-17 | `tests/guardrails/test_changelog_fragment_policy.py`, `test_markdown_links.py`, `tests/contract/test_release_body_workflow.py` | Remote blobs dbd5e8776797f12536b3bc2bd613143b85f3fc4a, cafefdac69006ddf7544e5a57a101f0f63fbcc38, and 1cc8f57837685ff5a4de8ce8baffa9a8213a4ad0. | TEST-1 to TEST-3 (RC-35, RC-36, RC-37, RC-70). |
| S-18 | `.github/PULL_REQUEST_TEMPLATE.md` | Remote blob ed03e8f36f20962d9c7bbd74cde192d5adfdcc77. | Template answers (RC-40). |
| S-19 | `pyproject.toml`, `Containerfile`, `.gitattributes`, `.gitignore` | Remote blobs eca34c826ea44ba4f2faefc07d04c2c117e99751, bc9249a19f6f181e7ea0e2c4b565a139d16d9253, 1745af40eeb78dfb5034e6cb2872bf3e0baed923, and 17eadfadb35a59e191a61c78877569ad747ddcc7. | Version, labels, merge attribute, and ignored folder (RC-41, RC-42, RC-43, RC-61). |
| S-20 | `.specify/scripts/powershell/spec-route.ps1` | Remote blob 37293a255f9b5de20ccb2b3ef0ad15717bab2826. | Route width and base (RC-52). |
| S-21 | Reusable image workflow in `jmorrison-juniper/misthelper-devtools` at ref `79a5e45970e876f1656d69520d9635cea1aa25ef` | Remote blob 45a1b413c6f33194357240f8c9d7504454f15a2c. Read with `gh api`. | Push default and label input (RC-53). |
| S-22 | `docker/metadata-action` README at ref `v6` | `https://api.github.com/repos/docker/metadata-action/contents/README.md?ref=v6`, read with `gh api`. | Revision label in the output example (RC-54). |
| S-23 | Skill `container-registry-products` | `C:\Users\jmorrison\.agents\skills\container-registry-products\SKILL.md` lines 8 and 10. `05-managed\01-ghcr-package-identity-and-restoration.md` lines 29, 68, and 169 to 170. | Digest identity, public tag deletion, and restore window. |
| S-24 | Local repository state (read-only) | `git rev-parse HEAD` returns `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. `git ls-files changelog.d` returns 334 files excluding `README.md`. | Consistency with the remote count (RC-01, RC-15). This local state proves no remote fact by itself. |
| S-25 | Remote GitHub reads (`gh api`, `gh pr view`, `gh pr list`, `gh release list`, `gh release view`, `gh run list`, `gh search code`) | Endpoints under `repos/jmorrison-juniper/MistHelper` and the rows that name them. | Issue facts, pull request state, releases, runs, and blob reads. |
| S-26 | Validator `spec-drafts\_meta\validate-drafts.ps1` | Read-only helper in META_DIR. | Self-review counts. |

Route arithmetic (not a remote fact): the route digits 0, 0, 1, 2, 3, 0, 1, 1 equal `1*5^5 + 2*5^4 + 3*5^3 + 0*5^2 + 1*5 + 1` = 3125 + 1250 + 375 + 0 + 5 + 1 = 4756. The reference route 0, 0, 1, 2, 4, 1, 4, 0 equals 4920 by the same rule.

## Issue Facts

These facts come from `gh issue view 4756` and the linked pull request search. The record cites each comment by its date.

| Item | Value |
| - | - |
| Number and state | 4756, OPEN |
| Title | chore(release): publish release v26.11.10.22.38 |
| Labels | `chore`, `docs`, `in-progress` |
| Author | `jmorrison-juniper` (repository owner) |
| Created and updated | 2026-11-10T22:38:23Z and 2026-11-11T01:33:05Z |
| Body goal | Publish release `v26.11.10.22.38` from current `main`. |
| Body plan | Seven steps. Create a `release/` branch. Add the release heading and fragment entries to `CHANGELOG.md`. Keep Unreleased empty and remove collected fragments. Open and merge the preparation pull request after its checks pass. Push an annotated tag on the merge commit. Verify the artifacts, container tags, and OCI revision. Set a concise title and body. |
| Body acceptance | Four criteria. `CHANGELOG.md` records all collected entries under the heading. `changelog.d/` holds only its README after the merge. The tagged release workflow publishes the wheel, source archive, ZIP, and container image. The release and image identify the tagged commit. |
| Body current state | Names `v26.09.28.19.49` as latest (RC-60, stale) and 288 fragments (P-02, stale). Says the latest main commit has the Python 3.15 minimum and passing checks (P-03, present). |
| Comment 1, 2026-11-10T22:41:20Z | Lists 14 open pull requests that the owner says modify 14 fragments. Says the release tag is unused. Says a clean release branch exists with no file changes. Asks the owner to merge or close the pull requests first (RC-17, RC-04, RC-05). |
| Comment 2, 2026-11-10T23:17:53Z | Main advanced to `c9aa2bbc` after PR 4757 merged and added `changelog.d/issue-4755-2fa-login.md`. Counts 289 fragments. Asks for a recheck before separately authorized preparation. States that post-merge workflows are unverified. |
| Comment 3, 2026-11-11T01:33:05Z | Main at `3b70ce21` holds 289 fragments. A scan of 18 open pull requests found no overlap. The comment does not authorize a release, a tag, a branch change, or removal of unmerged fragments. |
| Error text | None. The issue names no error output. |
| Reproduction steps | None. The issue is a release request. |
| Linked pull requests | None. The search for `4756` returns no pull request (RC-58). |

## Premise Check

The issue states premises that current evidence changes. Each row names the evidence.

| ID | Issue premise | Current evidence | Result | Row |
| - | - | - | - | - |
| P-01 | The latest GitHub release is `v26.09.28.19.49`. | The latest release is `v26.11.21.06.27`, published 2026-11-21. | Stale | RC-02 |
| P-02 | `main` holds 288 release-note fragments. | `main` holds 334 fragments, excluding `README.md`. Nine were added after the latest release. | Stale | RC-15, RC-16 |
| P-03 | The latest `main` commit includes the Python 3.15 minimum and passing checks. | `requires-python` is `>=3.15` at line 23. The Quality Gates run succeeded at `f03c6c9`. | Present | RC-41, RC-21 |
| P-04 | Tag `v26.11.10.22.38` is unused. | No tag matches `v26.11.10`. | Present | RC-04 |
| P-05 | A clean release branch exists with no file changes. | No `release/` branch exists. | Absent | RC-05 |
| P-06 | The 14 hold pull requests each modify a fragment on `main`. | 13 of the 14 merged, and their fragments are on `main`. PR 4208 is open and adds `pr-4208.md`, which is absent from `main`. | Stale | RC-17, RC-18, RC-19 |
| P-07 | The release publishes the wheel, source archive, standalone ZIP, and container image. | The release workflow declares these outputs. The previous release shows three assets. | Present | RC-03, RC-23 to RC-28 |
| P-08 | The release and the image identify the correct tagged commit. | No release exists for the new tag. The revision label cannot be read yet. | Unverified | U-3 |
| P-09 | The tag `v26.11.10.22.38` is the release name. | The tag equals the issue creation time, and it sorts before `v26.11.21.06.27`. | Present as a fact, changed by D-1 | RC-59, RC-02 |
| P-10 | `changelog.d/` holds only `README.md` after the release merge. | Achievable. T006 deletes the collected fragments. | Future | FR-002, SC-001 |
| P-11 | The release adds its entries to `CHANGELOG.md` (issue plan step 2). | `CHANGELOG.md` has no section for `v26.11.21.06.27`. Its newest section is `26.09.28.19.49`. | Absent | RC-08, RC-10 |

## Decisions

### D-1 Release stamp replaces the issue tag

- **Decision**: Use `v` plus a release stamp that T003 sets. The stamp uses UTC time in the form `YY.MM.DD.HH.MM`. It sorts after `26.11.21.06.27` and matches no existing tag.
- **Alternatives**: (a) Keep `v26.11.10.22.38`, as the issue states. (b) Set the stamp at tag push time. (c) Set the stamp at branch time, T003. Chosen: (c).
- **Rationale**: The issue tag equals the issue creation time at 22:38 UTC on 2026-11-10 (RC-59). It sorts before the latest release (RC-02). The constitution says the release coordinator writes the stamp (RC-47). Setting the stamp at branch time lets the CHANGELOG heading and the tag use the same value.
- **Risk**: The owner may reject a changed name. The title, the heading, and the image tag change with the name. The owner accepts the name when OWN-001 runs.
- **Human decision**: No.

### D-2 Collect every fragment at branch time

- **Decision**: Collect every fragment on `main` when the release branch opens. Delete each collected fragment in the release pull request. Keep `changelog.d/README.md`.
- **Alternatives**: (a) Collect only the nine fragments added after the latest release (RC-16). Leave 325 fragments, which fails FR-002. (b) Collect every fragment. Chosen: (b). (c) Keep the fragments and write only a summary. The coordinator rule deletes fragments in the release (RC-44).
- **Rationale**: The owner acceptance criteria require an empty `changelog.d/` after the merge. The README gives the coordinator that work (RC-44). The dated fragments on `main` are on or after 2026-09-28. The earlier release collected 21 fragments (RC-13).
- **Risk**: The section holds about 83 KB of fragment text. `CHANGELOG.md` grows from 527,193 bytes (RC-06). A fragment that merges after the branch opens stays in `changelog.d/` and fails SC-001. T-MERGE repeats the inventory check.
- **Human decision**: No.

### D-3 Release branch name

- **Decision**: Use `release/4756-release-publication`.
- **Alternatives**: (a) `chore/4756-release-publication`, the AGENTS pattern (RC-49, line 194). The changelog guard fails this head, because it allows a `CHANGELOG.md` edit only on a `release/` head (RC-35). (b) `release/` plus the stamp, with no issue number. (c) `release/4756-release-publication`. Chosen: (c).
- **Rationale**: The guard names `release/` as the only head that may edit `CHANGELOG.md` (RC-35). The issue number keeps the traceability that AGENTS requires (RC-49).
- **Risk**: The type `release` is not in the AGENTS type list (`feat`, `fix`, `chore`, `docs`). The guard test controls the rule for this change.
- **Human decision**: No.

### D-4 Section layout

- **Decision**: Write one level-two section for the release stamp and the UTC date. Copy the two introduction sentences from the earlier release section pattern (RC-13). Add the entry sentence from line 105 (RC-14). Write each fragment as one level-three entry in ordinal name order. Keep the bullets unchanged.
- **Alternatives**: (a) Group the bullets under Added, Changed, Fixed, Removed, and Security headings. The earlier release section mixes both forms (RC-10 to RC-14). Grouping rewrites each bullet and can lose context. (b) Copy each entry as it stands, with the heading level normalized. Chosen: (b). (c) One paragraph for each fragment.
- **Rationale**: The fragment README defines the entry shape (RC-44, lines 35 to 39). The earlier section uses the same entry sentence (RC-14). Ordinal name order can be repeated by any reviewer.
- **Risk**: The section is long. Readers find an entry by its issue number, which each bullet keeps.
- **Human decision**: No.

### D-5 Package version stays

- **Decision**: Keep `version = "2.1.0"` in `pyproject.toml` (RC-41).
- **Alternatives**: (a) Set the package version to the release stamp. This changes the wheel and sdist names, and it adds a version format that the package does not use. (b) Keep `2.1.0`. Chosen: (b).
- **Rationale**: The previous release assets carry `2.1.0` in their file names (RC-03). The constitution defines the stamp for the release identity (RC-47). A package version change is outside this issue.
- **Risk**: The package version and the release stamp differ. The image version label reads `2.1.0` (RC-42). OWN-004 records the observed label.
- **Human decision**: No.

### D-6 Owner hold on PR 4208

- **Decision**: HUMAN-DECISION-REQUIRED. Merge or close PR 4208 before T-PR starts. The release pull request does not include the PR 4208 fragment, because that fragment is not on `main`.
- **Alternatives**: (a) Start T-PR now. The owner comment says release preparation waits for these pull requests (owner comment 1). (b) Wait for the owner decision. Chosen: (b). (c) Close PR 4208 from the agent. FR-018 forbids this.
- **Rationale**: The owner comments state the hold (owner comments 1 and 3). Whether a feature ships in this release is a product priority decision (brief section 6). PR 4208 changes 82 files (RC-19).
- **Risk**: The release waits. The owner must choose before T001 can finish.
- **Human decision**: Yes.

### D-7 Pull request title, body, and Closes

- **Decision**: Use the title `chore(release): prepare release` followed by the release tag. The body holds `Closes #4756`, the fragment count, the gate results, and the template answers. Template items 36 and 38 are marked not applicable, with the reason, because the release changes `CHANGELOG.md` by design (RC-40).
- **Alternatives**: (a) `Refs #4756` keeps the issue open until the owner completes the steps. This breaks AGENTS line 224 (RC-49). (b) `Closes #4756`. Chosen: (b).
- **Rationale**: AGENTS requires `Closes` in the body, because a squash merge reads the body (RC-49, line 224). The summary comment lists the owner steps as open (OWN-001 to OWN-005).
- **Risk**: The issue closes at merge (RC-32). The owner keeps the summary comment current or reopens the issue.
- **Human decision**: No.

### D-8 Owner-only steps

- **Decision**: The owner performs OWN-001 to OWN-005. The agent performs no tag, no release, and no release text edit (FR-018).
- **Alternatives**: (a) The agent tags and publishes. Rejected: the orchestrator forbids it, and the issue asks for the publication decision to stay with the owner. (b) The owner performs the steps. Chosen: (b).
- **Rationale**: The constitution names the release coordinator for the stamp (RC-47). The orchestrator instruction records the steps as owner-only.
- **Risk**: The owner may delay the steps. The summary comment keeps the steps visible.
- **Human decision**: No.

### D-9 One serial merge slot

- **Decision**: Use one serial merge slot. While the release pull request is open, no other merge proceeds, and no other pull request receives the `auto-merge` label. Strict checks and linear history stay enabled (RC-22). The rule comes from `copilot-instructions` lines 485 to 493 (RC-45).
- **Alternatives**: (a) A merge queue. Rejected: the owner must approve queue settings (RC-51). (b) A serial slot. Chosen: (b). (c) An admin bypass. Rejected: `enforce_admins` is true (RC-22).
- **Rationale**: The rule keeps one branch current with `main` and all required checks green. The release fragment inventory then stays fixed.
- **Risk**: A dependency pull request that already has the label can merge during the window. The owner must remove the label first.
- **Human decision**: No.

### D-10 Owner verifies the image

- **Decision**: The owner verifies the image with pull and inspect commands (OWN-004). The agent pulls and pushes no image.
- **Alternatives**: (a) The agent pulls and verifies. Allowed, but the agent has no release authority. (b) The owner verifies. Chosen: (b). (c) The agent pushes an image from a local machine. Rejected: the Zscaler proxy blocks local push (RC-48).
- **Rationale**: The release workflow builds and pushes the image (RC-25 and RC-30). The documented inspect command reads the revision label (RC-50), and the documented pull command reads the image (RC-66).
- **Risk**: The proxy may block a pull as well (U-2). The owner records the failure, and the agent does not work around it.
- **Human decision**: No.

### D-11 Merge-triggered container build

- **Decision**: Keep the existing workflows unchanged. Record the side effect. A separate issue must track a workflow change.
- **Alternatives**: (a) Change `auto-merge.yml` so it skips the container build for a `CHANGELOG.md`-only merge. This changes a shared workflow and falls outside this issue. (b) Keep the workflows and record the effect. Chosen: (b). (c) Delay the merge until the tag exists. Not possible, because the tag points to the merge commit.
- **Rationale**: Each merge dispatches `container-build.yml` (RC-31). That workflow builds without a version override (RC-30) and pushes by default (RC-53). The release build moves `latest` again (RC-25 and RC-26).
- **Risk**: A consumer may pull an image with an automatic stamp and no release. OWN-004 checks `latest` after the release build.
- **Human decision**: No.

## Remote Verification Table

Each row is one remote check. The STATUS file lists the same 70 rows in the same order. The result uses the values present, absent, partial, or stale.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Main head is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. | refs/heads/main | main | not applicable | present | 0 |
| RC-02 | Latest release is `v26.11.21.06.27` at commit `a9d848c98481f0e69c6b0e52131caf76120bba52`, tag object `c2ac5fcee826e2e84e5cd114345a51a59f463939`. | release v26.11.21.06.27 | a9d848c98481f0e69c6b0e52131caf76120bba52 | not applicable | present | 0 |
| RC-03 | Release `v26.11.21.06.27` publishes a wheel, a source archive, and a ZIP named with `2.1.0` or the release tag. | release assets of v26.11.21.06.27 | a9d848c98481f0e69c6b0e52131caf76120bba52 | not applicable | present | 0 |
| RC-04 | No tag matches `v26.11.10.22.38`. | refs/tags/v26.11.10.22.38 | main | not applicable | absent | 0 |
| RC-05 | No release branch exists. | refs/heads/release/* | main | not applicable | absent | 0 |
| RC-06 | `CHANGELOG.md` blob on main is 527,193 bytes. | CHANGELOG.md | main | 2ddb493c8be66eddba8aa5825794c4f7b89f8048 | present | 1 |
| RC-07 | `CHANGELOG.md` at the release commit is the same blob as main. | CHANGELOG.md | a9d848c98481f0e69c6b0e52131caf76120bba52 | 2ddb493c8be66eddba8aa5825794c4f7b89f8048 | present | 1 |
| RC-08 | `CHANGELOG.md` has no section for `v26.11.21.06.27`. | CHANGELOG.md | main | 2ddb493c8be66eddba8aa5825794c4f7b89f8048 | absent | 0 |
| RC-09 | `CHANGELOG.md` line 13 holds the Unreleased heading. | CHANGELOG.md | main | 2ddb493c8be66eddba8aa5825794c4f7b89f8048 | present | 13 |
| RC-10 | `CHANGELOG.md` line 15 holds the heading for `26.09.28.19.49`. | CHANGELOG.md | main | 2ddb493c8be66eddba8aa5825794c4f7b89f8048 | present | 15 |
| RC-11 | `CHANGELOG.md` line 6 states the version format `YY.MM.DD.HH.MM`. | CHANGELOG.md | main | 2ddb493c8be66eddba8aa5825794c4f7b89f8048 | present | 6 |
| RC-12 | `CHANGELOG.md` lines 8 to 11 warn against feature branch edits and name `changelog.d`. | CHANGELOG.md | main | 2ddb493c8be66eddba8aa5825794c4f7b89f8048 | present | 8 |
| RC-13 | `CHANGELOG.md` lines 17 and 18 state that the `26.09.28.19.49` release collects 21 fragments. | CHANGELOG.md | main | 2ddb493c8be66eddba8aa5825794c4f7b89f8048 | present | 17 |
| RC-14 | `CHANGELOG.md` line 105 defines the entry sentence for the release section. | CHANGELOG.md | main | 2ddb493c8be66eddba8aa5825794c4f7b89f8048 | present | 105 |
| RC-15 | `changelog.d/` holds 334 fragments excluding `README.md`, with 83,416 bytes. Three are dated, and all three are on or after 2026-09-28. | changelog.d/ | main | not applicable | present | 0 |
| RC-16 | Nine fragments were added after the latest release commit. | changelog.d/ (compare a9d848c to main) | main | not applicable | present | 0 |
| RC-17 | The owner comment says 14 hold fragments are absent from `main`. Thirteen are present now. | changelog.d/ (14 fragments named by owner comment 1) | main | not applicable | stale | 0 |
| RC-18 | `changelog.d/pr-4208.md` is absent from `main`. | changelog.d/pr-4208.md | main | not applicable | absent | 0 |
| RC-19 | PR 4208 is open, changes 82 files, and adds `changelog.d/pr-4208.md`. | PR 4208 file list | jmorrison-juniper-4200-migrate-mistwanperformance | not applicable | present | 0 |
| RC-20 | PR 4813 is open and adds `changelog.d/issue-4776-csv-carriage-returns.md`. | PR 4813 file list | jmorrison-juniper-csv-carriage-return-preservation | not applicable | present | 0 |
| RC-21 | The Quality Gates run 45774119357 succeeded on `main` at `f03c6c9`. | .github/workflows/ci.yml (run 45774119357) | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | not applicable | present | 0 |
| RC-22 | Branch protection on `main` requires 15 status contexts, strict checks, linear history, and admin enforcement. Reviews are not required. | branches/main/protection | main | not applicable | present | 0 |
| RC-23 | `release.yml` runs on tags that match `v*.*.*`. | .github/workflows/release.yml | main | e81c05798c7609344d2d59b94114d7d9f76263be | present | 5 |
| RC-24 | The `build-python` job runs on `ubuntu-latest`. | .github/workflows/release.yml | main | e81c05798c7609344d2d59b94114d7d9f76263be | present | 12 |
| RC-25 | `release.yml` derives the standalone ZIP name from the tag. | .github/workflows/release.yml | main | e81c05798c7609344d2d59b94114d7d9f76263be | present | 42 |
| RC-26 | `release.yml` builds the container with the reusable image workflow and tags it `latest`. | .github/workflows/release.yml | main | e81c05798c7609344d2d59b94114d7d9f76263be | present | 85 |
| RC-27 | `release.yml` generates release notes through the GitHub API. | .github/workflows/release.yml | main | e81c05798c7609344d2d59b94114d7d9f76263be | present | 130 |
| RC-28 | `release.yml` creates the release from the prepared body and three file globs. | .github/workflows/release.yml | main | e81c05798c7609344d2d59b94114d7d9f76263be | present | 146 |
| RC-29 | `container-build.yml` runs on a push to `main`. | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 5 |
| RC-30 | `container-build.yml` tags `latest` with an automatic stamp when no version override is given. | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 114 |
| RC-31 | `auto-merge.yml` dispatches `container-build.yml` after each merge. | .github/workflows/auto-merge.yml | main | 9d26134dd84cf50008a17fd878772102ce355983 | present | 65 |
| RC-32 | `close-linked-issues.yml` closes issues only after a merged pull request. | .github/workflows/close-linked-issues.yml | main | 42a085ac6240518b028862c290ec9502a5b13b2a | present | 46 |
| RC-33 | `ci.yml` runs the changelog fragment guard. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 298 |
| RC-34 | The `ci.yml` shard paths include `tests/contract` and `tests/guardrails`. | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 255 |
| RC-35 | The changelog guard allows a `CHANGELOG.md` edit only on a `release/` head. | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 75 |
| RC-36 | The changelog guard requires the text `changelog.d` in `CHANGELOG.md`. | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 251 |
| RC-37 | The markdown link guard checks every relative link in the tracked tree. | tests/guardrails/test_markdown_links.py | main | cafefdac69006ddf7544e5a57a101f0f63fbcc38 | present | 1 |
| RC-38 | `release_body.py` builds the footer link to `CHANGELOG.md` at the tag. | scripts/release_body.py | main | 714052b2a0f3f0aa4a59d0f09c9dbefb343fb274 | present | 91 |
| RC-39 | `release_body.py` caps the body at 125,000 code points and switches to the summary form. | scripts/release_body.py | main | 714052b2a0f3f0aa4a59d0f09c9dbefb343fb274 | present | 167 |
| RC-40 | PR template item 38 requires `CHANGELOG.md` to stay unchanged. Item 36 requires one fragment. | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 38 |
| RC-41 | `pyproject.toml` holds version `2.1.0` at line 3 and requires Python 3.15 at line 23. | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 3 |
| RC-42 | The `Containerfile` sets the image version label to `2.1.0`. | Containerfile | main | bc9249a19f6f181e7ea0e2c4b565a139d16d9253 | present | 27 |
| RC-43 | `.gitattributes` applies `merge=union` to `CHANGELOG.md`. | .gitattributes | main | 1745af40eeb78dfb5034e6cb2872bf3e0baed923 | present | 34 |
| RC-44 | The `changelog.d/README.md` gives the release coordinator the aggregate step and the deletion of collected fragments, at lines 67 to 72. | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 67 |
| RC-45 | The serial merge slot rule and the pause rule are at lines 485 to 493. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 485 |
| RC-46 | The test-artifacts row says Git ignores generated evidence. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 339 |
| RC-47 | The constitution states the version format `YY.MM.DD.HH.MM` in UTC, and the release coordinator writes the stamp. | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 406 |
| RC-48 | The constitution states that local `podman push` behind Zscaler is blocked. | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 334 |
| RC-49 | AGENTS states the branch name rule, the worktree rule, `Closes` in the body, the squash merge, and the auto-merge label rule at lines 194 to 239. | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| RC-50 | The container deployment page shows `podman image inspect` for the revision label. | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 274 |
| RC-51 | The quality gates page states that queue settings need separate owner approval. | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 127 |
| RC-52 | `spec-route.ps1` sets the route width to 8 at line 7 and the base to 5 at line 17. | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| RC-53 | The reusable container workflow pushes by default at line 60 and passes metadata labels to the build at line 211. | misthelper-devtools .github/workflows/reusable-container-image.yml | 79a5e45970e876f1656d69520d9635cea1aa25ef | 45a1b413c6f33194357240f8c9d7504454f15a2c | present | 60 |
| RC-54 | The `docker/metadata-action` v6 README lists the revision label in its output example. | https://api.github.com/repos/docker/metadata-action/contents/README.md?ref=v6 | v6 | not applicable | present | 245 |
| RC-55 | The route folder `specs/numbered/0/0/1/2/3/0/1/1` is absent. | specs/numbered/0/0/1/2/3/0/1/1 | main | not applicable | absent | 0 |
| RC-56 | No folder named `4756-` exists under `specs`. | specs | main | not applicable | absent | 0 |
| RC-57 | The reference record `4920-ex-hardware-inventory-csv` has a `spec.md`. | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-58 | No pull request links issue 4756. | gh pr list search 4756 | main | not applicable | absent | 0 |
| RC-59 | The issue tag equals the issue creation time, 2026-11-10T22:38:23Z. | Issue 4756 createdAt | not applicable | not applicable | present | 0 |
| RC-60 | The issue body names `v26.09.28.19.49` as the latest release. | Issue 4756 body | not applicable | not applicable | stale | 0 |
| RC-61 | `.gitignore` ignores `/test-artifacts/`. | .gitignore | main | 17eadfadb35a59e191a61c78877569ad747ddcc7 | present | 107 |
| RC-62 | The constitution principle headings I to VII start at line 38. | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-63 | The constitution Principle IV steps 10 to 12 cover the main build, the revision check, and deployment at lines 166 to 171. | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 166 |
| RC-64 | The constitution technology section starts at line 274 and names Podman as the primary runtime at line 300. | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 274 |
| RC-65 | The constitution testing section names Windows 11 for local development at line 363. | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 363 |
| RC-66 | The container deployment page documents `podman pull` for the latest image at line 309. | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 309 |
| RC-67 | `copilot-instructions` gives the bootstrap commands for a new worktree at lines 27 to 30. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 27 |
| RC-68 | The local gates table Tests row names the pytest command for the changed test file at line 61. | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| RC-69 | The release body of `v26.11.21.06.27` ends with a footer that links `CHANGELOG.md` at that tag. | Release body of v26.11.21.06.27 | v26.11.21.06.27 | not applicable | present | 0 |
| RC-70 | `test_release_body_workflow.py` states that it proves the release body source without a release run. | tests/contract/test_release_body_workflow.py | main | 1cc8f57837685ff5a4de8ce8baffa9a8213a4ad0 | present | 1 |

## Unverified

| ID | Claim | Reason | Evidence that exists |
| - | - | - | - |
| U-1 | Anonymous pulls of `ghcr.io/jmorrison-juniper/misthelper` work. | The package visibility setting was not read. | RC-66 documents the plain pull command. The skill states that public GHCR images permit anonymous pulls (`05-managed\01-ghcr-package-identity-and-restoration.md` line 20). |
| U-2 | A pull through the corporate proxy works. | The owner network was not tested. | RC-48 documents a push block. Pull behavior is not stated. |
| U-3 | The image version label reads the release stamp after the build. | No image exists for the new stamp. The label source for the build is not read. | RC-42 sets `2.1.0` in the Containerfile. OWN-004 records the observed label. |
| U-4 | The merge-triggered build pushes an image with an automatic stamp. | No merge has happened. | RC-30 and RC-31 show the workflow path. The run result is unread. |
| U-5 | `Closes #4756` closes the issue at merge. | No merge has happened. | RC-32 shows the close workflow. |
| U-6 | GitHub generated release notes follow the previous-release rule. | The GitHub documentation URLs were blocked for this session. The fetch tool returned an address block for `docs.github.com`. | RC-69 records the observed footer of the previous release. |
| U-7 | The runtime output of `docker/metadata-action` v6 holds the revision label. | Only the README example was read. | RC-54 shows the example output. |
| U-8 | Some fragments hold relative links that break at the repository root. | The 334 bodies were not read one by one. | T004 applies the rule. TEST-2 checks the result (RC-37). |
| U-9 | All 15 required checks pass on the release pull request. | The pull request does not exist yet. | RC-22 names the 15 contexts. |
| U-10 | Branch protection has no other rule that blocks the release merge. | Only the fields in RC-22 were read. | RC-22 states the rules read. |
