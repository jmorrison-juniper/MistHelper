# Research: Menu 97 SQLite Write Status

## Method

- The truth order is remote `main`, read through `gh`. Local search only found candidates. Each code claim cites a remote blob SHA and a line from the decoded remote text.
- One remote tree call fetched 11,404 entries. The tree reports `truncated` as False.
- Line numbers come from the decoded contents of each file at `ref=main`. Each decode used `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main`.
- The mistapi package is local only. Its blob SHA is the Git object hash of the local file, computed with `git hash-object --no-filters` without writing an object.
- No test, build, linter, formatter, install, container, or repository script ran. No repository file changed.
- The remote tip at the snapshot is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, and local HEAD matches it.

## Issue Facts

- Issue 4722 is open. Its title is "Runtime: menu 97 reports SQLite success after a failed write". It was created on 2026-11-09T22:08:46Z and updated on 2026-11-09T22:38:16Z. The author is `jmorrison-juniper`.
- Labels: `bug` and `MistHelper.py`. The issue carries no status label.
- Requirement: "When a write fails, the exporter must report the failure and preserve the information needed for a safe recovery. It must not report a successful export or remove a recoverable checkpoint as if the write succeeded."
- Requirement: the issue shares `src/operations/exporting/export/device_events_52w_exporter.py` with issue #4721. Coordinate the repair under one file owner. Do not publish competing pull requests for that file.
- Reproduction on main commit `3964d21d03f9f5717cb8eafb7272ecff21f5362a`: create a checkpoint with the token `existing-resume-token`. Mock `searchOrgDeviceEvents` to return one event. Mock the writer to return False. Call `export()` with `output_format="sqlite"`. The checkpoint is removed and completion is logged.
- Error text in the log: `All org device events (52w) exported to SQLite table OrgDeviceEvents_52w (DB: %s)`. The reproduction also printed `SQLite writer result: False` and `Existing resume checkpoint: removed`.
- Comment IC_kwDOQltU8c8AAAABkoW1-A (2026-11-09T22:29:59Z): the later SQLite batch path also fails. A control that raises OSError stops the export and keeps the checkpoint.
- Comment IC_kwDOQltU8c8AAAABkoggfg (2026-11-09T22:38:15Z): a partially rejected later batch still returns True. A False check does not detect a partial batch. A recovery design needs a reliable full-batch result.
- Related issues: #4721 (open, label `in-progress`), #4723 (open, timestamp-only key defect), and #3350 (closed, partial-batch True contract).
- The issue reproductions used mocks and a temporary SQLite file. No live Mist request was made.

## Findings From Remote Main

- The exporter already stops on a False result for the first and later SQLite batches. The helper that raises is at lines 252 to 263 (R-05). The first-batch and later-batch branches call it (R-06, R-07). PR #4834 merged these guards on 2026-11-19 (R-02, R-03).
- PR #4834 used `Refs #4722` and `Refs #4721`. It did not close either issue (R-02).
- The partial-batch defect remains. The writer returns True when at least one row inserts (R-15). The default contract comes from issue #3350 (R-26).
- The writer does not accept a full-batch flag (R-17, R-18). No test covers a partial batch on the extended exporter module (R-41).
- The exporter call at line 258 sets only the format override (R-10). The issue reproduction blob (R-11) differs from the current exporter blob, so the reproduction predates PR #4834.
- Open PR #4813 changes `data_exporter.py` (R-04). This record sequences the pull request after #4813 merges.
- The mistapi call exists (R-12, R-65). The OpenAPI operation exists (R-59). The `next` value is a cursor or a URL (R-63). The exporter passes it unchanged (R-13).

## Decisions

Each decision names its alternatives, the chosen option, the reason, and the risk. The chosen option is the recommended option. No decision needs a human decision under section 6 of the brief.

