# Upgrade Service Contract

**Module**: `src/firmware/upgrade_service.py`
**Feature**: 1823-upgrade-capture-portal

## Why this module exists

The four existing upgrade classes hold about 12000 lines, 1271 `print` calls, and
80 `input` calls. A web request cannot drive that code, because the code writes to
a terminal and waits for a person at a keyboard.

`src/firmware/firmware_manager.py` also holds four module globals at lines 34 to
37, and the save-and-restore blocks at lines 1736 and 1797 are not thread safe.
Two concurrent web requests for two organizations would corrupt each other.

This module is the clean seam. It holds no `print`, no `input`, and no module
global. Every function is pure or performs one cloud call. The portal calls this
module. The portal never calls `firmware_manager`.

`MistHelper.py` needs no change for this seam.

## Rules for every function in this module

1. At most 5 parameters, 5 logical blocks, and 25 lines. A request object carries
   any wider input.
2. No mutable module state. Every value the function needs arrives as a parameter.
3. Every function is safe to call from several threads at once.
4. Every function logs at info level before its action and at debug level after
   its action, with `%s` placeholders and ASCII characters only.
5. No function prints. No function reads standard input.
6. No function logs a token value or a password value.

---

## 1. Data types

Every type is a frozen dataclass, so a value cannot change after a thread receives
it.

### `DeviceTarget`

| Field | Type | Notes |
| --- | --- | --- |
| `mac` | `str` | Lower case, no separator |
| `name` | `str` | |
| `device_type` | `str` | `ap`, `switch`, or `gateway` |
| `model` | `str` | |
| `version_before` | `str` | |
| `version_target` | `str` | |
| `site_id` | `str` | |

### `GatewayFamily`

An enumeration with two members: `JUNOS` and `SSR`.

### `UpgradeOptions`

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `reboot` | `bool` | `True` | Switches and gateways only. The cloud reboots an access point on its own. |
| `junos_file_action` | `bool` | `False` | Maps to the cloud field for a Junos file action. |
| `strategy` | `str` | `"big_bang"` | The cloud upgrade strategy. |
| `start_time` | `int or None` | `None` | Epoch seconds for a delayed start. |

### `UpgradePlan`

| Field | Type | Notes |
| --- | --- | --- |
| `scope` | `str` | `site` or `org` |
| `endpoint` | `str` | The SDK function name the plan will call |
| `targets` | `tuple[DeviceTarget, ...]` | |
| `body` | `Mapping[str, object]` | The request body |
| `warnings` | `tuple[str, ...]` | Plain sentences for the operator |

### `UpgradeSubmission`

| Field | Type | Notes |
| --- | --- | --- |
| `upgrade_id` | `str or None` | `None` when the cloud returned no identifier |
| `scope` | `str` | `site` or `org` |
| `accepted` | `tuple[str, ...]` | MAC addresses the cloud accepted |
| `rejected` | `tuple[tuple[str, str], ...]` | MAC address with the reason |
| `raw_status` | `int` | The HTTP status code |

### `CancelOutcome`

| Field | Type | Notes |
| --- | --- | --- |
| `cancelled` | `tuple[str, ...]` | |
| `already_writing` | `tuple[str, ...]` | |
| `no_cancel_available` | `tuple[str, ...]` | |
| `message` | `str` | One plain sentence for the operator |

---

## 2. Public functions

### `classify_gateway(device) -> GatewayFamily`

Reads one device record and returns the family.

- Returns `GatewayFamily.SSR` when the device type equals `ssr`, or when the model
  string holds `SSR` or `128T`.
- Returns `GatewayFamily.JUNOS` for every other gateway.

The existing discriminator at `src/firmware/firmware_manager.py:2291` uses the
same test. This function repeats the test without the module state.

**Why the split matters.** A Junos gateway rides the same site device upgrade call
that a switch rides. A session smart router rides a separate endpoint family. The
repository has no Junos gateway upgrade path today, so that path is new work.

### `build_body(targets, options, family) -> Mapping[str, object]`

Builds the request body for one call. Pure. Performs no input and output.

Rules the body must follow.

