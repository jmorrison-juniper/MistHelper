# Tasks: Resolve the open clear-text logging alerts

**Feature**: `1034-codeql-cleartext-logging`

**Branch**: `1034-codeql-cleartext-logging`

**Date**: 2026-08-05

**Input**: Design documents in `specs/1034-codeql-cleartext-logging/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`,
`contracts/verdict-register.md`, `contracts/credential_console.md`

---

## Format

`- [ ] [TaskID] [P?] [Story?] Description with the file path`

- **[P]**: The task runs in parallel with the other `[P]` tasks in the same block. A `[P]`
  task touches a different file, or the task only reads.
- **[Story]**: The user story that owns the task. The setup phase, the foundational phase,
  and the polish phase carry no story label.
- **PENDING OPERATOR**: The task needs a live Mist organization, a live network host, a
  human reader, or a GitHub write token. This session cannot run the task.

---

## The pull request grouping

The feature ships as four pull requests. Research note R-012 records the reason. Each pull
request is independently mergeable.

| Pull request | Phases | Stories | Tasks | Closes |
| - | - | - | - | - |
| PR 1 | 1, 2, 3 | US1 | T001 to T016 | #1735 |
| PR 2 | 4 | US6 | T017 to T027 | #1736 |
| PR 3 | 5, 6 | US3, US5 | T028 to T049 | #1733, #1734 |
| PR 4 | 7, 8, 9 | US4, US2 | T050 to T066 | #1737 |

User story 2 spans all four pull requests. Each pull request appends its own rows to the
verdict register. Pull request 4 counts the rows, reconciles the register with the GitHub
security tab, and closes the five tracking issues.

---

## Repository rules that every task obeys

1. Every executable line that a task adds carries an inline comment. The comment states the
   intent of the line.
2. Every action gains one `logging.info` call before the action and one `logging.debug`
   call after the action. The second call states the result.
3. Every prose file that a task changes passes the Simplified Technical English linter with
   a score of 80 or above.
4. Every command runs through `.venv\Scripts\python.exe`. The global interpreter in this
   workspace is broken.
5. No task hashes a secret. Pull request #1732 tried a SHA-256 digest, and CodeQL raised
   `py/weak-sensitive-data-hashing` at high severity. A task removes the value, uses a
   position label, or uses a count.

---

## Phase 1: Setup and baseline (PR 1)

**Purpose**: Confirm the tooling and record the starting state.

- [ ] T001 Verify the interpreter and the GitHub token. Run `.venv\Scripts\python.exe --version` and expect `Python 3.13` or a later version. Run `gh auth status` and expect a token with the `security_events` scope.
- [ ] T002 [P] Record the baseline open alert count. Run the check 1 command from `specs/1034-codeql-cleartext-logging/quickstart.md`. Expect the output `19`. Write the value and the date into a scratch note for task T004.
- [ ] T003 [P] Export the current alert list. Run `gh api "repos/:owner/:repo/code-scanning/alerts?state=open&per_page=100" --jq '.[] | select(.rule.id=="py/clear-text-logging-sensitive-data") | "\(.number)|\(.most_recent_instance.location.path)|\(.most_recent_instance.location.start_line)"'`. Expect 19 lines. Compare the output against the table in `specs/1034-codeql-cleartext-logging/research.md` under note R-001. A line difference means that a line drifted, so the anchor takes priority over the line number.

**Checkpoint**: The tooling works and the baseline is recorded.

---

## Phase 2: Foundational (PR 1)

**Purpose**: Create the register file. Every story appends rows to this file, so the file
must exist first.

**Blocking**: No story task that writes a register row can start until T004 completes.

- [ ] T004 Create `specs/1034-codeql-cleartext-logging/verdict-register.md`. Write the eleven-column header exactly as contract clause C-1 states. The columns are `Alert`, `Issue`, `File`, `Line`, `Anchor`, `Verdict`, `Reason`, `Author`, `Decided`, `Review`, `Trigger`. Add a preamble that names the baseline count from T002, the baseline date, and the reconciliation command from contract clause C-8. Add no data row.

**Checkpoint**: The register exists. Story work can start.

---

## Phase 3: User Story 1 - Protect the ZTP credential (Priority: P1) - PR 1 - MVP

**Goal**: The tool shows the ZTP password on an interactive terminal with a warning. The
tool withholds the password from every other destination.

**Independent Test**: Request the ZTP password with the output stream redirected to a file.
Confirm that the file holds no password. Then request the password on a live terminal and
confirm that the password appears after the warning.

**Covers**: FR-009 through FR-014, SC-005, alert 173, issue #1735.

### Tests for User Story 1

> Write these tests first. Confirm that they fail before the implementation starts.

