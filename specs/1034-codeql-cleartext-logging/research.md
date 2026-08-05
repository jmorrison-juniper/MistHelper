# Phase 0 Research: Resolve the open clear-text logging alerts

**Feature**: 1034-codeql-cleartext-logging

**Date**: 2026-08-05

**Input**: `specs/1034-codeql-cleartext-logging/spec.md`

This document records the research that removes every unknown from the Technical Context.
Each section states a decision, the reason for the decision, and the alternatives that the
research rejected.

---

## R-001: The exact alert inventory

**Decision**: The feature covers GitHub code scanning alerts 173 through 191. The count is
19. Every alert carries the security severity `high`.

**Evidence**: The command below ran against the repository on 2026-08-05 and returned 19.

```bash
gh api "repos/:owner/:repo/code-scanning/alerts?state=open&per_page=100" \
  --jq '[.[] | select(.rule.id=="py/clear-text-logging-sensitive-data")] | length'
```

| Alert | File | Line | Tracking issue |
| - | - | - | - |
| 173 | `src/device/_utility_commands_action.py` | 283 | #1735 |
| 174 | `src/site/address_audit/address_resolver.py` | 64 | #1733 |
| 175 | `src/site/address_audit/address_resolver.py` | 71 | #1733 |
| 176 | `src/site/address_audit/address_resolver.py` | 85 | #1733 |
| 177 | `src/site/address_audit/address_resolver.py` | 152 | #1733 |
| 178 | `src/site/address_audit/address_resolver.py` | 193 | #1733 |
| 179 | `src/site/address_audit/address_resolver.py` | 202 | #1733 |
| 180 | `src/site/address_audit/address_resolver.py` | 221 | #1733 |
| 181 | `src/site/address_audit/address_resolver.py` | 275 | #1733 |
| 182 | `src/site/address_audit/address_resolver.py` | 368 | #1733 |
| 183 | `src/site/address_audit/address_resolver.py` | 478 | #1733 |
| 184 | `src/capture/packet_capture.py` | 548 | #1734 |
| 185 | `src/capture/packet_capture.py` | 637 | #1734 |
| 186 | `src/capture/packet_capture.py` | 846 | #1734 |
| 187 | `src/capture/packet_capture.py` | 890 | #1734 |
| 188 | `src/ssh/ssh_runner_manager.py` | 110 | #1736 |
| 189 | `src/ssh/ssh_runner_manager.py` | 111 | #1736 |
| 190 | `starlink_dashboard.py` | 1343 | #1737 |
| 191 | `starlink_dashboard.py` | 1344 | #1737 |

**Alternatives rejected**: A manual read of the source files. A manual read misses the
alert number, and the alert number is the only stable key that the GitHub security tab
accepts for a dismissal.

---

## R-002: Does `isatty()` protect the ZTP credential inside a recorded SSH session?

**Decision**: No. An `isatty()` guard blocks a redirected stream and a pipe. It does not
block a recorded session. The guard is necessary. The guard is not sufficient.

**Evidence**: Two tests ran in a POSIX environment on 2026-08-05.

Test 1 redirected the output stream to a file.

```text
plain-redirect: False
```

Test 2 ran a child process under a pseudo-terminal while the parent wrote every byte to a
file. The file recorded the child's own answer.

```text
RECORDED_FILE_HELD: child_isatty= True
```

The container configuration confirms that the second shape applies to the SSH service. The
`Containerfile` writes `PermitTTY yes` and `ForceCommand /usr/local/bin/misthelper-session`
into `/etc/ssh/sshd_config.d/misthelper.conf`. An interactive client requests a
pseudo-terminal, so the server allocates one. The tool then sees an interactive terminal
even when the client records the screen to a file.

**Consequence**: The design must warn the operator on the interactive path. The warning is
the only control that covers the recorded session. Requirement FR-011 already states this
duty.

**Alternatives rejected**: An assumption that a recorded session behaves like a redirected
stream. The test above disproves that assumption.

---

## R-003: The mechanism that protects the ZTP credential

**Decision**: Combine a terminal check with an operator warning. Write the credential with
`sys.stdout.write()` from a new `CredentialConsole` class in `src/utils/console.py`. Do not
write the credential to a file.

**Reason**: The three candidates score as follows.

| Candidate | Blocks a redirected stream | Blocks a recorded session | Creates a credential at rest | Verdict |
| - | - | - | - | - |
| Terminal check with `isatty()` | Yes | No | No | Keep |
| Restricted file under `data/` | Yes | Yes | Yes | Reject |
| Explicit operator warning | No | No | No | Keep |

