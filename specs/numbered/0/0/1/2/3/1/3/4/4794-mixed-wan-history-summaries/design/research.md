# Research: Mixed WAN History Summaries

This file records the evidence and the decisions for issue 4794. Repository paths use forward slashes. The `remote check` numbers in this file match the rows of the remote verification table. Each row holds the path, the ref, the blob or commit SHA, the result, and the line.

## Sources

### Local files, hash-matched to main

Each file below has a `git hash-object` value that equals its blob SHA on `main`. The line numbers that this record cites are read from these local copies. The matching files are: `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, `.specify/scripts/powershell/spec-route.ps1`, the four templates in `.specify/templates/`, `documentation/quality-gates.md`, `documentation/architecture.md`, `documentation/development-setup.md`, `documentation/operator-guide.md`, `documentation/ASD-STE100_writing-guide.md`, and `documentation/mist-api-openapi31yaml.yaml`.

### Remote reads

The record uses these GitHub reads, all read only:

- `repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1` returned 11,404 rows and no truncation.
- `repos/jmorrison-juniper/MistHelper/git/trees/843be63bc837513b4442dae69da9f0db922e0ed1?recursive=1` for the candidate head.
- `contents` reads at `main`, at `843be63`, and at `07b7751` and `d7a706d`.
- `commits/<sha>` for the repair commit, the parent commit, and commit `15c69b11`.
- `compare` between `main` and the repair commit, and between the repair commit and the candidate head.
- `git/refs/heads` for `main` and the candidate branch.
- `gh issue view`, `gh pr view`, and `gh pr list` for issues 4200, 4793, 4794, 4795, and PR 4208.

### Local SDK

The installed package is `.venv\Lib\site-packages\mistapi-0.64.1.dist-info`. Its file `.venv\Lib\site-packages\mistapi\api\v1\orgs\devices.py` has the `git hash-object` value `90fe126e9c3e34d7784644016e12833b7359737d`. The SDK is outside the repository tree, so its rows cite the local path only.

### Upstream

No URL was fetched. The record has no upstream check.

### Skills

No skill was loaded. The issue concerns pure Python domain summaries. It has no Podman, container, or Juniper device scope, so the skill rules for those topics do not apply.

## Linked Work and State

These facts describe the state of GitHub objects. The brief lists them here, not in the remote table, because they are not code, test, configuration, or document claims.

- Issue 4794 is OPEN. Its labels are `bug`, `web-portal`, and `in-progress`. Its comment from 2026-11-13 keeps the issue open until the repair reaches main.
- PR 4208, titled `feat(web-portal): integrate WAN performance dashboards`, is OPEN and not merged. It is a draft. Its merge state is DIRTY and its mergeable state is CONFLICTING. Its head branch is `jmorrison-juniper-4200-migrate-mistwanperformance` at `843be63bc837513b4442dae69da9f0db922e0ed1`. It changes 82 files.
- The check rollup of head `843be63` reported 42 SUCCESS and 10 SKIPPED when this record read it. It reported no failure.
- The PR body reads `Refs #4200, #4793, #4794, #4795, #4797, and #4798. This PR does not close #4200.` It names issue 4794 without a closing keyword (remote check 47).
- Issue 4200 is OPEN, titled `Spec: Integrate MistWANPerformance into MistHelper portal`.
- Issue 4793 is OPEN, titled `Runtime: duplicate API sample in WAN history refresh`.
- Issue 4795 is OPEN, titled `Runtime: WAN gateway history disappears after an ordinary refresh`.
- Repair commit d7a706d was made on 2026-11-13 at 20:26:55 UTC. Its message names issues 4793, 4794, and 4795 (remote check 97). It changes 19 paths, which include history store, presentation, and test files (remote check 98).
- Comparing `main` with the repair commit reports `diverged`, with the repair commit ahead by 3 commits and behind by 52 commits. Comparing the repair commit with head `843be63` reports `ahead` by 30 commits and behind by 0 (remote check 44).
- Later commits touch `summary.py` on the head. Commit `2326357` on 2026-11-14 adds unit helpers and keeps the repair (remote checks 52 to 54). Commit `8758b55` on 2026-11-13 came before the repair.
- The local checkout is on branch `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. That SHA equals the remote tip (remote check 41). The local object store holds commit d7a706d and lacks commit 15c69b11. The local working tree has no `summary.py`. Local evidence supports no remote claim.

## Existing Record

No legacy record exists for issue 4794. A local glob for `specs/**/4794-*` found no folder. The remote tree has no path that contains `4794-` (remote check 36). The record is new.

## Route Verification

- The base-5 digits of 4794, with eight digit places, are `0 0 1 2 3 1 3 4`. The function `Get-SpecRadixSegments` in `.specify/scripts/powershell/spec-route.ps1` computes them (remote check 12). The result equals the route from the orchestrator.
- The function `Resolve-SpecFeaturePath` joins `specs/numbered`, the route, and the branch name. The record folder is `specs/numbered/0/0/1/2/3/1/3/4/4794-mixed-wan-history-summaries`.
- The route parent `specs/numbered/0/0/1/2/3` already holds five children, 0 to 4 (remote check 105). The route reuses child 1 (remote check 34), so the route adds no child to a full parent.
- The route parent `specs/numbered/0/0/1/2/3/1/3` holds no child yet (remote check 35). The record folder is absent (remote check 36).

## Decisions

### D-1 Delivery branch

- Options: (a) a new branch from main. (b) A branch stacked on the candidate branch. (c) The repair on the candidate branch.
- Decision: option (c).
- Reason: The defective module is absent on main (remote checks 37 to 40). AGENTS.md forbids a branch from another feature branch (remote check 2). The candidate already holds repair commit d7a706d (remote check 44).
- Risk: The issue cannot close before PR 4208 merges. The PR has conflicts (Linked Work).
- Human decision required: no.

### D-2 Test scope

- Options: (a) assert the daily summary only, as the current test does. (b) Assert all six summaries in the same test. (c) Write one parameterized test for each period kind.
- Decision: option (b).
- Reason: The builder calls the same helper for each period kind (remote checks 55 and 56). The current test asserts the daily summary only (remote check 62). One test keeps one shared fixture.
- Risk: Monthly hours depend on the calendar month. The test asserts `expected_hours` from each summary's period, not a constant (remote check 58).
- Human decision required: no.

### D-3 Presence check in `_has_events`

- Options: (a) keep the key-presence check (remote check 54). (b) Require a measured value in `_has_events`.
- Decision: option (a).
- Reason: `_complete` already removes unmeasured hours (remote check 52). The missing-evidence test expects a summary with zero complete hours and unknown totals (remote check 63). Option (b) would return `None` for that case, and the test would fail.
- Risk: A period with only incomplete event hours returns a summary with zero complete hours, not `None`. The portal shows zero complete windows and Unknown totals (remote check 68).
- Human decision required: no.

### D-4 Logging and comments

- Options: (a) no logging, as the candidate head has now. (b) One info line before the period build and one debug line after it. (c) One debug line only.
- Decision: option (b), with inline comments on each touched line.
- Reason: Principle VII requires an info line before and a debug line after each touched action (remote check 11). Principle VI requires inline comments on changed lines (remote check 10).
- Risk: Six period builds for one request add twelve log lines. The text stays short and ASCII.
- Human decision required: no.

### D-5 Publication of PR 4208

- Options: (a) publish PR 4208 as soon as the repair passes gates. (b) Publish after the issue 4200 gates pass and the orchestrator authorizes the merge. (c) Defer publication until the owner approves it.
- Decision: option (b), with owner approval. The owner must approve or defer the merge.
- Reason: The issue states that it does not authorize publication of the incomplete candidate. The release timing is a product priority.
- Risk: The operator fix waits. The repair stays on the candidate branch, so other work can continue.
- Human decision required: yes. The question is whether PR 4208 merges to main now, later, or not at all.

### D-6 Record slug and route

- Options: (a) `4794-mixed-wan-history-summaries`. (b) `4794-wan-history-flap-count`. (c) `4794-flap-count-null-safety`.
- Decision: option (a).
- Reason: The slug follows the issue title. The route follows from the base-5 result in Route Verification.
- Risk: None known.
- Human decision required: no.

### D-7 Record placement

- Options: (a) a docs commit on the candidate branch. (b) A docs-only branch from main. (c) No record in the repository.
- Decision: option (a).
- Reason: The record cites line numbers on the candidate head, so it belongs with that head. A docs-only branch from main would cite code that main lacks. The constitution requires a spec record for this change (remote check 106).
- Risk: The PR gains 13 Markdown files. A rebase changes the SHAs that the rows cite. Update each row that names `843be63`, `d7a706d`, or `07b7751` after the rebase.
- Human decision required: no.

### D-8 Rebase method

- Options: (a) rebase onto `origin/main` and push with `--force-with-lease`. (b) Merge main into the branch. (c) Squash the candidate history before the rebase.
- Decision: option (a).
- Reason: The constitution requires a rebase onto `origin/main` before a push (remote check 9). AGENTS.md requires a push with `--force-with-lease` (remote check 95).
- Risk: Caution: the rewrite changes every commit SHA on the branch. Record the old head `843be63` in a PR comment before the push, so the branch can be recovered.
- Human decision required: no.

### D-9 Conflict stop rule

- Options: (a) stop when conflicts exceed 20 lines (remote check 3). (b) Resolve every conflict. (c) Abandon the branch and restart from main.
- Decision: option (a). Stop, report the blocker, and leave the candidate unchanged.
- Reason: AGENTS.md names 20 lines as the limit for restarting from main (remote check 3). Abandoning the branch would discard 30 commits of candidate work, so the choice belongs to the owner.
- Risk: The repair waits for the owner. The blocker report gives the next action.
- Human decision required: no.

### D-10 Closing keyword

- Options: (a) add `Closes #4794` to the PR body. (b) Keep `Refs #4794`. (c) Close the issue by hand.
- Decision: option (a).
- Reason: AGENTS.md requires `Closes #<issue>` in the body (remote check 94). A squash merge reads the body (remote check 96 covers the squash rule). Closing by hand skips the verification that the repair reached main.
- Risk: The merge closes the issue at once. SC-005 checks main after the merge.
- Human decision required: no.

