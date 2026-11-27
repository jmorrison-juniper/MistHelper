# Contract: OrgConfirmPlanView

This contract covers the view class that builds the confirm page values from the stored plan. The class lives in `src/interfaces/portals/upgrade_portal/upgrade/org_child_controls.py`, after `OrgScheduleView`.

## Members

The class has five members, which is the limit of the five-item rule.

| Member | Kind | Parameters | Returns |
| - | - | - | - |
| `build` | public class method | `operation`, the stored plan record or `None` | A map with the seven keys of the data model. |
| `_site_rows` | private static method | `operation` | The list of SiteRow values. |
| `_route_rows` | private static method | `children`, `names` | A pair of lists. The first list holds the RouteRow values. The second list holds the PhaseRow values. |
| `_device_rows` | private static method | `children`, `names` | The list of DeviceRow values. |
| `_missing_details` | private static method | `operation`, `sites`, `routes`, `devices` | The list of MissingDetail values. |

Each method takes at most four parameters. Each method fits in 25 lines and holds at most five logical blocks.

## Behavior

| Input | Result |
| - | - |
| `None` | `complete` is true. Every list is empty. `cloud_call_count` is 0. |
| A record with an empty `children` list | `complete` is true. Every list is empty. `cloud_call_count` is 0. |
| A record with child records that pass the completeness rules | `complete` is true. `cloud_call_count` equals the child count. |
| A record that fails one or more completeness rules | `complete` is false. `missing` holds one MissingDetail for each failed rule instance. |

## Completeness Rules

The rules are the eight rules of `data-model.md`. Each failed instance adds one MissingDetail with its code and its subject.

## Calls and Side Effects

- The method calls no cloud service.
- The method writes no record and changes no state.
- The method reads the record through its keys only.

## Logging

- Before the build: one info line that names the aggregate identifier and the child count.
- After the build: one debug line that reports the count of routes, devices, and missing details.
- The lines use ASCII only. No line prints a MAC address, a token, or a site identifier.

## Comments

Each executable line carries an inline comment that explains its purpose. The comment states the cause and the purpose of the line, not the operation.
