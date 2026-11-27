# Research: WAN history replay safety

Each decision lists the alternatives, the chosen option, the reason, and the risk. Each remote claim has one row in the verification table. The row count matches `STATUS.json` and the summary. Line numbers refer to the remote files at the stated ref.

## Decisions

### D-1. Carrier of the repair

- **Decision**: Commit the fix to the candidate branch `jmorrison-juniper-4200-migrate-mistwanperformance`, which carries pull request #4208. Rebase that branch onto `origin/main` first. Create no stacked branch.
- **Alternatives considered**:
  - (a) New branch `fix/4793-wan-history-replay` from `main`. This fails, because main holds no WAN history writer (RC-01 to RC-04).
  - (b) New branch stacked on the candidate branch. `AGENTS.md` warns that a stacked branch causes a cascading conflict.
  - (c) New pull request that moves the WAN history stack to `main` first. This needs the whole unfinished #4200 feature, which the owner keeps unpublished.
  - (d) Commits on the candidate branch. Chosen.
- **Reason**: The only copy of the repair is on the candidate branch (RC-29, RC-30, RC-33, RC-61). Option (d) keeps one carrier and matches the candidate commit message, which names #4793.
- **Risk**: The carrier is large, and GitHub reports `CONFLICTING` (analysis A9). The fix waits for the owner decision in D-8.
- **Recommended option**: (d).
- **Human decision required**: no.

### D-2. Changed source data at an existing sample key

- **Decision**: Stop the whole write. Keep the prior rows unchanged. Raise ValueError with the source time.
- **Alternatives considered**:
  - (a) Stop the whole write and keep prior rows. Chosen.
  - (b) Skip the changed sample and write the rest of the batch.
  - (c) Store a second row under a new key.
  - (d) Replace the stored row.
- **Reason**: The issue requires append-only history and an explicit report. The candidate tests already pin option (a) (RC-49, RC-51). Option (b) hides a changed value. Option (c) breaks the sample key rule of the data model. Option (d) rewrites history.
- **Risk**: One changed value can block a batch until the API sample leaves the window. FR-013 names the time in the error and the log.
- **Recommended option**: (a).
- **Human decision required**: no.

### D-3. Two different values for one metric and timestamp in one API response

- **Decision**: Reject the response with ValueError before any write. Identical duplicates produce one sample.
- **Alternatives considered**:
  - (a) Keep the last value. This is the current behavior (RC-42).
  - (b) Keep the first value.
  - (c) Reject the response. Chosen.
  - (d) Log a warning and keep one value.
- **Reason**: The issue requires an explicit report. Option (a) hides a change. Option (b) is arbitrary. Option (d) reports the change but still stores one value. Option (c) follows the same rule as D-2.
- **Risk**: A live response with conflicting duplicates fails the refresh. Test N5 keeps identical duplicates valid.
- **Recommended option**: (c).
- **Human decision required**: no.

### D-4. Verification of the Arango commit

- **Decision**: Require `commit_transaction()` to return True. Raise ConnectionError when it does not.
- **Alternatives considered**:
  - (a) Leave the commit unchecked. This is the current behavior (RC-35).
  - (b) Check the result and raise. Chosen.
  - (c) Check the result and log only.
  - (d) Retry the commit.
- **Reason**: The constitution forbids a success report before a verified durable write (RC-11). Option (c) still reports success. Option (d) adds retry logic outside this issue. The pinned client returns bool (RC-28, RC-63).
- **Risk**: A commit that returns False now fails a write that looked successful before. Test N1 proves the new behavior.
- **Recommended option**: (b).
- **Human decision required**: no.

### D-5. Rollback path in `ArangoHistory.upsert`

- **Decision**: Call `ArangoArchive._abort` in the error branch. Add no method to `ArangoHistory`.
- **Alternatives considered**:
  - (a) Add a helper method to `ArangoHistory`. This makes six methods, and the limit is five. `ArangoHistory` already has `__init__`, `connect`, `upsert`, `read`, and `read_samples` (arango_history.py lines 115 to 213).
  - (b) Add a nested try block inside `upsert`. This adds more blocks to a method that already exceeds the limits.
  - (c) Reuse `ArangoArchive._abort`. Chosen. The method already guards rollback errors (RC-65).
  - (d) Leave the rollback call unguarded. This is the current behavior (RC-36).
