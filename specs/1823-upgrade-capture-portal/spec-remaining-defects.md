# Feature Specification: Upgrade Capture Portal — Remaining Walkthrough Defects

**Parent feature**: [`1823-upgrade-capture-portal`](./spec.md)

**Feature Branch**: `integration/upgrade-portal-fixes`

**Created**: 2026-08-27

**Status**: Draft

**Source**: A live browser walkthrough of the upgrade capture portal on 2026-08-27.
The walkthrough ran the portal on `127.0.0.1:8056`, ArangoDB on `9529`, and Redis
on `9379`. The organization was Morrison House. The site was Morrison House Site
with 8 devices. No firmware reached a device during the walkthrough.

**Input**: Seven open defects from the walkthrough. Issues #2096, #2097, #2098,
#2101, #2104, #2108, and #2109.

## Why this document exists

The parent specification `spec.md` describes the whole upgrade capture portal.
The walkthrough of 2026-08-27 found defects that the parent specification does not
yet resolve. Eleven sibling defects from the same batch are already fixed on this
branch. This document specifies the seven that remain.

This document extends the parent specification. It does not replace it. It reuses
every term from the parent glossary. A capture, a capture set, an upgrade job, a
site lock, a comparison result, a session owner, and the settle gate all keep the
meaning that `spec.md` gives them.

This document adds three new terms:

- A **standalone pre-check capture** is a capture that names no run. It records the
  state of a site before an upgrade, and no run document yet points at it.
- **Run adoption** is the act of an upgrade start. The start creates a run and then
  links the standalone pre-check capture of that site to the new run.
- A **dangling edge** is a `capture_for_run` edge whose run document does not exist.

### The already fixed sibling defects

This batch stays consistent with the eleven fixed defects. It follows their
patterns. A reader confirms the patterns with `git log main..HEAD`.

| Issue | What it fixed | Pattern this batch reuses |
| --- | --- | --- |
| #2092 | A capture start takes the site lock | #2108 builds on this grant |
| #2093 | The capture identifier field fills | The Result card reads through the document |
| #2094 | A capture shows as tables with a download | The capture view holds the new upgrade control |
| #2099 | The confirm warning reads the reboot option | The saved option travels to the page |
| #2100 | The upgrade pages name the site in words | #2097 reads the same site name and identifier |
| #2102 | A skipped section reports its true device count | #2109 copies this shape for clients |
| #2103 | The comparison offers a full export | The comparison view stays the export source |
| #2105 | (batch sibling) | Consistency only |
| #2106 | The history table fits a row on one line | Consistency only |
| #2107 | The history table names the device type | The run holds no single device type |

---

## User Scenarios & Testing *(mandatory)*

Each user story below resolves one defect. Each story states the operator value,
the priority, an independent test, and acceptance scenarios. Every acceptance
scenario is independently testable.

The stories run in dependency order. Story 1 is the data foundation. Story 2
builds the browser path on top of it. The other stories stand on their own.

---

### User Story 1 - A capture that names no run leaves a clean graph (Priority: P1)

Resolves **#2096**.

An operator starts a capture without an upgrade run. Today the capture invents a
run identifier, writes no run document, and writes an edge to a run that does not
exist. Every later page then reads a run that no document describes. The options
page reports 0 devices. The confirm page reports `Unknown site` and `None saved`.
The stored capture holds all 8 devices the whole time.

The portal must leave a graph that a query can walk. A capture that names no run
must stand alone and must write no dangling edge.

**Why this priority**: This defect is the root cause of #2097 and the blocker of
#2098. The store held six dangling edges and zero runs during the walkthrough. The
graph is the join between a capture and its run, so a broken graph breaks three
pages at once. No other story in this batch is trustworthy until this one lands.

**Independent Test**: Start a capture on a site with devices and name no run. Read
the edge collection. Confirm that the capture wrote no `capture_for_run` edge and
no run document. Then create a run through the documented endpoint and confirm that
every page renders the correct plan.

