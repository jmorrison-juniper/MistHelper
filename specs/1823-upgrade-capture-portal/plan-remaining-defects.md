# Implementation Plan: Remaining Walkthrough Defects

**Branch**: `integration/upgrade-portal-fixes` |
**Spec**: [`spec-remaining-defects.md`](./spec-remaining-defects.md) |
**Parent plan**: [`plan.md`](./plan.md)

**Input**: Seven walkthrough defects as user stories US1 through US7, with
functional requirements FR-096 through FR-127.

## Summary

This plan extends the in-flight upgrade portal feature. Eleven sibling defects
are already fixed on this branch. This plan resolves the seven that remain:
#2096, #2098, #2108, #2109, #2097, #2101, and #2104.

The work follows the architecture that the sibling fixes set. It touches the
same modules, keeps the same module boundaries, and uses the same three test
layers. It adds no new subpackage and no new third-party dependency.

The plan groups the seven stories into three phases. Phase A fixes the capture
graph, because every later trust depends on a clean graph. Phase B builds the
upgrade start from a verified pre-check, because it depends on the clean graph
and on run adoption. Phase C holds five independent stories that a reader lands
in parallel: the lock grant on a capture start, the client present count, the
unresolved-site lock message, the radio option groups, and one documentation
alignment.

## Technical Context

**Language/Version**: Python 3.13 or newer. `pyproject.toml` targets `py313`.
The plan adds no new language feature and no new runtime.

**Primary Dependencies**: No change from the parent plan. The work uses Flask,
the existing `python-arango` router, Redis for the site lock, and Playwright for
the browser tests. The plan adds no third-party dependency.

**Storage**: ArangoDB holds the captures, the runs, and the `capture_for_run`
edge collection. Redis holds the site lock only. This plan changes how the edge
collection fills. A run-less capture writes no edge. A run creation writes the
edge at adoption time. A one-time repair removes the dangling edges that the old
behavior left.

**Testing**: `pytest` with three layers. The unit layer stays offline, and an
autouse fixture blocks the network. The contract layer drives the Flask test
client. The Playwright layer drives the browser journeys. This plan adds tests
to each layer and regresses none of the 13842 unit tests or the 167 browser
tests.

**Target Platform**: No change. The container serves the portal under Gunicorn,
and a developer launch uses the Flask development server.

**Project Type**: Web application inside a larger command-line application. The
browser side uses server-rendered templates and a small amount of plain
JavaScript under a `'self'` content security policy. No build step exists and
none is added.

**Performance Goals**: No change from the parent plan. The repair reads once at
start and adds no request-time cost.

**Constraints**: Every asset loads from the application itself, because the
content security policy is `'self'` only. So the capture-start behavior and the
radio-group behavior live in `portal.js`, not in an inline script. Every
function obeys the Five-Item Rule: at most 5 parameters and at most 25 lines.
Every new line carries an inline comment that states why the line exists. Every
action logs at info level before the action and at debug level after it.

**Scale/Scope**: About 32 functional requirements across 7 user stories. The
estimated change is small and additive: one new store repair function, one new
store query, one new field on the client comparison, one new lock state, three
radio groups, and one documentation alignment. The plan opens no new module.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

Constitution version 1.4.0.

| Principle | Verdict | How the design complies |
| --- | --- | --- |
| I. Five-Item Rule | PASS | Each new function takes at most 5 parameters and holds at most 25 lines. A request context object or a dataclass carries any extra value. The repair function and the adoption function each read a small, named input. |
| II. Class-Based Architecture | PASS | Each change extends an existing class or adds a pure function in a named module. The client present count extends `ClientComparison`. The lock state extends the state constants of `select.py`. No wrapper module appears. Variable names use full words. |
| III. Safety-First | PASS | The upgrade start from a capture keeps the typed confirmation of the parent design. The repair only removes an edge whose run is absent, and it reads the run before it removes the edge. Viewing a comparison requires no typing. |
| IV. Full Deployment Pipeline | PASS | The change edits no deployment file, because the port and the container are unchanged. The pipeline runs unchanged. |
| V. Observability and Logging | PASS | Every new log record is ASCII and uses `%s` placeholders. The repair logs each removed edge with the edge key and the missing run key. The adoption logs the capture it adopts. |
| VI. Inline Comments | PASS | The implementation adds a comment on each new line that states why the line exists. The task list enforces this rule for each touched file. |
| VII. Action Logging | PASS | The repair, the adoption, the lock take, and the capture start each log before and after the action. The pair wraps every store write. |

