# Safety design: the BIOS, the FPGA, and the Mist Edge upgrade workflows

Issue: [#2158](https://github.com/jmorrison-juniper/MistHelper/issues/2158)

Status: design only. This document adds no user-visible control. It states the
boundaries that a later feature issue must obey.

## 1. Why these three workflows leave the ordinary page

The ordinary firmware page writes the operating system of a device. A failed
write there leaves a device that still holds a bootloader, and the cloud can
send the firmware again.

These three workflows do not share that property.

Warning: do not add a BIOS control or an FPGA control to the ordinary firmware
page. Such a control can cause permanent damage to the hardware. A BIOS write
and an FPGA write both replace the code that starts the hardware. An
interruption during the write leaves hardware that does not start, and no
software recovers it. The site must return the unit to the vendor.

The Mist Edge workflow leaves the page for a different reason. It upgrades five
separate services with five separate versions. It targets an appliance that
holds the tunnels of a whole site. Its option model does not fit a form that
names one version for one device.

## 2. The evidence that shapes this design

Every claim below comes from the local API contracts and from the installed
software development kit. Each row names its source.

| Claim | Source |
| - | - |
| The Mist API holds four BIOS and FPGA endpoints, and all four are POST | `documentation/mist-api-openapi31json.json`, searched for every path that names `bios` or `fpga` |
| No endpoint reads the state of a BIOS run or an FPGA run | The same search. The result holds no GET path |
| No endpoint cancels a BIOS run or an FPGA run | The same search. The result holds no cancel path |
| The software development kit offers the same four calls and no others | `mistapi/api/v1/sites/devices.py`, which holds `upgradeSiteDevicesBios`, `upgradeSiteDevicesFpga`, `upgradeDeviceBios`, and `upgradeDeviceFPGA` |
| A switch and a gateway report a BIOS version and an FPGA version for each module | The schemas `stats_switch_module_stat_item` and `stats_gateway_module_stat_item` |
| An access point reports neither version | No access point schema holds either name |
| The Mist Edge workflow offers a full lifecycle | `mistapi/api/v1/orgs/mxedges.py`, which holds `upgradeOrgMxEdges`, `getOrgMxEdgeUpgrade`, `cancelOrgMxEdgeUpgrade`, and the matching site calls |

### 2.1 The consequence of the missing endpoints

The portal shows a progress page for an ordinary run, and it offers a stop
button. Both read a cloud endpoint. Neither endpoint exists for a BIOS run or
for an FPGA run.

Warning: do not draw a progress bar or a stop button for a BIOS run or for an
FPGA run. Such a control can cause permanent damage to the hardware. The portal
cannot read the state of that run, and it cannot stop it. A control that
appeared to stop the run would tell the operator a falsehood at the one moment
when a falsehood damages hardware.

## 3. The run types

The portal keeps one run type today. This design adds three, and each one owns
its own confirmation page and its own record.

| Run type | Scope | Start call | Reads state | Cancels |
| - | - | - | - | - |
| `firmware` (today) | Site or organization | `upgradeSiteDevices`, `upgradeDevice`, `upgradeOrgSsrs` | Yes | Yes |
| `bios` | Site | `upgradeSiteDevicesBios`, `upgradeDeviceBios` | No | No |
| `fpga` | Site | `upgradeSiteDevicesFpga`, `upgradeDeviceFPGA` | No | No |
| `mxedge` | Organization or site | `upgradeOrgMxEdges` | Yes | Yes |

A run record carries its type. Every route that starts firmware reads the type
first, and it refuses a type that it does not own. Section 8 states the refusal
rules.

## 4. The BIOS workflow and the FPGA workflow

The two workflows share one option model, because their two schemas hold the
same four fields. They stay separate run types, because a site may need one and
not the other. A combined page would also invite an operator to run both at
once.

### 4.1 The request fields

| Field | Type | Rule |
| - | - | - |
| `device_ids` | List of identifiers | The portal always sends this list. Section 4.3 states why |
| `models` | List of model names | The portal never sends this list. Section 4.3 states why |
| `reboot` | Boolean | The cloud default is false. The portal sends the choice of the operator |
| `version` | Text | The exact BIOS version or FPGA version, such as `CDEN_P_EX1_00.15.01.00` or `REV37` |

The per-device call holds `reboot` and `version` alone, because the path names
the device.

### 4.2 The qualifying models

A device qualifies when its stats record reports the matching version. A switch
and a gateway report both versions for each module. An access point reports
neither version.

Rule: the page offers a device only when the module stats of that device report
a version for the operation. A device that reports no version qualifies for no
BIOS run and for no FPGA run.

This rule reads live data instead of a model list. A model list would age. An
aged list would either hide a device that qualifies or offer a device that does
not.

Note: a chassis holds several modules, and each module reports its own version.
The page names each module and its version, so the operator sees the unit that
the write reaches.

### 4.3 Why the portal never sends the model list

The `models` field upgrades every device of a named model at the site. An
operator who typed one model would start a hardware write on every unit of that
model, and no endpoint stops it.

Rule: the portal always sends `device_ids`. The page offers no model control at
all. An operator selects each device by name.

### 4.4 The warning text

The confirmation page carries this warning above the confirmation control.

> Warning: this run writes the code that starts the hardware. This run can cause
> permanent damage to the hardware. Do not remove power, and do not remove a
> cable, until the run ends. A unit that loses power during the write does not
> start again, and no software recovers it. The site must return that unit to
> the vendor.

A second warning names the missing controls.

> Warning: the cloud offers no way to read the state of this run and no way to
> stop it. This run can cause permanent damage to the hardware. After you start
> this run, the portal reports no progress and cancels nothing.

### 4.5 The confirmation

The ordinary page asks the operator to type one word. This page asks for more,
because the consequence is permanent.

1. The operator types the exact count of devices in the run.
2. The operator types the word `BIOS` or the word `FPGA`.
3. The operator confirms a maintenance window with a checkbox that names the
   date and the time.

The start button stays disabled until all three pass. Each control carries its
own stable test identifier.

### 4.6 The status read

The portal cannot read the run. It reads the devices instead.

After the start, the page polls the module stats of each device. It reports one
of three states for each device.

| State | Rule |
| - | - |
| `written` | The module reports the target version |
| `unchanged` | The module reports the earlier version |
| `unreachable` | The device answers no stats read |

The page never calls any of these three states a failure, because the portal
cannot tell a slow write from a stopped one. It reports the reading and the age
of the reading, and it leaves the judgment to the operator.

### 4.7 The recovery procedure

The portal shows this procedure on the status page of every BIOS run and of
every FPGA run.

1. Do not remove power from a device in the `unreachable` state. A unit that is
   still writing needs power to finish.
2. Wait 30 minutes from the start of the run. A BIOS write and an FPGA write
   both finish well inside that window.
3. If the device stays `unreachable` after 30 minutes, open a case with the
   vendor. Give the case the device serial number, the target version, and the
   start moment that the portal recorded.
4. Do not start a second run against a device in the `unreachable` state. A
   second write onto a half-written unit removes the last chance of a recovery.
5. If the device reports `unchanged` and it answers the stats read, the write
   did not begin. That device is safe, and the operator may start the run again.

The portal writes the serial number, the target version, and the start moment
into the run record, so step 3 needs no other source.

## 5. The Mist Edge workflow

This workflow reads a full lifecycle, so it keeps a progress page and a cancel
control.

### 5.1 The request fields

| Field | Type | Rule |
| - | - | - |
| `mxedge_ids` | List of identifiers | Required. The portal always sends the selected appliances |
| `versions` | Mapping of five services | `mxagent` and `tunterm` are required. The other three default to `current` |
| `allow_downgrades` | Mapping of five booleans | Each one defaults to false |
| `channel` | Text | `alpha`, `beta`, or `stable` |
| `distro` | Text | A code name such as `bullseye`. It overrides `versions` |
| `strategy` | Text | `big_bang`, `serial`, or `canary` |
| `canary_phases` | List of numbers | The canary strategy alone reads it |
| `max_failure_percentage` | Number | The default is 5 |
| `start_time` | Number | Epoch seconds. The default is now |

### 5.2 The two fields that need a guard

The `distro` field overrides every entry of `versions`. An operator who fills
both reads one plan on the page, and the cloud runs another.

Rule: the page refuses a run that names a distro and a version together. The
refusal names both controls.

The `allow_downgrades` mapping moves a service to an older build. A downgrade of
`tunterm` drops every tunnel that the appliance holds.

Rule: each downgrade control starts off. A run that turns one on carries a
warning that names each service under downgrade.

### 5.3 The warning text

> Warning: this appliance terminates the tunnels of one site or more. The
> upgrade drops every tunnel on the appliance during its reboot. This loss of
> service can stop the work of the site. Every wireless client on those tunnels
> loses the network until the appliance returns.

A second warning covers a cluster.

> Warning: the run holds two appliances or more of one cluster. A single wave
> reboots the cluster at once and removes the failover. This loss of failover
> can stop the work of the site. Choose the serial strategy to keep one
> appliance in service.

### 5.4 The confirmation, the status read, and the cancel

The confirmation follows the ordinary page. The operator types the word
`UPGRADE`.

The status page reads `getOrgMxEdgeUpgrade`. It reports the phase and the count
of each state.

The cancel control calls `cancelOrgMxEdgeUpgrade`. A cancel stops the appliances
that have not started. It does not reverse an appliance that already wrote the
firmware, and the page states that rule beside the control.

## 6. What the ordinary firmware page keeps

The ordinary page changes in no way. It holds no BIOS control, no FPGA control,
and no Mist Edge control. Its device table offers no Mist Edge appliance,
because an appliance is not a site device.

## 7. The pages and the identifiers

Each workflow owns its own path. A later feature issue fixes the stable test
identifiers of each control.

| Workflow | Options path | Confirmation path | Status path |
| - | - | - | - |
| BIOS | `/runs/<run_id>/bios/options` | `/runs/<run_id>/bios/confirm` | `/runs/<run_id>/bios/status` |
| FPGA | `/runs/<run_id>/fpga/options` | `/runs/<run_id>/fpga/confirm` | `/runs/<run_id>/fpga/status` |
| Mist Edge | `/runs/<run_id>/mxedge/options` | `/runs/<run_id>/mxedge/confirm` | `/runs/<run_id>/mxedge/status` |

## 8. The refusal rules

These rules keep the four workflows apart. A later feature issue proves each one
with a test.

1. The ordinary start route refuses a run whose type is not `firmware`.
2. Each new start route refuses a run whose type does not match its own.
3. The ordinary body builder never names a BIOS endpoint, an FPGA endpoint, or a
   Mist Edge endpoint. The allowed endpoint tuple of
   `src/firmware/upgrade_service.py` already holds this rule for the ordinary
   run, and each new workflow gets its own tuple.
4. A BIOS request and an FPGA request always carry `device_ids`, and they never
   carry `models`.
5. The status route of a BIOS run answers 404 for a read of a cloud run state.
   The status route of an FPGA run answers 404 for the same read. No such state
   exists.
6. The stop route refuses a BIOS run and an FPGA run, and the answer names the
   reason.

## 9. The follow-up issues

This design splits into three feature issues. Each one carries its own test plan
and its own acceptance criteria.

1. The BIOS and FPGA workflow. It covers sections 3, 4, 6, 7, and 8.
2. The Mist Edge workflow. It covers sections 3, 5, 6, 7, and 8.
3. The reader of the module stats that section 4.2 needs. It may merge into the
   first issue if the reader stays small.

## 10. The open questions

1. The vendor states that a BIOS write and an FPGA write finish well inside 30
   minutes. The exact figure needs a vendor source before section 4.7 states it
   as a rule instead of a guide.
2. The cluster membership of a Mist Edge needs a source. Section 5.3 names a
   cluster warning, and the portal needs a field that groups the appliances of
   one cluster.
3. The `distro` field names a code name. The portal needs a source for the code
   names that a given appliance accepts. Without that source the control stays a
   free text field with a warning.
