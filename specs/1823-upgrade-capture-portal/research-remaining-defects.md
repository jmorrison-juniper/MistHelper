# Phase 0 Research: Remaining Walkthrough Defects

**Parent plan**: [`plan.md`](./plan.md) | **This plan**: [`plan-remaining-defects.md`](./plan-remaining-defects.md)

**Spec**: [`spec-remaining-defects.md`](./spec-remaining-defects.md)

**Date**: 2026-08-27 | **Branch**: `integration/upgrade-portal-fixes`

## Why this document exists

The parent `research/` folder holds six reference documents for the whole
feature. This document does not repeat them. It records only the decisions that
the seven remaining defects need. The spec already resolved three product
decisions in its Clarifications section. This document resolves the design
unknowns that the code work needs.

Every decision below names the source lines that prove it. A reader confirms
each decision against the current branch.

## Decisions already fixed by the spec

The spec Clarifications section (Session 2026-08-27) closed three product
questions. The plan treats them as settled input.

1. A run-less capture stands alone. It writes no run and no edge.
2. The three single-choice controls become radio groups. The two version
   controls stay dropdowns.
3. The comparison keeps one difference table as the default view.

No `NEEDS CLARIFICATION` marker remains in the spec. No product decision is open.

## Design decision D1 - The standalone capture identifier

**Decision**: A capture that names no run builds its key from a fresh capture
nonce. The key keeps the form `cap-{hex}-01`. The document field `run_id` stays
empty. The nonce is a `uuid4` hex value, and the portal never stores the nonce
as a run identifier.

**Root cause**: `src/upgrade_portal/app/routes/capture.py:618` reads
`run_id = str(body.get(RUN_FIELD) or f"{RUN_PREFIX}{uuid.uuid4().hex}")`. A
start with no run invents a run identifier. That invented value flows into the
capture document `run_id` field. `capture/store.py::_link_capture_to_run`
(line 1491) then builds an edge from `run/{invented}` to the capture. No run
document exists at that key, so the edge dangles.

**Why the key cannot stay tied to the run**:
`src/upgrade_portal/capture/assembly.py::capture_key` (line 414) derives the key
from the run alone. `run_hex("")` returns an empty string, so
`capture_key("", 1)` returns `cap--01`.
`src/upgrade_portal/capture/collector.py::capture_identity` (line 949) records
this collision in its own docstring, and it raises `MISSING_RUN_MESSAGE` for an
empty run for that reason. A standalone capture therefore needs its own key
source that does not read a run.

**Rationale**: The nonce keeps the sanitizer-safe shape that
`data-model.md:45` fixes. The nonce holds no slash and no colon, so a retry
replaces the record instead of duplicating it. The empty `run_id` field means
`store.build_edge` (line 1351), `store.write_edge` (line 1458), and
`store._link_capture_to_run` (line 1516) all skip the edge, because each one
already guards an empty run identifier. So no dangling edge forms.

**Alternatives considered**:

- *Auto-create an unfinished run for every capture.* Rejected. The spec
  Clarifications rejected it. An unfinished run would make the upgrade control
  of #2098 refuse with the message that a run has not finished.
- *Keep `cap--01` for every standalone capture.* Rejected. A second standalone
  capture overwrites the first record, as `collector.py:954` records.
- *Store the nonce in the `run_id` field.* Rejected. The field then names a run
  that no document describes, which is the exact defect.

**Touch points**:

- `capture/assembly.py`: add a standalone key builder that reads a nonce, not a
  run. Keep `capture_key` for the run path.
- `app/routes/capture.py::build_job` (line 606): when the body names no run,
  set `run_id=""` and build the key from a nonce.
- `capture/collector.py::capture_identity` (line 949): accept a job that names
  no run and carries a prebuilt standalone key. Build the document from that key
  instead of raising.

## Design decision D2 - The one-time dangling-edge repair

**Decision**: A repair function lives in `src/upgrade_portal/capture/store.py`.
It scans the `capture_for_run` edge collection. It reads the run document that
each edge names in its `_from` field. It removes every edge whose run document
does not exist. It logs each removed edge. It leaves every capture document in
place.

**Call site**: the store bootstrap path that already ensures the collections and
the edge index. `store.py` holds `_ensure_collection` (line 577) and
`_edge_index_present` (line 632). The repair runs once beside that ensure work
at application start. A second run finds no dangling edge and removes nothing,
so the call is idempotent.

**Rationale**: The store module owns every read and write of the edge
collection. The repair reads and writes that same collection, so it belongs in
the same module. The ensure path already runs once for each worker at start, so
it is the natural home for a one-time repair.

**Alternatives considered**:

- *A separate menu operation.* Rejected for this batch. The walkthrough store
  held six dangling edges. A start-time sweep clears them with no operator
  action, which matches SC-017.
- *A migration script outside the package.* Rejected. The script would lose the
  ruff gate and the mypy gate that `src/` already covers.

**Safety**: The repair reads a run document by key before it removes an edge. It
never removes an edge whose run exists. It logs each removal with the edge key
and the missing run key, so an operator reads the audit trail.