**Post-design re-check**: PASS. The Phase 1 design added no new violation. The
contract deltas keep each request handler within 5 parameters. The data model
adds one field and one state, and it opens no new collection.

## Project Structure

### Documentation (this feature)

```text
specs/1823-upgrade-capture-portal/
├── plan.md                              # Parent plan, unchanged
├── plan-remaining-defects.md            # This file
├── spec-remaining-defects.md            # The spec this plan resolves
├── research-remaining-defects.md        # Phase 0 decisions for the seven defects
├── data-model-remaining-defects.md      # Phase 1 entity deltas
├── data-model.md                        # Parent model, edited for FR-100
└── contracts/
    ├── remaining-defects-deltas.md      # Phase 1 contract deltas
    ├── http-api.md                      # Parent contract, edited for H1..H3
    ├── site-lock.md                     # Parent contract, edited for S1
    └── ui-testids.md                    # Parent contract, edited for U1..U2
```

### Source code (repository root)

The table names the source file for each story and the change it carries. Every
path lives under `src/upgrade_portal/` unless the row states otherwise.

| Story | File | Change |
| --- | --- | --- |
| US1 | `capture/assembly.py` | Add a standalone key builder that reads a capture nonce, not a run. |
| US1 | `app/routes/capture.py` | In `build_job`, set an empty run identifier and a nonce key when the body names no run. |
| US1 | `capture/collector.py` | Let `capture_identity` accept a standalone job and stop raising for an empty run. |
| US1 | `capture/store.py` | Add `repair_dangling_edges`. Call it once from the ensure path. Keep the empty-run guard on the edge writers. |
| US2 | `app/routes/upgrade.py` | In `create_run`, adopt the newest verified standalone pre-check and write the `pre` edge. |
| US2 | `capture/store.py` | Add `latest_standalone_precheck(site_id)`. |
| US2 | `app/assets/templates/capture/capture.html` | Add the start-upgrade control and its error region. |
| US2 | `app/assets/static/js/portal.js` | Post the run, read the run identifier, open the options page, render a refusal. |
| US3 | `app/routes/capture.py` | Thread the lock grant from `capture_conflict` through `launch_capture` into the 202 body. |
| US3 | `runtime/lock.py` | Ensure the stored run value is an empty string, never the text `None`. |
| US3 | `app/assets/static/js/portal.js` | On a capture-start success, read the grant and call the existing lock painters. |
| US4 | `compare/clients.py` | Add `proved_present` and a section-size reader. Fill it in `compare_clients`. |
| US4 | `compare/statistics.py` | Add the proved present count to the client present count. |
| US5 | `app/routes/select.py` | Add the `site_unknown` state. Return it when the site identifier is empty. |
| US5 | `app/assets/templates/partials/lock_banner.html` | Add one sentence for the new state. |
| US6 | `app/assets/templates/upgrade/options.html` | Turn three controls into radio groups. Keep the version dropdowns. |
| US6 | `app/assets/static/js/portal.js` | Read the checked radio for each group. |
| US6 | `app/assets/static/css/portal.css` | Style the radio groups. |
| US7 | `spec.md` | Amend FR-065, FR-066, and US2 AS1 to match the single-table view. |

### Tests (repository root)

