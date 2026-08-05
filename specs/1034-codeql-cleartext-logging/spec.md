# Feature Specification: Resolve the open clear-text logging alerts

**Feature Branch**: `1034-codeql-cleartext-logging`

**Created**: 2026-08-04

**Status**: Draft

**Input**: User description: "Create a feature specification for resolving all 19 open CodeQL `py/clear-text-logging-sensitive-data` alerts in the MistHelper repository."

## Background

Pull request #1723 removed the `py/clear-text-logging-sensitive-data` exclusion from
`.github/codeql/codeql-config.yml` under issue #893. That exclusion hid real alerts. The
changelog then made a wrong claim of zero alerts. A read of `refs/heads/main` found 21
alerts. Pull request #1732 resolved the 2 alerts in `MistHelper.py`. It removed the partial
token preview and used a position label such as `2/3` instead.

19 alerts remain. Five GitHub issues track them. This feature covers all five issues.

| Issue | File | Alerts | Data in the log line |
| - | - | - | - |
| #1733 | `src/site/address_audit/address_resolver.py` | 10 | Physical street addresses |
| #1734 | `src/capture/packet_capture.py` | 4 | 3 MAC addresses and 1 constructed payload |
| #1735 | `src/device/_utility_commands_action.py` | 1 | A live ZTP password on the console |
| #1736 | `src/ssh/ssh_runner_manager.py` | 2 | A target host list and a user name |
| #1737 | `starlink_dashboard.py` | 2 | A GPS latitude and a GPS longitude |

An alert is not proof of a defect. A MAC address is a device identifier that this tool
exists to report. A user name and a host list are operational facts that an operator needs
before a bulk SSH run. This feature therefore records a verdict for each alert. It does not
assume that each alert is a defect.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Protect the ZTP credential (Priority: P1)

An operator asks for the ZTP password of a switch. The tool shows the password on the
screen. The operator reads the password and uses it. The password does not reach any
recording, any file, and any log.

Today the tool prints the password with a direct console write. An inline comment claims
that the tool never logs and never saves the password. That claim holds only on a live
terminal. The claim fails in three known conditions. The container serves SSH on port 2200
with a forced command launch, and a recorded SSH session captures the screen. A redirected
output stream or a pipe captures the screen. Issue #886 plans a mechanical move of every
console write to the logging framework, and that move would send the password to the log
file.

**Why this priority**: This alert is the only one that exposes a live credential. An
attacker who reads a captured session gains device access. Every other alert exposes an
identifier or a location, not a secret.

**Independent Test**: Request the ZTP password with the output stream redirected to a file.
Confirm that the file holds no password. Confirm that the tool states why it withheld the
password. Then request the password on a live terminal and confirm that the password
appears.

**Acceptance Scenarios**:

1. **Given** an operator runs the tool on a live terminal, **When** the operator requests a
   ZTP password, **Then** the tool shows the password and shows a warning that names the
   capture risk.
2. **Given** an operator runs the tool with the output stream redirected to a file, **When**
   the operator requests a ZTP password, **Then** the tool withholds the password from the
   redirected stream and states the reason.
3. **Given** a reviewer reads the source, **When** the reviewer reads the comment near the
   password display, **Then** the comment states the true behavior and names the protection.

---

### User Story 2 - Record one verdict for each alert (Priority: P2)

A security reviewer opens the verdict register. The register holds one row for each of the
19 alerts. Each row holds one verdict of `fixed`, `false_positive`, or
`accepted_with_rationale`. Each row holds a written reason. The reviewer closes the five
issues with confidence, because no alert lacks a decision.

**Why this priority**: The register makes the whole feature auditable. Without the register
a later reader cannot tell a deliberate acceptance from a missed alert. The register also
gates the other stories, because each story ends with a verdict.

**Independent Test**: Count the rows in the register. Confirm the count is 19. Confirm that
each row holds exactly one of the three verdict values and a written reason.

**Acceptance Scenarios**:

1. **Given** the register exists, **When** a reviewer counts the rows, **Then** the count
   equals the alert count of 19.
2. **Given** a row holds the verdict `false_positive`, **When** a reviewer opens the GitHub
   security tab, **Then** the matching alert shows a dismissal with the same written reason.
