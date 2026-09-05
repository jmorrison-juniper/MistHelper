# Phase 0 Research: Upgrade Pre-Check and Post-Check Portal

**Feature**: 1823-upgrade-capture-portal
**Branch**: `feat/1823-upgrade-capture-portal`
**Date**: 2026-08-19

## How to read this file

This file is an index and a decision record. It does not repeat the detailed
research. Six reference documents under `specs/1823-upgrade-capture-portal/research/`
hold the detail. Every claim in those documents cites a file and a line. Treat
them as authoritative.

Section 1 lists the reference documents. Section 2 records the decisions that the
plan builds on. Section 3 records the two open questions that this phase closed
with a fresh check against the installed SDK. Section 4 lists the places where the
documentation and the code disagree.

---

## 1. Reference documents

| Document | Subject |
| --- | --- |
| `research/capture-data-sources.md` | Every cloud call that a capture makes, and the traps in each one |
| `research/settle-gate-apis.md` | Device events, device statistics, and upgrade status fields |
| `research/upgrade-reuse.md` | What the existing upgrade code can supply, and the new seam |
| `research/storage-and-locking.md` | Database routing, the capture document, and the site lock |
| `research/concurrency-auth-conventions.md` | Threads, authentication, and the repository quality gates |
| `research/web-portal.md` | The existing portal, and what the new portal must not copy |

---

## 2. Decisions

### D1. Place the new application outside `web_portal/`

**Decision**: Create the package `src/upgrade_portal/`.

**Rationale**: `pyproject.toml:161` excludes `web_portal` from ruff.
`pyproject.toml:273-281` excludes `web_portal` from mypy. Code inside
`web_portal/` loses two quality gates. The mypy command names `src/`, so a
package under `src/` gains lint coverage and type coverage with no change to any
gate command.

**Alternatives rejected**: A package inside `web_portal/` loses ruff and mypy. A
package at the repository root escapes the mypy target list until somebody edits
the command.

### D2. Use port 8056 with the variable `CAPTURE_PORT`

**Decision**: The default port is 8056. The environment variable `CAPTURE_PORT`
overrides it.

**Rationale**: `compose.yml` publishes 2200, 8055, 8529, 6379, 8001, and 11434.
The second application in this repository uses 5173, 8000, and 80. Port 8056 is
free and sits next to the existing portal port.

**Alternatives rejected**: Reuse of `WEB_PORT` would stop the two applications
from running together.

### D3. Poll a JSON endpoint every 30 seconds

**Decision**: The browser polls a JSON status endpoint. The portal does not use
server-sent events.

**Rationale**: The existing event bus caps subscribers at 10
(`web_portal/services/event_bus.py:24`). Each open stream holds a request thread
for its whole life. The subscriber map lives in process memory, so a second
worker breaks it.

**Alternatives rejected**: The event bus fails above 10 users and blocks a move to
more workers.

### D4. Store a capture with the `natural_pk` strategy

**Decision**: Register `upgradeCaptureWrite` and `upgradeRunWrite` as
`natural_pk`.

**Rationale**: `composite_pk` dual-writes to Redis, and the Redis JSON writer
applies an expiry to every key (`src/db/redis_writer.py:598`). FR-032a forbids a
storage path that expires a record. `auto_increment_with_unique` mints a fresh
identifier on every write (`src/db/arango_writer.py:4039`), so a retry would
duplicate the record instead of replacing it.

### D5. Add a new upgrade seam at `src/firmware/upgrade_service.py`

**Decision**: Add a module with `build_body`, `plan_upgrade`, `invoke_upgrade`,
and `classify_gateway`, plus frozen dataclasses. Call that module from the
portal.

**Rationale**: The four existing upgrade classes hold 12023 lines, 1271 `print`
calls, and 80 `input` calls (`research/upgrade-reuse.md` section 6.1). A web
request cannot drive that code. `firmware_manager.py:34-37` holds four module
globals, and the save-and-restore blocks at `:1736` and `:1797` are not thread
safe. Two web requests for two organizations corrupt each other.

**Alternatives rejected**: Reuse through `InputInterceptor`
(`web_portal/services/input_hook.py:16`) fails, because the prompt order changes
with the inventory.

### D6. Put concurrency at the call-group level