**Acceptance Scenarios**:

1. **Given** an operator starts a capture and names no run, **When** the capture
   saves, **Then** the portal writes no run document and writes no `capture_for_run`
   edge for that capture.
2. **Given** the store already holds a run and its captures, **When** a query walks
   the graph from the run, **Then** the query reaches every capture of that run and
   finds a run document for each edge.
3. **Given** the store holds six dangling edges from the old behavior, **When** the
   one-time repair runs, **Then** the repair removes every dangling edge, logs each
   removed edge, and leaves the capture documents in place.
4. **Given** a fresh run and its captures, **When** a test reads back every edge of
   the run, **Then** the test finds the run document for each edge.
5. **Given** the run-less capture decision, **When** a reader opens
   `data-model.md`, **Then** the document states the decision and the standalone
   capture identifier rule.

---

### User Story 2 - The browser leads from a capture to an upgrade (Priority: P1)

Resolves **#2098**.

An operator finishes a capture. No control on any page takes the operator to the
upgrade flow. During the walkthrough the operator had to build the run by hand from
the browser console. No template links to the options page, and no script creates a
run. User Story 3 of the parent specification is the whole upgrade half
of this feature, and the browser cannot reach it.

The portal must offer a control that creates the run and opens the options page.

**Why this priority**: The upgrade half of the feature is unreachable without this
control. User Story 2 of the parent also depends on a second capture that only a
run produces. This story unblocks both.

**Independent Test**: Sign in, take the site lock, and run a capture. Press the new
upgrade control. Confirm that the browser reaches the options page and then the
confirm page with no typed address.

**Acceptance Scenarios**:

1. **Given** a verified capture on screen, **When** the operator reads the capture
   result, **Then** the portal shows a control that starts an upgrade for that site.
2. **Given** the operator holds the site lock, **When** the operator presses the
   upgrade control, **Then** the portal creates the run through
   `POST /api/sites/<site_id>/runs` and opens the options page of the new run.
3. **Given** the portal creates the run, **When** the options page loads, **Then**
   the page lists every device of the adopted pre-check capture and names the site.
4. **Given** the operator does not hold the site lock, **When** the operator presses
   the upgrade control, **Then** the portal refuses and names the lock holder.
5. **Given** a run of that site has not finished, **When** the operator presses the
   upgrade control, **Then** the portal refuses and names that run.
6. **Given** the site list is on screen, **When** a browser test drives the journey,
   **Then** the test reaches the confirm page with no typed address.

---

### User Story 3 - The lock banner tells the truth after a capture takes the site (Priority: P1)

Resolves **#2108**.

A capture start now takes the site lock, which #2092 added. The page that starts
the capture never repaints its lock banner. The operator reads `This site is free`
on a site that the same click just locked. The page still offers a `Take the site`
button. A reload then shows the truth. The lock store held the grant the whole time.

The portal must repaint the banner the moment a capture start takes the site.

**Why this priority**: The banner states a false fact about who holds a production
site. A second operator who watches the screen reads that the site is free. The
renewal beat may also fail to start, so a lock a capture took can expire during a
real upgrade. This is a safety defect.

**Independent Test**: Sign in and open the capture page of a free site. Press
`Start the capture` and do not press `Take the site`. Read the banner with no
reload. Confirm that the banner reports the operator as the holder.

**Acceptance Scenarios**:

1. **Given** a capture start grants the site lock, **When** the start succeeds,
   **Then** the banner reports that the operator holds the site with no reload.
2. **Given** the operator now holds the site, **When** the banner repaints, **Then**
   the take control disappears and the release control appears.
3. **Given** a capture start took the lock, **When** the first renewal period
   passes, **Then** the lock survives, because the renewal beat runs.
4. **Given** the session names no owner, **When** a capture start takes no lock,
   **Then** the banner stays unchanged and reports no false hold.