- **Reason**: Option (c) adds no member and no block. It reuses guarded code in the same module.
- **Risk**: The call crosses a private static method of a sibling class. Test N2 covers the path, and a code comment states the reason.
- **Recommended option**: (c).
- **Human decision required**: no.

### D-6. Operator-visible text for a conflict

- **Decision**: Keep the generic 503 text of the portal in this change. Defer the conflict-specific text to a follow-up issue.
- **Alternatives considered**:
  - (a) Add a typed exception class in `record_codec.py`. This becomes a sixth class in a module that holds five (RC-37 and the five-child rule).
  - (b) Match the error text in `live_routes.py`. This couples the route to message wording.
  - (c) Defer the text to a follow-up issue. Chosen.
- **Reason**: Options (a) and (b) break a rule or create brittle code. Option (c) keeps this change inside the structure rules. The log still names the sampled time (FR-013).
- **Risk**: The operator sees a generic message for a conflict. Item U-1 in `analysis.md` tracks the follow-up.
- **Recommended option**: (c).
- **Human decision required**: no.

### D-7. Test strategy

- **Decision**: Use real SQLite under `tmp_path`, a patched `GatewayInsights.collect_for_port`, and mocked Arango objects. Run no live service.
- **Alternatives considered**:
  - (a) Live ArangoDB run. This needs a running service and a credential.
  - (b) Live Mist run. This needs a credential and a network call.
  - (c) Real SQLite, a patched collector, and mocked Arango. Chosen.
  - (d) Mocked SQLite. This skips the SQLite key and transaction behavior that the issue describes.
- **Reason**: The owner states that no live acceptance is claimed (issue comment IC_kwDOQltU8c8AAAABmSNu_Q). Option (c) is deterministic and needs no credential.
- **Risk**: Live Arango behavior stays unverified (item U-2 in `analysis.md`).
- **Recommended option**: (c).
- **Human decision required**: no.

### D-8. Publication of the candidate branch to `main`

- **Decision**: Hold the merge of PR #4208 until the owner approves the feature scope. Then merge the candidate with the fix.
- **Alternatives considered**:
  - (a) Merge PR #4208 now.
  - (b) Hold the merge until the owner approves the feature scope. Recommended.
  - (c) Close PR #4208 and rebuild a narrower stack from `main`.
- **Reason**: The issue body states that the candidate remains unpublished. Publication of an unfinished feature is a product priority decision for the owner. Option (c) costs much more than the repair. Option (a) overrides the stated hold.
- **Risk**: The repair waits for the owner. Task T-MERGE stays blocked until the decision.
- **Recommended option**: (b).
- **Human decision marker**: `HUMAN-DECISION-REQUIRED`. The owner decides this item.

### D-9. Location of this record

- **Decision**: Commit this record folder on the candidate branch with the fix. The pull request body states `Closes #4793`.
- **Alternatives considered**:
  - (a) Separate documentation branch from `main` that names `Refs #4793`. This does not match the pull request contract, which needs `Closes #4793`.
  - (b) Commit the record on the candidate branch with the fix. Chosen.
  - (c) Keep the record only in the session folder. This leaves no repository record.
- **Reason**: Option (b) keeps one pull request that closes #4793 only after the merge reaches `main`. Option (a) would close the issue too early if the body used the closing keyword.
- **Risk**: The record adds files to the large candidate pull request. The record keeps five children at each level (analysis consistency checks).
- **Recommended option**: (b).
- **Human decision required**: no.

## Existing Record Search

