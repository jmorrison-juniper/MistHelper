# HTTP API Contract

**Feature**: 1823-upgrade-capture-portal
**Base**: The application serves on port 8056 by default. `CAPTURE_PORT` overrides
the port.

Read `README.md` in this folder first. It defines the error envelope, the
cross-site request forgery rule, and the status codes.

---

## 1. Authentication and organization

### `GET /` — landing

Redirects to `/auth/signin` when no session exists. Redirects to `/select/org`
when a session exists.

### `GET /auth/signin` — sign-in page

Returns the sign-in form. Requires no session.

### `POST /auth/signin` — sign in

| Item | Value |
| --- | --- |
| Body | `{ "email": "<string>", "password": "<string>" }` |
| 200 | `{ "next": "/select/org" }` |
| 200 | `{ "next": "/auth/twofactor" }` when the cloud asks for a second factor |
| 400 | `bad_credentials` |
| 429 | `rate_limited` |

The portal never logs the body. The portal never stores the password. The portal
holds the resulting cloud session in a per-user registry keyed by the session
owner.

### `GET /auth/twofactor` — second factor page

Returns the second factor form. Requires no session, because the sign-in is not
complete and the registry holds nothing yet.

### `POST /auth/twofactor` — second factor

| Item | Value |
| --- | --- |
| Body | `{ "code": "<string>" }` |
| 200 | `{ "next": "/select/org" }` |
| 400 | `bad_two_factor_code` |

### `POST /auth/signout` — sign out

Clears the session and drops the cloud session from the registry. Returns `200`
with `{ "next": "/auth/signin" }`.

### `GET /select/org` — organization list

| Item | Value |
| --- | --- |
| Query | `q` optional text filter, `offset` default 0 |
| 200 | The organization picker page |

A managed service provider account sees every organization it may reach. The
picker filters the list and divides it into pages inside the portal itself. One
page holds 25 rows. `q` carries the same name as the site list filter. `offset`
carries the same name as the history page.

### `POST /select/org` — choose an organization

| Item | Value |
| --- | --- |
| Body | `{ "org_id": "<uuid>" }` |
| 200 | `{ "next": "/select/site" }` |
| 403 | `org_not_permitted` |

---

## 2. Site selection and inventory

### `GET /select/site` — site list

Returns the site picker for the chosen organization. Each row shows the site name,
the device count, and the lock state.

### `GET /select/site/<site_id>` — site inventory page

Returns the device list of one site as a page. Answers `404` and an empty picker
when the chosen organization holds no such site.

### `GET /api/sites` — site list as JSON

| Item | Value |
| --- | --- |
| Query | `q` optional text filter |
| 200 | `{ "sites": [ { "site_id", "name", "device_count", "locked_by", "lock_state" } ] }` |
| 400 | `org_not_chosen` when neither the path nor the session names an organization |
| 403 | `org_not_permitted` |

`GET /api/orgs/<org_id>/sites` reaches the same handler and answers the same body.
The two paths are one endpoint, not two. `/api/sites` reads the organization from
the session. `/api/orgs/<org_id>/sites` reads it from the path, and the path value
wins.

The row carries five names, not four. The field `locked_by` is `null` when no lock
exists. It holds an email address when a lock exists. The field `lock_state` holds
`free`, `locked`, or `unknown`. The word `unknown` means the lock store did not
answer, which `contracts/site-lock.md` asks a read to survive. Reading this
endpoint never needs the lock.

### `GET /api/sites/<site_id>/inventory` — inventory for the capture view

| Item | Value |
| --- | --- |
| 200 | `{ "devices": [ ... ], "counts": { ... } }` |
| 404 | `site_not_found` |

This call reads the physical view with `vc=True`, so every chassis member appears.
The device statistics call passes `type="all"`, because the default returns access
points only.

---

## 3. Site lock

### `POST /api/sites/<site_id>/lock` — take the lock

| Item | Value |
| --- | --- |
| Body | `{ "confirm": "<string or absent>" }` |
| 200 | `{ "lock_token": "<opaque>", "expires_in": 3600, "state": "acquired" }` |
| 400 | `org_not_chosen` when the session names no organization |
| 400 | `confirmation_required` with `details.needed_text` when a takeover needs the word `CONFIRM` |
| 409 | `site_locked` with `details.actor_email` and `details.cooldown_remaining` |
| 503 | `lock_store_unreachable` |
| 503 | `takeover_audit_failed` when the portal cannot record a takeover, which leaves the site with the current holder |

