# Confirmation Page Contract

This contract covers the multi-site confirm page. The route `GET /upgrade/org/confirm` renders the template `upgrade/org_confirm.html` with the values from `confirm_page()`. The contract names the sections, the stable identifiers, and the wording. Each existing identifier stays unchanged.

## Sections in Order

| Order | Section | Shown when | Stable identifier | Content |
| - | - | - | - | - |
| 1 | Summary card | Always | `org-upgrade-confirm` (existing) | Organization, Sites, Devices, Device families, Firmware, and Strategy lines. |
| 2 | Device families line | Always | `org-upgrade-families` (new on the paragraph) | The label of each family token, joined with commas. |
| 3 | Reboot lines | When the reboot option is set | `org-upgrade-reboot-at` and `org-upgrade-reboot-moment` (existing) | Unchanged. |
| 4 | Advanced summary | When the advanced summary has lines | `org-upgrade-advanced-summary` (existing) | Unchanged. |
| 5 | Start line and reschedule form | When the schedule is defined | `org-upgrade-start-line` and `org-upgrade-reschedule-form` (existing) | Unchanged. |
| 6 | Selected sites table | Always | `org-upgrade-site-table`, with rows `org-upgrade-site-row-<site_id>` | Columns: Site, Site identifier, Planned devices. |
| 7 | Child routes table | When the plan holds child routes | `org-upgrade-child-table`, with rows `org-upgrade-child-row-<child_id>` | Columns: Route, Scope, Device family, Sites, Planned devices. |
| 8 | Planned devices table | When the plan holds planned devices | `org-upgrade-device-table`, with rows `org-upgrade-device-row-<mac>` | Columns: Site, Device name, MAC address, Model, Device family, Current version, Target version. |
| 9 | Phases table | When a child body sends a phase value | `org-upgrade-phase-table`, with rows `org-upgrade-phase-row-<child_id>` | Columns: Route, Site, Phase list, Failure limit. |
| 10 | Cloud calls line | Always | `org-upgrade-cloud-calls` | The text "Cloud calls:" and the count. |
| 11 | Missing details list | When the plan is not complete | `org-upgrade-plan-missing` | One list item for each missing detail, in order. |
| 12 | Scope warning and write-disabled caution | Existing rule | `org-upgrade-scope-warning` and `org-upgrade-write-disabled` (existing) | Unchanged. |
| 13 | Pre-check table | Existing rule | `org-upgrade-prechecks` and `org-upgrade-precheck-row-<site_id>` (existing) | Unchanged. |
| 14 | Typed field and start control | Existing rule | `org-upgrade-confirmation` and `org-upgrade-start` (existing) | The field stays disabled while any gate is closed. |
| 15 | Back link | Existing rule | none | Unchanged. |

## Labels and Wording

| Value | Text on the page |
| - | - |
| Family token `ap` | AP |
| Family token `switch` | switch |
| Family token `gateway` | gateway |
| Family token `ssr` | session smart router |
| Child scope `org` | Organization |
| Any other child scope | Site, followed by the site name |
| Stable build in a device row | The vendor stable build |
| Empty device name | No name |
| Empty model or empty current version | Not read |
| Phase list of `10` and `100` | 10%, 100% |
| Empty phase list | None |
| Failure limit per phase `0` and `0` | Per phase: 0, 0. |
| Failure limit percentage `5` | Share: 5%. |
| Cloud calls of three | Cloud calls: 3. |

The missing-detail list uses one sentence for each code. The sentence names the subject after its colon.

| Code | Sentence | Subject |
| - | - | - |
| `route_name_missing` | A child route has no route name. | Route position, for example "child route 2". |
| `device_family_unknown` | A device family is not known. | Route position and the token. |
| `route_without_device` | A child route has no planned device. | Route name and scope. |
| `device_mac_missing` | A planned device has no MAC address. | Site name and device name. |
| `device_site_missing` | A planned device has no site identifier. | Device name. |
| `device_version_missing` | A planned device has no target version. | Device name or MAC address. |
| `device_site_not_selected` | A planned device is not at a selected site. | MAC address. |
| `site_without_device` | A selected site has no planned device. | Site name. |

## Escaping

All values reach the page through Jinja autoescape. The site name, the device name, the model, and the route name appear as escaped text. The template marks no value as safe (FR-011).

## Start Control Rule

The typed field `org-upgrade-confirmation` is disabled when any of the following holds. Writes are disabled. A pre-check is not ready. The plan is not complete. The start button `org-upgrade-start` keeps its existing attributes.

## Stability

- For the same stored plan, each identifier stays the same on each render.
- Rows follow the child order. Within a child, rows follow the target order.
- The rows contain each value as stored. The template does not sort or rename a value.