- [ ] T005 [P] [US1] Create `tests/unit/test_credential_console_behavior.py`. Patch `sys.stdout.isatty` to return `True` and assert that the written text holds the warning before the secret and that the method returns `True`. Patch `sys.stdout.isatty` to return `False` and assert that the written text holds the label, holds the withhold notice, holds no character of the secret, and that the method returns `False`. Capture the log records and assert that no record holds the secret.
- [ ] T006 [P] [US1] Create `tests/unit/test_credential_console_contract.py`. The test reads the source of `src/utils/console.py` and the source of `src/device/_utility_commands_action.py`. The test fails when the reveal path holds a `print(` call, when the reveal path holds a `logging.` call that takes the secret variable, or when `_render_ztp_response` passes the credential to any callable other than `CredentialConsole.reveal`. This test is the durable marker for issue #886 that requirement FR-014 needs. Contract clauses C-2, C-6, and C-8 state the rules.

### Implementation for User Story 1

- [ ] T007 [US1] Add the `CredentialConsole` class to `src/utils/console.py`. The class holds one public static method `reveal(label: str, secret: str) -> bool`. The method calls `sys.stdout.isatty()` once. The reveal branch writes the recording warning first and then writes the label and the secret. The withhold branch writes the label, the withhold notice, and the remedy. Every write uses `sys.stdout.write()`, because ruff does not select the `T20` rule family today and a `sys.stdout.write()` call therefore survives the mechanical migration of issue #886. The method logs `logging.info("Credential display requested for %s", label)` before the write and `logging.debug("Credential display outcome for %s: %s", label, outcome)` after the write. Neither log line holds the secret, any part of the secret, or a digest of the secret. Contract clauses C-1 through C-6 state the full behavior.
- [ ] T008 [US1] Rewrite `_render_ztp_response` in `src/device/_utility_commands_action.py`. Replace the line `print(f"\n-> ZTP Password: {ztp_credential}")  # noqa: T201` with a call to `CredentialConsole.reveal("ZTP Password", ztp_credential)`. The inert `# noqa: T201` marker leaves the file with that line, because ruff does not select `T20` and the marker therefore silences nothing.
- [ ] T009 [US1] Correct the comment block above the credential display in `src/device/_utility_commands_action.py`. Delete the claim that the tool never logs and never saves the password, because that claim holds only on a live terminal. Delete the line `print("-> (Password displayed on console only - not logged or saved)")`, because the new withhold notice and the new warning replace it. Write one comment line that names the terminal check and names the recording limit. Requirement FR-013 and contract clause C-7 state the rule.

### Verification for User Story 1

- [ ] T010 [US1] Append the register row for alert 173 to `specs/1034-codeql-cleartext-logging/verdict-register.md`. Set `Issue` to `1735`, `File` to `src/device/_utility_commands_action.py`, `Verdict` to `fixed`, `Review` to `-`, and `Trigger` to `-`. Set `Anchor` to `src/device/_utility_commands_action.py::UtilityCommandsAction._render_ztp_response :: "-> ZTP Password: "`. The reason states that a terminal check and an operator warning replace the bare console write.
- [ ] T011 [US1] Run the new unit tests. Command: `.venv\Scripts\python.exe -m pytest tests\unit\test_credential_console_behavior.py tests\unit\test_credential_console_contract.py -q`. Expected output: every test passes and the exit code is `0`.
- [ ] T012 [US1] PENDING OPERATOR. Run quickstart check 4. Command: `python MistHelper.py --menu 144 > data\ztp_redirect_test.txt`, then `Select-String -Path data\ztp_redirect_test.txt -Pattern 'ZTP Password:'`. Expected result: the file holds the label and the withhold notice, and the file holds no credential value. Delete the file after the check. This task needs a live Mist organization and a laboratory device. **Warning**: this check returns a real credential, so never run it against a production device.
- [ ] T013 [US1] PENDING OPERATOR. Run quickstart check 5. Command: `python MistHelper.py --menu 144` on an interactive terminal with no redirection. Expected result: the screen shows the recording warning first and then shows the credential. This task needs a human reader, because a test harness has no terminal.
- [ ] T014 [US1] Run the quality gates exactly as the workflow runs them. Commands: `.venv\Scripts\python.exe -m ruff check .`, `.venv\Scripts\python.exe -m black --check --diff .`, `.venv\Scripts\python.exe -m mypy src/ --config-file pyproject.toml`, `.venv\Scripts\python.exe -m radon cc src/ -n C`, `.venv\Scripts\python.exe -m bandit -r src/ MistHelper.py starlink_dashboard.py`, `.venv\Scripts\python.exe -m pytest --cov --cov-fail-under=80`. Expected result: every command exits with the code `0`. **Warning**: `radon` honors no suppression marker. A block above the complexity value of 10 fails the gate, so decompose the block instead of annotating it.
- [ ] T015 [US1] Run the Simplified Technical English linter on the changed prose. Command: `.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs\1034-codeql-cleartext-logging\verdict-register.md`. Expected result: the score is 80 or above.
- [ ] T016 [US1] PENDING OPERATOR. Open pull request 1 from the branch `1034-codeql-cleartext-logging`. The title names the ZTP credential guard. The body holds `Closes #1735` and a link to `specs/1034-codeql-cleartext-logging/verdict-register.md`. Wait for CodeQL to finish before you add the `auto-merge` label.