`state` holds `acquired`, `resume`, or `takeover`. `resume` means the same
operator and the same browser returned to a lock they already hold.

The first attempt sends no `confirm` value. If the lock is free, the portal grants
it. If the lock is held and the cooldown has passed, the portal answers `400` with
`confirmation_required`. The browser then asks the operator to type `CONFIRM` and
repeats the call with that value.

This endpoint is the only one that names the lock holder and the cooldown. The
capture refusal in section 4 and the run refusals in section 5 carry less. Each of
those two sections states what its own refusal carries.

### `POST /api/sites/<site_id>/lock/heartbeat` — extend the lock

| Item | Value |
| --- | --- |
| Body | `{ "lock_token": "<opaque>" }` |
| 200 | `{ "expires_in": 3600 }` |
| 409 | `lock_lost` when the token no longer matches |

### `DELETE /api/sites/<site_id>/lock` — release the lock

| Item | Value |
| --- | --- |
| Body | `{ "lock_token": "<opaque>" }` |
| 200 | `{ "released": true }` |
| 409 | `lock_lost` |

The browser sends the token alone, and both bodies hold that one field. The lock
module needs the whole lock record. The signed session holds that record under the
key `site_lock_records`, indexed by site. Each route reads the stored record,
compares the token the browser sent, and passes the whole record to the lock
module. A token that differs answers `lock_lost` before the store is read. The
browser therefore never holds the record, and no operator address reaches the page
from these two routes.

---

## 4. Capture

### `POST /api/sites/<site_id>/captures` — start a capture

| Item | Value |
| --- | --- |
| Body | `{ "tier": 2, "run_id": "<string or null>", "role": "pre" }` |
| 202 | `{ "capture_id": "<string>", "status_url": "/api/captures/<id>/status" }` |
| 400 | `bad_tier` when `tier` is not 2 or 3 |
| 404 | `site_not_found` when the chosen organization holds no such site |
| 409 | `site_locked` when a different operator holds the site lock |
| 409 | `pre_check_locked` when the named run already sent firmware |

The portal starts the work in the background and answers at once. `tier` defaults
to 2.

The `pre_check_locked` refusal protects the one reading of a site before its
upgrade. The capture identifier derives from the run alone, so a repeat pre-check
of the same run carries the identifier of the first one and replaces that stored
document in place. Before the run sends firmware, that replacement is what the
operator asked for, and the portal accepts it. After the run sends firmware, the
new reading describes upgraded devices, and the comparison would then measure the
upgraded site against itself. The route refuses there, so no worker starts and no
store write ever opens. The rule reads the run state, so a stopped run and a
failed run both keep the pre-check they hold.

The rule guards the pre-check half alone. The run driver owns the post half and
gives it the second ordinal, so a post-check writes its own document and collides
with nothing.

The lock gates this endpoint for a second operator only. The operator who holds
the lock still starts their own capture. The documented journey takes the lock
first and the pre-check second, so a presence-only test would refuse that operator
their own capture.

This refusal carries no `details` object, so it names no holder. The lock endpoint
in section 3 does name the holder. The difference between the two answers is real
and has no stated reason.

An unreachable lock store does not stop a capture. `contracts/site-lock.md`
reserves the fail-closed `503` for the lock acquire, because that path leads to a
firmware write. The same document asks a read to continue when the store is
unreachable, and it states that a capture reads only.

### `GET /api/captures/<capture_id>/status` — capture progress

| Item | Value |
| --- | --- |
| 200 | See the body below |
| 404 | `capture_not_found` |

```json
{
  "capture_id": "cap-ab12cd34-01",
  "state": "collecting",
  "percent": 40,
  "sections": {
    "devices": "done", "clients_wired": "running",
    "clients_wireless": "pending", "clients_guest": "pending",
    "extras": "skipped", "alarms": "pending"
  },
  "counts": { "devices_total": 128, "clients_wireless": 0 },
  "partial_reasons": [],
  "verified": false,
  "message": "Reading wired clients."
}
```

The browser polls this endpoint every 30 seconds. The portal does not use
server-sent events.

### `GET /api/captures/<capture_id>` — the whole capture