| Rule | Reason |
| --- | --- |
| Send `reboot` for a switch or a gateway only | The cloud reboots an access point on its own |
| Send the Junos file action field for a Junos device only | The cloud rejects the field elsewhere |
| Send a canary phase list whenever the strategy is canary | The existing switch upgrader sends a canary strategy with no phase list |
| Never send an unread field | The existing access point upgrader sets a parallelism value that no body builder reads |

### `plan_upgrade(targets, options, org_id, site_id) -> tuple[UpgradePlan, ...]`

Groups the targets by device type and by gateway family, then returns one plan for
each group. Pure. Performs no cloud call.

Grouping rules.

| Group | Scope | Endpoint |
| --- | --- | --- |
| Access points | site | `upgradeSiteDevices` |
| Switches | site | `upgradeSiteDevices` |
| Junos gateways | site | `upgradeSiteDevices` |
| Session smart routers | **org** | `upgradeOrgSsrs` |

**Why a session smart router always uses organization scope.** The installed SDK
offers `cancelOrgSsrUpgrade` at `mistapi/api/v1/orgs/ssr.py:173`. No site-scope
cancel exists for that family. `mistapi/api/v1/sites/ssr.py` holds
`getSiteSsrUpgrade` and `upgradeSsr` only. A run that started at site scope would
have no way to stop, which FR-038 forbids.

The function adds a warning when a target list mixes families, so that the
operator sees the split before the start.

### `invoke_upgrade(session, plan) -> UpgradeSubmission`

Performs one cloud call for one plan. Returns the submission record.

- Never retries on its own. The caller owns the retry policy.
- Never raises for a cloud error status. It records the status in `raw_status`.
- Raises `ValueError` when the plan is malformed.

### `cancel_upgrade(session, plan, upgrade_id, last_status=None) -> CancelOutcome`

Performs the cancel call that matches the plan scope and family.

| Family and scope | Function | Source |
| --- | --- | --- |
| Access point, switch, Junos gateway at site scope | `cancelSiteDeviceUpgrade` | `mistapi/api/v1/sites/devices.py:1289` |
| Access point, switch, Junos gateway at org scope | `cancelOrgDeviceUpgrade` | `mistapi/api/v1/orgs/devices.py:894` |
| Session smart router at org scope | `cancelOrgSsrUpgrade` | `mistapi/api/v1/orgs/ssr.py:173` |

The cloud describes the behavior as best effort. A device that already upgraded
stays untouched. A device in mid-flash may still complete. The function sorts each
MAC address into `cancelled` or `already_writing` from `last_status`, the upgrade
status the portal read last, and it writes one plain sentence into `message`.
`last_status` has a default, so every three-argument call still works.

If a future family offers no cancel function, the function places every MAC
address into `no_cancel_available` and writes a message that says so plainly.
FR-038f covers that case.

### `read_upgrade_status(session, scope, identifier, upgrade_id, family=GatewayFamily.JUNOS) -> Mapping[str, object]`

Reads the status of one upgrade.

The scope alone does not name the cloud function for a session smart router, so
`family` names it. `family` has a default, so every four-argument call still
works.

Two rules protect correctness.

1. The response names the phase field `current_phase`, not `phase`.
2. The response holds `reboot_in_progress` as a list of MAC addresses, not as a
   boolean. The cloud may return the list at the top level of the answer, or
   inside the `targets` mapping. Read the top level first, then fall back to
   `targets`.

**Never call `getOrgSsrUpgrade`.** The installed SDK builds the cancel path inside
that function at `mistapi/api/v1/orgs/ssr.py:167`, so the status read would post
to the wrong path. Use `getSiteSsrUpgrade` for a site-scope read, or read the
device statistics for an organization-scope read.

### `list_available_versions(session, site_id, models) -> Mapping[str, tuple[str, ...]]`

Returns the version list for each model. Reads the cloud once for the site and
groups the answer by model.

---

## 3. What this module must never do

| Prohibition | Reason |
| --- | --- |
| Import `firmware_manager` | That module holds four globals and two unsafe save-and-restore blocks |
| Call `print` | A web request has no terminal |
| Call `input` or `safe_input` | A web request has no keyboard |
| Write a file to the process working directory | Every output belongs under `data/` |
| Hold a module global | Two threads would share it |
| Log a token or a password | FR-009 |