5. **Given** a lock that names no run, **When** the portal writes the lock record,
   **Then** the record holds an empty run value and never the text `None`.
6. **Given** the capture page is on screen, **When** a browser test presses the
   start control, **Then** the test reads the truthful banner with no reload.

---

### User Story 4 - The comparison proves a quiet site kept every client (Priority: P1)

Resolves **#2109**.

The comparison skips a section when the two capture digests match. The client
counters then stay at zero. An operator reads `Clients present: 0` for a site where
every client came back. A quiet site is the site where every digest matches, and a
quiet site is the normal case for a well-run upgrade at night. So the report reads
`0 clients present` exactly when the upgrade went well. The statistics also carry a
`Client return rate`, and a present count of zero drives that rate to zero.

Issue #2102 fixed the same fault for devices in commit `c9431881`. This story
copies that shape for clients, so the two halves match.

**Why this priority**: The present count answers the question the operator asked.
Did the clients come back after the upgrade. The comparison exists to prove an
upgrade did no harm. A false zero on a healthy site defeats the whole comparison.

**Independent Test**: Compare two verified captures of a quiet site whose wired
clients and wireless clients did not change. Confirm that the present count equals
the true client count and that the return rate reads correctly.

**Acceptance Scenarios**:

1. **Given** two captures whose wired clients all match, **When** the portal builds
   the comparison, **Then** the report shows the true count of present wired clients.
2. **Given** two captures whose wireless clients all match, **When** the portal
   builds the comparison, **Then** the report shows the true count of present
   wireless clients. The same holds for the guest list.
3. **Given** a skipped client section, **When** the portal reads the client return
   rate, **Then** the rate reads the corrected present count.
4. **Given** a client section that is truly empty, **When** the portal builds the
   comparison, **Then** the present count reads zero, so the fix hides no real empty
   section.
5. **Given** two identical captures, **When** a test asserts the present count,
   **Then** the count equals the client count and a second test guards against a
   double count.

---

### User Story 5 - Every page reports the same site lock (Priority: P2)

Resolves **#2097**.

The capture page reads the site lock and reports `You hold this site`. The options
page of a run on the same site reports `The portal cannot read the lock state right
now`. The two pages disagree at the same moment. The lock store answered every read.
The options page resolves the site through the run, the run document did not exist,
and no site identifier reached the lock read. The message named the wrong cause, so
it sent the operator to the wrong place.

The site lock contract reserves the unreachable wording for a lock store that does
not answer. A missing site identifier is a different fault and needs a different
message.

**Why this priority**: The fix for #2096 removes the root cause, because a run now
exists and the site resolves. This story adds the distinct message and the test for
the case where a run identifier still resolves to nothing. It protects the operator
from a message that names a healthy store as broken.

**Independent Test**: Open a page whose run identifier resolves to no run. Confirm
that the page reports that it cannot name the site. Confirm that the page does not
report an unreachable lock store.

**Acceptance Scenarios**:

1. **Given** a page that cannot name the site, **When** the page reads the lock,
   **Then** the page reports that it cannot name the site and does not report an
   unreachable lock store.
2. **Given** a page that names the site, **When** the page reads the lock, **Then**
   the page reports the true lock state, and that state agrees with every other page
   in the same session.
3. **Given** a run identifier that resolves to no run, **When** a test opens that
   page, **Then** the test confirms the site-unresolved message and no false
   unreachable message.

---

### User Story 6 - The upgrade options show every choice at once (Priority: P3)

Resolves **#2101**.

The parent specification asks for radio groups. The options page renders two
dropdowns and two checkboxes. The behavior is equivalent, because each control
accepts one choice and every default is safe. A radio group has one advantage on a
page that leads to a firmware write. It shows every choice at once. A dropdown hides
the choices until the operator opens it.

The version list is the exception. One model offered more than 20 versions during
the walkthrough, and a radio group of 20 versions is not readable. A dropdown is the
right control there.