- D-1 Scope. Options: (a) fix the SQLite partial-batch path only. (b) Also change the CSV resume path and the key strategy. (c) Close issue 4722 as fixed. Chosen: (a). Reason: the False path is present on remote main (R-05 to R-09). The CSV path belongs to issue 4721. The key collapse belongs to issue 4723. Issue comment IC_kwDOQltU8c8AAAABkoggfg keeps the partial batch open. Risk: CSV rows can still be lost until issue 4721 closes. Caution: the owner must track issue 4721.

- D-2 Detection of partial batches. Options: (a) an opt-in full-batch flag on SQLite writes. (b) A changed writer result for every caller. (c) A table row count after each batch. (d) A documented limit. Chosen: (a). Reason: only the checkpointed 52-week exporter needs a full-batch result. Option (b) reverses the issue #3350 contract for every SQLite caller (R-26). Option (c) fails because `_commit_and_verify` counts the whole table (R-22), and `INSERT OR REPLACE` hides a replaced row (R-21). Option (d) leaves issue 4722 open. Risk: every checkpointed SQLite write must keep the flag. TC-08 and TC-10 guard this.

- D-3 Storage of a rejected batch. Options: (a) discard the whole batch and return False. (b) Keep the stored rows and return False. Chosen: (a). Reason: False then means no row of the batch remains. The next run requests the same page again. The composite key makes the retry idempotent (R-49 and R-21). Option (b) leaves rows that the checkpoint does not cover. Risk: the next run repeats one page request. This costs API calls and loses no data. Caution: the repeat request uses the same continuation token.

- D-4 Call path in DataExporter. Options: (a) a new helper for full-batch SQLite requests. (b) A sixth argument on `_dispatch_format_write`. (c) A new public method. Chosen: (a). Reason: `_dispatch_format_write` has five arguments (R-31). Its SQLite branch calls `_write_sqlite_format` with three arguments (R-34), and a test pins that call (R-36). Option (b) breaks the five-argument rule. Option (c) adds public surface. Risk: the helper repeats the exception handling of `_dispatch_format_write`. TC-07 covers the repeated handling.

- D-5 Writer call shape. Options: (a) a keyword argument on `write`, passed through two methods. (b) A constructor argument. (c) A setter attribute. Chosen: (a). Reason: `__init__` already spans 24 lines (R-23). A constructor argument pushes it past the 25-line limit. A setter attribute hides state from callers. Risk: two intermediate methods gain one argument each. Both stay under the five-argument limit.

- D-6 Test placement. Options: (a) edit existing test modules. (b) Add new test modules. Chosen: (a). Reason: `tests/unit/export` holds 55 children (R-103), and `tests/integration` holds 26 children (R-102). The constitution forbids new direct children in noncompliant directories (R-86). Option (b) breaks that rule. Risk: the diffs in existing modules grow. The sequencing rule in D-8 limits the conflicts.

- D-7 Test strategy. Options: (a) mock-based unit tests, plus one real-writer test that uses a trigger. (b) Mock-based tests only. (c) Real-database tests only. Chosen: (a). Reason: issue comment IC_kwDOQltU8c8AAAABkoggfg shows that mocks cannot prove the row behavior. Mocks alone (option b) cannot show a partial batch. Real-database tests alone (option c) hide the control flow that the exporter tests cover. Risk: the trigger behavior is unverified until a run passes. See Unverified item U-4.

- D-8 File ownership and sequencing. Options: (a) start now and rebase later. (b) Wait for PR #4813 to merge, or obtain a handover. (c) Avoid `data_exporter.py`. Chosen: (b). Reason: AGENTS.md requires one open pull request for each file (R-71). Option (c) is not possible, because the flag must reach the SQLite branch in `data_exporter.py` (D-4). Option (a) creates a conflict on the same file. Risk: the start of T-PR depends on #4813. Caution: a rebase after #4813 can conflict on `data_exporter.py`.

- D-9 Polyglot mirror. Options: (a) keep the current behavior. (b) Skip the mirror after a rejected SQLite batch. (c) Reverse the mirror writes. Chosen: (a). Reason: the mirror receives the same rows again on the next successful run. Its upsert behavior is unverified (U-6). Changing mirror semantics belongs to a separate issue. The operator-facing defect is the SQLite result. Risk: the backends differ until the next successful run. Caution: the mirror can hold rows that the SQLite table discarded.