**Checkpoint**: User story 1 is complete and independently shippable. The only live
credential in the alert set is now protected.

---

## Phase 4: User Story 6 - Restore the operator echo contract (Priority: P6) - PR 2

**Goal**: The SSH plan echo reaches the screen through the `echo()` helper and reaches the
log at the information level.

**Independent Test**: Start a bulk SSH run. Confirm that the plan echo still shows the same
text on the screen. Confirm that the log records the echo at the information level.

**Covers**: FR-015 through FR-017, SC-006, SC-010, alerts 188 and 189, issue #1736.

**Reuse rule**: Use the existing `echo()` helper in `src/utils/console.py` that spec 1031
added. Do not write a second helper.

### Tests for User Story 6

- [ ] T017 [P] [US6] Create `tests/unit/test_ssh_runner_echo_plan.py`. Patch the `echo` name that `src/ssh/ssh_runner_manager.py` imports. Call `SSHRunnerManager._echo_plan` with a host list, a user name, and a command list. Assert that the patched `echo` receives three calls. Assert that the message text matches the earlier text. Capture the log records and assert that every record carries the `INFO` level and that no record carries the `WARNING` level.

### Implementation for User Story 6

- [ ] T018 [US6] Convert the three echo calls in `SSHRunnerManager._echo_plan` in `src/ssh/ssh_runner_manager.py` at the lines 110, 111, and 112. Replace each `logging.warning("!? ...", ...)` call with an `echo("...", ...)` call. Drop the `!?` prefix, because the helper owns the console write. Keep the operator-visible words unchanged, because requirement SC-010 forbids the loss of a plan line. Alert 188 sits on line 110 and alert 189 sits on line 111. Line 112 carries no alert, and the task converts it anyway, because a mixed method confuses the next reader.
- [ ] T019 [US6] Convert the two remaining echo calls in `src/ssh/ssh_runner_manager.py` at the lines 307 and 323. Both calls sit inside `_execute_multi_host`. Replace each `logging.warning("\n!? ...", ...)` call with an `echo("...", ...)` call. Note R-009 in `specs/1034-codeql-cleartext-logging/research.md` records this disposition.
- [ ] T020 [P] [US6] Convert the two flagged echo calls in `src/ssh/runtime/app_runner.py` at the lines 301 and 341. Replace each `logger.warning("!? ...", ...)` call with an `echo("...", ...)` call. Leave the lines 180, 219, 221, 224, 260, and 268 unchanged, because note R-009 records those as an input prompt or as an existing information-level call.
- [ ] T021 [US6] Run the sweep of `src/ssh/` and reconcile the result. Command: `Select-String -Path src\ssh\*.py, src\ssh\**\*.py -Pattern '!\?' | ForEach-Object { "$($_.Path):$($_.LineNumber)" }`. Compare the output against the sweep table in note R-009. Expected result: every remaining line matches a `Keep` row in that table. A line with no recorded disposition fails the check, so add a row for it. Requirement FR-017 needs this record.

### Verification for User Story 6

- [ ] T022 [US6] Append the register rows for alert 188 and alert 189 to `specs/1034-codeql-cleartext-logging/verdict-register.md`. Set `Issue` to `1736`, `File` to `src/ssh/ssh_runner_manager.py`, `Verdict` to `fixed`, `Review` to `-`, and `Trigger` to `-`. Set the anchor of alert 188 to `src/ssh/ssh_runner_manager.py::SSHRunnerManager._echo_plan :: "!? Target hosts: %s"`. Set the anchor of alert 189 to `src/ssh/ssh_runner_manager.py::SSHRunnerManager._echo_plan :: "!? Username: %s"`. The reason states that the line moved to the `echo()` helper at the information level. Add a note that names the sweep result from T021.
- [ ] T023 [US6] Run the unit tests. Command: `.venv\Scripts\python.exe -m pytest tests\unit\test_ssh_runner_echo_plan.py -q`. Expected output: every test passes and the exit code is `0`.
- [ ] T024 [US6] PENDING OPERATOR. Run quickstart check 6. Command: `python MistHelper.py --menu 60`, then `Select-String -Path data\script.log -Pattern 'Target hosts' | Select-Object -Last 3`. Expected result: the screen shows the target hosts, the user name, and the command count. The matching log lines carry the `INFO` level and not the `WARNING` level. This task needs live network hosts.
- [ ] T025 [US6] Run the quality gates with the six commands from T014. Expected result: every command exits with the code `0`.
- [ ] T026 [US6] Run the Simplified Technical English linter on `specs\1034-codeql-cleartext-logging\verdict-register.md` with a minimum score of 80.
- [ ] T027 [US6] PENDING OPERATOR. Open pull request 2. The title names the SSH echo conversion. The body holds `Closes #1736`. Wait for CodeQL before you add the `auto-merge` label.

