# Feature Specification: Take a post-check capture of each site of a multi-site upgrade

**Issue**: #3244
**Feature Branch**: `feat/3244-multisite-postcheck`
**Status**: Implemented
**Found by**: the multi-site journey of #3200, finding F-upj-multisite-012

## Problem

A single-site run takes a second capture after the client phase ends. The
run page then links to the comparison of the two captures. The operator uses
that comparison to prove that the devices and the clients came back after the
upgrade.

A multi-site operation takes a pre-check capture of each site (#3243). The
phase watch follows each cascade phase to the end (#3245). But no code takes a
second capture, and the progress page shows no comparison link. The operator
of a multi-site upgrade therefore has no proof that each site came back.

## User Story 1 (P1): The operator compares each site after a multi-site upgrade

**Acceptance scenarios**:

1. **Given** a multi-site operation whose four phases ended, **When** the
   phase watch ends, **Then** the portal takes one post-check capture of each
   site before the watch reads "Finished".
2. **Given** a post-check capture that verified, **When** the operator reads
   the progress page, **Then** the row of that site links to the capture and
   to the comparison with the pre-check capture of that site.
3. **Given** the comparison link of one site, **When** the operator opens it,
   **Then** the comparison page shows the pre-check capture and the post-check
   capture of that site.
4. **Given** a post-check capture that did not verify, **When** the watch
   ends, **Then** the row of that site reads "Failed", and the watch reason
   names that site.

## User Story 2 (P2): The operator follows the captures while they run

**Acceptance scenarios**:

1. **Given** a running phase, **When** the operator reads the progress page,
   **Then** each site row of the post-check card reads "Waiting".
2. **Given** a running post-check stage, **When** the page polls, **Then** the
   page repaints each row with no reload, and the poll continues.
3. **Given** a watch that ended with no capture for a site, **When** the
   operator reads the page, **Then** that row states why no capture exists.

## User Story 3 (P2): A cancel still leaves the evidence

**Acceptance scenarios**:

1. **Given** a running operation, **When** the operator cancels it, **Then**
   the portal takes the post-check capture of each site before the watch
   reads "Stopped". The single-site driver does the same after a stop
   (FR-038g).

## Requirements

- **FR-001**: After the last phase ends, the walk MUST take the post-check
  captures before it writes the finished watch state.
- **FR-002**: After a cancel, the walk MUST take the post-check captures
  before it writes the stopped watch state. This rule applies to a cancel
  during the start wait and to a cancel during a phase.
- **FR-003**: Each post-check capture MUST be a capture with no run, the
  ordinal 2, and the role `post`. The key MUST have the form
  `cap-<32 hexadecimal digits>-02`.
- **FR-004**: Each capture MUST read its site at the tier of the pre-check
  capture of that site. If the operation holds no pre-check capture of that
  site, the capture MUST read tier 2.
- **FR-005**: The walk MUST take the captures one site at a time, in the
  order of the site selection.
- **FR-006**: The operation record MUST keep one row for each site in the
  field `post_captures`. Each row holds the site, the site name, the tier,
  the state, the capture key, and one sentence.
- **FR-007**: The row state MUST be one of `running`, `verified`, `failed`,
  `held`, or `skipped`.
- **FR-008**: A resumed walk MUST keep each row in a final state. A resumed
  walk MUST take a new capture for a row that holds `running`.
- **FR-009**: If the post-check mode is `manual`, the walk MUST take no
  capture, and each row MUST hold `held`.
- **FR-010**: If the cloud accepted no firmware write for a site, the walk
  MUST take no capture of that site, and its row MUST hold `skipped`.
- **FR-011**: If one capture fails, the walk MUST continue with the next
  site. If no phase failed, the finished watch MUST name the first failed
  capture as its reason.
- **FR-012**: The progress page MUST show a card with one row for each site.
  Each row shows the site name, the state, one sentence, the capture link,
  and the comparison link.
- **FR-013**: The comparison link MUST appear only when the post-check row
  holds `verified` and the operation holds a pre-check capture of that site.
  The link MUST open `/compare?before=<pre-check key>&after=<post-check key>`.
- **FR-014**: The status poll MUST return the same rows in the field
  `postchecks`. The page MUST repaint the rows on each poll with no reload.
- **FR-015**: The phase watch MUST stay active while the stage runs, so the
  poll continues until the last capture ends.
- **FR-016**: A record that holds no phase watch MUST show no post-check
  card.
- **FR-017**: No log line may hold the cloud session or the capture job.
- **FR-018**: A cancel request that arrives during the stage MUST NOT stop
  the stage. The captures then show the state of each site after the phases.

## Non-goals

- A button that starts a held capture. `config.read_post_check_mode` names
  the manual mode as a future switch, and the single-site mode has no button
  either.
- The renewal of the site locks. Issue #3333 holds that change. The capture
  contract allows a capture with no site lock.
- The single-site defect #3355. A failed single-site capture still lets the
  run read complete. Issue #3355 holds that repair.
- Two captures at the same time. One API token serves every operator, so the
  stage reads one site at a time.