3. **Given** a row holds the verdict `fixed`, **When** the CodeQL scan runs on `main`,
   **Then** the matching alert no longer appears.

---

### User Story 3 - Decide the stance on street addresses (Priority: P3)

A support engineer receives a support package for a site. The package holds the run log of
the address audit. The engineer expects the package to hold only the data that the support
case needs. The team has made a written decision about whether a street address belongs in
that log.

The address audit exists to compare and correct site addresses, so the log holds addresses
by design. The open question is the travel of that log. Menu 101 builds a support package
for a site, and the package can leave the operator network.

**Why this priority**: This issue holds 10 of the 19 alerts. The data is personal data, and
it travels. The exposure is wider than the other remaining alerts, but the data is not a
credential.

**Independent Test**: Run the address audit. Read the resulting log at the default log
level. Confirm that the log content matches the recorded decision.

**Acceptance Scenarios**:

1. **Given** the team recorded a decision, **When** a reviewer reads the register, **Then**
   the register names the chosen option and the reason.
2. **Given** the decision demotes the address lines to the debug level, **When** the audit
   runs at the default level, **Then** the log holds no street address.
3. **Given** the decision keeps the address lines, **When** a reviewer reads the register,
   **Then** the register states the effect on the support package.

---

### User Story 4 - Decide the stance on GPS coordinates (Priority: P4)

An operator reads the Starlink dashboard log. The log holds the position of a terminal. The
team has made a written decision about whether a precise latitude and a precise longitude
belong in that log.

**Why this priority**: A precise coordinate pair identifies a physical location. The
exposure is smaller than the address exposure, because the log holds 2 alerts and does not
travel in the site support package.

**Independent Test**: Run the dashboard. Read the log. Confirm that the log content matches
the recorded decision.

**Acceptance Scenarios**:

1. **Given** the team recorded a decision, **When** a reviewer reads the register, **Then**
   the register names the chosen option and the reason.
2. **Given** a worker plans an edit to `starlink_dashboard.py`, **When** the worker reads
   the register, **Then** the register names the coordination duty with issue #1721.

---

### User Story 5 - Decide the stance on capture identifiers (Priority: P5)

A network engineer runs a packet capture. The log names the device under capture. The team
has made a written decision for each of the 3 MAC address alerts and for the 1 constructed
payload alert.

The removed exclusion comment argued that CodeQL misreads a MAC address as private data,
because the variable name holds the text `mac`. A MAC address is a device identifier that
this tool exists to report. The constructed payload is a separate question, because a
payload can hold fields that the log must not hold.

**Why this priority**: The 3 MAC address alerts are the strongest false positive
candidates, so the expected security gain is small. The payload alert still needs a real
review, so the story stays in scope.

**Independent Test**: Read the register rows for the 4 alerts. Confirm that each MAC row
states why a device identifier is not private data. Confirm that the payload row names each
field that the payload holds.

**Acceptance Scenarios**:

1. **Given** a MAC address row holds the verdict `false_positive`, **When** a reviewer reads
   the reason, **Then** the reason states that the value is a device identifier.
2. **Given** the payload row exists, **When** a reviewer reads the reason, **Then** the
   reason lists the fields of the payload and states whether any field holds a secret.

---

### User Story 6 - Restore the operator echo contract in the SSH runner (Priority: P6)

An operator starts a bulk SSH run. The tool echoes the target host list, the user name, and
the command count. The operator confirms the plan before the run starts. The echo reaches
the screen through the standard echo path, and the log records the echo at the information
level.

The two flagged lines carry the `!?` prefix. That prefix marks a legacy console echo, and
the lines still call the warning log level. Spec 1031, merged as pull request #1694,
replaced about 170 such echoes with an `echo()` helper. The helper writes to the screen and
logs at the information level. The sweep missed these two lines.

**Why this priority**: The security risk is the lowest of the six stories, because a host
list and a user name are operational facts. The story still corrects a real defect that the
earlier sweep missed.

**Independent Test**: Start a bulk SSH run. Confirm that the plan echo still appears on the
screen with the same text. Confirm that the log records the echo at the information level.
Then search `src/ssh/` for the `!?` prefix and confirm the result matches the register.

**Acceptance Scenarios**:

1. **Given** an operator starts a bulk SSH run, **When** the tool echoes the plan, **Then**
   the screen text matches the earlier text.
