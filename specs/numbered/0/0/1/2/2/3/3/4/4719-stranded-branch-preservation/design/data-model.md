# Data Model: Stranded Branch Preservation

## Terms

- **Head**: The commit that a branch ref points to. Each head has a full 40-character SHA.
- **Ahead**: The number of commits reachable from a head and not reachable from `main`. Git reports it with `rev-list --count`.
- **Paths**: The number of changed path entries between `main` and a head. Git reports them with `diff --name-only`.
- **Held**: A branch is held when a pull request has the branch name as its head and the head SHA equals the branch head.
- **Stranded**: A branch is stranded when it has commits ahead of `main` and no pull request holds its head.

## Entities

### StrandedBranch

- Natural key: the branch name under `refs/heads/`, for example `fix/3158-wip-controls`.
- Attributes: head SHA, ahead count, paths count, owner head check, overlap pull requests, privacy flag, batch.
- Rule: A branch is stranded until a pull request holds its current head.

### HeadHolder

- Natural key: the pull request number.
- Attributes: head ref name, head SHA, state (OPEN, CLOSED, or MERGED), draft flag.
- Rule: A closed or merged pull request keeps only the head SHA that it had when it closed.

### TrackingIssue

- Natural key: the issue number.
- Attributes: title, state, creation time in UTC, comment count.
- Rule: After task T022, exactly one open issue carries the tracking title.

### OwnerHold

- Natural key: the comment node ID.
- Attributes: scope (publication, privacy, or deletion), statement, time in UTC.
- Rule: An action in the held scope waits for a released hold.

### ReportRow

- Natural key: the branch name with the head SHA, within one report.
- Attributes: branch name, commits ahead, age in days.
- Rule: The weekly report lists one row for each stranded branch.

## Relationships

- A StrandedBranch has zero or one HeadHolder whose head SHA equals the branch head.
- A TrackingIssue lists zero or more ReportRow values.
- An OwnerHold applies to zero or more StrandedBranch values.

## State transitions

| From | Event | To | Gate |
| - | - | - | - |
| Stranded | A draft preservation pull request opens for the head | Held (open) | Owner releases the publication hold (task T010) |
| Held (open) | The pull request closes without a merge | Held (closed) | The head SHA stays unchanged |
| Held (closed) | The branch receives a new commit | Stranded | Caution: a closed pull request keeps only its old head |
| Held (open) | The pull request merges | Held (merged) | The squash commit reaches `main` |
| Stranded | The branch is deleted | Removed | Warning: deletion destroys the only copy of unheld work. Out of scope (decision D-4). |

## Inventory

The table lists the 51 branches of issue #4719 in the order of the issue body. The columns are:

- **Head**: The first eight characters of the head SHA. The full SHA is in `design/research.md`, rows 46 to 96.
- **Ahead**: The commit count from `rev-list --count`.
- **Paths**: The path entry count from `diff --name-only`.
- **Overlap**: The open pull request and the number of shared path names, with the path name.
- **Owner check**: `same` means the head equals the owner comment value. `not recorded` means no comment value exists. `private` means the owner placed a privacy hold.
- **Batch**: `1` for the clean batch, `2` for the deferred overlap batch, and `3` for the privacy-held branch.
- **Commit subjects**: The subjects of the commits ahead, newest first. Multiple subjects are joined with ` / `.