The restricted file fails for two reasons. First, the container documentation directs the
operator to run `chmod -R 777 data/` before the first run, so the container makes the whole
directory world readable. A file mode of `0600` cannot survive that instruction. Second,
Windows does not honor a POSIX file mode, and Windows is the stated local development
platform. The file would therefore hold a live credential in a readable location on both
platforms. That result is worse than the current screen display.

The terminal check and the operator warning cover different threats, so the design keeps
both. The terminal check satisfies FR-009 and FR-010. The operator warning satisfies FR-011.

**Alternatives rejected**:

- A hash of the credential. Pull request #1732 tried a SHA-256 fingerprint for a related
  alert. CodeQL rejected that change with the query `py/weak-sensitive-data-hashing` at high
  severity. Do not hash a credential for a display label.
- A typed confirmation prompt before the reveal. The prompt does not remove the recording
  risk, because the operator still sees the credential on the recorded screen. The prompt
  also adds a step that acceptance scenario 1 does not describe.

---

## R-004: How the ZTP protection survives the print-to-logging migration of issue #886

**Decision**: Write the credential with `sys.stdout.write()`, not with `print()`. Add a
guard test that fails when the reveal path gains a `logging` call or a `print()` call.

**Reason**: The ruff configuration in `pyproject.toml` does not select the `T20` rule family
today. A comment in that file states the plan for issue #886. The plan is to enable `T20`
and to convert 5053 `print()` sites to logging calls. A `sys.stdout.write()` call is not a
`print()` call, so the `T20` rule never flags it and the mechanical migration never sees it.

The current `# noqa: T201` marker on line 283 is inert, because ruff does not select `T20`.
A comment alone does not stop a mechanical migration. A test does. The guard test is the
enforcement that FR-014 requires.

**Alternatives rejected**:

- A `# noqa: T201` marker with a longer comment. A marker is advice. A migration script can
  drop the marker along with the `print()` call.
- A per-file ignore in `pyproject.toml`. A per-file ignore silences the whole file, and
  FR-008 forbids a suppression that covers a whole file.

---

## R-005: The travel path of the address audit log

**Decision**: The site support package does not hold the address audit log. The street
address in the log reaches `data/script.log` only.

**Evidence**: Menu 101 maps to `DataCollectionManager.generate_support_packages`. The method
`_generate_site_packages` builds one dictionary for each site. The dictionary holds the keys
`alarms`, `events`, `devices`, `device_stats`, `port_stats`, and `speedtests`. The method
then writes `SupportPackage_<site_id>.csv`. No step reads `data/script.log`, and no step
copies the log into the package.

**Consequence**: The spec assumption that the package can hold the audit log is wrong. The
verdict register must record the corrected fact under FR-019. The exposure is narrower than
the spec assumed. The exposure is still real, because an operator attaches `data/script.log`
to a support case by hand.

**Alternatives rejected**: A trust of the spec assumption without a read of the code. The
code read changed the answer, and the register must state the true answer.

---

## R-006: The stance on the ten address alerts

**Decision**: Record one policy. The policy is: no street address at the information level
and no street address at the warning level. The debug level may hold a street address. Every
demoted line gains a site identifier, so the operator keeps the ability to correlate.

**Reason**: FR-018 offers three options. The single policy above combines the first option
and the second option, and it covers all ten alerts with one rule. A single rule is easier
to review than ten separate calls.

The ten alerts split into two shapes.

| Shape | Lines | Action |
| - | - | - |
| The log line carries the cache key, and the cache key is the address | 64, 71, 478 | Log the site identifier in place of the key |
| The log line carries the address inside the message body | 85, 152, 193, 202, 221, 275, 368 | Move the line to the debug level |

The method `AddressResolver._build_query_key` lowercases the query and collapses the
whitespace. The method returns the address itself. The three `key=%s` lines therefore print
the full street address. CodeQL is correct on those three lines.

Line 85 is a warning that reports a failed resolve. A move to the debug level would hide an
operator signal. Line 85 therefore keeps the warning level and gains the site identifier in
place of the query.

**Open dependency**: The dataclass `ResolveCandidates` holds no `site_id` field and no
`site_name` field. The plan adds a `site_id` field to that dataclass. The audit engine
already holds `site.site_id` at the call site, so the value is available. The five-item rule
caps the parameter count of a function at five. The rule does not cap the field count of a
configuration object, and `ResolveCandidates` already holds six fields.

**Alternatives rejected**:

- An acceptance with a written reason and no code change. The address is personal data, and
  the project rule is fix over suppress.
- A new hash of the address as the log key. A hash removes the ability of the operator to
  correlate a log line with a site. The site identifier does that job better.

---

## R-007: The stance on the four capture alerts

**Decision**: Record the verdict `false_positive` for the three MAC address alerts and for
the payload alert.

**Reason**: A MAC address is a device identifier. MistHelper exists to report device
identifiers. The three lines read `logging.debug("Selected and normalized <type> MAC: %s",
<var>)`. CodeQL matched the text `mac` in the variable name. The value is not private data.

The payload alert is a separate case. The payload is built inside `_scan_single_ap_run`. The
dictionary holds the keys `type`, `ap_mac`, `band`, `max_pkt_len`, and the keys that
`_gather_scan_radio_params` returns. Those keys are the channel, the bandwidth, and the
duration. No key holds a secret. The construction is local and closed, so the field list is
complete.

**Alternatives rejected**: A demotion of the three MAC lines to a lower level. The lines are
already at the debug level, so no lower level exists.

---

## R-008: The stance on the two GPS alerts

**Decision**: Record the verdict `accepted_with_rationale` with a stated expiry. The next
review trigger is issue #886.

**Reason**: The two lines sit inside `_dump_diagnostics_location`. The docstring names the
method a diagnostics dump. Both lines call `print()`, so the value reaches the operator
screen and reaches no log file. The CodeQL query assumes a log sink. That assumption does
not hold today.

The assumption will hold after issue #886 converts the two `print()` calls to logging calls.
The acceptance therefore carries an expiry. A guard test enforces the expiry. The test fails
when either line becomes a logging call.

**Alternatives rejected**:

- A permanent acceptance with no expiry. FR-007 requires a next review trigger, and a
  permanent acceptance names none.
- A reduction of the coordinate precision. The operator invokes the dump to read the exact
  position, so a coarse value defeats the purpose of the command.

---

## R-009: The stance on the two SSH runner alerts

**Decision**: Record the verdict `fixed`. Convert both lines to the `echo()` helper.

**Reason**: The method `SSHRunnerManager._echo_plan` calls `logging.warning` three times.
Each call carries the `!?` prefix. That prefix marks a legacy console echo. Spec 1031 added
`echo()` in `src/utils/console.py`. The helper prints the message and logs it at the
information level. The two flagged lines are exactly the shape that spec 1031 replaced.

The third line in the same method reports a command count. That line carries no personal
data, so CodeQL did not flag it. The conversion covers all three lines, because a mixed
method would confuse the next reader.

**Sweep result**: A search of `src/ssh/` found 18 occurrences of the `!?` prefix across 6
files. The table below records the disposition of each group. FR-017 requires this record.

| File | Lines | Disposition |
| - | - | - |
| `src/ssh/ssh_runner_manager.py` | 110, 111, 112 | Convert under this feature |
| `src/ssh/ssh_runner_manager.py` | 307, 323 | Convert under this feature |
| `src/ssh/batch/batch_executor.py` | 307 | Keep. The call already uses the information level |
| `src/ssh/command/command_runner.py` | 282 | Keep. The call writes through an injected writer |
| `src/ssh/runtime/app_runner.py` | 180, 268 | Keep. The prefix belongs to an input prompt |
| `src/ssh/runtime/app_runner.py` | 219, 221, 224, 260 | Keep. The calls already use the information level |
| `src/ssh/runtime/app_runner.py` | 301, 341 | Convert under this feature |
| `src/ssh/runtime/interactive_mode.py` | 70, 151 | Keep. The prefix belongs to an input prompt |
| `src/ssh/shell_execution/shell_executor.py` | 399 | Keep. The line reports a real truncation warning |

**Alternatives rejected**: A change of the log level with no move to `echo()`. That change
would drop the message from the screen, because the console handler runs at the warning
level. Requirement SC-010 forbids the loss of any plan line.

---

## R-010: The location and the shape of the verdict register

**Decision**: Store the register at
`specs/1034-codeql-cleartext-logging/verdict-register.md`. Use one Markdown table with one
row for each alert.

**Reason**: FR-003 requires the feature directory. A Markdown table renders in the GitHub
issue view, so a reviewer reads it without a download. The five tracking issues link to the
file, and the link stays valid after the merge.

The stable anchor is the qualified symbol path plus a quoted fragment of the log template. A
line number drifts after any edit above the line. A symbol path survives a line move. The
contract `contracts/verdict-register.md` states the full column list.

**Alternatives rejected**:

- A CSV file. A CSV file does not render in the GitHub issue view.
- A GitHub project board. A board lives outside the repository, so a reader cannot audit the
  decision from a checkout.

---

## R-011: How the register stays in step with the GitHub security tab

**Decision**: Treat the register as the source of truth for the reason. Treat the security
tab as the source of truth for the state. Reconcile the two with one command.

**Reason**: The two stores hold different facts. The register holds the author, the date,
the anchor, and the reason. The security tab holds the open state and the dismissed state.
A single source cannot hold both, because the security tab has no field for an anchor.

The reconciliation command lists every dismissed alert with its reason. A reviewer compares
that output against the register.

```bash
gh api "repos/:owner/:repo/code-scanning/alerts?state=dismissed&per_page=100" \
  --jq '.[] | select(.rule.id=="py/clear-text-logging-sensitive-data")
        | "\(.number)|\(.dismissed_reason)|\(.dismissed_comment)"'
```

The GitHub API accepts three dismissal reasons. The register maps its verdicts as follows.

| Register verdict | API `dismissed_reason` |
| - | - |
| `false_positive` | `false positive` |
| `accepted_with_rationale` | `won't fix` |
| `fixed` | No dismissal. The next scan closes the alert |

**Alternatives rejected**: A manual dismissal through the web interface with no register
entry. That path loses the anchor and the author, and FR-002 requires both.

---

## R-012: The pull request split

**Decision**: Split the work across four pull requests. Land them in the stated order.

**Reason**: Three forces drive the split.

1. User story 1 is the only story that exposes a live credential. That fix must not wait for
   a triage debate about a street address.
2. User story 4 depends on a coordination check against issue #1721. A wait on that check
   must not block the credential fix.
3. CodeQL reports a new result after a merge to `main`. A smaller pull request returns a
   faster and clearer verdict signal.

| Order | Pull request | Stories | Files |
| - | - | - | - |
| 1 | ZTP credential guard | US1 | `src/utils/console.py`, `src/device/_utility_commands_action.py`, tests |
| 2 | SSH echo conversion | US6 | `src/ssh/ssh_runner_manager.py`, `src/ssh/runtime/app_runner.py`, tests |
| 3 | Address and capture stance | US3, US5 | `src/site/address_audit/`, register rows |
| 4 | GPS stance and register close-out | US4, US2 | `starlink_dashboard.py`, register, issue closure |

The register file receives rows in every pull request. The final pull request checks the
count and closes the five issues.

**Alternatives rejected**: One pull request for the whole feature. A single pull request
would hold a credential fix behind a coordination wait, and it would give one coarse CodeQL
signal for six independent decisions.

---

## R-013: The coordination check against issue #1721

**Decision**: Run the check below immediately before any edit to `starlink_dashboard.py`.
Stop when the check reports an open pull request that touches the file.

```bash
gh pr list --state open --json number,title,headRefName,files \
  --jq '.[] | select(.files[].path=="starlink_dashboard.py")
        | "#\(.number) \(.headRefName) \(.title)"'
```

**Reason**: Issue #1721 reports that `starlink_dashboard.py` configures logging after the
bootstrap. That fix edits the module header. This feature edits
`_dump_diagnostics_location` near line 1343. The two regions do not overlap today. A
concurrent edit still creates a rebase conflict, so the order matters.

**Agreed order**: Issue #1721 lands first when its pull request is open. This feature waits.
This feature lands first when no such pull request is open. The register records the
observed state and the date.

**Alternatives rejected**: A merge of both changes in one pull request. The two changes have
different owners and different tracking issues.

---

## R-014: The Simplified Technical English check

**Decision**: Grade every document that this feature adds with the local linter. Use a
minimum score of 80.

```bash
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 `
  specs/1034-codeql-cleartext-logging/plan.md `
  specs/1034-codeql-cleartext-logging/research.md `
  specs/1034-codeql-cleartext-logging/data-model.md `
  specs/1034-codeql-cleartext-logging/quickstart.md `
  specs/1034-codeql-cleartext-logging/verdict-register.md
```

**Reason**: The `STE compliance` job grades a fixed file list. That list holds
`documentation/ASD-STE100_writing-guide.md` and `tools/ste_linter/README.md`. The job also
triggers only on a change under `documentation/`. A document under `specs/` therefore never
reaches the job. Requirement FR-027 still applies, so the author runs the linter by hand.

**Alternatives rejected**: An extension of the graded file list in the workflow. That change
edits a shared gate, and the spec places any CodeQL configuration change and any workflow
change outside the scope of this feature.