**Why this priority**: The behavior already works and every default is safe. This
story aligns the code with the requirement and improves the reading of the page. It
ranks below the defects that block or falsify a result.

**Independent Test**: Open the options page. Confirm that the strategy group, the
reboot group, and the Junos file action group each render as a radio group. Confirm
that the version controls stay dropdowns. Confirm that every default is unchanged.

**Acceptance Scenarios**:

1. **Given** the options page loads, **When** the operator reads the strategy group,
   **Then** the group renders as a radio group that shows every strategy at once.
2. **Given** the options page loads, **When** the operator reads the reboot group and
   the Junos file action group, **Then** each renders as a radio group with two
   choices.
3. **Given** the options page loads, **When** the operator reads the version
   controls, **Then** the per-device control and the apply-to-every-device control
   stay dropdowns.
4. **Given** a fresh options page, **When** the operator reads the defaults, **Then**
   the strategy defaults to all devices at once, the reboot defaults to yes, and the
   Junos file action defaults to no.
5. **Given** the operator saves the options, **When** the portal builds the option
   body, **Then** the body holds the same three values and the same defaults as
   before this change.

---

### User Story 7 - The comparison view matches the specification (Priority: P3)

Resolves **#2104**.

The parent specification asks for two captures shown side by side. The comparison
page shows one difference table. Each row carries the outcome and the value before
and the value after. The single table is the better reading. It puts the before
value and the after value on one row, so the eye does not travel between two tables.
Two tables side by side repeat every unchanged row twice. They ask the reader to
compare by eye, which is the manual method this feature replaces. The walkthrough
supports the single table, because it marked a roaming client as `moved` and named
both access points on one row.

**Why this priority**: The working code holds the better design. This story aligns
the specification with the code and records the reason. It changes words, not
behavior, so it ranks last.

**Independent Test**: Open the comparison of two captures. Confirm that the page
shows one device difference table and one client difference table. Confirm that each
changed row names the value before and the value after.

**Acceptance Scenarios**:

1. **Given** two saved captures, **When** the operator runs the comparison, **Then**
   the page shows one device difference table and one client difference table.
2. **Given** a client that moved between the two captures, **When** the portal builds
   the comparison, **Then** one row names the outcome `moved` and both access points.
3. **Given** the comparison page and the specification, **When** a reviewer reads
   both, **Then** the two agree, and `spec.md` records the reason for the single
   difference table.
4. **Given** a reviewer wants the side-by-side view, **When** the team adds a
   two-table view, **Then** the difference table stays the default and a control
   switches to the two-table view.

---

### Edge Cases

- **A capture that names a run that does exist.** The capture writes its capture and
  its edge as before. Only a capture that names no run stands alone.
- **A second standalone pre-check of one site.** The upgrade start adopts the most
  recent verified standalone pre-check of the site. An older standalone pre-check
  stays readable by site and by date.
- **An upgrade start after adoption.** The adopted pre-check fills the run pre-check
  field, so the confirm page reports the capture as saved and the begin control can
  enable.
- **A site with a locked run.** The upgrade control refuses and names the unfinished
  run, so an operator never starts a second run on a busy site.
- **A dangling edge that a slow write left behind.** The one-time repair removes it.
  A monitor may report the count of dangling edges as zero after the repair.
- **A quiet site with real zero clients.** The present count reads zero, because the
  client index of the skipped section is empty. The fix never invents a client.
- **A partial client document in a skipped section.** The present count reads the
  larger of the two client index sizes, so a lost row never lowers a proved count.
- **A capture start with no session owner.** The start takes no lock, so the banner
  stays free and the fix paints no false hold.
- **A version list of one value.** The version control stays a dropdown with one
  option, because the control type must not change with the size of the list.

---

## Clarifications

### Session 2026-08-27

The walkthrough issues ask the specifier to choose one answer for three open
decisions. This session records the three choices.