- Local search of `specs\` for folders that start with `4793-` returned 0 matches.
- Remote tree of `main` (`git/trees/main?recursive=1`) returned 0 matches for `4793` (RC-07).
- The file list of pull request #4208 contains no 4793 record (RC-60).
- Result: `existing_record.found` is false. No legacy record exists to verify or reuse.

## Remote Verification

The table lists each check. Blob SHA values for folder rows are tree SHA values. For commit rows, the blob SHA column holds the commit SHA. The `Ref` column names the ref that the check used. `main` means the remote default branch. `head` means the candidate head `843be63bc837513b4442dae69da9f0db922e0ed1`.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
|----|-------|------|-----|----------|--------|------|
| RC-01 | Absent on main: SQLite history module | `src/interfaces/wan_performance/integration/sqlite_history.py` | main | none | absent | 0 |
| RC-02 | Absent on main: Arango history module | `src/interfaces/wan_performance/integration/arango_history.py` | main | none | absent | 0 |
| RC-03 | Absent on main: record codec with the replay policy | `src/interfaces/wan_performance/integration/record_codec.py` | main | none | absent | 0 |
| RC-04 | Absent on main: live service with refresh_port | `src/interfaces/wan_performance/collection/live_service.py` | main | none | absent | 0 |
| RC-05 | Absent on main: rate sample builder | `src/interfaces/wan_performance/collection/snapshot_records.py` | main | bb73aed2de9a3e8db18c6f83ea057a7c48ef1c74 | absent | 0 |
| RC-06 | Present on main: refresh store is the only integration module | `src/interfaces/wan_performance/integration/refresh_store.py` | main | 76ff0cdcc6abe7e8aed874a9e9e6bc89ad2cf8c8 | present | 0 |
| RC-07 | Absent on main: any specs record for issue 4793 | `specs/**/4793-*` | main | none | absent | 0 |
| RC-08 | Absent on main: repair commit reachable from main (compare status diverged) | commit `d7a706d71cf13661cf33e5b4a96ddafd79b6b67b` | main | d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | absent | 0 |
| RC-09 | Present on main: base-5 route rule | `.specify/scripts/powershell/spec-route.ps1` | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-10 | Present on main: Five-Item Rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-11 | Present on main: verified durable write rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 319 |
| RC-12 | Present on main: rebase before push rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 511 |
| RC-13 | Present on main: AGENTS writing style section | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RC-14 | Present on main: AGENTS closing keyword rule | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| RC-15 | Present on main: AGENTS squash merge rule | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 235 |
| RC-16 | Present on main: local gates table | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RC-17 | Present on main: Symbols gate row | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 73 |
| RC-18 | Present on main: STE gate row | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| RC-19 | Present on main: spec template | `.specify/templates/spec-template.md` | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| RC-20 | Present on main: plan template | `.specify/templates/plan-template.md` | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| RC-21 | Present on main: tasks template | `.specify/templates/tasks-template.md` | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| RC-22 | Present on main: checklist template | `.specify/templates/checklist-template.md` | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| RC-23 | Present on main: reference record spec | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-24 | Present on main: reference record plan | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/plan.md` | main | 686c89f85ee7c094526bafaf782d4398f6c523ff | present | 0 |
| RC-25 | Present on main: reference record tasks | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/tasks.md` | main | 72bd85483706269fdf809322b2dca38a0e1d5698 | present | 0 |
| RC-26 | Present on main: reference record research | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/research.md` | main | 2e4aaa714e56fff7f96a2af9e686e9f5c06224a7 | present | 0 |
| RC-27 | Present on main: Mist OpenAPI file | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 0 |
| RC-28 | Present on main: python-arango pin 8.3.7 | `requirements.txt` | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 197 |
| RC-29 | Present on candidate: branch head commit | commit `843be63bc837513b4442dae69da9f0db922e0ed1` | head | 843be63bc837513b4442dae69da9f0db922e0ed1 | present | 0 |
| RC-30 | Present on candidate: SQLite upsert | `src/interfaces/wan_performance/integration/sqlite_history.py` | head | 0f6df95406b922ecf51acd23f22b00e593d6dc09 | present | 103 |
| RC-31 | Present on candidate: SQLite sample key is identity and sampled_at | `src/interfaces/wan_performance/integration/sqlite_history.py` | head | 0f6df95406b922ecf51acd23f22b00e593d6dc09 | present | 133 |
| RC-32 | Present on candidate: SQLite checks existing samples before insert | `src/interfaces/wan_performance/integration/sqlite_history.py` | head | 0f6df95406b922ecf51acd23f22b00e593d6dc09 | present | 144 |
| RC-33 | Present on candidate: Arango upsert | `src/interfaces/wan_performance/integration/arango_history.py` | head | 0aa4dc6e4d622de6e99b6bcbe7277af69095b56f | present | 133 |
| RC-34 | Present on candidate: Arango checks existing samples before insert | `src/interfaces/wan_performance/integration/arango_history.py` | head | 0aa4dc6e4d622de6e99b6bcbe7277af69095b56f | present | 173 |
| RC-35 | Absent on candidate: Arango verifies the commit result | `src/interfaces/wan_performance/integration/arango_history.py` | head | 0aa4dc6e4d622de6e99b6bcbe7277af69095b56f | absent | 178 |
| RC-36 | Absent on candidate: Arango keeps the original error when rollback fails | `src/interfaces/wan_performance/integration/arango_history.py` | head | 0aa4dc6e4d622de6e99b6bcbe7277af69095b56f | absent | 180 |
| RC-37 | Present on candidate: sample replay policy class | `src/interfaces/wan_performance/integration/record_codec.py` | head | 393db6201e5c90df78873df58b8d0e3c8baeffa5 | present | 400 |
| RC-38 | Present on candidate: source comparison ignores collection time | `src/interfaces/wan_performance/integration/record_codec.py` | head | 393db6201e5c90df78873df58b8d0e3c8baeffa5 | present | 430 |
| RC-39 | Absent on candidate: changed-data error names the source time | `src/interfaces/wan_performance/integration/record_codec.py` | head | 393db6201e5c90df78873df58b8d0e3c8baeffa5 | absent | 424 |
| RC-40 | Present on candidate: selected-port refresh method | `src/interfaces/wan_performance/collection/live_service.py` | head | 434d0e4e83ddb8b848c6caa00d553a4f86382f8e | present | 56 |
| RC-41 | Present on candidate: rate sample builder | `src/interfaces/wan_performance/collection/snapshot_records.py` | head | a4d3d1f9c7407aa37702a4e9a2d7b65ce1e1df33 | present | 230 |
| RC-42 | Absent on candidate: conflicting values for one metric and timestamp are rejected | `src/interfaces/wan_performance/collection/snapshot_records.py` | head | a4d3d1f9c7407aa37702a4e9a2d7b65ce1e1df33 | absent | 241 |
| RC-43 | Present on candidate: store error tuple includes ValueError | `src/interfaces/wan_performance/presentation/live_routes.py` | head | 98827fc73a3d241859f539a03451d5cccf4d2e48 | present | 45 |
| RC-44 | Absent on candidate: conflict-specific operator text | `src/interfaces/wan_performance/presentation/live_routes.py` | head | 98827fc73a3d241859f539a03451d5cccf4d2e48 | absent | 336 |
| RC-45 | Present on candidate: sample natural key is identity and source time | `src/interfaces/wan_performance/domain/measurement.py` | head | bec652f726330e1990b0ab0281c0c05abcb88bba | present | 193 |
| RC-46 | Present on candidate: GatewayInsights.collect_for_port | `src/interfaces/wan_performance/collection/snapshot_client.py` | head | 88899eecece6666c6c3a7b377fe1e3d703ee1bd4 | present | 121 |
| RC-47 | Present on candidate: HistorySelection.open chooses SQLite or Arango | `src/interfaces/wan_performance/integration/history_repository.py` | head | e114ed1a82c8762debbcc65a7d283f07ea4924bf | present | 212 |
| RC-48 | Present on candidate: SQLite replay test | `tests/unit/wan_performance/test_history_repository.py` | head | 87cdafb890339ee361f0447ae932679ee9d6d93c | present | 713 |
| RC-49 | Present on candidate: SQLite changed-data test | `tests/unit/wan_performance/test_history_repository.py` | head | 87cdafb890339ee361f0447ae932679ee9d6d93c | present | 727 |
| RC-50 | Present on candidate: SQLite rollback test | `tests/unit/wan_performance/test_history_repository.py` | head | 87cdafb890339ee361f0447ae932679ee9d6d93c | present | 1033 |
| RC-51 | Present on candidate: mocked Arango replay test | `tests/unit/wan_performance/test_history_repository.py` | head | 87cdafb890339ee361f0447ae932679ee9d6d93c | present | 881 |
| RC-52 | Absent on candidate: unconfirmed Arango commit test | `tests/unit/wan_performance/test_history_repository.py` | head | 87cdafb890339ee361f0447ae932679ee9d6d93c | absent | 0 |
| RC-53 | Absent on candidate: Arango rollback failure test | `tests/unit/wan_performance/test_history_repository.py` | head | 87cdafb890339ee361f0447ae932679ee9d6d93c | absent | 0 |
| RC-54 | Partial on candidate: port refresh test without API samples | `tests/unit/wan_performance/test_live_service.py` | head | 7df41998d0cb17c58925cd06cfa0007e826e229b | partial | 133 |
| RC-55 | Absent on candidate: repeated API sample port refresh test | `tests/unit/wan_performance/test_live_service.py` | head | 7df41998d0cb17c58925cd06cfa0007e826e229b | absent | 0 |
| RC-56 | Absent on candidate: conflicting duplicate snapshot test | `tests/unit/wan_performance/test_snapshot_records.py` | head | 9af0112d5fa6bdfeabd334b2860cdcf9cc7a91ab | absent | 0 |
| RC-57 | Present on candidate: raw sample rules documented | `documentation/wan-performance.md` | head | ef2f1e2d888ddb34e79e10f7f5edf8be9b257692 | present | 437 |
| RC-58 | Present on candidate: selected-port rate requests align six timestamps | `documentation/wan-performance.md` | head | ef2f1e2d888ddb34e79e10f7f5edf8be9b257692 | present | 303 |
| RC-59 | Present on candidate: changelog fragment names issue 4793 | `changelog.d/pr-4208.md` | head | 3d571a370f9cd3b6a7e3367b96dcc652ddf4653e | present | 19 |
| RC-60 | Absent on candidate: 4793 record in the pull request file list | pull request #4208 file list | head | none | absent | 0 |
| RC-61 | Present on GitHub: repair commit d7a706d | commit `d7a706d71cf13661cf33e5b4a96ddafd79b6b67b` | d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | d7a706d71cf13661cf33e5b4a96ddafd79b6b67b | present | 0 |
| RC-62 | Absent on GitHub: reproduction commit 15c69b1 (HTTP 422) | commit `15c69b1176f7ae7c24e010aba3d29915ef228610` | 15c69b1176f7ae7c24e010aba3d29915ef228610 | 15c69b1176f7ae7c24e010aba3d29915ef228610 | absent | 0 |
| RC-63 | Present upstream: python-arango 8.3.7 commit returns bool | `https://api.github.com/repos/arangodb/python-arango/contents/arango/database.py?ref=8.3.7` | 8.3.7 | a0a51ff9a50833f4acf22485c7d244180062457a | present | 3510 |
| RC-64 | Absent locally: python-arango not installed in the venv | `.venv\Lib\site-packages\arango` | local | none | absent | 0 |
| RC-65 | Present on candidate: ArangoArchive._abort guards rollback errors | `src/interfaces/wan_performance/integration/arango_history.py` | head | 0aa4dc6e4d622de6e99b6bcbe7277af69095b56f | present | 108 |
| RC-66 | Present on candidate: mocked upsert test asserts a commit call | `tests/unit/wan_performance/test_history_repository.py` | head | 87cdafb890339ee361f0447ae932679ee9d6d93c | present | 836 |
| RC-67 | Present on candidate: hourly replacement round-trip test | `tests/unit/wan_performance/test_history_repository.py` | head | 87cdafb890339ee361f0447ae932679ee9d6d93c | present | 679 |
| RC-68 | Present on main: route folder holds three children and no child 3 | `specs/numbered/0/0/1/2/3/1` | main | 42d51be54c337e7b0c6c5abba0ed6513cbd390d6 | present | 0 |
| RC-69 | Present on candidate: document states a confirmed Arango commit for archive appends | `documentation/wan-performance.md` | head | ef2f1e2d888ddb34e79e10f7f5edf8be9b257692 | present | 46 |

