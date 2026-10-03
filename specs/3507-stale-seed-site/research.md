# Research: The two stale seed runs move to a site of their own

**Issue**: #3507
**Spec**: [spec.md](./spec.md)

## R1. The cause of the failure

**Finding**: The create call answers 409, because a stale seed run holds the first site.

- The route `POST /api/sites/<site_id>/runs` calls `site_refusal`.
  That function calls `live_run_at_site`, and the helper reads each run of the site through `runs_for_site`.
- `runs_for_site` keeps each record whose `site_id` equals the site.
  The helper `run_is_live` then counts each record that is not in a final state.
- Both stale seed runs hold `site_id` `22222222-2222-2222-2222-222222222222`.
  The state `awaiting_confirmation` and the state `stopping` are not final.
- The helper `_create_run` of `test_existing.py` reads the 409 answer, and it drives the run that the answer names.

**Evidence**: The red run on `main` at `65819b80` gave `1 failed, 7 passed, 2 skipped, 1 error in 21.45s`.
The failure and the error name `/api/runs/e2e-stale-stopping-0001/cancel answered 409`.
The two skips come from `test_the_canceled_run_reads_as_canceled_after_a_reload` and `test_a_live_run_offers_no_retry`.

## R2. Why the default order hides the fault

**Finding**: Pytest does not run the modules in name order.

The collection of `tests/e2e/upgrade_portal` lists 48 modules in two sorted groups.
Modules 1 to 35 form the first group, and modules 36 to 48 form the second group.
Pytest groups the tests by fixture, so `test_bulk.py` is module 27 and `test_existing.py` is module 43.
The bulk cancel test and the reconcile test end both stale seed runs before module 43 starts.

**Consequence**: A new module, a new fixture, or a plugin that changes the order can make the full run fail.

## R3. The repair

**Decision**: Move the two stale seed runs to a new site. This is the first repair that the issue names.

**Rationale**:

- Four other modules create runs on the first site: `test_capture.py`, `test_stop.py`, `test_upgrade.py`, and `test_two_operators.py`.
  A live seed run on the first site is a trap for each of them in another order.
- The move removes the trap for each module at one time.
- The bulk tests are the only readers of the two stale seed runs, so the move changes two tests only.

**Alternative rejected**: Let `test_existing.py` choose a site that holds no seed run.
That change repairs one module and leaves the trap for the other four modules.

## R4. The identifier of the stale site

**Decision**: `35073507-3507-3507-3507-350735073507`, with the name `E2E Stale Runs Site`.

**Rationale**:

- The value has the shape of a site identifier of the cloud, like every other seed site that a lock takes.
- The digits name the issue, so a reader can find the reason.
- No other seed, test, or stand-in read uses the value.
- The stand-in cloud does not list the site, so no row of the site picker moves.

**Check**: The portal does not test the form of a site identifier.
The only check in `persistence/runs.py` refuses an empty value or a value that is not a string.

## R5. One module holds the stale seed

**Decision**: Add `tests/e2e/upgrade_portal/stale_run_seeds.py` with the class `StaleRunSeeds`.

**Rationale**:

- The newer seeds follow this pattern: `OrgEndedSeeds`, `OrgCancelSeeds`, and `LaterCheckSeeds`.
- Today, the two run keys exist twice, once in the conftest and once in `test_bulk.py`.
  One module removes the second copy.
- The class has four methods: `pre_cloud_record`, `stopping_record`, `records`, and `write`.

## R6. The design of the seed-site guard

**Decision**: The direct test reads the real seed, the real site list, and the real rule.

1. It calls the seed writer `_write_fixture_runs` of the browser conftest.
   A recording store keeps each record that the writer saves, and a stand-in application gives an empty context.
2. It reads the listed sites through `stand_in_cloud_read("listOrgSites")`.
3. It decides with the shipped helper `run_is_live` of `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py`.

**Rationale**: Each input comes from the source that the browser server uses, so the guard cannot drift from the seed.

**Measure**: A trial read on `main` found 14 records.
Only the two stale seed runs are live on a listed site.

| Group | Records | Site field |
| - | - | - |
| Single-site runs | 8 | `site_id` |
| Multi-site operations | 6 | `site_ids`, with no `site_id` |

**Alternatives rejected**:

- A copied list of live states. The copy drifts when the state model changes.
- A browser test. It is slow, and it depends on the order that R2 describes.

**Cost**: The import of the browser conftest takes about 5 seconds in a new interpreter.

## R7. The skip of the fixture `scheduled_run_page`

**Decision**: The fixture fails when the run page holds no schedule region.
The message names the run key and the state that the page shows.

**Rationale**: The skip hid this fault, and pytest counts a skip as a pass.
A run that the test built holds the state `created`, so the region must exist.
A run that an earlier test left past the pre-check is also a fault, and the maintainer must see it.

**Scope limit**: The helper `_create_run` keeps its 409 path.
The module `test_capture.py` leaves a live run on the first site today, and `test_existing.py` drives that run in the default order.
A separate issue records that fault.

## R8. The two final seed runs stay on the first site

**Decision**: `e2e-failed-run-0001` and `e2e-stopped-run-0001` stay on the first site.

**Rationale**: Both runs are in a final state, so the live-run guard ignores them.
The retry tests take the lock of the first site, and the retry control reads that lock.

## R9. The multi-site operations

**Finding**: A multi-site operation names its sites in the `site_ids` field, and its `site_id` field holds no value.
The memory store and the network store both filter on the `site_id` field.
So no multi-site operation blocks a single-site create call.
The guard reads the `site_id` field only, which matches the site scan.