- Q: Issue #2096 asks whether a run-less capture creates its run or stands alone.
  Which answer holds? → A: The capture stands alone. A capture that names no run
  writes no run identifier and no edge. The upgrade start creates the run and adopts
  the pre-check. This keeps the run collection honest, and it fits #2098, where the
  upgrade start is the one control that creates a run. The other answer was rejected,
  because an auto-created unfinished run would make the #2098 control refuse with the
  message that a run has not finished.
- Q: Issue #2101 asks whether the code changes to radio groups or the requirement
  changes to accept any single-choice control. Which answer holds? → A: The code
  changes. The strategy group, the reboot group, and the Junos file action group
  become radio groups. The two version controls stay dropdowns, because a version
  list can hold more than 20 values. FR-017 gains the version-list exception.
- Q: Issue #2104 asks whether the comparison shows one difference table or two
  captures side by side. Which answer holds? → A: The comparison keeps the single
  difference table as the default. The parent specification changes to describe the
  difference table and to record the reason. A two-table view may sit behind a
  control later, and the difference table stays the default.

---

## Requirements *(mandatory)*

### Functional Requirements

These requirements extend the parent requirement set. They continue the number
sequence after FR-095. When the implementation folds them into `spec.md`, keep
these numbers.

#### A clean capture graph (#2096)

- **FR-096**: A capture that names no run MUST NOT invent a run identifier, MUST NOT
  write a run document, and MUST NOT write a `capture_for_run` edge. The capture
  stands alone as a pre-check for its site.
- **FR-097**: The portal MUST NOT write a `capture_for_run` edge whose run document
  does not exist. The portal never writes a dangling edge.
- **FR-098**: A one-time repair MUST remove every existing dangling edge. The repair
  MUST log each removed edge and MUST leave every capture document in place.
- **FR-099**: A test MUST read back every edge of a fresh run and MUST find the run
  document for each edge.
- **FR-100**: `data-model.md` MUST record the run-less capture decision and the
  identifier rule for a standalone capture.

#### The path from a capture to an upgrade (#2098)

- **FR-101**: A verified capture MUST offer a control that starts an upgrade for the
  site of that capture.
- **FR-102**: The upgrade control MUST create the run through
  `POST /api/sites/<site_id>/runs` and MUST carry the new run identifier to the
  options page.
- **FR-103**: When it creates the run, the portal MUST adopt the most recent verified
  standalone pre-check capture of that site. The portal MUST write the
  `capture_for_run` edge with role `pre` and MUST set the run pre-check field.
- **FR-104**: The upgrade control MUST refuse when the operator does not hold the
  site lock, and MUST name the holder.
- **FR-105**: The upgrade control MUST refuse when a run of that site has not
  finished, and MUST name that run.
- **FR-106**: A browser test MUST walk from the site list to the confirm page with no
  typed address.

#### A truthful lock banner on a capture start (#2108)

- **FR-107**: After a capture start grants the site lock, the portal MUST repaint the
  lock banner. The banner MUST report that the operator holds the site, with no reload.
- **FR-108**: After the grant, the portal MUST hide the take control and MUST show the
  release control.
- **FR-109**: `POST /api/sites/<site_id>/captures` MUST report the lock grant in its
  answer when the start took the lock.
- **FR-110**: The portal MUST start the lock renewal beat for a lock that a capture
  start took. A test MUST prove the lock survives past its first renewal period.
- **FR-111**: A capture start that takes no lock, because the session names no owner,
  MUST leave the banner unchanged and MUST report no false hold.
- **FR-112**: The stored lock record MUST hold an empty run value, and never the text
  `None`, when the lock names no run.

#### A truthful client present count (#2109)

- **FR-113**: When a digest match skips a client section, the client comparison MUST
  report the count of present clients of that section. The count follows the shape
  that #2102 set with `DeviceComparison.proved_unchanged`.
- **FR-114**: The proved present count MUST read the client index size of the skipped
  section. It MUST take the larger of the two sizes. A partial document then never
  lowers the count.