| Item | Value |
| --- | --- |
| 200 | The capture document, as `data-model.md` section 3 defines it |
| 404 | `capture_not_found` |
| 409 | `capture_not_verified` when the portal has not read the key back |
| 409 | `schema_version_too_new` when a later version of the portal wrote the capture |

### `GET /captures/<capture_id>` — the capture page

| Item | Value |
| --- | --- |
| Query | `site_id`, which the page needs when the capture does not exist yet |
| 200 | The human view of one capture |

The page renders for a capture the portal does not know. It renders an empty
panel in that case, and the browser polls nothing.

The literal segment `new` names a capture that does not exist yet. The inventory
page links to `/captures/new?site_id=<site_id>`, which is the first write step of
the journey. The page reads the site from the query, because a capture that does
not exist names no site. A known capture names its own site, and the page then
ignores the query value.

The query value fills two fields. It fills the target of the start control, and
it fills the site of the lock banner. Without it the page renders with no site,
and the start control posts to no site.

---

## 5. Upgrade run

### `POST /api/sites/<site_id>/runs` — create a run

| Item | Value |
| --- | --- |
| Body | `{ "tier": 2 }` |
| 201 | `{ "run_id": "run-<hex>", "state": "created" }` |
| 400 | `org_not_chosen` when the session names no organization |
| 400 | `site_not_chosen` when neither the path nor the session names a site |
| 409 | `site_locked` with `details.actor_email` when a different operator holds the site lock |
| 409 | `upgrade_already_running` with `details.run_id` when a run of this site has not finished |
| 500 | `run_write_failed` when the run store refused the write |
| 503 | `lock_store_unreachable` when the portal cannot read the site lock |

`POST /api/runs` reaches the same handler and answers the same body. The two paths
are one endpoint, not two. The path above names the site. `POST /api/runs` reads
the site from the signed session.

### `GET /api/runs/<run_id>/versions` — available versions

| Item | Value |
| --- | --- |
| 200 | `{ "by_model": { "<model>": ["<version>", ...] } }` |
| 404 | `run_not_found` |

### `POST /api/runs/<run_id>/options` — choose the upgrade options

| Item | Value |
| --- | --- |
| Body | See below |
| 200 | `{ "targets": [ ... ], "warnings": [ ... ] }` |
| 400 | `bad_option` |

```json
{
  "targets": [ { "mac": "<string>", "version_target": "<string>" } ],
  "reboot": true,
  "junos_file_action": false,
  "strategy": "big_bang",
  "start_time": null
}
```

`junos_file_action` maps to the cloud field that this feature never names in its
own model. `reboot` applies to switches and gateways only, because the cloud
reboots an access point on its own.

`start_time` is optional and holds whole epoch seconds. An empty value starts the
upgrade at once. The portal answers `400 bad_option` for a moment that is already
past by more than 120 seconds, because the cloud would write firmware immediately
while the operator believes the work waits. The portal answers `400 bad_option`
for a moment more than one year ahead, because the cloud accepts that value and
the upgrade never runs. The start call replays the stored moment without these
two checks, so a run that waits for confirmation past its own start time still
upgrades.

### `POST /api/runs/<run_id>/start` — start the upgrade

| Item | Value |
| --- | --- |
| Body | `{ "confirm": "CONFIRM" }` |
| 202 | `{ "state": "upgrade_submitting" }` |
| 400 | `confirmation_required` when `confirm` is wrong |
| 404 | `run_not_found` |
| 409 | `pre_capture_missing` when no verified pre-check exists |
| 409 | `site_locked` with `details.actor_email` when a different operator holds the site lock |
| 409 | `upgrade_targets_missing` when the saved plan names no device |
| 500 | `run_write_failed` when the run store refused the write |
| 503 | `lock_store_unreachable` when the portal cannot read the site lock |

The portal refuses to start unless a verified pre-check capture exists.

The portal also refuses to start a plan that names no device. An operator who
opens the options page and saves it without a chosen version saves an empty
plan. A start of that plan would send nothing and would still report a complete
run, so the operator would read a site that never changed as an upgraded site.

An earlier version of this table named `lock_lost` here. The route raises
`site_locked` instead. That is the same code that section 3 and section 4 use for
this class of refusal. The code `lock_lost` belongs to the heartbeat and to the
release, where a token stops matching a stored lock.