## Sources

- Issue #4793: `gh issue view 4793 -R jmorrison-juniper/MistHelper --json number,title,body,state,labels,comments,createdAt,updatedAt,author` (read only). The issue is OPEN. Labels: `bug`, `web-portal`, `in-progress`.
- Related issues: #4200 is OPEN and titled "Spec: Integrate MistWANPerformance into MistHelper portal". #4794 is OPEN. #4795 is OPEN. #4208 is a pull request, OPEN, not merged.
- Pull request #4208: `gh pr view 4208 -R jmorrison-juniper/MistHelper`. Head `843be63bc837513b4442dae69da9f0db922e0ed1`. Branch `jmorrison-juniper-4200-migrate-mistwanperformance`. Merge state `CONFLICTING`. Review decision empty. The body does not contain `Closes #4793`. The status rollup shows 42 SUCCESS and 10 SKIPPED. The file list contains no 4793 record.
- Compare API, with base `main` and head `d7a706d71cf13661cf33e5b4a96ddafd79b6b67b`: status `diverged`, 3 commits ahead, and 52 commits behind.
- Remote trees: `repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1` (11,404 entries, not truncated) and `repos/jmorrison-juniper/MistHelper/git/trees/843be63bc837513b4442dae69da9f0db922e0ed1?recursive=1` (not truncated).
- Remote file bodies: the GitHub contents API, read for each file path and ref, decoded from base64. Line numbers come from the decoded text.
- Local files read for process rules: `AGENTS.md`, `.github\copilot-instructions.md`, `.specify\memory\constitution.md`, and four templates in `.specify\templates\`. The two instruction files are stale copies (see item U-g below).
- Local reference record: `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv\` (shape only).
- Local grep of `documentation\mist-api-openapi31yaml.yaml` for `points`, `timestamp_source`, and rate fields. The grep found no insight `points` schema.
- Local grep of `documentation\quality-gates.md`, `architecture.md`, `container-deployment.md`, `operator-guide.md`, and `development-setup.md` for WAN, SQLite, and ArangoDB terms. These documents hold no WAN replay rule. They confirm that SQLite and ArangoDB store the data.
- Upstream: `https://api.github.com/repos/arangodb/python-arango/contents/arango/database.py?ref=8.3.7`. The file blob is `a0a51ff9a50833f4acf22485c7d244180062457a`. The method `commit_transaction(self) -> bool` appears at line 3510. The method `abort_transaction(self) -> bool` appears at line 3519.
- Local search for `specs\` folders that start with `4793-` returned 0 matches.
- No web fetch was used. The upstream check used the GitHub API.

## Skills

No skill was loaded. The defect lies in repository code and in the SQLite and ArangoDB write paths. The brief lists Podman and Juniper device skills for other cases. No listed skill covers this code.

## Unverified

- U-a: The issue states that the API returns a previously retained sample timestamp. This work makes no Mist request. The local OpenAPI copy has no located insight `points` schema. The claim stays unverified.
- U-b: The issue reproduction at commit `15c69b1176f7ae7c24e010aba3d29915ef228610` cannot run. GitHub returns HTTP 422 (RC-62). The local commit is not available to this review.
- U-c: The owner states a local selected-port run with six API samples and two poll observations. The repository holds no committed test for that run. This review did not repeat it (RC-54, RC-55).
- U-d: Live ArangoDB persistence. The owner states no live acceptance claim. This review uses no live service.
- U-e: The rebase outcome of pull request #4208. The merge state is `CONFLICTING` (see Sources). This review performs no fetch and no rebase.
- U-f: Gate results and the STE score of the new text. This review runs no linter, test, or build.
- U-g: Parity of the local checkout with remote `main`. The local instruction files differ from remote `main` in length. This record cites remote lines only.
- U-h: The reason for the 10 SKIPPED status checks on pull request #4208. This review did not inspect the skipped jobs.