- **FR-115**: The client return rate MUST read the corrected present count.
- **FR-116**: A genuine measured zero MUST still read zero, so the fix MUST NOT hide a
  real empty client section.
- **FR-117**: A test MUST compare two identical captures and MUST assert that the
  present count equals the client count. A test MUST guard against a double count.

#### A distinct message for an unresolved site (#2097)

- **FR-118**: A page that cannot name its site MUST report that it cannot name the
  site. The page MUST NOT report an unreachable lock store for this condition.
- **FR-119**: A page that names its site MUST report the true lock state. That state
  MUST agree with every other page in the same session.
- **FR-120**: A test MUST cover a page whose run identifier resolves to no run.

#### Radio groups on the options page (#2101)

- **FR-121**: The portal MUST show the strategy group, the reboot group, and the
  Junos file action group as radio groups. Each radio group accepts one choice.
- **FR-122**: The portal MUST keep the per-device version control and the
  apply-to-every-device version control as dropdowns. A version list can hold more
  than 20 values, which a radio group cannot show well.
- **FR-123**: Each radio group MUST keep the current default. The strategy defaults to
  all devices at once. The reboot defaults to yes. The Junos file action defaults to
  no.
- **FR-124**: The saved option body MUST hold the same three values and the same
  defaults as before this change.

#### The single difference table (#2104)

- **FR-125**: The comparison MUST show one device difference table and one client
  difference table. Each changed row names the value before and the value after.
- **FR-126**: If the portal adds a two-table side-by-side view, the difference table
  MUST stay the default, and a control MUST switch to the two-table view.
- **FR-127**: `spec.md` MUST record the reason for the single difference table.

### Amendments to the parent requirements

The implementation MUST apply these amendments to `spec.md`. The amendments align
the parent requirements with the decisions above.

- **Amend FR-017**. Old text: "The portal MUST show each option group as a radio
  group that accepts exactly one selection." New text: "The portal MUST show the
  strategy group, the reboot group, and the Junos file action group as radio groups
  that each accept one selection. The portal MUST show the version lists as
  dropdowns, because a version list can hold more than 20 values, which a radio
  group cannot show well."
- **Amend FR-065**. Old text: "The portal MUST show the first capture and the second
  capture as two sorted tables side by side." New text: "The portal MUST show one
  device difference table and one client difference table. Each changed row names the
  value before and the value after in one row, so the reader compares no two tables
  by eye."
- **Amend FR-066**. Old text: "Both tables MUST use the same sort order, so that the
  operator sees which rows are missing and which rows are new." New text: "Each
  difference table MUST sort by address, so that a reader finds a device or a client
  by one key. A two-table side-by-side view is optional and MUST NOT replace the
  difference table as the default."
- **Amend User Story 2, Acceptance Scenario 1**. Old text: "Then the portal shows
  both captures as two tables that use the same sort order." New text: "Then the
  portal shows one device difference table and one client difference table, each
  sorted by address, and each changed row names the value before and the value
  after."
- **Amend User Story 2 story text and User Story 3 story text** to match the
  difference table and the version-list exception. The story text MUST NOT contradict
  FR-017, FR-065, or FR-066.

### Data model decision (#2096)

`data-model.md` MUST record the decision that a run-less capture stands alone. The
record MUST state four facts.

1. A capture that names no run writes no run document and no `capture_for_run` edge.
2. A standalone capture builds its own identifier and does not derive it from a run.
3. An upgrade start creates the run and writes the edge at adoption time.
4. A one-time repair removes every dangling edge that the old behavior left.

---

## Web Interface Contract

This batch changes the web interface, so it records the interface behavior and the
test identifiers. The behavior lives in `portal.js`, because the content security
policy is `self` only and blocks an inline script. The identifiers extend
`contracts/ui-testids.md`.

### New test identifiers