**Checkpoint**: User story 6 is complete. The operator keeps every plan line, and the
warning channel keeps its signal.

---

## Phase 5: User Story 3 - Decide the stance on street addresses (Priority: P3) - PR 3

**Goal**: The address audit log holds no street address at the information level and no
street address at the warning level. Each changed line names a site identifier instead.

**Independent Test**: Run the address audit at the default log level. Read `data/script.log`
and confirm that the log holds no street address.

**Covers**: FR-018, FR-019, FR-026, alerts 174 through 183, issue #1733.

**Policy**: Note R-006 records one policy for all ten alerts. No street address reaches the
information level. No street address reaches the warning level. The debug level may hold a
street address. Every changed line gains a site identifier, so the operator keeps the
ability to correlate a log line with a site.

### Correction and prerequisite for User Story 3

- [ ] T028 [US3] Correct requirement FR-019 in `specs/1034-codeql-cleartext-logging/spec.md`. Note R-005 proves that `_generate_site_packages` never reads `data/script.log`, and a code search returns zero references. The site support package therefore does not hold the address audit log. Rewrite FR-019 to state that the decision records the true travel path, which is `data/script.log` only. Correct the matching assumption line that reads "Menu 101 builds the site support package, and that package can hold the address audit log." Correct the matching sentence in the user story 3 narrative.
- [ ] T029 [US3] Add a `site_id` field to the `ResolveCandidates` dataclass in `src/site/address_audit/models.py`. Use the type `str` with the default `""`. Write an inline comment that states why the field exists, which is that the resolver logs a site identifier in place of a street address. The five-item rule caps a function parameter count at five. The rule does not cap the field count of a configuration object, and `ResolveCandidates` already holds six fields.
- [ ] T030 [US3] Populate the new field at the single construction site. The site is `src/site/address_audit/audit_engine.py` near line 625. Pass the site identifier that the engine already holds. Add an inline comment on the new argument.

### Tests for User Story 3

- [ ] T031 [P] [US3] Create `tests/unit/test_address_resolver_log_redaction.py`. Build a `ResolveCandidates` object with a known street address and a known site identifier. Capture the log records at every level. Assert that no record at the information level holds the street address. Assert that no record at the warning level holds the street address. Assert that the changed records hold the site identifier. Assert that the debug level still carries the detail that an engineer needs.

### Implementation for User Story 3

- [ ] T032 [US3] Change the two log calls in `AddressResolver.resolve` in `src/site/address_audit/address_resolver.py` at the lines 64 and 71. The method `_build_query_key` lowercases the query and collapses the whitespace, so the cache key is the street address itself. Log `candidates.site_id` in place of `key`. Alert 174 sits on line 64 and alert 175 sits on line 71.
- [ ] T033 [US3] Change the log call in `AddressResolver._from_cache` in `src/site/address_audit/address_resolver.py` at line 478. The call reads `logging.debug("cache hit for %s", key)`, and the key is the street address. Log the site identifier in place of the key. Alert 183 sits on this line.
- [ ] T034 [US3] Change the log call in `AddressResolver._resolve_uncached` in `src/site/address_audit/address_resolver.py` at line 85. Keep the warning level, because the line reports a failed resolve and a demotion would hide an operator signal. Log the site identifier in place of the query string. Alert 176 sits on this line.
- [ ] T035 [US3] Change the log call in `src/site/address_audit/address_resolver.py` at line 152. The call already uses the debug level. Remove the resolved address from the message body and log the site identifier and the suite value only. Alert 177 sits on this line.
- [ ] T036 [US3] Change the two log calls in `src/site/address_audit/address_resolver.py` at the lines 193 and 202. Move both calls from the information level to the debug level. Log the site identifier in the message body. Alert 178 sits on line 193 and alert 179 sits on line 202.
- [ ] T037 [US3] Change the log call in `src/site/address_audit/address_resolver.py` that starts at line 220 and carries alert 180 on line 221. Keep the warning level, because the call reports a real mismatch. Replace the street value with the site identifier.
- [ ] T038 [US3] Change the log call in `src/site/address_audit/address_resolver.py` at line 275. Move the call from the information level to the debug level and log the site identifier. Alert 181 sits on this line.
- [ ] T039 [US3] Change the log call in `src/site/address_audit/address_resolver.py` at line 368. The call logs the conflicting house numbers at the information level. Move the call to the debug level and log the site identifier and the count of the distinct values. Alert 182 sits on this line.