- D-10 Release-note fragment name. Options: (a) `issue-4722-partial-batch.md`. (b) `pr-<number>.md`. (c) `<YYYY-MM-DD>-partial-batch.md`. Chosen: (a). Reason: the pull request does not exist yet. The fragment name is unused on remote main (R-52). The changelog README lists the issue form (R-53). The name rule matches the guard at R-54. Risk: the fragment name stays after the pull request opens. The README says to keep the first name.

## Remote Verification

| # | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | Remote main tip is f03c6c9b36d612a48d7b9652998c2fd87dd777ca | refs/heads/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R-02 | PR #4834 merged on 2026-11-19 with Refs #4722 and no closing keyword | PR #4834 | main | 19bec34ea1edfae30782fc0f23dde44b3516e369 | present | 0 |
| R-03 | PR #4834 merge commit is an ancestor of main | commit 19bec34ea1edfae30782fc0f23dde44b3516e369 | main | 19bec34ea1edfae30782fc0f23dde44b3516e369 | present | 0 |
| R-04 | Open PR #4813 changes data_exporter.py | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 0 |
| R-05 | SQLite batch helper raises RuntimeError when the writer returns False | src/operations/exporting/export/device_events_52w_exporter.py | main | 97e574382993ca34d56108d6cbf660d047b74be4 | present | 260 |
| R-06 | First-batch SQLite branch raises before the checkpoint write | src/operations/exporting/export/device_events_52w_exporter.py | main | 97e574382993ca34d56108d6cbf660d047b74be4 | present | 304 |
| R-07 | Later-batch SQLite branch raises before the checkpoint advance | src/operations/exporting/export/device_events_52w_exporter.py | main | 97e574382993ca34d56108d6cbf660d047b74be4 | present | 324 |
| R-08 | Streaming loop writes the checkpoint after each append | src/operations/exporting/export/device_events_52w_exporter.py | main | 97e574382993ca34d56108d6cbf660d047b74be4 | present | 340 |
| R-09 | Completion removes the checkpoint and logs completion after streaming | src/operations/exporting/export/device_events_52w_exporter.py | main | 97e574382993ca34d56108d6cbf660d047b74be4 | present | 118 |
| R-10 | SQLite batch call requests a full-batch write | src/operations/exporting/export/device_events_52w_exporter.py | main | 97e574382993ca34d56108d6cbf660d047b74be4 | absent | 258 |
| R-11 | Issue reproduction blob db6d6b1092be47feaddd7c8ac70d66e1d0254b7b is no longer the exporter blob | src/operations/exporting/export/device_events_52w_exporter.py | main | db6d6b1092be47feaddd7c8ac70d66e1d0254b7b | stale | 0 |
| R-12 | Exporter calls mistapi searchOrgDeviceEvents | src/operations/exporting/export/device_events_52w_exporter.py | main | 97e574382993ca34d56108d6cbf660d047b74be4 | present | 160 |
| R-13 | Exporter passes the raw next value as the continuation token | src/operations/exporting/export/device_events_52w_exporter.py | main | 97e574382993ca34d56108d6cbf660d047b74be4 | present | 334 |
| R-14 | Empty-result branch ignores the write result | src/operations/exporting/export/device_events_52w_exporter.py | main | 97e574382993ca34d56108d6cbf660d047b74be4 | present | 123 |
| R-15 | Writer returns True for a partial batch | src/foundation/support/refactors/sqlite_database_writer.py | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 475 |
| R-16 | Writer discards a batch with zero inserted rows | src/foundation/support/refactors/sqlite_database_writer.py | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 469 |
| R-17 | Writer write() accepts a full-batch flag | src/foundation/support/refactors/sqlite_database_writer.py | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | absent | 88 |
| R-18 | Writer rejects a partial batch when a full batch is requested | src/foundation/support/refactors/sqlite_database_writer.py | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | absent | 459 |
| R-19 | Per-row failure handler returns False after logging the row | src/foundation/support/refactors/sqlite_database_writer.py | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 412 |
| R-20 | Rollback undoes uncommitted writes | src/foundation/support/refactors/sqlite_database_writer.py | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 547 |
| R-21 | Writer uses INSERT OR REPLACE for key-based inserts | src/foundation/support/refactors/sqlite_database_writer.py | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 362 |
| R-22 | Commit verification counts all rows of the table | src/foundation/support/refactors/sqlite_database_writer.py | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 505 |
| R-23 | Writer __init__ spans 24 lines | src/foundation/support/refactors/sqlite_database_writer.py | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 59 |
| R-24 | _finish_batch spans 17 lines | src/foundation/support/refactors/sqlite_database_writer.py | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 459 |
| R-25 | Existing writer message uses the term rolled back | src/foundation/support/refactors/sqlite_database_writer.py | main | 8931ee6b705bb351a45a9b2f8a046fc18ec43ccd | present | 464 |
| R-26 | Writer test pins a partial batch to True | tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py | main | 62f9c0c2cb725302430b1c3fa7a803462807e22d | present | 653 |
| R-27 | Writer test keeps old rows after a failed batch | tests/unit/config/foundation/support/refactors/data/storage/test_sqlite_database_writer.py | main | 62f9c0c2cb725302430b1c3fa7a803462807e22d | present | 633 |
| R-28 | ExportBackendOptions defines format_override | src/foundation/models/dataclasses/export_backend_options.py | main | 929e170a977e5659378da45386ced3acefe52e9a | present | 28 |
| R-29 | ExportBackendOptions defines require_full_batch | src/foundation/models/dataclasses/export_backend_options.py | main | 929e170a977e5659378da45386ced3acefe52e9a | absent | 0 |
| R-30 | write_with_format_selection returns the primary write result | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 180 |
| R-31 | write_with_format_selection dispatches through _dispatch_format_write | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 173 |
| R-32 | write_with_format_selection spans 28 lines | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 153 |
| R-33 | Polyglot mirror runs after the primary write | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 176 |
| R-34 | _dispatch_format_write passes three arguments to _write_sqlite_format | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 147 |
| R-35 | _write_sqlite_format calls write() without a flag | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 386 |
| R-36 | Dispatch test pins the three-argument SQLite call | tests/unit/export/test_data_exporter.py | main | 8e91cbe472c2068183c15fca1fa350d1b76f9d34 | present | 170 |
| R-37 | Constructor test pins the writer arguments | tests/unit/export/test_data_exporter.py | main | 8e91cbe472c2068183c15fca1fa350d1b76f9d34 | present | 466 |
| R-38 | Extended exporter tests include the first-batch SQLite test | tests/unit/test_device_events_52w_exporter_extended.py | main | 2361f5b0048d7834f63b8c360066a35344484f23 | present | 574 |
| R-39 | Extended exporter tests include the later-batch SQLite test | tests/unit/test_device_events_52w_exporter_extended.py | main | 2361f5b0048d7834f63b8c360066a35344484f23 | present | 597 |
| R-40 | Extended exporter tests include the SQLite success test | tests/unit/test_device_events_52w_exporter_extended.py | main | 2361f5b0048d7834f63b8c360066a35344484f23 | present | 625 |
| R-41 | Extended exporter tests include a partial-batch test | tests/unit/test_device_events_52w_exporter_extended.py | main | 2361f5b0048d7834f63b8c360066a35344484f23 | absent | 0 |
| R-42 | Extended exporter tests assert the SQLite format override | tests/unit/test_device_events_52w_exporter_extended.py | main | 2361f5b0048d7834f63b8c360066a35344484f23 | present | 259 |
| R-43 | Empty-result test pins the CSV call | tests/unit/test_device_events_52w_exporter.py | main | de5aa5a82d9824bcc0dc158c49846923e828cd0b | present | 29 |
| R-44 | End-to-end SQLite 52-week test exists | tests/unit/prod_readiness/standalone/operations/exporting/reports/test_exports.py | main | a6da81f5622bccde7f3b09b02fcc6071d36ffdb0 | present | 57 |
| R-45 | Integration pattern sets DATABASE_PATH on the root module | tests/integration/test_menu_12_sqlite_upsert.py | main | dddc6ff274da362797e5a3ddcffb43d056d38401 | present | 27 |
| R-46 | Menu 97 has category resource_intensive | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 178 |
| R-47 | Menu 97 entry calls device_events_52w | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 5229 |
| R-48 | device_events_52w builds the exporter from the global output format | src/operations/exporting/export/org_alarm_event_exporter.py | main | b46c4b156f1bccac870aa469375c90927bd4f9c9 | present | 160 |
| R-49 | searchOrgDeviceEvents primary key is a composite key | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 267 |
| R-50 | MistHelper re-exports DeviceEvents52wExporter | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 587 |
| R-51 | Release-note fragment from PR #4834 exists | changelog.d/issue-4722-export-writes.md | main | b5107fd476dddf383504d4ac9f8168be80e752af | present | 0 |
| R-52 | New fragment name changelog.d/issue-4722-partial-batch.md is unused | changelog.d/issue-4722-partial-batch.md | main | not in tree | absent | 0 |
| R-53 | Changelog README lists the three name forms | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 24 |
| R-54 | Changelog guard accepts issue-named fragments | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 39 |
| R-55 | Changelog guard requires a change type word | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 45 |
| R-56 | Operator guide has no 52-week or checkpoint text | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | absent | 0 |
| R-57 | README has no menu 97 text | README.md | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | absent | 0 |
| R-58 | MIST_API_GET_ENDPOINTS lists searchOrgDeviceEvents | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 507 |
| R-59 | OpenAPI defines the searchOrgDeviceEvents path and operationId | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 8667 |
| R-60 | OpenAPI defines the search_after cursor parameter | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 60227 |
| R-61 | OpenAPI defines duration with relative units | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 59637 |
| R-62 | OpenAPI defines limit with default 100 and no maximum | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 59742 |
| R-63 | OpenAPI defines the response next field as a cursor or URL | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 94038 |
| R-64 | OpenAPI device_type value all is valid | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 77056 |
| R-65 | mistapi defines searchOrgDeviceEvents with the exporter arguments | .venv\Lib\site-packages\mistapi\api\v1\orgs\devices.py | local | 90fe126e9c3e34d7784644016e12833b7359737d | present | 259 |
| R-66 | Pinned mistapi version is 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | local | 86b3b7003d569a1311af4085e7e269a52decd795 | present | 3 |
| R-67 | AGENTS defines the writing style rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| R-68 | AGENTS defines the inline comment rule | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 97 |
| R-69 | AGENTS defines the action logging rule | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 104 |
| R-70 | AGENTS defines the test rule | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 133 |
| R-71 | AGENTS defines the parallel agent file rule | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 242 |
| R-72 | Copilot instructions define the local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 57 |
| R-73 | Copilot instructions define the full-suite commands | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 87 |
| R-74 | Copilot instructions define the test quality procedure | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 95 |
| R-75 | Copilot instructions define the label rules | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 433 |
| R-76 | Copilot instructions define the changelog fragment rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| R-77 | Copilot instructions define the pull request title rules | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 507 |
| R-78 | CI defines MYPY_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-79 | CI defines VULTURE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R-80 | CI defines PYDOCSTYLE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| R-81 | CI defines INTERROGATE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R-82 | CI defines INTERROGATE_THRESHOLD with default 90 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 123 |
| R-83 | CI defines VULTURE_CONFIDENCE with default 70 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 127 |
| R-84 | STE linter configuration file exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 1 |
| R-85 | Pull request template requires a linked spec issue | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 3 |
| R-86 | Constitution Principle I sets the five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R-87 | Constitution Principle III sets safety rules | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| R-88 | Constitution Principle IV sets the full pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| R-89 | Constitution Principle V sets ASCII logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 182 |
| R-90 | Constitution Principle VI sets inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R-91 | Constitution Principle VII sets action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R-92 | Constitution output backend rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 312 |
| R-93 | Constitution operational store rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 315 |
| R-94 | Constitution export boundary rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 320 |
| R-95 | Constitution testing section | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 361 |
| R-96 | Constitution documentation section | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 398 |
| R-97 | Spec template shape | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 1 |
| R-98 | Plan template shape | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 1 |
| R-99 | Tasks template shape | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 1 |
| R-100 | Checklist template shape | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 1 |
| R-101 | Reference record spec shape | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| R-102 | tests/integration holds 26 children | tests/integration | main | e5b3e9f9d45a2b2694d923b6dbb484f1c530c818 | present | 0 |
| R-103 | tests/unit/export holds 55 children | tests/unit/export | main | f87e46d24e73c34cda279cc88a5dfd16c26d55e4 | present | 0 |
| R-104 | changelog.d holds 335 children | changelog.d | main | ece56396f47d31dfed7bebe6c69f6dda39f53d83 | present | 0 |
| R-105 | Copilot instructions require Python 3.15 or newer | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 20 |
| R-106 | Copilot instructions give the worktree bootstrap commands | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 29 |

