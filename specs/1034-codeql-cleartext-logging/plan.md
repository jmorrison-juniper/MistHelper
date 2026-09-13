# Implementation Plan: Resolve the open clear-text logging alerts

**Branch**: `1034-codeql-cleartext-logging` | **Date**: 2026-08-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/1034-codeql-cleartext-logging/spec.md`

## Summary

The repository holds 19 open CodeQL alerts for the query
`py/clear-text-logging-sensitive-data`. The alert numbers run from 173 through 191. Five
GitHub issues track them. This feature records one verdict for each alert and fixes every
alert that a code change can fix.

The technical approach has four parts.

1. Add a `CredentialConsole` class to `src/utils/console.py`. The class checks the output
   destination, warns the operator, and withholds the ZTP credential from any destination
   that is not an interactive terminal.
2. Convert the two flagged SSH echo lines to the `echo()` helper that spec 1031 introduced.
3. Apply one address policy to the ten address alerts. The policy keeps a street address out
   of the information level and out of the warning level.
4. Record every decision in a verdict register under the feature directory. Dismiss each
   non-fixed alert in the GitHub security tab with the same written reason.

Research note R-002 changed the design. A test proved that `sys.stdout.isatty()` returns
`True` inside a recorded session. A terminal check alone therefore cannot protect the
credential, and the design adds an operator warning to cover that gap.

## Technical Context

**Language/Version**: Python 3.13 or newer. The `pyproject.toml` file targets `py313`.

**Primary Dependencies**: `mistapi>=0.63.1`. This feature adds no dependency.

**Storage**: No database change. The verdict register is a Markdown file under
`specs/1034-codeql-cleartext-logging/`. The run log stays at `data/script.log`.

**Testing**: pytest. Run every command through `.venv\Scripts\python.exe`. The global Python
interpreter in this workspace is broken.

**Target Platform**: Windows 11 for local development. A Podman container on Linux for the
SSH service and the web portal.

**Project Type**: A single command-line project with a menu registry and a `src/` package
tree.

**Performance Goals**: No performance target. Every change is a log call, a display call, or
a document.

**Constraints**:

- A terminal check does not block a recorded SSH session. See research note R-002.
- The container serves SSH on port 2200 with `PermitTTY yes` and a forced command launch.
- Issue #886 will convert 5053 `print()` calls to logging calls. The credential protection
  must survive that migration.
- Issue #1721 edits `starlink_dashboard.py`. This feature must not edit that file at the
  same time.

**Scale/Scope**: 19 alerts across 5 source files. The feature touches 5 source files, adds
5 test files, and adds 6 documents.

## Constitution Check

*GATE: This section passed before Phase 0 research. The section passed again after Phase 1
design.*

| Principle | Assessment | Result |
| - | - | - |
| I. Five-item rule | `CredentialConsole.reveal` takes 2 parameters and stays under 25 lines. The class holds 1 public method. The dataclass `ResolveCandidates` gains a seventh field, and the rule caps a parameter count, not a field count | Pass |
| II. Class-based architecture | The new code lives in the `CredentialConsole` class. The class is not a wrapper, because it owns the terminal check and the warning text | Pass |
| III. Safety-first | The feature exists to keep a credential out of a log. The design adds no input call, so it needs no `safe_input()` call. Contract clause C-9 records the rule for any future prompt | Pass |
| IV. Full deployment pipeline | Each pull request runs the pipeline. See `quickstart.md` check 9 | Pass |
| V. Observability and logging | Every new log call uses ASCII text and `%s` formatting. No new log call carries a secret | Pass |
| VI. Inline comments | Every changed line gains an inline comment. Every touched block gains comments on its uncommented lines | Pass |
| VII. Action logging | `CredentialConsole.reveal` logs before the write and after the write. Neither line holds the secret | Pass |
| Fix over suppress | The default action is a code fix. The feature adds no new `# noqa` marker and no new `# nosec` marker. A dismissal carries evidence and a review trigger | Pass |

The Complexity Tracking table below holds no entry, because the design raises no violation.

## Project Structure

### Documentation (this feature)