**Decision**: Run six independent capture call groups through
`ConnectionPoolExecutor` with about four workers. Keep the pages inside one group
sequential. Never fan out per device.

**Rationale**: `mistapi.get_all` follows a cursor, so pages inside one group must
run in order. A per-device fan-out costs about 125 times the requests for no gain.
The rate limit is 5000 calls each hour for each token
(`src/utils/rate_limiting.py:56`).

### D7. Use threads, not asyncio

**Decision**: Use `ThreadPoolExecutor` and `ConnectionPoolExecutor`.

**Rationale**: The core application contains no `async def`. Every asyncio match
in the repository lives in a separate project directory. No event loop exists to
join.

### D8. Use an integer schema version

**Decision**: The capture document carries `schema_version` as an integer. The
first release writes the value 1.

**Rationale**: The spec Constraints section states that two conventions disagree
and that this feature must choose one and record the choice. An integer supports
a forward migration and a range query. A text value does not.

### D9. Verify the database write by a read-back

**Decision**: After the portal writes a capture, the portal reads the document key
back and compares it. The portal reports the true outcome to the operator.

**Rationale**: `WriteResult.success` is not proof. `src/export/data_exporter.py:141`
gates every polyglot write on a container check, and `src/db/router.py:372-382`
returns `success=True` after it writes zero rows. Issue #1824 tracks the repair. A
read-back does not wait for that repair.

### D10. Name the theme file `magenta.css`

**Decision**: The brand theme file is `magenta.css`. The brand name appears only
inside the file content.

**Rationale**: `.gitignore:31-35` and `.dockerignore:93-96` exclude any path that
matches `*tmo*`, `*TMO*`, `*t-mobile*`, or `*T-Mobile*`. A brand-named file would
stay untracked and would never reach the container image. `ThemeManager` finds a
theme by a glob of `*.css` (`web_portal/services/config.py:197-215`), so the name
needs no code change.

### D11. Fetch the inventory twice for the two features

**Decision**: The upgrade path fetches the inventory with the virtual chassis
parameter omitted. The capture path fetches the inventory with `vc=True`.

**Rationale**: An upgrade targets the logical device. A capture must record every
physical member. One shared fetch cannot serve both views.

---

## 3. Questions closed in this phase

### Q1. Does the cloud offer a cancel action for an upgrade?

**Answer: yes, for every device type in scope, but the scope differs by family.**

Verified against the installed `mistapi` 0.63.3 package and the vendored
specifications.

| Family | Function | Source | HTTP |
| --- | --- | --- | --- |
| Access point, switch, Junos gateway | `cancelSiteDeviceUpgrade(mist_session, site_id, upgrade_id)` | `mistapi/api/v1/sites/devices.py:1289` | `POST /api/v1/sites/{site_id}/devices/upgrade/{upgrade_id}/cancel` |
| Access point, switch, Junos gateway | `cancelOrgDeviceUpgrade(mist_session, org_id, upgrade_id)` | `mistapi/api/v1/orgs/devices.py:894` | `POST /api/v1/orgs/{org_id}/devices/upgrade/{upgrade_id}/cancel` |
| Session smart router | `cancelOrgSsrUpgrade(mist_session, org_id, upgrade_id)` | `mistapi/api/v1/orgs/ssr.py:173` | `POST /api/v1/orgs/{org_id}/ssr/upgrade/{upgrade_id}/cancel` |

The cancel semantics match FR-038c and FR-038d exactly. The vendored
specification states the behavior in two places. Line 11 of
`documentation/api/utilities/POST_sites_site_id_devices_upgrade_upgrade_id_cancel.md`
reads "Best effort to cancel an upgrade. Devices which are already upgraded wont
be touched". Line 64 of the same file reads "Cancellation is best-effort. Devices
mid-flash may still complete."

**One gap.** No site-scope cancel function exists for the session smart router.
`mistapi/api/v1/sites/ssr.py` holds 75 lines and offers `getSiteSsrUpgrade` at
`:17` and `upgradeSsr` at `:45` only. If the portal starts a session smart router
upgrade through the site-scope `upgradeSsr` call, the portal has no matching
cancel. The plan therefore drives every session smart router upgrade through the
organization-scope call, so that the cancel path exists. If a future path has no
cancel, FR-038f applies without change.