## Sources

- Remote files: the paths and blob SHAs in the table above. The GitHub repository is `jmorrison-juniper/MistHelper`.
- Local mistapi package: `.venv\Lib\site-packages\mistapi\api\v1\orgs\devices.py` (lines 259 to 274) and `.venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA` (line 3). The pin in `requirements.txt` is `mistapi>=0.64.0,<0.65`.
- Local reference record: `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`. The shape comes from its `spec.md`, `plan.md`, `tasks.md`, and `analysis.md`. Its content is not reused.
- GitHub issue #4722 comments: IC_kwDOQltU8c8AAAABkoW1-A (2026-11-09T22:29:59Z) and IC_kwDOQltU8c8AAAABkoggfg (2026-11-09T22:38:15Z).
- GitHub pull requests: #4834 (merged, https://github.com/jmorrison-juniper/MistHelper/pull/4834) and #4813 (open, https://github.com/jmorrison-juniper/MistHelper/pull/4813).
- Related issues: #4721 (open, in-progress), #4723 (open), #3350 (closed).
- Web sources: none fetched. The record uses no web_fetch result.
- Skills: none loaded. The issue concerns Python export code and the mistapi SDK. No Podman or Juniper device behavior is in scope.

## Unverified

- U-1: The live Mist API value of `next` is unknown. The OpenAPI text says cursor or URL (R-63). No live request was made, and the brief forbids one for this record.
- U-2: The API accepts `duration=52w`. The OpenAPI lists relative units such as 2w and states no maximum (R-61).
- U-3: The API accepts `limit=1000`. The OpenAPI sets a default of 100 and states no maximum (R-62).
- U-4: The SQLite trigger rejects one row and lets the other inserts continue. The evidence comes from issue comment IC_kwDOQltU8c8AAAABkoggfg. The local writer code catches a per-row error (R-19). TC-10 must prove this behavior.
- U-5: Whether the existing writer and exporter tests pass on remote main is unverified. This record ran no tests. The pull request CI for #4834 reported success on its head before the merge. T-LOCAL-GATES must prove the current state.
- U-6: The polyglot mirror behavior after a rejected batch. The record keeps the current behavior (D-9). The mirror was not run.
- U-7: Principle IV steps 10 to 12 (main build, revision label, and deployment health) are owner-controlled. The agent did not run them.
- U-8: The shard timings and coverage numbers for the new change. The gates measure them after the change.
- U-9: The owner has not decided whether PR #4813 merges before this change. The sequencing in D-8 depends on that decision.