```text
specs/1034-codeql-cleartext-logging/
├── plan.md                          # This file
├── spec.md                          # The authoritative input
├── research.md                      # Phase 0 output. 14 research notes
├── data-model.md                    # Phase 1 output. 6 entities
├── quickstart.md                    # Phase 1 output. 12 validation checks
├── verdict-register.md              # Created during implementation. 19 rows
├── contracts/
│   ├── verdict-register.md          # The register format. 11 clauses
│   └── credential_console.md        # The credential primitive. 9 clauses
└── tasks.md                         # Created by /speckit.tasks. Not part of this plan
```

### Source Code (repository root)

```text
src/
├── utils/
│   └── console.py                   # Holds echo(). Gains the CredentialConsole class
├── device/
│   └── _utility_commands_action.py  # Alert 173. Calls CredentialConsole.reveal
├── ssh/
│   ├── ssh_runner_manager.py        # Alerts 188 and 189. Converts to echo()
│   └── runtime/
│       └── app_runner.py            # Two extra "!?" echoes from the sweep
├── site/
│   └── address_audit/
│       ├── address_resolver.py      # Alerts 174 through 183. Applies the address policy
│       └── models.py                # ResolveCandidates gains a site_id field
└── capture/
    └── packet_capture.py            # Alerts 184 through 187. No code change

starlink_dashboard.py                # Alerts 190 and 191. No code change

tests/unit/
├── test_credential_console_contract.py       # The guard test for issue #886
├── test_credential_console_behavior.py       # The reveal branch and the withhold branch
├── test_ssh_runner_echo_plan.py              # The echo() conversion
├── test_address_resolver_log_redaction.py    # The address policy
└── test_starlink_location_dump_guard.py      # The expiry guard for the GPS acceptance
```

**Structure Decision**: The feature keeps the existing single-project layout. The new class
joins `src/utils/console.py`, because that module already owns console output. A new module
would add a fifteenth file to `src/utils/`, and the existing module is the correct semantic
home.

## The order of work

The feature ships as four pull requests. Research note R-012 records the reason.

| Order | Pull request | Stories | Blocked by |
| - | - | - | - |
| 1 | ZTP credential guard | US1 | Nothing |
| 2 | SSH echo conversion | US6 | Nothing |
| 3 | Address and capture stance | US3, US5 | Nothing |
| 4 | GPS stance and register close-out | US4, US2 | Issue #1721. See check 12 |

User story 1 holds priority P1 and ships alone. The story is independently testable, it
touches no file that another story touches, and it is the only story that protects a live
credential.

The remaining stories must not land as one pull request. Two reasons drive the split. User
story 4 waits on a coordination check against issue #1721, and a wait must not block a
security fix. CodeQL reports a result after a merge to `main`, so a smaller pull request
returns a clearer signal for each decision.

Each pull request adds its own rows to the verdict register. Pull request 4 checks the row
count, runs the reconciliation command, and closes the five tracking issues.

## The verdict register

**Location**: `specs/1034-codeql-cleartext-logging/verdict-register.md`.

**Columns**: `Alert`, `Issue`, `File`, `Line`, `Anchor`, `Verdict`, `Reason`, `Author`,
`Decided`, `Review`, `Trigger`. Contract clause C-1 fixes the order.

**Key**: The `Alert` column holds the GitHub alert number. The number is the only key that
the security tab accepts for a dismissal.

**Anchor**: The `Anchor` column holds the qualified symbol path and a quoted fragment of the
log template. A line number drifts after an edit above the line. A symbol path does not.

**Synchronization**: The register is the source of truth for the reason, the author, the
date, and the anchor. The GitHub security tab is the source of truth for the open state and
the dismissed state. One command reconciles the two. Contract clause C-8 states the command.

## The proposed verdicts

The register records the final decision. The table below states the proposal that each pull
request confirms. Research notes R-006 through R-009 hold the evidence.