| Layer | File | Purpose |
| --- | --- | --- |
| unit | `tests/unit/upgrade_portal/test_capture_standalone_key.py` | The standalone key is unique and writes no edge (US1). |
| unit | `tests/unit/upgrade_portal/test_store_repair_dangling_edges.py` | The repair removes a dangling edge, keeps a live edge, and is idempotent (US1). |
| unit | `tests/unit/upgrade_portal/test_run_adopts_precheck.py` | The run adopts the newest standalone pre-check (US2). |
| unit | `tests/unit/upgrade_portal/test_compare_client_present_counts.py` | The client present count reads proved present with no double count (US4). |
| unit | `tests/unit/upgrade_portal/test_lock_record_empty_run.py` | The stored lock record holds an empty run, never `None` (US3). |
| unit | `tests/unit/upgrade_portal/test_lock_banner_site_unknown.py` | An empty site reads the `site_unknown` state (US5). |
| contract | `tests/contract/upgrade_portal/test_capture_start_lock_grant.py` | The 202 carries the grant after a lock take (US3). |
| contract | `tests/contract/upgrade_portal/test_run_create_adopts_precheck.py` | The run create writes the `pre` edge (US2). |
| contract | `tests/contract/upgrade_portal/test_upgrade_options.py` | The options body keeps the field names under radio groups (US6). |
| e2e | `tests/e2e/upgrade_portal/test_capture.py` | The capture-to-upgrade journey needs no typed address (US2). |
| e2e | `tests/e2e/upgrade_portal/test_upgrade.py` | The radio groups drive the options page (US6). |

## Design notes that the task list depends on

Each note names the verified source line that the change touches. The Phase 0
research document holds the full rationale. This section states the boundary and
the touch point only.

### US1 - The capture graph is honest

The capture route invents a run identifier at `capture.py:618` when the body
names no run. The invented value writes a dangling edge through
`store._link_capture_to_run` (line 1491). The fix keeps the run identifier empty
for a run-less capture and builds the capture key from a nonce in
`assembly.py`. The collector at `collector.py:949` stops raising for an empty
run when the job carries a standalone key. The store edge writers already skip
an empty run, so no edge forms. A new `repair_dangling_edges` in `store.py`
removes the edges that the old behavior left, and it runs once from the ensure
path near `store.py:577`.

**Boundary**: The route decides the identity. The assembly builds the key. The
collector builds the document. The store owns every edge read and write. The fix
respects each boundary and adds no cross-module reach.

### US2 - The upgrade starts from a verified pre-check

The capture page gains a control that starts an upgrade for its site. The
browser posts to `POST /api/sites/<site_id>/runs`, reads the new run
identifier, and opens the options page. No operator types a site address
(SC-018). The server `create_run` (upgrade.py:766) adopts the newest verified
standalone pre-check through a new `store.latest_standalone_precheck` query, and
it writes the `pre` edge to the new run. The existing lock refusal and live-run
refusal stay in front of the adoption.

**Boundary**: The route owns the run creation and the adoption call. The store
owns the query and the edge write. The template and `portal.js` own the browser
step. This story depends on US1, because the adoption trusts a clean graph.

### US3 - The capture start returns the lock grant

`capture.py::take_site_lock` (line 761) already acquires the grant, and
`store_lock_record` (line 789) already stores it. The 202 body does not yet
carry the grant, so the banner never repaints. The fix threads the grant from
`capture_conflict` (line 814) through `launch_capture` into the 202 body. The
browser reads the grant and calls the existing painters `paintLockHeld`
(portal.js:1928) and `startLockBeat` (portal.js:2185). The stored lock record
holds an empty run value, never the text `None` (FR-112).

**Boundary**: The route threads the grant. The runtime lock owns the record
shape. The browser reuses the existing painters and adds none.

### US4 - The client present count reads proved present

The client half mirrors the device fix in commit `c9431881`.
`compare/clients.py` adds `proved_present` to `ClientComparison` and fills it in
`compare_clients` (line 494). A client comparison holds three sections, so the
reader sums the proved present count over the skipped sections, and each section
reads the larger of the two client index sizes. `compare/statistics.py`
(count_clients, line 338) adds the proved present count to the present count. The
return rate corrects itself, because the present count feeds both halves of the
rate.

**Boundary**: The comparison builder owns the field. The statistics reader owns
the roll-up. The `to_dict` contract keeps its two keys, so the page reads the
count through the statistics object.

### US5 - The banner names an unresolved site

`select.py::site_lock_state` (line 614) returns `unknown` for a page that holds
no site identifier, so the banner shows the sentence reserved for an unreachable
store. The fix adds a `site_unknown` state constant, returns it from
`lock_banner_context` (line 1790) when the site identifier is empty, and adds
one sentence to `lock_banner.html`. The `unknown` sentence stays reserved for an
unreachable store (FR-118).

**Boundary**: The route owns the state decision. The template owns the wording.
The change does not touch the `held`, `free`, or `locked` wording.

