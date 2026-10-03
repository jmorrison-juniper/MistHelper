# Research: The browser test portal keeps its lock audit trail inside its own run

**Issue**: #3498
**Spec**: [spec.md](spec.md)

## R1: Where the trail path comes from

`src/interfaces/portals/upgrade_portal/runtime/lock.py` line 531 sets `AUDIT_DIRECTORY` to
`data`. The function `_audit_path` reads that constant at call time. It puts
a relative directory under the checkout root, and it keeps an absolute
directory as written. Its docstring states the reason: a test points the
trail at its own directory without a reload of the module.

The writer `_append_audit_line` and the public reader `audit_trail_path` both
call `_audit_path`. One change of the constant therefore moves the writer and
the reader together.

**Decision**: Set `AUDIT_DIRECTORY` to the absolute artifact directory of the
run, inside the test process that serves the portal.

## R2: Who reads the trail

`read_audit_rows` in `src/interfaces/portals/upgrade_portal/compare/lock_audit.py` reads
`audit_trail_path()`. The history route `audit_history_rows` calls that
reader. The Audit log card therefore follows the placement with no other
change.

## R3: Why the process scrub cannot move the trail

`build_child_environment` in `tests/support/upgrade_portal_e2e/environment.py`
removes the credential variables and the output path variables. The audit
directory is a module constant, not a variable, so no scrub reaches it.

## R4: Where the placement happens

| Option | Result |
| - | - |
| A new environment variable that `src/` reads | Rejected. It changes the production code, and a production variable that moves an audit trail is a new risk. |
| A change of the working directory of the child | Rejected. `_audit_path` anchors a relative directory at the checkout root, not at the working directory. |
| An assignment of the constant in `build_stand_in_app`, before `create_app` | Chosen. Only the child process runs that function, and it runs before the first route exists. |

The child runs no pytest fixture, so no `monkeypatch` object exists there.
A direct assignment is the plain form. Ruff rule B010 refuses `setattr`
with a constant name. The type checker does not read `tests/`.

**Decision**: A new class `AuditTrailIsolation` in
`tests/support/upgrade_portal_e2e/records/audit.py` owns the placement. The
module holds one class today, and the support package already holds five
children. `environment.py` already holds more than five members.

## R5: The guard

The existing session fixture `persistent_store_baseline` compares three
header values. `add_e2e_run_header` in `src/interfaces/portals/upgrade_portal/app/factory.py`
sets each value to the fixed text "0". The fixture compares 0 with 0. It
measured no file while the test portal wrote 176 lines to the trail of the
#3492 worktree.

The parent test process can read the checkout trail directly.

**Decision**: A new session fixture counts the lines of the checkout trail.
The fixture `capture_portal_server` depends on it. The first count therefore
runs before the child starts. The second count runs after the child stops.

- A count of lines gives the reader a number of records. The trail is an
  append-only file with one record on each line.
- An absent trail counts 0. A fresh checkout holds no trail.
- A trail that the guard cannot read raises an error. A required guard must
  fail when it cannot read its input.
- A changed count raises an `AssertionError`. The message names the path,
  the two counts, and the repair.
- A `pytest_terminal_summary` hook prints the measure. The fixture also
  writes a JSON record in the artifact directory. This is the pattern of
  `persistent_store_baseline`.

## R6: The journey

A take by the operator who already holds the site answers `resume`, and
`_grant_to_same_owner` writes no take row. A lock that another journey left
behind answers `site_locked`. Issue #3497 holds one such leak.

The lock route and the capture page accept any site key. The capture start
page `/captures/new?site_id=<site>` shows the lock banner of the site in the
query. The function `store_chosen_site` writes the signed browser session
only. The take therefore changes no server record that another journey reads.

**Decision**: The journey uses the site key
`34983498-3498-3498-3498-349834983498`. No other journey and no seed uses
that key. The operator is the operator that every test drives. The journey
opens the capture start page of the site. It presses the take control and
the release control. It then reads the history of the site and the history
with no site. It also reads the run trail from the parent process and names the two
actions of the site.

The site is not in the site list, so no count of the site list changes.

## R7: The main checkout

The production container mounts `./data` of the main checkout at
`/app/data`. A lock action of a real operator during a browser run in the
main checkout changes the count, and the guard then fails.

**Decision**: The guard message states this cause. The documentation of the
fixture states a Caution: run the browser suite in a worktree.

## R8: The red proof

1. Direct tests of the guard decision, with no browser and no network. A
   line written between the two counts fails the guard.
2. A browser run with the guard and without the placement. The existing
   test `test_the_holder_reads_a_held_banner_with_a_release_control` takes
   and releases a lock. The guard then fails, and the pull request links
   that result.