| Alerts | File | Proposed verdict | Basis |
| - | - | - | - |
| 173 | `_utility_commands_action.py` | `fixed` | R-003. A terminal check and a warning replace the bare print |
| 174, 175, 183 | `address_resolver.py` | `fixed` | R-006. The cache key is the address. The line logs the site identifier instead |
| 176 | `address_resolver.py` | `fixed` | R-006. The warning keeps its level and logs the site identifier |
| 177 through 182 | `address_resolver.py` | `fixed` | R-006. The lines move to the debug level |
| 184, 185, 186 | `packet_capture.py` | `false_positive` | R-007. A MAC address is a device identifier that the tool exists to report |
| 187 | `packet_capture.py` | `false_positive` | R-007. The payload holds a type, a MAC, a band, a packet length, a channel, a bandwidth, and a duration. No field holds a secret |
| 188, 189 | `ssh_runner_manager.py` | `fixed` | R-009. The lines move to the `echo()` helper at the information level |
| 190, 191 | `starlink_dashboard.py` | `accepted_with_rationale` | R-008. The lines print to an operator-invoked dump and reach no log. The acceptance expires when issue #886 converts them |

## How to verify the result

The full check list lives in `quickstart.md`. The single command that proves the outcome
follows.

```bash
gh api "repos/:owner/:repo/code-scanning/alerts?state=open&per_page=100" \
  --jq '[.[] | select(.rule.id=="py/clear-text-logging-sensitive-data")] | length'
```

The command returned `19` on 2026-08-05. That value is the baseline. The expected value at
the end of the feature is `0`.

The end state has four parts.

1. The open alert count for the query is `0`.
2. The register holds 19 rows, and every row holds a verdict and a reason.
3. Every dismissed alert carries a comment that matches its register reason.
4. The five tracking issues are closed.

## Test strategy

A CodeQL count is not a unit test. The count reflects a scan of `main` after a merge, and it
proves the outcome of the whole feature. A unit test proves the branch logic of one change
before the merge. The feature needs both.

| Story | Automated test | What the test proves | What the test cannot prove |
| - | - | - | - |
| US1 | `test_credential_console_behavior.py` patches `sys.stdout.isatty` and asserts the two branches | The withhold branch writes no secret. The reveal branch writes the warning first | The real terminal path. A test harness has no terminal, so check 5 needs a human |
| US1 | `test_credential_console_contract.py` reads the two source files | The reveal path holds no `print(` call and no `logging.` call that takes the secret | That a future migration honors the contract. The test fails the migration instead |
| US2 | No automated test | Nothing | The register is a document. A reviewer counts the rows with check 2 and reconciles with check 3 |
| US3 | `test_address_resolver_log_redaction.py` captures the log records | The information level and the warning level hold no street address. The debug level still holds one | That no other module logs the address. Check 7 covers the run |
| US4 | `test_starlink_location_dump_guard.py` reads the source | The two lines still call `print()` and not `logging` | That the coordinates are safe. The test only enforces the stated expiry |
| US5 | No automated test | Nothing | The verdict is a triage decision with no code change. Research note R-007 holds the evidence |
| US6 | `test_ssh_runner_echo_plan.py` patches `echo` and captures the log | The method calls `echo()` and logs at the information level. The text is unchanged | The screen output of a live run. Check 6 covers that |

The coverage gate needs 80 percent. Every new module carries a test, so the feature raises
the covered line count and cannot lower the ratio.

## Coordination duties

**Issue #1721**: The issue reports that `starlink_dashboard.py` configures logging after the
bootstrap. Run check 12 in `quickstart.md` immediately before any edit to that file. When
the check prints an open pull request, stop and wait. Issue #1721 lands first in that case.
Record the observed state and the date in the register. Requirement FR-023 requires the
record.

**Issue #886**: The issue plans a mechanical migration of 5053 `print()` calls to logging
calls. This feature performs no part of that migration. The boundary is as follows. This
feature owns the credential reveal path and the two GPS dump lines. Issue #886 owns every
other `print()` call. The guard tests in `test_credential_console_contract.py` and
`test_starlink_location_dump_guard.py` fail when the migration crosses that boundary. The
register names the boundary. Requirement FR-024 requires the name.

## Complexity Tracking

> This section holds an entry only when the Constitution Check reports a violation.

The Constitution Check reported no violation. This table is empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | Not applicable | Not applicable |