A repeat start answers `202` with the state the run already holds. FR-038 accepts
one begin action for each run, so the second call sends nothing.

### `GET /api/runs/<run_id>/status` — run progress

| Item | Value |
| --- | --- |
| 200 | See the body below |
| 404 | `run_not_found` |

```json
{
  "run_id": "run-ab12cd34",
  "state": "settling_switches",
  "phase_order": ["gateways", "switches", "aps", "clients"],
  "phases": [
    { "name": "gateways", "state": "settled", "settled_at": "<iso>" },
    { "name": "switches", "state": "waiting", "settled": 4, "total": 9,
      "note": "The portal could not read the device statistics." }
  ],
  "targets": [
    { "mac": "<string>", "name": "<string>", "device_type": "switch",
      "state": "rebooting", "version_before": "<string>",
      "version_target": "<string>", "version_after": null }
  ],
  "stop_request": null,
  "pre_capture_id": "cap-ab12cd34-01",
  "post_capture_id": null,
  "message": "Waiting for 5 switches to return."
}
```

The body carries a tenth key, `lock`, only when the run record holds a lock entry.
A healthy run carries no such key, and the key reports a fault alone.

Each phase entry carries six keys, whatever the example above shows. The view
fills `name`, `state`, `settled`, `total`, `settled_at`, and `note` on every
phase, so the page reads one shape. The key `note` names the source that the
last poll round could not read. It holds empty text when every read answered,
and it never holds null.

```json
{
  "lock": { "state": "lost", "message": "<sentence>", "at": "<iso>" }
}
```

The field list of `lock` is a whitelist. The view copies `state`, `message`, and
`at`, and copies no other name. A later writer can add a lock token or an operator
address to that entry on the run record, and neither value reaches the browser.
The key sits last in the body, so it never hides a key that this contract fixes.

The browser polls this endpoint every 30 seconds.

### `POST /api/runs/<run_id>/stop` — stop the run

| Item | Value |
| --- | --- |
| Body | `{ "confirm": "STOP" }` |
| 200 | See the body below |
| 400 | `confirmation_required` when `confirm` is not exactly `STOP` |
| 404 | `run_not_found` |
| 409 | `site_locked` with `details.actor_email` when a different operator holds the site lock |
| 409 | `run_not_stoppable` when the run already finished |
| 503 | `lock_store_unreachable` when the portal cannot read the site lock |

```json
{
  "state": "stopping",
  "outcome": {
    "cancelled": ["<mac>", "<mac>"],
    "already_writing": ["<mac>"],
    "no_cancel_available": [],
    "message": "The portal cancelled 2 devices. 1 device is writing firmware and will finish."
  }
}
```

The stop never interrupts a device that is writing firmware. The cloud states that
the cancel is best effort and that a device in mid-flash may still complete. The
`message` field says that plainly to the operator.

FR-038i binds this control to the operator who holds the site lock. The lock check
runs before every other check of this route, so a second operator reads
`site_locked` even when the run already finished.

### The unreadable lock store

The three routes above write. Each one answers `503` `lock_store_unreachable`
when the portal cannot read the site lock. `contracts/site-lock.md:116` fixes
that rule and forbids a fallback lock. The body names no operator, because the
portal read no holder and any address there would be a guess.

A read keeps the opposite rule. `GET /api/sites` marks the row `unknown`, and the
capture start in section 4 still starts. A capture writes no firmware, and a page
writes nothing at all. Only an upgrade route writes firmware to a device, so only
an upgrade route fails closed.

### `GET /runs/<run_id>/options` — the options page

Returns the page that picks a target version for each device. Requires a session.
A run that the store does not hold renders an empty page instead of a `404`.

### `GET /runs/<run_id>/confirm` — the confirm page

Returns the page that reads the typed word `CONFIRM`. Requires a session. A run
that the store does not hold renders a locked page instead of a `404`. FR-035
unlocks the start control only when the record names a verified pre-check.

### `GET /runs/<run_id>` — the run page

Returns the live run view with the phase list and the device table.

---

## 6. Comparison and history

### `GET /api/comparisons` — compare two captures

| Item | Value |
| --- | --- |
| Query | `before=<capture_id>&after=<capture_id>` |
| 200 | The comparison body |
| 400 | `capture_site_mismatch` when the two captures name different sites |
| 409 | `capture_not_verified` |
| 409 | `schema_version_too_new` when a later version of the portal wrote either capture |