### D-11 mistapi version wording

- Options: (a) fix the wording in this change. (b) File a separate issue. (c) Leave the drift unrecorded.
- Decision: option (b).
- Reason: The drift does not change summary behavior. The repository files disagree on the lower bound (remote checks 7, 23, and 25). A separate issue keeps this change surgical.
- Risk: The drift remains until the separate issue lands.
- Human decision required: no.

## Remote Verification Table

Each row is one check. The table holds 106 rows. The STATUS file holds the same 106 entries. For commit rows, the SHA column holds the commit SHA.

| # | Claim | Path | Ref | Blob or commit SHA | Result | Line |
| - | - | - | - | - | - | - |
| 1 | AGENTS.md defines the writing style section | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| 2 | AGENTS.md forbids a branch from another feature branch | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 197 |
| 3 | AGENTS.md stops a branch when a conflict exceeds 20 lines | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 268 |
| 4 | copilot-instructions defines the local gates section | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| 5 | copilot-instructions STE gate row lists the Markdown files | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| 6 | copilot-instructions defines managed specs roots and the numeric route rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159 |
| 7 | copilot-instructions states mistapi range 0.64.0 which pyproject does not state | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | stale | 21 |
| 8 | constitution Principle I five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| 9 | constitution Principle IV full deployment pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| 10 | constitution Principle VI inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| 11 | constitution Principle VII action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| 12 | spec-route computes base-5 route segments | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| 13 | spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| 14 | plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| 15 | tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| 16 | checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| 17 | quality gates document exists | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 0 |
| 18 | architecture document exists | documentation/architecture.md | main | b4cab54be36d223b7eba879ca99b838f508938ce | present | 0 |
| 19 | development setup document exists | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 0 |
| 20 | operator guide names no WAN event summary rule | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 63 |
| 21 | STE writing guide exists | documentation/ASD-STE100_writing-guide.md | main | b464165aae116a17bb3031d3cef9b84a95589c0a | present | 0 |
| 22 | OpenAPI defines operation searchOrgDeviceEvents | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 8672 |
| 23 | pyproject pins mistapi at 0.64.1 or later below 0.65 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| 24 | pyproject sets ruff and black line length to 120 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 202 |
| 25 | requirements pins mistapi 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| 26 | ci.yml defines MYPY_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| 27 | ci.yml defines VULTURE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| 28 | ci.yml defines PYDOCSTYLE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| 29 | ci.yml defines INTERROGATE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| 30 | STE linter configuration exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| 31 | pull request template exists | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 0 |
| 32 | auto-merge workflow exists | .github/workflows/auto-merge.yml | main | 9d26134dd84cf50008a17fd878772102ce355983 | present | 0 |
| 33 | reference record folder 4920 exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv | main | 00922155516e4f21e34a0bf75613fae7ab481193 | present | 0 |
| 34 | route child 1 exists under specs/numbered/0/0/1/2/3 | specs/numbered/0/0/1/2/3/1 | main | 42d51be54c337e7b0c6c5abba0ed6513cbd390d6 | present | 0 |
| 35 | route parent 2/3/1/3 holds no child yet | specs/numbered/0/0/1/2/3/1/3 | main | none | absent | 0 |
| 36 | record folder for issue 4794 is not in the repository yet | specs/numbered/0/0/1/2/3/1/3/4/4794-mixed-wan-history-summaries | main | none | absent | 0 |
| 37 | summary module is absent on main | src/interfaces/wan_performance/domain/summary.py | main | none | absent | 0 |
| 38 | calendar module is absent on main | src/interfaces/wan_performance/domain/calendar.py | main | none | absent | 0 |
| 39 | calendar test module is absent on main | tests/unit/wan_performance/test_calendar_summaries.py | main | none | absent | 0 |
| 40 | WAN documentation is absent on main | documentation/wan-performance.md | main | none | absent | 0 |
| 41 | main tip is the baseline for absence checks | refs/heads/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| 42 | candidate branch head is 843be63 | refs/heads/jmorrison-juniper-4200-migrate-mistwanperformance | jmorrison-juniper-4200-migrate-mistwanperformance | 843be63bc837513b4442dae69da9f0db922e0ed1 | present | 0 |
| 43 | repair commit d7a706d exists | commit d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | present | 0 |
| 44 | repair commit d7a706d is an ancestor of the candidate head | commit d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | 843be63bc837513b4442dae69da9f0db922e0ed1 | d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | present | 0 |
| 45 | parent commit 07b7751 exists | commit 07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc | 07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc | 07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc | present | 0 |
| 46 | commit 15c69b11 cited by the issue does not exist | commit 15c69b1176f7ae7c24e010aba3d29915ef228610 | 15c69b1176f7ae7c24e010aba3d29915ef228610 | 15c69b1176f7ae7c24e010aba3d29915ef228610 | absent | 0 |
| 47 | PR 4208 body refers to 4794 without a closing keyword | pull request 4208 body | pull/4208 | none | partial | 0 |
| 48 | parent commit _has_events checks only key presence | src/interfaces/wan_performance/domain/summary.py | 07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc | aa9c3fac65344ed43fc1d571a157c67bc456bc26 | present | 333 |
| 49 | parent commit _complete reads the flap_count entry without a presence check | src/interfaces/wan_performance/domain/summary.py | 07b7751fb9e6c0e8d285d2adb9b0273bc5aae4fc | aa9c3fac65344ed43fc1d571a157c67bc456bc26 | present | 338 |
| 50 | repair commit makes link-event totals optional | src/interfaces/wan_performance/domain/summary.py | d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | 6ee318bd17dc386b0fb0ca09d938ba7d5ac9e658 | present | 47 |
| 51 | repair commit _complete uses a presence and None check | src/interfaces/wan_performance/domain/summary.py | d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | 6ee318bd17dc386b0fb0ca09d938ba7d5ac9e658 | present | 341 |
| 52 | candidate head _complete keeps the presence and None check | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 354 |
| 53 | candidate head LinkEventSummaries.build keeps totals unknown without known or complete hours | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 337 |
| 54 | candidate head _has_events checks key presence | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 346 |
| 55 | candidate head CalendarSummaries.build calls LinkEventSummaries.build for each summary | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 130 |
| 56 | candidate head CalendarSummaries.build builds daily weekly monthly and rolling summaries | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 124 |
| 57 | candidate head rolling windows are 3h 12h and 24h | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 157 |
| 58 | CalendarPeriod defines expected_hours | src/interfaces/wan_performance/domain/calendar.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88e0598aa66d24086e9dfe0378c374af87ea9305 | present | 64 |
| 59 | MetricMeasurement value may be None | src/interfaces/wan_performance/domain/measurement.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | bec652f726330e1990b0ab0281c0c05abcb88bba | present | 25 |
| 60 | HourlyMeasurement natural_key combines identity and hour | src/interfaces/wan_performance/domain/measurement.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | bec652f726330e1990b0ab0281c0c05abcb88bba | present | 103 |
| 61 | mixed event and ordinary hours test exists on candidate head | tests/unit/wan_performance/test_calendar_summaries.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 1037a9760ef4281f6252b53cae2c21c1f21f0e6e | present | 222 |
| 62 | mixed event and ordinary hours test asserts the daily summary only | tests/unit/wan_performance/test_calendar_summaries.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 1037a9760ef4281f6252b53cae2c21c1f21f0e6e | partial | 243 |
| 63 | missing event evidence test exists on candidate head | tests/unit/wan_performance/test_calendar_summaries.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 1037a9760ef4281f6252b53cae2c21c1f21f0e6e | present | 252 |
| 64 | known zero flaps test exists on candidate head | tests/unit/wan_performance/test_calendar_summaries.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 1037a9760ef4281f6252b53cae2c21c1f21f0e6e | present | 274 |
| 65 | e2e test renders missing evidence as Unknown | tests/e2e/web_portal/test_wan_performance_live.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d485c28afb5bf4bd6de20ba9291feb9b267babac | present | 2295 |
| 66 | live history read calls CalendarSummaries.build | src/interfaces/wan_performance/presentation/live_routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 76 |
| 67 | offline dashboard calls CalendarSummaries.build | src/interfaces/wan_performance/presentation/routes.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 1b7dbc5dfe0c56ca6cea9dd6bf15847b4dae80fc | present | 136 |
| 68 | template guards unknown link-event totals | src/interfaces/wan_performance/presentation/templates/wan_performance/live.html | 843be63bc837513b4442dae69da9f0db922e0ed1 | 1f63bc8316b05052cdb3d0bf554c5b9159a40593 | present | 409 |
| 69 | template renders Unknown for absent flap count | src/interfaces/wan_performance/presentation/templates/wan_performance/live.html | 843be63bc837513b4442dae69da9f0db922e0ed1 | 1f63bc8316b05052cdb3d0bf554c5b9159a40593 | present | 417 |
| 70 | selected-port refresh persists hourly records | src/interfaces/wan_performance/collection/live_service.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 434d0e4e83ddb8b848c6caa00d553a4f86382f8e | present | 74 |
| 71 | ordinary refresh builds snapshot records | src/interfaces/wan_performance/collection/live_service.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 434d0e4e83ddb8b848c6caa00d553a4f86382f8e | present | 43 |
| 72 | snapshot records name flap_count only in the gateway insight set | src/interfaces/wan_performance/collection/snapshot_records.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | a4d3d1f9c7407aa37702a4e9a2d7b65ce1e1df33 | present | 140 |
| 73 | snapshot client calls searchOrgDeviceEvents | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 468 |
| 74 | snapshot client sets measured zero flaps when a complete event search is empty | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 575 |
| 75 | snapshot client counts event transitions as flap_count | src/interfaces/wan_performance/collection/snapshot_client.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 581 |
| 76 | WAN documentation says ordinary hours do not enter event summaries | documentation/wan-performance.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | ef2f1e2d888ddb34e79e10f7f5edf8be9b257692 | present | 340 |
| 77 | WAN documentation says unknown stays unknown and known zero remains zero | documentation/wan-performance.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | ef2f1e2d888ddb34e79e10f7f5edf8be9b257692 | present | 341 |
| 78 | WAN documentation says natural key upserts replace the row | documentation/wan-performance.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | ef2f1e2d888ddb34e79e10f7f5edf8be9b257692 | present | 444 |
| 79 | changelog fragment names issue 4794 | changelog.d/pr-4208.md | 843be63bc837513b4442dae69da9f0db922e0ed1 | 3d571a370f9cd3b6a7e3367b96dcc652ddf4653e | present | 19 |
| 80 | local mistapi 0.64.1 defines searchOrgDeviceEvents | .venv/Lib/site-packages/mistapi/api/v1/orgs/devices.py | local mistapi 0.64.1 | 90fe126e9c3e34d7784644016e12833b7359737d | present | 259 |
| 81 | local mistapi 0.64.1 is installed | .venv/Lib/site-packages/mistapi-0.64.1.dist-info | local mistapi 0.64.1 | none | present | 0 |
| 82 | bootstrap script exists on the candidate head | scripts/bootstrap_worktree.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | ce48473e4574e1118fd9ce9619df6c816e346ae5 | present | 0 |
| 83 | integration modules hold no link-event field name | src/interfaces/wan_performance/integration | 843be63bc837513b4442dae69da9f0db922e0ed1 | none | absent | 0 |
| 84 | HourlyMeasurement dataclass declares identity hour and metrics | src/interfaces/wan_performance/domain/measurement.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | bec652f726330e1990b0ab0281c0c05abcb88bba | present | 64 |
| 85 | candidate head LinkEventSummary totals are optional | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 47 |
| 86 | candidate head PeriodSummary holds link_event_summary | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 73 |
| 87 | test_summary_without_matching_records_is_empty exists on candidate head | tests/unit/wan_performance/test_calendar_summaries.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 1037a9760ef4281f6252b53cae2c21c1f21f0e6e | present | 335 |
| 88 | candidate head selects records by identity before summaries build | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 121 |
| 89 | copilot-instructions states that a new worktree needs Python 3.15.2 and a venv | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 28 |
| 90 | copilot-instructions bootstrap command runs scripts/bootstrap_worktree.py | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 29 |
| 91 | copilot-instructions gate table rows run from Compile at line 57 to STE at line 74 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 57 |
| 92 | copilot-instructions full-suite test quality command | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 145 |
| 93 | copilot-instructions pytest-chunks command for the unit shard | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 87 |
| 94 | AGENTS.md requires Closes issue in the pull request body | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| 95 | AGENTS.md requires a push with force-with-lease | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 203 |
| 96 | AGENTS.md requires a squash merge to main | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 235 |
| 97 | repair commit message names issues 4793 4794 and 4795 | commit message of d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | present | 0 |
| 98 | repair commit file list includes integration presentation and test files beyond issue 4794 | commit file list of d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | present | 0 |
| 99 | no test asserts a None link-event summary for snapshot-only periods | tests/unit/wan_performance/test_calendar_summaries.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 1037a9760ef4281f6252b53cae2c21c1f21f0e6e | absent | 0 |
| 100 | selected-port refresh upserts the insight records it builds | src/interfaces/wan_performance/collection/live_service.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | 434d0e4e83ddb8b848c6caa00d553a4f86382f8e | present | 77 |
| 101 | insight parser requires the exact expected metric set including flap_count for a port | src/interfaces/wan_performance/collection/snapshot_records.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | a4d3d1f9c7407aa37702a4e9a2d7b65ce1e1df33 | present | 143 |
| 102 | candidate head LinkEventSummaries.build selects hours with CalendarPeriod.contains | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 332 |
| 103 | candidate head observed up percent stays unknown unless both minute totals are known | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 340 |
| 104 | candidate head flap total sums only complete hours | src/interfaces/wan_performance/domain/summary.py | 843be63bc837513b4442dae69da9f0db922e0ed1 | d9862865a7236ada781de566e35c5b5aa57dd130 | present | 339 |
| 105 | route parent specs/numbered/0/0/1/2/3 already holds five children 0 to 4 | specs/numbered/0/0/1/2/3 | main | a1c84837ea062a10365e2afd44ac19a2f2356dd7 | present | 0 |
| 106 | constitution Complexity-Driven SpecKit Escalation section requires a spec for multi-file changes | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 420 |