### Verification for User Story 3

- [ ] T040 [US3] Append the ten register rows for the alerts 174 through 183 to `specs/1034-codeql-cleartext-logging/verdict-register.md`. Set `Issue` to `1733` and `File` to `src/site/address_audit/address_resolver.py` on every row. Set the anchor of each row to the qualified symbol path and the quoted format string fragment, as entity E-004 states. The anchor holds no street address. Record the corrected travel path from T028 in the reason of at least one row, because requirement FR-019 needs that statement.
- [ ] T041 [US3] Run the unit tests. Command: `.venv\Scripts\python.exe -m pytest tests\unit\test_address_resolver_log_redaction.py -q`. Expected output: every test passes and the exit code is `0`.
- [ ] T042 [US3] PENDING OPERATOR. Run quickstart check 7. Run the address audit at the default log level, then run `Select-String -Path data\script.log -Pattern 'Resolving address \(key='`. Expected result: no match. This task needs a live Mist organization and the customer address file.
- [ ] T043 [US3] Run the quality gates with the six commands from T014. Expected result: every command exits with the code `0`.
- [ ] T044 [US3] Run the Simplified Technical English linter on the two changed prose files. Command: `.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs\1034-codeql-cleartext-logging\spec.md specs\1034-codeql-cleartext-logging\verdict-register.md`. Expected result: both files score 80 or above.

**Checkpoint**: The address audit no longer prints a street address at an operator-visible
log level.

---

## Phase 6: User Story 5 - Decide the stance on capture identifiers (Priority: P5) - PR 3

**Goal**: The four capture alerts hold a recorded verdict with evidence.

**Independent Test**: Read the four register rows. Confirm that each MAC row states why a
device identifier is not private data. Confirm that the payload row lists every field.

**Covers**: FR-020, FR-021, alerts 184 through 187, issue #1734.

**Code change**: None. Note R-007 records the evidence.

- [ ] T045 [P] [US5] Confirm the payload field list in `src/capture/packet_capture.py`. Read the dictionary that `_scan_single_ap_run` builds near line 890. Confirm the keys `type`, `ap_mac`, `band`, and `max_pkt_len`. Confirm the keys that `_gather_scan_radio_params` returns, which are the channel, the bandwidth, and the duration. Write the confirmed list into the reason of the row that task T047 creates. A new key that this task finds needs a fresh review before the verdict stands.
- [ ] T046 [US5] Append the three register rows for the alerts 184, 185, and 186 to `specs/1034-codeql-cleartext-logging/verdict-register.md`. Set `Issue` to `1734`, `File` to `src/capture/packet_capture.py`, and `Verdict` to `false_positive`. The lines sit at 548, 637, and 846. Each line reads `logging.debug("Selected and normalized <type> MAC: %s", <var>)`. The reason states that the value is a device identifier that MistHelper exists to report, and that the query matched the text `mac` in the variable name. Set `Review` to a date one year ahead and set `Trigger` to a change of the log template on that line, because contract clause C-5 needs both fields.
- [ ] T047 [US5] Append the register row for alert 187 to `specs/1034-codeql-cleartext-logging/verdict-register.md`. Set `Issue` to `1734`, `File` to `src/capture/packet_capture.py`, `Line` to `890`, and `Verdict` to `false_positive`. The reason lists every field from T045 and states that no field holds a secret. Set `Review` and `Trigger` as clause C-5 needs. Requirement FR-021 needs the field list.
- [ ] T048 [US5] PENDING OPERATOR. Dismiss the alerts 184, 185, 186, and 187 in the GitHub security tab. Command per alert: `gh api -X PATCH "repos/:owner/:repo/code-scanning/alerts/<number>" -f state=dismissed -f dismissed_reason="false positive" -f dismissed_comment="<register reason>"`. The comment repeats the register reason exactly, because contract clause C-7 needs the match. This task needs a token with a write scope on the security events.
- [ ] T049 [US5] PENDING OPERATOR. Open pull request 3. The title names the address stance and the capture stance. The body holds `Closes #1733` and `Closes #1734`. Wait for CodeQL before you add the `auto-merge` label.

**Checkpoint**: Pull request 3 is complete. Fourteen of the nineteen alerts now hold a
verdict.

---

## Phase 7: User Story 4 - Decide the stance on GPS coordinates (Priority: P4) - PR 4

