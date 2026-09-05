# The seam shape audit

Issue #1991 asked for this record. A live run of the upgrade capture portal on
2026-08-24 found six defects in one sitting. Four of them shared one cause. A
stand-in in the test suite answered a simpler shape than the real callee. The
reader agreed with the stand-in, and both disagreed with the cloud. The whole
suite was green through all of it.

This page records every seam of the portal, the call that its route makes, and
the callable that a real portal falls back to. It also states the rule for a new
stand-in.

## How the audit runs

`src/upgrade_portal/app/seam_shapes.py` holds the record. Every seam reader calls
`check_stand_in` the moment it reads an injected stand-in. The function compares
the stand-in against the recorded call and reports a difference at once.

The outcome depends on one environment variable.

| Setting | Where | Outcome of a difference |
| - | - | - |
| `UPGRADE_PORTAL_SEAM_STRICT` set | `tests/conftest.py` sets it for every suite run | The seam raises `SeamShapeError`. |
| The variable unset | Every real portal | The seam writes one error line and keeps working. |

Warning: do not remove the `os.environ.setdefault` line from `tests/conftest.py`.
Without it the suite accepts a stand-in of any shape, and the fault of issue
#1991 returns with no signal.

`tests/unit/upgrade_portal/test_seam_shapes.py` guards the record itself. One
test resolves the fallback of each seam and asserts that the fallback answers its
own recorded call. A record that drifts from the code then fails at once.

## Why the record names the call and not the callee

The first draft of this audit recorded a module function for each seam. Three
seams then reported a difference that was not real, because the seam does not
fall back to the function its name suggests.

The call is the one fact that the stand-in and the fallback must both satisfy.
So the record names the call.

## The seams

| Seam key | Route | The call the route makes | The fallback |
| - | - | - | - |
| `MIST_READER` | select | 1 positional and further keywords | `app/routes/select.py default_cloud_read` |
| `DEVICE_READER` | select | `session`, `org_id`, `site_id` by keyword, or the last two alone | `capture/devices.py read_inventory` |
| `STATISTICS_READER` | select | 2 positional | `capture/devices.py read_device_statistics` |
| `SITE_LOCK_READER` | select | 2 positional | `runtime/lock.py read_site_locks` |
| `CLOUD_LOGIN` | auth | 3 positional | `app/routes/auth.py default_cloud_login` |
| `CLOUD_TOKEN_SESSION` | auth | 1 positional | `app/routes/auth.py default_token_session` |
| `CLOUD_BROWSER_TOKEN_SESSION` | auth | 2 positional | `app/routes/auth.py default_browser_token_session` |
| `CLOUD_TOKEN_IDENTITY` | auth | 1 positional | `app/routes/auth.py default_token_identity` |
| `CAPTURE_RUNNER` | capture | 1 positional | `app/routes/capture.py default_runner` |
| `CAPTURE_LOADER` | capture and review | 1 positional | Two different store readers. See finding 2. |
| `CAPTURE_LISTER` | review | 1 positional | `app/routes/review.py store_capture_rows` |
| `RUN_LISTER` | review | 1 positional | `app/routes/review.py store_run_rows` |
| `RUN_LAUNCHER` | upgrade | 1 positional | `app/wiring.py start_upgrade_run` |
| `STOP_RUNNER` | upgrade | 1 positional | `app/wiring.py cancel_run` |
| `UPGRADE_VERSIONS` | upgrade | 3 positional | `upgrade/options.py read_model_versions` |
| `UPGRADE_OPTIONS_VIEW` | upgrade | 3 positional | `upgrade/options.py build_options_view` |
| `UPGRADE_OPTIONS_BUILDER` | upgrade | 2 positional | None. See finding 3. |

Three further seams hold an object with named methods rather than one callable.
They are `RUN_STORE`, `PRECHECK_ADOPTER`, and `LOCK_STORE_CLIENT`. Each route
already checks the method names of the injected object and falls back when a name
is missing, so no call record fits them.

## The findings

### Finding 1. No stand-in in the suite differs today

The audit ran the guard in strict mode across 3546 portal tests. Every stand-in
answered the call of its seam. The four instances that issue #1991 names were
already fixed, and no new one arrived after them.

This is the recorded list the issue asked for. The list is empty, and the guard
now keeps it empty.

### Finding 2. One key, two routes, two fallbacks

`app/routes/capture.py` and `app/routes/review.py` both read the key
`CAPTURE_LOADER`. Both call it with one capture key, so one call record fits
both. The two fallbacks differ. The capture route falls back to
`capture/store.py load_capture`, and the review route falls back to
`capture/store.py load_capture_for_comparison`.

A test that injects this key replaces the loader of both routes at once. The
record states this, and no call record names a fallback for it.

### Finding 3. Two seams carry a name that promises a different shape

`CAPTURE_LISTER` and `RUN_LISTER` read like the store functions `list_captures`
and `list_runs`. Those functions take a query object. The routes call the seam
with a site key instead, and the fallback is an adapter inside the route that
builds the query. A reader who trusts the seam name would write a stand-in of the
wrong shape.

`UPGRADE_OPTIONS_BUILDER` has no fallback at all. The route hands the run record
and the request body. The module reader `build_options_record` takes four values,
so it cannot serve as the fallback, and `app/wiring.py install_seams` leaves the
key empty on purpose.

No change is proposed for these three. Each one works, and a rename would touch
every test that injects the key. The record now states the true shape, which is
what a stand-in author needs.

### Finding 4. One route still branches on the stand-in shape

`app/routes/select.py call_device_reader` reads the signature of the device
reader and drops the session when the reader names none. The comment there states
the reason. A contract stand-in takes the two identifiers, and the real reader
takes the session first.

That branch is the fault of issue #1991 turned into a permanent rule. It is the
one place where a stand-in is allowed to answer a simpler shape than the cloud.
The record holds both calls, so the guard accepts both and refuses a third.

A later change may remove the branch and move every stand-in onto the real shape.
That work is larger than this audit, because it edits every contract test that
injects a device reader.

## The rule for a new stand-in

Follow these five steps when you add a seam or a stand-in.

1. Start from the real callable. Read its signature before you write the
   stand-in, and give the stand-in the same parameters in the same order.
2. Record the seam in `SEAM_SHAPES`. State the call the route makes, not the
   callee you expect.
3. Give the seam a fallback when one exists. The guard then proves the record
   against real code on every test run.
4. Do not widen a stand-in with `*args` and `**kwargs` to silence the guard. The
   open shape passes every check and proves nothing.
5. If the real callable answers an object rather than a plain list or a plain
   dictionary, copy that object in the stand-in.
   `tests/unit/upgrade_portal/test_privilege_shapes.py` shows the pattern.

## What this audit does not cover

The guard compares the call shape. It does not compare the return shape. Two of
the four defects of issue #1991 were return-shape faults. A stand-in answered a
`list` where the real reader answers a `DeviceRead` that carries its rows under
`records`.

A return-shape check needs a declared type for each seam, and several seams
answer `Any` today. That work belongs to a later issue.