### US6 - The options page uses radio groups

`options.html` turns the strategy control, the reboot control, and the
Junos-file-action control into radio groups. The two version controls stay
dropdowns (FR-122). The `portal.js` form collector reads the checked radio for
each group. The saved body keeps the same three field names with the same
defaults, so `plain_options` (upgrade.py:835) reads the same values (FR-124).
The old identifiers retire and the new group and option identifiers land in the
same change, so no existing test reads a stale identifier.

**Boundary**: The change lives in the template, the browser collector, and the
stylesheet. The body building does not change.

### US7 - The comparison keeps one difference table

`compare/render.py` already builds one device difference table and one client
difference table, each under a header with a before summary and an after
summary. The work amends `spec.md` FR-065, FR-066, and US2 AS1 to match the
working view, and it records the reason (FR-127). No behavior changes.

**Boundary**: This story is documentation only.

## Phases

**Phase A - The honest graph (US1).** Land the standalone key, the empty run
identifier, the collector change, and the repair. This phase comes first,
because Phase B and the whole comparison trust a clean graph.

**Phase B - The pre-check to upgrade journey (US2).** Land the adoption query,
the run adoption, the capture-page control, and the browser step. This phase
depends on Phase A.

**Phase C - The five independent stories (US3, US4, US5, US6, US7).** A reader
lands each of these in parallel with the others, because they touch separate
modules. US3 touches the lock path. US4 touches the comparison. US5 touches the
banner state. US6 touches the options template. US7 touches the spec prose.

## Complexity Tracking

This plan adds no tracked constitution violation. Each new function stays within
the Five-Item Rule. The plan opens no new subpackage and no new module, so the
child count of `src/` does not rise. The plan adds one field, one state, one
query, one repair function, and three radio groups.

## Risks

1. **The standalone key collides.** A weak key source could reuse `cap--01` and
   overwrite a stored capture. Mitigation: the key reads a fresh `uuid4` nonce,
   and a unit test asserts two standalone captures hold different keys and write
   no edge.
2. **The repair removes a live edge.** A wrong scan could remove an edge whose
   run exists. Mitigation: the repair reads the run document before it removes
   the edge, logs each removal, and a unit test seeds one live edge and one
   dangling edge in the same store. A second run removes zero (SC-017).
3. **The adoption picks the wrong pre-check.** A loose query could adopt a
   post-check or a run-linked capture. Mitigation: the query filters role `pre`,
   an empty run identifier, and a verified state, and it reads the newest by
   date. A unit test seeds several captures and asserts the newest verified
   standalone one wins.
4. **The stored run value reads `None`.** A `str(None)` leak would store the
   text `None` and break FR-112. Mitigation: the capture start builds the lock
   request with an empty string, and a unit test asserts the stored record never
   holds `None`.
5. **The grant threading changes the refusal path.** A careless thread could
   send a grant on a refusal. Mitigation: the grant rides the 202 success only,
   and a contract test asserts a refusal carries no grant and a no-owner start
   carries no grant.
6. **The radio rename breaks existing tests.** The retired identifiers appear in
   `test_upgrade.py` and `test_upgrade_options.py`. Mitigation: the change
   updates the contract test and the browser test in the same commit, so the 167
   browser tests and the 13842 unit tests stay green.
7. **The new lock state leaks the reserved message.** A wrong branch could show
   the unreachable-store sentence for an unresolved site. Mitigation: the
   `site_unknown` branch is distinct, the `unknown` sentence stays reserved, and
   a unit test reads the state for an empty site.
8. **A touched line misses a gate.** Every touched line must carry an inline
   comment, stay within 25 lines and 5 parameters, and log before and after each
   action. Mitigation: the task list names the gate set for each file, and the
   quality gates run in the branch pipeline before merge.

## Dependencies outside this plan

- The eleven sibling fixes already on the branch. This plan builds on the lock
  grant of commit `64476ddc` (#2092) and the device present count of commit
  `c9431881` (#2102).
- The existing browser painters `paintLockHeld`, `paintLockFree`, and
  `startLockBeat` in `portal.js`. The Assumptions section of the spec confirms
  they exist, so US3 reuses them.
- The three product decisions in the spec Clarifications section. They are
  settled input, and this plan does not reopen them.