## Design decision D3 - The proved present client count

**Decision**: The client comparison copies the shape of the #2102 device fix in
commit `c9431881`. `ClientComparison` gains a `proved_present` integer.
`compare_clients` fills it from the size of each skipped client section.
`count_clients` adds it to the present count.

**Rationale**: The device half already proved this shape. Commit `c9431881`
added `DeviceComparison.proved_unchanged`, a `_proved_unchanged_count` reader,
and one line in `count_devices`. The client half mirrors each part. The two
halves then read the same way, which the spec asks for.

**The three-section difference**: A device comparison holds one section. A
client comparison holds three sections: wired, wireless, and guest. The reader
therefore sums the proved present count over the skipped sections, not over one
section. Each section count reads the larger of the two client index sizes, as
FR-114 asks.

**The double-count guard**: A skipped section holds no delta. So the read
present count of a skipped section is zero, and the proved present count carries
the whole number. One of the two numbers is always zero for each section, so no
client is counted twice. A unit test asserts this rule (FR-117).

**Touch points**:

- `compare/clients.py`: add `proved_present` to `ClientComparison`, add a
  section-size reader, fill the field in `compare_clients` (line 494).
- `compare/statistics.py::count_clients` (line 338): add the proved present
  count to `present`. The return rate reads the corrected present count with no
  further change, because `present` feeds both the numerator and the
  denominator.

## Design decision D4 - The lock grant on a capture start

**Decision**: The capture start answer carries the lock grant when the start
took the lock. The browser reads the grant and calls the existing painters. The
stored lock record holds an empty run value.

**Rationale**: `capture.py::take_site_lock` (line 761) already acquires the
grant. `capture.py::store_lock_record` (line 789) already stores it. The answer
does not yet carry the grant to the browser, so the banner never repaints. The
fix threads the grant into the 202 body and reads it in `portal.js`.

**The painters already exist**: `portal.js` holds `paintLockHeld` (line 1928),
`paintLockFree` (line 1959), and `startLockBeat` (line 2185). The Assumptions
section of the spec confirms this. Story 3 calls these functions and adds no new
painter.

**The empty run value**: `runtime/lock.py::LockRecord.run_id` (line 564) and
`LockRequest.run_id` (line 727) both hold a run identifier. A capture start
names no run, so the request must carry an empty string. A value of `str(None)`
would store the text `None`, which FR-112 forbids. The capture start builds the
request with an empty run value, and a unit test asserts the stored record never
holds `None`.

## Design decision D5 - The unresolved-site lock state

**Decision**: The lock banner gains a fifth state for a page that cannot name
its site. `src/upgrade_portal/app/routes/select.py` adds the state constant.
`lock_banner_context` (line 1790) returns the new state when the site
identifier is empty. `partials/lock_banner.html` adds one sentence for the new
state.

**Root cause**: `site_lock_state` (line 614) returns `unknown` for a site that
the lock index does not name. `lock_banner_context` reads an empty site
identifier as `unknown` too, because the lock key needs both halves. The banner
then shows the sentence reserved for an unreachable lock store. The two faults
share one message, so the message names a healthy store as broken.

**Rationale**: The site-lock contract reserves the unreachable wording for a
store that does not answer. A missing site identifier is a different fault. A
distinct state gives the operator the true cause and does not send the operator
to check a healthy store.

**Dependency note**: Story 1 removes the root cause, because a run then exists
and the site resolves. The distinct state still lands, so a run identifier that
resolves to nothing reads the correct message (FR-120). The `unknown` sentence
stays reserved for an unreachable store (FR-118 and FR-119).

## Design decision D6 - The radio group body

**Decision**: The three single-choice controls become radio groups. The saved
option body does not change. `plain_options` (upgrade.py:835) reads the same
three field names with the same defaults.

**Rationale**: A radio group submits the same field name as a select control or
a checkbox. So `strategy`, `reboot`, and `junos_file_action` still reach
`plain_options` with the same values. The change lives in the template, in the
`portal.js` form collector, and in the stylesheet. The body building stays
unchanged, which FR-124 asks for.

**The version-list exception**: One model offered more than 20 versions in the
walkthrough. A radio group of 20 values is not readable. So the two version
controls stay dropdowns, which FR-122 asks for.

## Design decision D7 - The single difference table

**Decision**: The comparison view needs no code change. It already builds one
device difference table and one client difference table.
`src/upgrade_portal/compare/render.py` builds a header with a before summary and
an after summary, and it builds one difference table for each kind. The work is
a documentation alignment of `spec.md`.

**Rationale**: The walkthrough supported the single table. The table marked a
roaming client as `moved` and named both access points on one row. The parent
requirements FR-065 and FR-066 still describe two side-by-side tables, so the
implementation amends those requirements to match the working view.

## Open risks carried into the plan

- The standalone key must never collide and must never form an edge. The plan
  carries a unit test for both rules.
- The repair must remove only an edge whose run is absent. The plan carries a
  test for a live edge and a dangling edge in one store.
- The radio identifier rename changes existing tests. The plan updates the
  contract tests and the browser tests in the same change.
