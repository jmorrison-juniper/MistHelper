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

Returns the organization picker. A managed service provider account sees every
organization it may reach. The picker paginates and filters in the portal itself.

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

### `GET /api/sites` — site list as JSON

| Item | Value |
| --- | --- |
| Query | `q` optional text filter |
| 200 | `{ "sites": [ { "site_id", "name", "device_count", "locked_by" } ] }` |

`locked_by` is `null` when no lock exists. `locked_by` holds an email address when
a lock exists. Reading this endpoint never needs the lock.

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
| 200 | `{ "lock_token": "<opaque>", "expires_in": 300 }` |
| 409 | `site_locked` with `details.actor_email` and `details.cooldown_remaining` |
| 400 | `confirmation_required` when a takeover needs the word `CONFIRM` |

The first attempt sends no `confirm` value. If the lock is free, the portal grants
it. If the lock is held and the cooldown has passed, the portal answers `400` with
`confirmation_required`. The browser then asks the operator to type `CONFIRM` and
repeats the call with that value.

### `POST /api/sites/<site_id>/lock/heartbeat` — extend the lock

| Item | Value |
| --- | --- |
| Body | `{ "lock_token": "<opaque>" }` |
| 200 | `{ "expires_in": 300 }` |
| 409 | `lock_lost` when the token no longer matches |

### `DELETE /api/sites/<site_id>/lock` — release the lock

| Item | Value |
| --- | --- |
| Body | `{ "lock_token": "<opaque>" }` |
| 200 | `{ "released": true }` |
| 409 | `lock_lost` |

---

## 4. Capture

### `POST /api/sites/<site_id>/captures` — start a capture

| Item | Value |
| --- | --- |
| Body | `{ "tier": 2, "run_id": "<string or null>", "role": "pre" }` |
| 202 | `{ "capture_id": "<string>", "status_url": "/api/captures/<id>/status" }` |
| 400 | `bad_tier` when `tier` is not 2 or 3 |
| 409 | `site_locked` |

The portal starts the work in the background and answers at once. `tier` defaults
to 2.

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

### `GET /captures/<capture_id>` — the capture page

Returns the human view of one capture.

---

## 5. Upgrade run

### `POST /api/sites/<site_id>/runs` — create a run

| Item | Value |
| --- | --- |
| Body | `{ "tier": 2 }` |
| 201 | `{ "run_id": "run-<hex>", "state": "created" }` |
| 409 | `site_locked` |

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
  "strategy": "big_bang"
}
```

`junos_file_action` maps to the cloud field that this feature never names in its
own model. `reboot` applies to switches and gateways only, because the cloud
reboots an access point on its own.

### `POST /api/runs/<run_id>/start` — start the upgrade

| Item | Value |
| --- | --- |
| Body | `{ "confirm": "UPGRADE" }` |
| 202 | `{ "state": "upgrade_submitting" }` |
| 400 | `confirmation_required` when `confirm` is wrong |
| 409 | `pre_capture_missing` when no verified pre-check exists |
| 409 | `lock_lost` |

The portal refuses to start unless a verified pre-check capture exists.

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
    { "name": "switches", "state": "waiting", "settled": 4, "total": 9 }
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

The browser polls this endpoint every 30 seconds.

### `POST /api/runs/<run_id>/stop` — stop the run

| Item | Value |
| --- | --- |
| Body | `{ "confirm": "STOP" }` |
| 200 | See the body below |
| 400 | `confirmation_required` when `confirm` is not exactly `STOP` |
| 404 | `run_not_found` |
| 409 | `run_not_stoppable` when the run already finished |

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

```json
{
  "before": { "capture_id": "...", "started_at": "..." },
  "after":  { "capture_id": "...", "started_at": "..." },
  "statistics": {
    "devices_unchanged": 120, "devices_changed": 8,
    "devices_added": 0, "devices_removed": 0,
    "clients_present": 1840, "clients_moved": 96,
    "clients_added": 12, "clients_missing": 30,
    "client_return_rate": 0.984
  },
  "device_deltas": [ ... ],
  "client_deltas": [ ... ],
  "skipped_sections": ["extras"]
}
```

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

### `GET /api/sites/<site_id>/history` — capture history

| Item | Value |
| --- | --- |
| Query | `limit` default 25, `offset` default 0 |
| 200 | `{ "captures": [ ... ], "total": 0 }` |

Each row carries `capture_id`, `role`, `started_at`, `capture_status`,
`actor_email`, and `stored_size_bytes`. The size satisfies FR-032b, which asks the
portal to record the stored size because retention is unlimited.

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
