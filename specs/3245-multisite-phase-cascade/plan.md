# Implementation Plan: The cascade phases of a multi-site upgrade

**Issue**: #3245
**Spec**: [spec.md](./spec.md)

## Technical context

- Python 3.13, Flask 3, and the `mistapi` SDK 0.63.
- No new dependency.
- The capture portal runs gunicorn with one worker and four threads. A registry of threads in one process is therefore safe.
- The store is the run store of the upgrade routes. Each write uses `compare_and_set_run` on `record_version`.

## Research result

The single-site driver calls `_submit(record)` and then `_cascade(record)`. The upgrade submitter sends every plan in one step. The cascade then runs `PhaseSettleGate.settle` for each phase in turn. The single-site cascade is therefore a watch in the phase order. It is not a write order. The multi-site mode gets the same watch. Issue #3332 holds the write order question.

## Design

### New package `src/upgrade_portal/upgrade/org_cascade/`

| Module | Class | Purpose |
| - | - | - |
| `record.py` | `OrgPhaseTargets`, `OrgPhaseEntries`, `OrgPhaseStore` | Collect the devices of one phase from the child jobs. Build and update the phase entries. Write the record through a bounded compare-and-set. |
| `readers.py` | `OrgStatisticsReader`, `BudgetSleep`, `OrgSettleAnchors` | Read the statistics of one phase. Stretch the round wait. Read the anchors before the first write. |
| `walk.py` | `OrgCascadeDeps`, `OrgCascade`, `OrgCascadeRegistry` | Walk the four phases. Keep one watch thread for each operation. |
| `view.py` | `OrgPhaseView` | Build the public phase fields of the page and the poll. |

The package holds five children with `__init__.py`, which obeys the 5-item rule.

### Record fields

| Field | Shape | Writer |
| - | - | - |
| `settle_anchors` | `{mac: {"uptime_before": int or null, "last_seen_before": int or null}}` | The submission route, one time. |
| `phases` | Four entries in the single-site shape. | The watch. |
| `phase_watch` | `{"state": text, "note": text, "reason": text or null, "anchor_note": text}` | The submission route and the watch. |

The watch never adds a key to `child["targets"]`, because `_plan_from_child` rebuilds `DeviceTarget(**target)` from each entry. Each compare-and-set write stamps `updated_at` on the record itself, so the watch fields hold no time.

### The walk

1. Read the record. If the watch state is `finished`, `stopped`, or `failed`, return.
2. If the start time is in the future, write `waiting_for_start`. Sleep in slices of `gate.POLL_INTERVAL_SECONDS` (20 seconds), and read the stop request after each slice. The site lock life bounds the count of slices.
3. Write `running`.
4. For each phase in `PHASE_ORDER`:
   1. Skip a phase that already ended. A resumed watch keeps its result.
   2. If `cancellation.requested` is true, write `stopped` and return.
   3. Apply the client gate rule with `driver.client_gate_open`.
   4. Collect the devices. Skip an empty family.
   5. Write the phase state `waiting` with its total.
   6. Build one `PhaseSettleGate` and call `settle`.
   7. If the cloud did not accept some devices, fail the phase and name the count in the note.
   8. Write the outcome, and keep the first failure reason.
5. Write `finished` with the first failure reason.

### The statistics reads

- `read_fleet_statistics` gets the keyword `device_type`, with the default `STATISTICS_TYPE`. The single-site call does not change.
- If every device of one phase sits at one site, the reader reads that site with the type `all`. Otherwise it reads the organization with the family type.
- The reader counts the pages of the last read.
- `BudgetSleep` multiplies each wait by `max(1, (1 + pages) / 2)`. One round costs one event read and the statistics pages. The single-site budget assumes two calls in each round.

### The route hooks

- `_submit_aggregate`: after the site locks and before the service submission, `_prepare_phase_watch` reads the anchors and stores them with the initial phases and the watch state. After the submission, `_start_phase_watch` starts the watch.
- `_refresh_aggregate`: after the status read, call `_start_phase_watch`. The page and the status poll both call `_refresh_aggregate`, so this call resumes a watch after a restart.
- `_aggregate_record_view`: add `phases`, `phase_watch`, and `phase_active`.
- `aggregate_summary`: set `current_phase` to the label of the waiting phase.
- The config key `ORG_SETTLE_ANCHOR_READER` lets a test replace the anchor read. The config key `ORG_CASCADE_STARTER` lets a test replace the thread start.

### The page

- A new partial `partials/org_phase_list.html` holds the "Cascade phases" card. `org_progress.html` includes it after the status card. `progress.html` does not change.
- The unit test `test_org_phase_list_parity.py` renders the real single-site page and the real partial, and compares the phase cells, the poll sentence, and the reason line. This test keeps the two pages equal without a change to the single-site template.
- `portal.js`: `paintOrgUpgradeStatus` calls `paintRunPhases(document, status)` and paints the watch line. The poll stops only when the aggregate state ended and `phase_active` is false.

## Decisions

- Two config seams replace the cloud edge in the tests. The anchor read and the thread start are the only calls that a test replaces.
- A stop puts each waiting phase entry back to `pending`. No thread waits for that phase after the stop, so the page must not show a wait.
- The registry keeps one watch thread for each operation in one process. The capture portal runs one gunicorn worker, so one process holds every thread.
- A resumed walk keeps each phase that ended as `settled`, `skipped`, or `failed`. It continues with the first phase that did not end.
- One event reader serves the whole walk, as in the single-site wiring. The failure events of an early phase then stay in the event window of a later phase.
- The submission writes the anchors with one compare-and-set try. A failed read or a lost race leaves no watch fields, and the upgrade continues (FR-002).
- The watch thread starts only after the submission ends and the cloud accepts a child job. Until then, the exclusion count of a phase can change.
- The stand-in cloud of the browser tests gives each job a new identifier. A cancel in one test then cannot end a job of a later test.
- The shared browser step `OrgCancelSteps.cancel` waits for the page reload that the page script starts after a cancel. A test reload that runs first cuts off the reload of the script.

## Test plan

| Layer | File | Proof |
| - | - | - |
| Unit | `tests/unit/upgrade_portal/test_org_cascade_record.py` | The target collection, the excluded states, the reboot copy, the entries, the bounded compare-and-set. |
| Unit | `tests/unit/upgrade_portal/test_org_cascade_readers.py` | The site read and the family read, the page count, the budget factor, the anchor read and its failure. |
| Unit | `tests/unit/upgrade_portal/test_org_cascade_walk.py` | The rehearsal walk, the skip, the client gate, the scheduled start, the stop, the resume, the call budget, one thread. |
| Unit | `tests/unit/upgrade_portal/test_org_cascade_view.py` | The public fields and the current phase label. |
| Unit | `tests/unit/upgrade_portal/test_org_phase_list_parity.py` | The multi-site card and the single-site page show the same phase cells. |
| Contract | `tests/contract/upgrade_portal/test_org_phase_watch_contract.py` | The submission stores the anchors and starts the watch. The parser reads a broken confirmation body as empty text, and the route then stores nothing. The poll resumes the watch. The page renders each cell. |
| E2E | `tests/e2e/upgrade_portal/test_org_phase_cascade_journey.py` | The browser shows the section, and the screenshots prove each cell. |

The single-site phase tests must pass with no change.

## Risks

- The watch thread shares the cloud session of the operator. The single-site driver does the same.
- A compare-and-set conflict with a route write makes one write fail. The route writes again on the next poll, and the watch tries again at once.
- The watch holds no site lock. Issue #3333 adds the renewal.
