# Data Model: Multi-Site Confirm Page Plan Detail

This feature reads the stored aggregate plan record. It adds no stored field, no table, and no migration. The view builds five value groups from the record on each read. It writes nothing.

## Source Record

The source is the durable aggregate record that `AggregateUpgradeService.build()` writes (`src/operations/execution/firmware/aggregate_upgrade_service.py`, lines 188 to 212). The fields that this feature reads are:

| Field | Type | Source line | Meaning |
| - | - | - | - |
| `site_ids` | list of text | 202 | The selected sites, in the order of the selection. |
| `site_names` | map from site identifier to text | 203 | The approved name of each selected site. |
| `children` | list of child records | 212 | One record for each cloud call of the plan. |
| `state` | text | 208 | `planned` before any cloud call. The view reads it only for context. |

Each child record holds the keys that `_base_child()` writes (lines 769 to 786) and the keys that `_ap_child()` and `_plan_child()` add:

| Key | Type | Source line | Meaning |
| - | - | - | - |
| `child_id` | text, `child-<uuid4 hex>` | 771 | The plan-scoped identity of the child. |
| `route` | text | 773 | The cloud route name, for example `upgradeOrgDevices`. |
| `scope` | text | 774 | `org` for an organization route. A site route carries the site scope. |
| `org_id` | text | 775 | The organization identifier. |
| `site_id` | text or null | 776 | The site identifier of a site route. Null for an organization route. |
| `device_family` | text | 777 | `ap`, `switch`, `gateway`, or `ssr`. |
| `site_name` | text | 663 to 684 and 743 to 760 | The approved name of the site or the joined names of the organization child. |
| `targets` | list of target records | 663 to 684 and 743 to 760 | One record for each planned device of the child. |
| `body` | map | 685 to 708 and 743 to 760 | The exact request body of the child. |
| `reboot_at` | integer, optional | 762 to 767 | The reboot moment of a site child. |

Each target record holds the keys that `_target_record()` writes (lines 787 to 799):

| Key | Type | Meaning |
| - | - | - |
| `mac` | text | The device MAC address. It is the natural key of the device in the plan. |
| `name` | text | The device name at the time of the plan. It may be empty. |
| `device_type` | text | The planner family, `ap`, `switch`, `gateway`, or `ssr`. |
| `model` | text | The device model. It may be empty. |
| `version_before` | text | The version before the upgrade. It may be empty. |
| `version_target` | text | The version that the operator chose. |
| `site_id` | text | The selected site of the device. |

## ConfirmPlan

The view returns one map for each plan. The map has seven keys.

| Key | Type | Rule |
| - | - | - |
| `complete` | boolean | True when every rule in "Completeness rules" passes. True for a plan with no child route. |
| `missing` | list of MissingDetail | Empty when `complete` is true. Otherwise one entry for each failed rule. |
| `cloud_call_count` | integer | The number of child records. Each child record is one cloud call. |
| `sites` | list of SiteRow | One row for each entry of `site_ids`, in the same order. |
| `routes` | list of RouteRow | One row for each child record, in the same order. |
| `devices` | list of DeviceRow | One row for each target of each child, in the same order. |
| `phases` | list of PhaseRow | One row for each child whose body sends a phase value. |

## SiteRow

| Key | Type | Rule |
| - | - | - |
| `site_id` | text | The natural key of the site. It comes from `site_ids`. |
| `site_name` | text | The value of `site_names` for the site. Empty text when the name is absent. The template shows the identifier when the name is empty. |
| `device_count` | integer | The number of targets across all children whose `site_id` equals this site. |

## RouteRow

| Key | Type | Rule |
| - | - | - |
| `child_id` | text | The plan-scoped natural key of the child. |
| `route` | text | The route name from the child record. |
| `scope` | text | The scope from the child record, `org` or a site scope. |
| `family` | text | The device family token from the child record. The template maps it to a label. |
| `site_names` | list of text | The approved names of the sites that the child covers. For an organization route, this is every site of its targets. |
| `device_count` | integer | The number of targets of the child. |
| `sends_stable` | boolean | True when the child body `version` equals the stable word `stable`. |

## DeviceRow

| Key | Type | Rule |
| - | - | - |
| `child_id` | text | The child that holds the device. |
| `site_id` | text | The target `site_id`. When it is absent, the child `site_id` is used. |
| `site_name` | text | The site name for `site_id`. Empty text when the name is absent. |
| `name` | text | The target name. Empty text when the name is absent. The template shows "No name". |
| `mac` | text | The target MAC address. The natural key of the device row. |
| `model` | text | The target model. Empty text when the model is absent. The template shows "Not read". |
| `family` | text | The child `device_family` token. |
| `version_before` | text | The target `version_before`. Empty text when absent. The template shows "Not read". |
| `version_target` | text | The target `version_target`. |
| `stable` | boolean | Equal to `sends_stable` of the child. When true, the template shows "The vendor stable build" in place of `version_target`. |

## PhaseRow

| Key | Type | Rule |
| - | - | - |
| `child_id` | text | The child whose body sends the value. |
| `route` | text | The route name of the child. |
| `site_name` | text | The site name of the child, or the joined names for an organization route. |
| `phases` | list of integer | The `canary_phases` value of the body. Empty when the body holds none. |
| `max_failures` | list of integer | The `max_failures` value of the body. Empty when the body holds none. |
| `max_failure_percentage` | integer or null | The `max_failure_percentage` value of the body. Null when the body holds none. |

## MissingDetail

| Key | Type | Meaning |
| - | - | - |
| `code` | text | One of `route_name_missing`, `device_family_unknown`, `route_without_device`, `device_mac_missing`, `device_site_missing`, `device_version_missing`, `device_site_not_selected`, or `site_without_device`. |
| `subject` | text | The subject that the message names. It is a route position, a site name, a device name, or a MAC address. |

## Completeness Rules

A plan with no child record is complete. Otherwise the plan is complete only when each rule below holds.

1. Each child record has a non-empty `route`.
2. Each child record has a `device_family` in the set `ap`, `switch`, `gateway`, or `ssr`.
3. Each child record holds at least one target.
4. Each target holds a non-empty `mac`.
5. Each target has a `site_id`, or its child has a non-empty `site_id`.
6. Each target has a `site_id` that is one of the `site_ids` of the plan.
7. Each target has a non-empty `version_target`, unless its child body sends the stable version.
8. Each entry of `site_ids` holds at least one target.

Warning: a planned device without a MAC address cannot be matched to its firmware write. Rule 4 therefore also applies on submit.

## Natural Keys and Identity

- The site natural key is `site_id`. It comes from the Mist organization site list.
- The device natural key inside a plan is `mac`. The same MAC address may appear in another plan.
- The child key `child_id` is unique within one plan. Its value includes a random UUID, so the value differs between plans.
- The view reads the keys without changing them. It sorts nothing and it renames nothing.

## State Transitions

- The view is read-only. It makes no transition.
- The plan states in the existing aggregate code are `planned`, `submission_claimed`, and the final states. The completeness check runs on each submit request for a plan that holds child records. It runs before the existing claim and replay checks. An incomplete plan therefore never reaches the claim logic.
- The completeness result is not stored. The view recomputes it on each read and on each submit request.

## Stored Shape Compatibility

A plan saved before this change has the same keys. No migration runs. A plan with missing keys follows the completeness rules. A plan with no child record keeps the AP-only path (FR-012).