2. **Given** the echo runs, **When** a reviewer reads the log, **Then** the log holds the
   echo at the information level and not at the warning level.
3. **Given** the sweep of `src/ssh/` finishes, **When** a reviewer reads the register,
   **Then** the register lists each remaining `!?` echo or states that none remain.

---

### Edge Cases

- What happens when a worker records the verdict `false_positive` and a later code change
  makes CodeQL raise the same alert again? The register must key each row on a stable
  anchor, because a line number drifts.
- What happens when the ZTP password request runs inside a recorded SSH session on port
  2200? The session recording is a capture, so the tool must apply the same protection that
  it applies to a redirected stream.
- What happens when issue #886 moves the ZTP console write to the logging framework? The
  protection must survive that move, or the migration must skip this call site by written
  agreement.
- What happens when a worker adds a suppression without a review date? The suppression is
  incomplete, and the review must reject it.
- What happens when an operator raises the log level to debug after the address lines move
  to debug? The address returns to the log, so the decision must state that condition.
- What happens when two workers edit `starlink_dashboard.py` at the same time under this
  feature and under issue #1721? The edits collide, so the register must name the order.

## Requirements *(mandatory)*

### Functional Requirements

#### Verdict record

- **FR-001**: The team MUST record exactly one verdict for each of the 19 alerts. The
  verdict MUST be `fixed`, `false_positive`, or `accepted_with_rationale`.
- **FR-002**: Each verdict record MUST hold the alert identifier, the source file, the line
  number, a stable anchor that survives a line move, the query name, the verdict, the
  written reason, the author, and the decision date.
- **FR-003**: The team MUST store the verdict register in the feature directory and MUST
  link the register from each of the five tracking issues.
- **FR-004**: For each alert with the verdict `false_positive` or `accepted_with_rationale`,
  the team MUST dismiss the alert in the GitHub security tab. The dismissal reason MUST
  match the written reason in the register.
- **FR-005**: The default action for an alert MUST be a code fix. The team MUST NOT record
  `false_positive` without evidence that the alert misreads the value.

#### Suppression format

- **FR-006**: The team MUST NOT add a bare suppression marker. Each suppression MUST carry a
  written justification.
- **FR-007**: Each suppression justification MUST state the reason, the review date, and the
  next review trigger.
- **FR-008**: A suppression MUST name the single alert that it silences. A suppression MUST
  NOT silence a whole file or a whole rule.

#### ZTP credential protection (issue #1735)

- **FR-009**: The tool MUST NOT write the ZTP credential to an output destination that is
  not an interactive terminal. A terminal check such as `isatty()` is an acceptable
  mechanism.
- **FR-010**: When the destination is not an interactive terminal, the tool MUST withhold
  the credential and MUST state the reason to the operator.
- **FR-011**: When the destination is an interactive terminal, the tool MUST show the
  credential and MUST warn the operator that a session recording captures the screen.
- **FR-012**: If the design writes the credential to a file under `data/`, the tool MUST
  restrict the file permissions to the owner and MUST state the file path to the operator.
- **FR-013**: The tool MUST NOT keep a comment that claims a behavior that the code does not
  provide. The comment near the credential display MUST state the true behavior.
- **FR-014**: The protection MUST hold after the print-to-logging migration of issue #886.
  The feature MUST record the contract that the later migration must honor.

#### SSH runner echo contract (issue #1736)

- **FR-015**: The tool MUST send the target host echo and the user name echo through the
  `echo()` helper that spec 1031 introduced.
- **FR-016**: The converted echo MUST keep the operator-visible text and MUST log at the
  information level instead of the warning level.
- **FR-017**: The team MUST search `src/ssh/` for every remaining `!?` console echo. The
  team MUST convert each one or MUST list each one in the register with a reason.

#### Street address stance (issue #1733)

- **FR-018**: The team MUST record one decision for the address audit log. The options are a
  move from the information level to the debug level, a switch to a site identifier in place
  of the address, and an acceptance with a written reason.
- **FR-019**: The recorded decision MUST state the effect on the site support package that
  menu 101 builds.

#### Capture identifier stance (issue #1734)

- **FR-020**: The team MUST record a verdict for each of the 3 MAC address alerts. A verdict
  of `false_positive` MUST state that the value is a device identifier that the tool exists
  to report.