| Identifier | Control | Story |
| --- | --- | --- |
| `capture-start-upgrade-button` | The control on the capture result that starts an upgrade | Story 2 |
| `capture-start-upgrade-error` | The region that names the lock holder or the unfinished run | Story 2 |

### Changed test identifiers (#2101)

The three single-choice controls change from a `select` or a `checkbox` to a radio
group. A radio group holds more than one input, so the interaction changes and the
identifiers change with it. The contract records the group identifier and the option
identifiers together.

| Old identifier | New group identifier | New option identifiers |
| --- | --- | --- |
| `upgrade-strategy-select` | `upgrade-strategy-group` | `upgrade-strategy-big-bang`, `upgrade-strategy-canary` |
| `upgrade-reboot-toggle` | `upgrade-reboot-group` | `upgrade-reboot-yes`, `upgrade-reboot-no` |
| `upgrade-junos-file-action-toggle` | `upgrade-junos-file-action-group` | `upgrade-junos-file-action-yes`, `upgrade-junos-file-action-no` |

The version controls keep `upgrade-version-select-all` and
`upgrade-version-select-{mac}`. Their identifiers do not change, because they stay
dropdowns.

### Reused test identifiers

- Story 3 reads `lock-banner`, `lock-state-message`, `lock-take-button`, and
  `lock-release-button`. It adds no identifier.
- Story 4 reads `compare-stat-clients-present` and `compare-stat-client-return-rate`
  through the `compare-stat-{name}` pattern. It adds no identifier.
- Story 5 reads `lock-state-message`. The message gains a sentence for the
  site-unresolved state, and a test reads the sentence.
- Story 7 keeps `compare-device-table` and `compare-client-table`. A later two-table
  view would add `compare-view-toggle`, `compare-before-table`, and
  `compare-after-table`.

### HTTP contract amendments

The implementation MUST record these amendments in `contracts/http-api.md`.

- `POST /api/sites/<site_id>/captures` MUST report the lock grant in the `202`
  answer when the start took the lock. The grant carries the token, the expiry, and
  the state, in the shape that `POST /api/sites/<site_id>/lock` returns.
- Section 5 MUST state that `POST /api/sites/<site_id>/runs` adopts the most recent
  verified standalone pre-check capture of the site. The adoption writes the edge and
  sets the run pre-check field.
- Section 4 MUST state that a capture with a null run identifier writes no run and no
  edge.

### Views, journeys, and assertions

- **Views**: The capture view gains the upgrade control. The options view renders
  three radio groups and two dropdowns. The comparison view keeps the single
  difference table.
- **Critical journey**: An operator moves from the site list, to the inventory, to
  the capture view, to the options view, to the confirm view, with no typed address.
- **Assertions**: A test asserts that the banner reports the holder after a capture
  start with no reload. A test asserts that the present count equals the client count
  for a quiet site. A test asserts that the strategy group shows every choice at once.
- **Artifacts**: A failed interface test produces a screenshot and a trace, as the
  parent stability contract requires.

---

## Key Entities

These entities extend the parent Key Entities. They add fields or behavior. They do
not replace any parent entity.

- **Standalone pre-check capture**: A capture that names no run. It records the state
  of a site before an upgrade. It writes no `capture_for_run` edge. An upgrade start
  adopts it into a run later. It stays readable by site and by date until then.
- **Upgrade run (adoption)**: The run gains one behavior. When an upgrade start
  creates the run, the run adopts the most recent verified standalone pre-check of
  the site. The run then holds the edge and the pre-check field.
- **Client comparison (proved present)**: The client half of the comparison gains a
  proved present count. A digest match proves every client of the section present,
  and the count states how many. The count mirrors `DeviceComparison.proved_unchanged`
  from #2102.
- **Site lock grant (on a capture start)**: The capture start answer gains the lock
  grant. The browser paints the held banner from the grant and starts the renewal
  beat. The stored record holds an empty run value and never the text `None`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

These criteria extend the parent success criteria. They continue the number sequence
after SC-016.