| # | Branch | Head | Ahead | Paths | Overlap | Owner check | Batch | Commit subjects |
| - | - | - | - | - | - | - | - | - |
| 1 | fix/3158-wip-controls | 0f6b375e | 1 | 7 | none | same | 1 | chore(web-portal): keep the uncommitted draft of #3158 [skip ci] |
| 2 | fix/3168-structured-signals | 69d19411 | 1 | 4 | none | same | 1 | chore(web-portal): keep the uncommitted draft of #3168 [skip ci] |
| 3 | fix/3183-status-fallback | 0c46332a | 1 | 10 | none | same | 1 | chore(web-portal): keep the uncommitted draft of #3183 [skip ci] |
| 4 | fix/3222-confirm-details | 18138f9b | 1 | 7 | none | same | 1 | fix(upgrade-portal): show complete confirmation plan |
| 5 | jmorrison-jnpr-snmp-fallback-delivery | 73a1edaa | 1 | 3 | none | same | 1 | fix(snmp): align the container base OID fallback |
| 6 | fix/3506-site-lock-logs | 8c8fc28d | 1 | 3 | none | same | 1 | fix(upgrade-portal): record site lock actions and refusals |
| 7 | recovery/2863-handoff-20261004 | 188956f9 | 1 | 8 | none | same | 1 | fix(api): refuse invalid tenant request identifiers |
| 8 | recovery/2711-handoff-20261004 | 9e943bfe | 1 | 1 | none | same | 1 | test(export): require the error record for template failures |
| 9 | recovery/3575-handoff-20261004 | 5746418f | 2 | 39 | none | same | 1 | test(websockets): prove failed capture response bodies / feat(websockets): support long packet captures |
| 10 | recovery/3700-handoff-20261004 | f253dd3b | 1 | 13 | none | same | 1 | fix(export): reject native Cradlepoint HTTP refusals |
| 11 | recovery/3701-handoff-20261004 | d2d2421d | 1 | 10 | none | same | 1 | fix(bootstrap): preserve macOS interpreter library paths |
| 12 | recovery/2752-handoff-20261004 | 024d42ff | 1 | 9 | none | same | 1 | fix(api): preserve HTTP status in retry diagnostics |
| 13 | recovery/2861-handoff-20261004 | 6cea98a9 | 1 | 11 | none | not recorded | 1 | fix(mist-session): reject unusable required tokens |
| 14 | recovery/2977-handoff-20261004 | d6e8eb86 | 1 | 24 | none | private | 3 | withheld (privacy hold) |
| 15 | recovery/3213-handoff-20261004 | 8090bc7d | 1 | 13 | #4208, 1 shared: deploy/.env.example | same | 2 | fix(upgrade-portal): document the stable capture session signing key |
| 16 | recovery/3326-handoff-20261004 | fa25a39c | 1 | 16 | none | same | 1 | fix(upgrade-portal): hide the failure percentage for Big bang |
| 17 | recovery/3329-handoff-20261004 | 7332749c | 1 | 8 | none | same | 1 | fix(upgrade-portal): count targets of known refused children |
| 18 | recovery/3295-handoff-20261004 | b1fe853f | 1 | 16 | none | same | 1 | fix(upgrade-portal): repair the sign-in credential layout |
| 19 | recovery/3728-handoff-20261004 | 533ced96 | 1 | 2 | none | same | 1 | test(web-portal): skip Maps title collection when Playwright is absent |
| 20 | recovery/3436-handoff-20261004 | 0a032e83 | 2 | 27 | none | same | 1 | fix(upgrade-portal): keep paged read results passive / fix(upgrade-portal): report lost capture and gate pages |
| 21 | recovery/3699-handoff-20261004 | c0261d9f | 1 | 18 | #4813, 1 shared: tests/unit/export/test_endpoint_family_exporter.py | same | 2 | fix(export): retain documented SLE trend objects |
| 22 | recovery/3375-handoff-20261004 | 499b764f | 1 | 12 | none | same | 1 | fix(tests): align capture seeds with lifecycle contracts |
| 23 | recovery/3158-handoff-20261004 | ecb0bc87 | 1 | 18 | none | same | 1 | fix(web-portal): add WIP target controls and result guidance |
| 24 | recovery/3743-handoff-20261004 | 4ecd16c7 | 1 | 14 | none | same | 1 | fix(export): reject failed WiFi response pages |
| 25 | recovery/3491-handoff-20261004 | 97139eb2 | 1 | 14 | none | same | 1 | fix(upgrade-portal): keep history records compact |
| 26 | recovery/2747-handoff-20261004 | 2d5695fb | 1 | 1 | none | same | 1 | test(ssh): verify native CLI shell refusals |
| 27 | recovery/3745-handoff-20261004 | 50e3d841 | 1 | 13 | none | same | 1 | fix(export): refuse failed organization webhook responses |
| 28 | recovery/3749-handoff-20261004 | 9f930182 | 1 | 1 | none | same | 1 | test(scripts): use native title guard path expectations |
| 29 | recovery/3161-handoff-20261004 | 33141f05 | 2 | 9 | none | same | 1 | test(web-portal): cover stale clipping frame race / fix(web-portal): disclose clipped result values |
| 30 | recovery/3388-handoff-20261004 | ea0a7467 | 1 | 14 | none | same | 1 | fix(upgrade-portal): refuse unsafe option number tokens |
| 31 | recovery/3380-handoff-20261004 | a3af99af | 1 | 7 | none | same | 1 | fix(upgrade-portal): verify capture click journey controls |
| 32 | recovery/3761-handoff-20261004 | ebc40dac | 1 | 5 | none | same | 1 | test(websocket): structure shell log assertions |
| 33 | recovery/3760-handoff-20261004 | 12f10ece | 2 | 2 | none | same | 1 | test(websocket_streams): correct the loopback client response handling / test(websocket_streams): narrow the nullable fake cloud on_connect handler |
| 34 | recovery/3769-handoff-20261004 | 54188ffc | 2 | 9 | none | same | 1 | fix(websocket): freeze cleanup terminal decisions / fix(websocket): wait for utility capture cleanup before completion |
| 35 | recovery/2708-handoff-20261004 | f195788a | 1 | 1 | none | same | 1 | test(mist): assert the complete list error text |
| 36 | recovery/3818-handoff-20261004 | 0bb31494 | 2 | 1 | none | same | 1 | test(export): assert Cradlepoint status behavior / test(export): keep Cradlepoint module in test analysis |
| 37 | recovery/3738-handoff-20261004 | c70007d4 | 2 | 9 | none | same | 1 | test(export): preserve CSV suffix qualification WIP / fix(export): preserve existing CSV filename suffixes |
| 38 | docs/3818-campaign-stop-20261004 | 8c3e6cac | 1 | 1 | none | same | 1 | docs(handoff): preserve the paused repair campaign |
| 39 | fix/3292-isolate-retry-e2e-sites | f706902a | 2 | 6 | none | same | 1 | fix(upgrade-portal): order retry imports / test(upgrade-portal): isolate retry fixtures |
| 40 | jmorrison-juniper-startup-dependency-reassessment | e849f3fe | 3 | 18 | none | same | 1 | fix(upgrade-portal): build request dependencies lazily / chore(upgrade-portal): preserve issue 3834 scope audit / docs(spec): generate issue 3834 implementation tasks |
| 41 | jmorrison-juniper-fix-2863-identifier-defaults-batch-1 | 6eec0e4b | 1 | 13 | none | same | 1 | fix(upgrade-portal): refuse missing scope identifiers |
| 42 | jmorrison-juniper-assessment-4026 | 83d197e3 | 3 | 12 | none | same | 1 | docs(spec): record issue 4026 validation / fix(web-portal): synchronize executor initialization / docs(spec): record operations portal concurrency |
| 43 | jmorrison-juniper-issue-3416-lint-pattern | 3d51242e | 2 | 1 | none | same | 1 | test(docs): hold complete diagram reference names / test(diagram): guard complete class references |
| 44 | jmorrison-juniper-false-success-family-4028 | 4be5f321 | 2 | 12 | none | same | 1 | test(export): strengthen client abort assertion / fix(export): reject menu 209 HTTP failures |
| 45 | jmorrison-jnpr-test-4035-menu-92-selection-result | 9851ed28 | 1 | 5 | none | same | 1 | test(web-portal): record menu 92 completion defect |
| 46 | jmorrison-juniper-issue-2746 | 4ebe402c | 2 | 42 | #4208, 1 shared: tests/unit/refactors/test_wlanradius_timer_manager_paths.py | same | 2 | test: preserve HTTP proof symbols / test: add HTTP 4xx failure proofs |
| 47 | jmorrison-juniper-coordinate-issue-work | 29c54897 | 1 | 3 | none | same | 1 | fix(org): handle http refusal in org name lookup |
| 48 | jmorrison-juniper-issue-4269-runtime-nested-feature-identity-in-speck-4a6090 | d8a7b9c7 | 1 | 8 | none | same | 1 | fix(specs): remove nested duplicate feature record |
| 49 | jmorrison-juniper-issue-2747-wan-probe-test-quality | db030903 | 1 | 1 | none | same | 1 | test(gateway): cover HTTP 503 template refusal |
| 50 | jmorrison-juniper-fix-4494-csrf-warning-prefix | 862f1a8c | 1 | 1 | none | same | 1 | test(upgrade-portal): wait for the accessible CSRF warning |
| 51 | jmorrison-juniper-local-build-revision | c80f2351 | 1 | 13 | #4208, 1 shared: deploy/.env.example | same | 2 | fix(container): label local builds with their source revision |

## Totals

| Measure | Value |
| - | - |
| Branches | 51 |
| Ahead, total | 66 |
| Paths, total | 515 |
| Batch 1 | 46 branches |
| Batch 2 | 4 branches |
| Batch 3 | 1 branch |
| Branches with an owner head check of `same` | 49 |

## Local-only branches

These two branches are outside the 51 rows, because the report reads remote branches only.

| Branch | Reported head | Remote copy | Local copy in this clone | Owner action |
| - | - | - | - | - |
| jmorrison-juniper-issue-triage-overlap-analysis | a4c7aa10 | absent | absent | Verify in the owner clone (task T014) |
| jmorrison-juniper-ssh-telemetry-test-repair | fd7f20a2 | absent | absent | Verify in the owner clone (task T014) |