Counts: present 94, absent 9, partial 2, stale 1. Total 106.

## Unverified

- U-1 Tests and gates did not run. The brief forbids running them in this research pass. Every expected result comes from the gate table or from code reading.
- U-2 The five-step reproduction did not run. Code reading supports the result. The parent lines 333 and 338 (remote checks 48 and 49) and the six summaries (remote checks 56 and 57) support the reasoning.
- U-3 The issue comment of 2026-11-13 states that the repaired reproduction returns one complete hour, 60 known up minutes, zero flaps, and 24 expected hours. The statement is the author's claim, and this pass did not check it.
- U-4 Commit 15c69b11 and the macOS, Python 3.15.2 environment in the issue cannot be checked. The commit is absent (remote check 46).
- U-5 Mixed hours in production data cannot be checked. This pass had no data access. The premise rests on the snapshot record rule (remote check 72) and the documentation (remote check 76).
- U-6 The size of the rebase conflicts is unknown. The PR merge state is DIRTY and CONFLICTING. The size appears only after the rebase.
- U-7 The CI result after the rebase is unknown. The check rollup for head `843be63` showed no failure when this record read it.
- U-8 Visual rendering in a browser was not checked. The e2e test uses the Flask test client (remote check 65), so it does not prove layout.
- U-9 The mistapi package behavior for versions 0.64.0 and 0.64.1 was not checked against a package index. The repository files state the pins (remote checks 7, 23, and 25).
- U-10 The event search inside `GatewayInsights.collect_for_port` was not traced line by line. The record relies on the insight parser contract (remote checks 72 and 101) and the event metric builder (remote checks 73 to 75).