- **SC-017**: After 20 consecutive run-less captures, zero `capture_for_run` edges
  point at a run document that does not exist. (#2096)
- **SC-018**: An operator walks from the site list to the confirm page in the browser
  with no typed address, in under 2 minutes. (#2098)
- **SC-019**: After a capture start takes the site, the banner reports the true holder
  with no reload, in 100 percent of starts. (#2108)
- **SC-020**: A lock that a capture start took survives at least one full renewal
  period with no manual action, in 100 percent of runs. (#2108)
- **SC-021**: A comparison of a quiet site with N clients reports N present clients and
  a 100 percent client return rate. (#2109)
- **SC-022**: A comparison of a truly empty client section reports zero present
  clients, so the fix hides no real empty section. (#2109)
- **SC-023**: The options page and the capture page report the same lock holder for a
  locked site, in 100 percent of reads in one session. (#2097)
- **SC-024**: The options page shows every strategy choice and every switch option with
  no click to open a control. (#2101)
- **SC-025**: The comparison page and `spec.md` agree on the shape of the comparison
  view, and a reviewer finds no contradiction. (#2104)

---

## Assumptions

### Assumptions and defaults

- The eleven sibling defects are fixed on this branch, and their patterns hold. This
  batch stays consistent with them.
- The write path `POST /api/sites/<site_id>/runs` works. The walkthrough proved it,
  because a run created by hand moved the run count from zero to one and every page
  then rendered correctly.
- The lock painter functions `paintLockHeld`, `paintLockFree`, and `startLockBeat`
  already exist in `portal.js`. Story 3 calls the existing functions.
- The compare modules `clients.py`, `statistics.py`, and `diff.py` hold the #2102
  pattern. Story 4 copies that pattern for clients.
- Every option default on the options page is safe today. Story 6 preserves each
  default.

### Constraints

- The Simplified Technical English writing guide governs every word of the interface
  and the documentation.
- The test identifier contract governs every new control and every changed control.
- The content security policy is `self` only. Every behavior lives in `portal.js`,
  and every color lives in a stylesheet.
- The comparison must render a large site in seconds, so the digest skip stays. The
  client fix must count a skipped section without comparing its rows.

### Out of scope

- Any change to the eleven fixed sibling defects.
- Any new upgrade option beyond the three options and the two version controls.
- A run across several sites at the same time.
- A change to the digest skip that makes the comparison render a large site in
  seconds.
- The two-table side-by-side comparison view. The view is optional and this batch
  keeps the single difference table as the default.

### Dependencies

- `POST /api/sites/<site_id>/runs`, which `create_run` in `app/routes/upgrade.py`
  answers.
- `POST /api/sites/<site_id>/captures`, which grants the lock and now reports the
  grant.
- The lock painter and the renewal beat in `portal.js`.
- The compare modules and the #2102 device pattern in commit `c9431881`.
- `contracts/http-api.md`, `contracts/ui-testids.md`, `contracts/site-lock.md`, and
  `data-model.md`, which this batch amends.

---

## Traceability

| Issue | User Story | Priority | New requirements | Amendments | Success criteria |
| --- | --- | --- | --- | --- | --- |
| #2096 | Story 1 | P1 | FR-096 to FR-100 | data-model.md | SC-017 |
| #2098 | Story 2 | P1 | FR-101 to FR-106 | http-api.md | SC-018 |
| #2108 | Story 3 | P1 | FR-107 to FR-112 | http-api.md | SC-019, SC-020 |
| #2109 | Story 4 | P1 | FR-113 to FR-117 | none | SC-021, SC-022 |
| #2097 | Story 5 | P2 | FR-118 to FR-120 | site-lock.md, ui-testids.md | SC-023 |
| #2101 | Story 6 | P3 | FR-121 to FR-124 | FR-017, ui-testids.md | SC-024 |
| #2104 | Story 7 | P3 | FR-125 to FR-127 | FR-065, FR-066, US2 AS1 | SC-025 |