### Q2. Does a Junos gateway upgrade ride `upgradeSiteDevices`?

**Answer: yes, and the repository has no Junos gateway upgrade path today.**

Three lines of evidence support the cloud side.

1. The request body of `POST /api/v1/sites/{site_id}/devices/upgrade` declares
   `reboot` as "For Switches and Gateways only (APs are automatically rebooted)".
2. The same body declares `snapshot` as "For Junos devices only". A Junos gateway
   is a Junos device.
3. The vendored device statistics examples hold a live Junos gateway record with
   `"type": "gateway"` and a firmware update block. See
   `documentation/api/orgs/GET_orgs_org_id_stats_devices.md:7574` and
   `documentation/api/sites/GET_sites_site_id_stats_devices.md:7565`.

The repository side is clear and negative. `research/upgrade-reuse.md` section 4.4
reports zero matches for the Junos gateway model family across `src/firmware/`.
The switch upgrader filters on `d.get("type") == "switch"`
(`src/firmware/bulk_switch_upgrader.py:898`), so a gateway never enters that path.

**Result**: the Junos gateway path is new work, but it is the same cloud call that
the switch path already makes. The only new logic is the family split.
`classify_gateway` performs that split. The one existing discriminator is
`_is_ssr_inventory_row` at `src/firmware/firmware_manager.py:2291`, which matches
a type value of `ssr` or a model string that holds `SSR` or `128T`.

---

## 4. Places where the documentation and the code disagree

The plan routes around each item. No item blocks the feature.

1. Every vendored file under `documentation/api/` names the SDK path as
   `mistapi.api.v1.utilities.upgrade.*`. That package does not exist in
   `mistapi` 0.63.3. The real paths are `mistapi.api.v1.sites.devices`,
   `mistapi.api.v1.orgs.devices`, `mistapi.api.v1.orgs.ssr`, and
   `mistapi.api.v1.sites.ssr`.
2. `documentation/api/sites/GET_sites_site_id_stats_devices.md:7591` names
   `mistapi.api.v1.sites.stats_-_devices.listSiteDevicesStats()`. That name is not
   a valid Python identifier.
3. Both event search documents advise a `page` parameter. The real cursor is
   `search_after`.
4. The vendored notes attribute the upgrade endpoints to menu 90, 99, and 100. The
   live menu numbers are 137, 154, 155, and 156. Treat the vendored notes as
   unreliable.
5. `fwupdate.status` declares `"type": "object"` in the specification, but the
   value is a string.
6. `documentation/api/sites/GET_sites_site_id_clients_search.md:232` gives
   `last_ssid` the description that belongs to `last_username`.
7. `mistapi/api/v1/orgs/ssr.py:167` builds the cancel path inside
   `getOrgSsrUpgrade`. The status call therefore reads the cancel path. This is an
   SDK defect. The portal must not call `getOrgSsrUpgrade`.
8. `src/device/_utility_commands_show.py:384-385` claims menu 137 for the top
   command. The real menu number is 125.
9. `src/firmware/firmware_manager.py:3713` writes `ActiveUpgrades.json` to the
   process working directory. Every output belongs under `data/`.
10. `src/db/retention.py:100` reads an attribute named `_database`, but
    `ArangoDBWriter` names the handle `self._db` (`src/db/arango_writer.py:3903`).
    Storage usage always reports 0.0 and the purge never runs. Record this. Do not
    repair it in this feature, because FR-032 wants unlimited retention.
11. `src/refactors/endpoint_primary_key_strategies.py:22` lists the strategy names
    `auto_pk` and `time_series` in its module docstring. Neither name appears in
    any entry. The docstring is stale.
12. `src/auth/interactive/msp_org_selector.py:155-156` hard-codes `current_page = 0`
    and `total_pages = 1`. The navigation branches at `:208` and `:210` can never
    run. The portal builds its own organization picker.
13. `src/firmware/bulk_ap_upgrader.py:1025` sets `p2p_parallelism`, but no body
    builder reads it. The access point site path drops the value.
14. `src/firmware/bulk_switch_upgrader.py` sends a canary strategy with no canary
    phase list.
15. The coverage floor differs between `pyproject.toml:419-420`, which sets 90, and
    `.github/workflows/ci.yml:71`, which sets 80. Target 90.