**Goal**: The two Starlink coordinate alerts hold a recorded acceptance with a stated
expiry.

**Independent Test**: Read the two register rows. Confirm that each row names the option,
the reason, the review date, and the trigger.

**Covers**: FR-022, FR-023, alerts 190 and 191, issue #1737.

**Code change**: None to `starlink_dashboard.py`. The verdict is
`accepted_with_rationale`, so the two `print()` calls stay. Phase 7 adds one guard test that
only reads the file.

- [ ] T050 [US4] Run the coordination check against issue #1721 before any task in this phase touches `starlink_dashboard.py`. Command: `gh pr list --state open --json number,title,headRefName,files --jq '.[] | select(.files[].path=="starlink_dashboard.py") | "#\(.number) \(.headRefName) \(.title)"'`. Expected result: no output. If the command prints a pull request, stop and wait for that pull request to merge. Issue #1721 lands first in that case. Quickstart check 12 states this rule.
- [ ] T051 [US4] Record the T050 result in `specs/1034-codeql-cleartext-logging/verdict-register.md`. Write the observed state, the date, and the agreed order in a note below the table. Requirement FR-023 needs this record. State that the chosen verdict needs no edit to `starlink_dashboard.py`, so the collision risk is zero for this feature.
- [ ] T052 [US4] Create `tests/unit/test_starlink_location_dump_guard.py`. The test reads the source of `starlink_dashboard.py` and finds the method `_dump_diagnostics_location`. The test asserts that the latitude line and the longitude line still call `print()`. The test fails when either line becomes a `logging` call. The test is the expiry enforcement that note R-008 needs, because the acceptance stands only while the value reaches no log sink.
- [ ] T053 [US4] Append the register rows for alert 190 and alert 191 to `specs/1034-codeql-cleartext-logging/verdict-register.md`. Set `Issue` to `1737`, `File` to `starlink_dashboard.py`, and `Verdict` to `accepted_with_rationale`. The lines sit at 1343 and 1344. Set the anchor of alert 190 to `starlink_dashboard.py::StarlinkDashboard._dump_diagnostics_location :: "  - Latitude: "` and the anchor of alert 191 to the matching longitude fragment. The reason states that the operator invokes the dump, that both lines call `print()`, and that the value reaches no log file. Set `Trigger` to the merge of issue #886. Set `Review` to the ISO date that the team agrees.
- [ ] T054 [US4] PENDING OPERATOR. Dismiss the alerts 190 and 191 in the GitHub security tab. Command per alert: `gh api -X PATCH "repos/:owner/:repo/code-scanning/alerts/<number>" -f state=dismissed -f dismissed_reason="won't fix" -f dismissed_comment="<register reason>"`. Note R-011 maps the verdict `accepted_with_rationale` to the API reason `won't fix`.
- [ ] T055 [US4] Run the unit test and the quality gates. Command: `.venv\Scripts\python.exe -m pytest tests\unit\test_starlink_location_dump_guard.py -q`, then the six commands from T014. Expected result: every command exits with the code `0`.

**Checkpoint**: All nineteen alerts now hold a verdict.

---

## Phase 8: User Story 2 - Record one verdict for each alert (Priority: P2) - PR 4

**Goal**: The register holds one complete row for each of the nineteen alerts, and the
GitHub security tab agrees with the register.

**Independent Test**: Count the rows in the register. Confirm the count is 19. Confirm that
each row holds exactly one of the three verdict values and a written reason.

**Covers**: FR-001 through FR-008, FR-024, SC-002, SC-003, SC-004, SC-007.