```json
{
  "before": { "capture_id": "...", "started_at": "..." },
  "after":  { "capture_id": "...", "started_at": "..." },
  "site_name": "...",
  "org_name": "...",
  "statistics": {
    "devices_unchanged": 120, "devices_changed": 8,
    "devices_added": 0, "devices_removed": 0,
    "devices_version_changed": 8,
    "clients_present": 1840, "clients_moved": 96,
    "clients_added": 12, "clients_missing": 30,
    "client_return_rate": 0.985,
    "elapsed_seconds": 2280.0
  },
  "device_deltas": [ ... ],
  "client_deltas": [ ... ],
  "skipped_sections": ["extras"]
}
```

The `statistics` object holds 11 names, as data-model.md section 7.4 requires.
An earlier version of this example listed 9 and omitted
`devices_version_changed` and `elapsed_seconds`. Read the object as a superset,
because a later release can add a name.

The return rate is `(clients_present + clients_moved) / (clients_present +
clients_moved + clients_missing)`, rounded to 3 places. For the numbers above
that is `1936 / 1966`, which is `0.985`. An earlier version of this example
printed `0.984`, because it cut the digits instead of rounding them.

`skipped_sections` lists each section whose digest matched, so the comparison did
no further work there.

### `GET /compare` — the comparison page

Takes the same two query values and renders the human view.

### `GET /api/comparisons/export` — download a comparison

| Item | Value |
| --- | --- |
| Query | `before`, `after`, `format=csv` or `format=json` |
| 200 | A file attachment |
| 400 | `bad_format` |
| 409 | `schema_version_too_new` |

This route shares its reader with `GET /api/comparisons`, so it refuses a
capture that a later release wrote. An export of a capture the portal cannot
read would write a wrong file.

### `GET /api/sites/<site_id>/history` — capture history

| Item | Value |
| --- | --- |
| Query | `limit` default 25, `offset` default 0 |
| 200 | `{ "captures": [ ... ], "total": 0 }` |

Each row carries eight names: `capture_id`, `role`, `started_at`,
`capture_status`, `actor_email`, `stored_size_bytes`, `device_count`, and
`client_count`. The size satisfies FR-032b, which asks the portal to record the
stored size because retention is unlimited. The first six names come from this
contract. The portal adds the two counts from the stored `counts` map, because a
history without them says little about the site.

The route holds `limit` between 1 and 200, and `offset` between 0 and 1000000.
This contract sets no bound, and an unbounded limit lets one request read the
whole unlimited store.

### `GET /api/sites/<site_id>/runs/history` — run history

| Item | Value |
| --- | --- |
| Query | `limit` default 25, `offset` default 0 |
| 200 | `{ "runs": [ ... ], "total": 0 }` |

The path sits below the site and below `runs`. `POST /api/sites/<site_id>/runs`
in section 5 already means "create a run", and one path with two meanings would
confuse a reader.

This endpoint shapes no row. It answers each stored run row as the store holds
it, which the capture history above does not do. Reading this endpoint never
needs the lock. No history route reads the lock, because a read that waited for a
lock would hide the record from the operator who watches another upgrade.

### `GET /history` — the history page

Returns the human view of the same list, for one site or for the organization.

---

## 7. Health

### `GET /healthz` — liveness

| Item | Value |
| --- | --- |
| 200 | `{ "status": "ok", "version": "<string>" }` |

Requires no session. Reports no credential and no organization name.

### `GET /readyz` — readiness

| Item | Value |
| --- | --- |
| 200 | `{ "status": "ready", "database": "ok", "redis": "ok" }` |
| 503 | `{ "status": "not_ready", "database": "unreachable", "redis": "ok" }` |

The database check performs a real write and a real read-back against a scratch
key. A check that only opens a connection would report ready while every write
silently failed.

One answer serves every caller for 5 seconds. The endpoint needs no session,
because an orchestrator probe cannot sign in, so any client that reaches the
port can call it. Without the cache each call drives one document store write
and one lock store write.

The window is shorter than the interval an orchestrator uses, so a genuine probe
always finds the answer expired and always reaches both stores. Two calls inside
the same window read one probe and report the same body. A caller that needs a
fresh reading must wait out the window. The window must stay shorter than the
shortest probe interval in use.