- **FR-021**: The team MUST review the constructed payload alert as a separate case. The
  reason MUST list the fields that the payload holds and MUST state whether any field holds
  a secret.

#### GPS coordinate stance (issue #1737)

- **FR-022**: The team MUST record one decision for the latitude value and the longitude
  value in the Starlink dashboard log.

#### Coordination

- **FR-023**: The feature MUST NOT edit `starlink_dashboard.py` at the same time as issue
  #1721. The register MUST name the agreed order of the two changes.
- **FR-024**: The feature MUST NOT perform the print-to-logging migration of issue #886. The
  register MUST name the boundary between this feature and that migration.

#### Quality

- **FR-025**: The feature MUST NOT introduce a new alert of the query
  `py/clear-text-logging-sensitive-data`.
- **FR-026**: A change that removes a value from a log line MUST keep the operator able to
  identify the record. The change MUST supply a non-sensitive identifier in place of the
  removed value.
- **FR-027**: Every document that this feature adds MUST follow the Simplified Technical
  English rules in `documentation/ASD-STE100_writing-guide.md`.

### Key Entities

- **Alert**: One CodeQL result for the query `py/clear-text-logging-sensitive-data`. Key
  attributes are the alert identifier, the source file, the line number, a stable anchor,
  and the tracking issue.
- **Verdict**: The decision for one alert. The value is `fixed`, `false_positive`, or
  `accepted_with_rationale`. A verdict holds a written reason, an author, and a date.
- **Verdict register**: The table that holds one verdict record for each alert. The register
  is the single audit record for the feature.
- **Suppression justification**: The written note that accompanies a suppression marker in
  the source. It holds the reason, the review date, and the next review trigger.

## Out of Scope

- The 2 alerts in `MistHelper.py`. Pull request #1732 already resolved them.
- Issue #1721, which reports that `starlink_dashboard.py` configures logging after the
  bootstrap. This feature only records the coordination duty.
- The print-to-logging migration of issue #886. This feature only records the contract that
  the migration must honor for the ZTP credential.
- Any other CodeQL query. This feature covers one query only.
- Any change to the CodeQL configuration file. The exclusion removal is already complete.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The open alert count for the query `py/clear-text-logging-sensitive-data` on
  `main` reaches 0. A code change removes an alert with the verdict `fixed`. A dismissal in
  the GitHub security tab removes an alert with the verdict `false_positive` or
  `accepted_with_rationale`.
- **SC-002**: 19 of 19 alerts hold exactly one verdict in the register.
- **SC-003**: 100 percent of the dismissed alerts show a dismissal reason that matches the
  register text.
- **SC-004**: 100 percent of the surviving suppressions state a reason, a review date, and a
  next review trigger.
- **SC-005**: A ZTP password request with a redirected output stream produces 0 occurrences
  of the credential in the captured output.
- **SC-006**: `src/ssh/` holds 0 unconverted `!?` console echoes, or the register lists each
  remaining one with a reason.
- **SC-007**: All five tracking issues reach the closed state.
- **SC-008**: The feature introduces 0 new alerts of the same query.
- **SC-009**: Each document that this feature adds scores 80 or above with the Simplified
  Technical English linter. The `STE compliance` job enforces that score for the documents
  in its graded list.
- **SC-010**: A bulk SSH run still shows the plan echo on the screen. The operator loses 0
  lines of plan information.

## Assumptions

- The alert list and the line numbers are correct for `main` at the start of the feature.
  Line numbers drift, so the register keys each row on a stable anchor in addition to the
  line number.
- A dismissal in the GitHub security tab is the recorded representation of the verdict
  `false_positive` and of the verdict `accepted_with_rationale`.
- The `echo()` helper that spec 1031 introduced is available to `src/ssh/` and is the correct
  target for the two flagged lines.
- Menu 101 builds the site support package, and that package can hold the address audit log.
- The container serves SSH on port 2200 with a forced command launch, so a recorded session
  can capture the console.
- The project rule of fix over suppress comes from `.github/copilot-instructions.md` and
  governs every verdict in this feature.
- The `STE compliance` job triggers on changes under `documentation/` and grades a fixed
  file list with a minimum score of 80. A document that this feature adds outside that list
  still follows the same rules.