- [ ] T056 [US2] Run quickstart check 2. Command: `Select-String -Path specs\1034-codeql-cleartext-logging\verdict-register.md -Pattern '^\| 1[78][0-9] \|' | Measure-Object | Select-Object -ExpandProperty Count`. Expected output: `19`. Invariant INV-1 needs this count.
- [ ] T057 [US2] Read every row and confirm the four contract clauses. Confirm that each `Verdict` cell holds `fixed`, `false_positive`, or `accepted_with_rationale`, per clause C-3. Confirm that no `Reason` cell is blank and that no cell reads `see above`, per clause C-4. Confirm that each non-fixed row holds a `Review` value and a `Trigger` value, per clause C-5. Confirm that no anchor holds a street address, a coordinate, a MAC address, or a credential, per clause C-6.
- [ ] T058 [US2] Record the boundary with issue #886 in `specs/1034-codeql-cleartext-logging/verdict-register.md`. State that this feature owns the credential reveal path and the two GPS dump lines. State that issue #886 owns every other `print()` call. Name the two guard tests that fail when the migration crosses the boundary, which are `tests/unit/test_credential_console_contract.py` and `tests/unit/test_starlink_location_dump_guard.py`. Requirement FR-024 needs this record.
- [ ] T059 [US2] PENDING OPERATOR. Run quickstart check 3 and reconcile the two stores. Command: `gh api "repos/:owner/:repo/code-scanning/alerts?state=dismissed&per_page=100" --jq '.[] | select(.rule.id=="py/clear-text-logging-sensitive-data") | "\(.number)|\(.dismissed_reason)|\(.dismissed_comment)"'`. Expected result: six lines that cover the alerts 184, 185, 186, 187, 190, and 191. Each line matches one register row. A line with no matching row fails the check, and a dismissed register row with no matching line fails the check.
- [ ] T060 [US2] PENDING OPERATOR. Add a comment to each of the issues 1733, 1734, 1735, 1736, and 1737. The comment holds the register path and names the rows that belong to that issue. Contract clause C-10 and requirement FR-003 need the link.
- [ ] T061 [US2] PENDING OPERATOR. Run quickstart check 1 after pull request 4 merges to `main` and after the next CodeQL scan completes. Command: the check 1 command from `quickstart.md`. Expected output: `0`. A pull request branch reports a different count, so run this check only after the merge.
- [ ] T062 [US2] PENDING OPERATOR. Handle a residual alert from the address work. The query flags a logging call at every level, so a move to the debug level protects the operator log but may leave the alert open. If T061 reports a count above zero, read the residual alert numbers. For each residual address alert, either remove the value from the log template or change the register verdict from `fixed` to `accepted_with_rationale` with a review date and a trigger. Then dismiss the alert with the matching reason and rerun T061.
- [ ] T063 [US2] PENDING OPERATOR. Close the issues 1733, 1734, 1735, 1736, and 1737 after T061 reports `0`. Success criterion SC-007 needs the closed state on all five issues.

**Checkpoint**: The audit record is complete and matches the GitHub security tab.

---

## Phase 9: Polish and cross-cutting concerns - PR 4

- [ ] T064 [P] Add the changelog entry to `CHANGELOG.md`. Use the `version YY.MM.DD.HH.MM` format with a UTC timestamp. Name the five issues and the four pull requests. State the resolved alert count.
- [ ] T065 Run quickstart check 10 on every feature document. Command: `.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs\1034-codeql-cleartext-logging\plan.md specs\1034-codeql-cleartext-logging\research.md specs\1034-codeql-cleartext-logging\data-model.md specs\1034-codeql-cleartext-logging\quickstart.md specs\1034-codeql-cleartext-logging\verdict-register.md specs\1034-codeql-cleartext-logging\tasks.md specs\1034-codeql-cleartext-logging\contracts\verdict-register.md specs\1034-codeql-cleartext-logging\contracts\credential_console.md`. Expected result: every file scores 80 or above.
- [ ] T066 PENDING OPERATOR. Open pull request 4. The title names the GPS stance and the register close-out. The body holds `Closes #1737` and links the register. Wait for CodeQL before you add the `auto-merge` label.

---

## The alert to task map

Every alert holds a code task or a verdict task and a register task. The table proves that
no alert lacks a decision.

| Alert | File | Issue | Code task | Register task | Verdict |
| - | - | - | - | - | - |
| 173 | `src/device/_utility_commands_action.py` | 1735 | T008, T009 | T010 | `fixed` |
| 174 | `src/site/address_audit/address_resolver.py` | 1733 | T032 | T040 | `fixed` |
| 175 | `src/site/address_audit/address_resolver.py` | 1733 | T032 | T040 | `fixed` |
| 176 | `src/site/address_audit/address_resolver.py` | 1733 | T034 | T040 | `fixed` |
| 177 | `src/site/address_audit/address_resolver.py` | 1733 | T035 | T040 | `fixed` |
| 178 | `src/site/address_audit/address_resolver.py` | 1733 | T036 | T040 | `fixed` |
| 179 | `src/site/address_audit/address_resolver.py` | 1733 | T036 | T040 | `fixed` |
| 180 | `src/site/address_audit/address_resolver.py` | 1733 | T037 | T040 | `fixed` |
| 181 | `src/site/address_audit/address_resolver.py` | 1733 | T038 | T040 | `fixed` |
| 182 | `src/site/address_audit/address_resolver.py` | 1733 | T039 | T040 | `fixed` |
| 183 | `src/site/address_audit/address_resolver.py` | 1733 | T033 | T040 | `fixed` |
| 184 | `src/capture/packet_capture.py` | 1734 | None | T046 | `false_positive` |
| 185 | `src/capture/packet_capture.py` | 1734 | None | T046 | `false_positive` |
| 186 | `src/capture/packet_capture.py` | 1734 | None | T046 | `false_positive` |
| 187 | `src/capture/packet_capture.py` | 1734 | T045 | T047 | `false_positive` |
| 188 | `src/ssh/ssh_runner_manager.py` | 1736 | T018 | T022 | `fixed` |
| 189 | `src/ssh/ssh_runner_manager.py` | 1736 | T018 | T022 | `fixed` |
| 190 | `starlink_dashboard.py` | 1737 | None | T053 | `accepted_with_rationale` |
| 191 | `starlink_dashboard.py` | 1737 | None | T053 | `accepted_with_rationale` |

The alerts sit in five source files. Note R-009 reports six files for the `!?` console echo
sweep, and that sweep is a separate count.

---

## Dependencies and execution order

### Phase dependencies

- Phase 1 has no dependency and starts at once.
- Phase 2 depends on Phase 1. Phase 2 blocks every register write in every story.
- Phase 3 depends on Phase 2. Phase 3 is the minimum viable product.
- Phase 4 depends on Phase 2 only. Phase 4 does not depend on Phase 3.
- Phase 5 depends on Phase 2 only.
- Phase 6 depends on Phase 2 only.
- Phase 7 depends on Phase 2 and on the T050 coordination check.
- Phase 8 depends on Phase 3, Phase 4, Phase 5, Phase 6, and Phase 7. The register must hold
  all nineteen rows before the count check runs.
- Phase 9 depends on Phase 8.

### Story dependencies

- User story 1 depends on nothing. It ships first and alone.
- User story 6 depends on nothing.
- User story 3 depends on nothing.
- User story 5 depends on nothing.
- User story 4 depends on the issue #1721 coordination check.
- User story 2 depends on every other story, because the register closes last.

### Task dependencies inside a story

- T005 and T006 run before T007, T008, and T009. Write the test first and watch it fail.
- T007 runs before T008, because the call site needs the new class.
- T029 and T030 run before T032 through T039, because the resolver reads the new field.
- T031 runs before T032 through T039.
- T045 runs before T047, because the row holds the confirmed field list.
- T050 runs before every other Phase 7 task.
- T056 runs after every register write task, which are T010, T022, T040, T046, T047, and
  T053.

### Parallel opportunities

| Block | Tasks | Reason |
| - | - | - |
| Phase 1 | T002, T003 | Both tasks only read the GitHub API |
| Phase 3 tests | T005, T006 | Two different new test files |
| Phase 4 | T017, T020 | A new test file and a different source file |
| Phase 5 | T031 | A new test file, separate from the source edits |
| Phase 6 | T045 | A read-only confirmation |
| Phase 9 | T064 | `CHANGELOG.md` touches no other task file |

The source edits in Phase 5 from T032 through T039 all touch
`src/site/address_audit/address_resolver.py`, so they run in sequence. The register writes
all touch one file, so they run in sequence.

Two workers can run Phase 4 and Phase 5 at the same time, because the two phases share no
file.

---

## Implementation strategy

### The minimum viable product

Pull request 1 alone is a shippable increment. It protects the only live credential in the
alert set. Stop after T016 and ship if the schedule needs a cut.

### The incremental order

1. Ship pull request 1. The credential risk closes first.
2. Ship pull request 2. The defect that the spec 1031 sweep missed closes next.
3. Ship pull request 3. The ten address alerts and the four capture alerts close.
4. Ship pull request 4. The register closes and the five issues close.

### Risks

| Risk | Effect | Response |
| - | - | - |
| A move to the debug level may not close a CodeQL alert. The query flags a logging call at any level | The address alerts stay open after pull request 3 merges | T062 handles the residual. Remove the value from the template or change the verdict |
| A recorded SSH session returns `True` from `isatty()` | The terminal check alone does not protect the credential | The reveal path writes the operator warning first. Note R-002 records the test |
| Issue #886 converts the credential write to a logging call | The credential reaches `data/script.log` | T006 creates the guard test. `sys.stdout.write()` is not a `print()` call, so the migration does not see the line |
| Issue #1721 edits `starlink_dashboard.py` at the same time | A rebase conflict | T050 gates Phase 7. This feature makes no edit to that file |
| A line number drifts before a task runs | A task edits the wrong line | Find the call site with the anchor text, not with the line number |

### The operator tasks

This session cannot run the tasks below. They need a live Mist organization, a live network
host, a human reader, or a GitHub write token.

| Task | What it needs |
| - | - |
| T012 | A live Mist organization and a laboratory switch |
| T013 | A human reader on an interactive terminal |
| T016, T027, T049, T066 | A GitHub write token for the pull request |
| T024 | Live network hosts for a bulk SSH run |
| T042 | A live Mist organization and the customer address file |
| T048, T054 | A GitHub token with a write scope on the security events |
| T059, T060, T061, T062, T063 | A GitHub token and a completed scan of `main` |
