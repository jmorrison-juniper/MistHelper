# Contract: Mist Payload Fields

This contract records the schema evidence for the request bodies and the local rules for each write family. The tests build the top-level allowlist from the schema properties when they run. This file lists the counts and the rules. It does not copy the full property lists.

Caution: The bundled schemas do not forbid unknown top-level fields for most objects. The local allowlist (D-6) rejects such fields in the tests and in future code.

## Schema Evidence

| Schema | Used by | Required fields | Property count | Unknown top-level fields | Composition | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `site` | W-01, W-02 | `name` | 20 | accepted | none | `sitetemplate_id` is a UUID string or null |
| `site_setting` | W-13 | none | 102 | accepted | none | No required field, so an empty body passes the schema |
| `mist_device` | W-04 | `type` in each variant | not applicable | rejected in each variant | one of `device_ap`, `device_switch`, `device_gateway`, by `type` | Type constants are read-only |
| `deviceprofile` | W-08, W-09 | `type` for AP, `name` and `type` for gateway and switch | not applicable | rejected in each variant | one of `deviceprofile_ap`, `deviceprofile_gateway`, `deviceprofile_switch`, by `type` | The gateway type is not read-only. The switch type is read-only. |
| `gateway_template` | W-05, W-06 | `name` | 33 | accepted | none | `type` and `dns_servers` are the verified fields |
| `inventory_update` | W-03 | `op` | 8 | accepted | none | `op` has five values |
| `mac_addresses` | W-11, W-12 | `macs` | 1 | accepted | none | `macs` needs at least one unique string and has no pattern |
| `network` | W-14, W-15 | `name` | 19 | accepted | none | `vlan_id` is a string or an integer from 1 to 4094 |
| `service` | W-17, W-18 | none | 27 | accepted | none | No required field, so an empty body passes the schema |
| `org_service_policy` | W-20, W-21 | none | 17 | accepted | none | No required field, so an empty body passes the schema |

Response schemas for successful writes are `site`, `site_setting`, `mist_device`, `deviceprofile`, `gateway_template`, `network`, `service`, `org_service_policy`, `response_org_inventory_change`, and `response_assign_success`. The response schemas do not require `id` (U-07).

## Semantic Notes From the Schema Descriptions

| Schema and field | Schema text (summarized) | Effect on this record |
| --- | --- | --- |
| `inventory_update.op` | Five values: `upgrade_to_mist`, `downgrade_to_jsi`, `assign`, `unassign`, and `delete`. `delete` removes inventory, and an assigned device is unassigned. | Warning: `delete` is destructive. W-03 stays disabled. |
| `inventory_update.macs` | Required for `assign`, `unassign`, `upgrade_to_mist`, and `downgrade_to_jsi`. | The rule is recorded for later families. |
| `inventory_update.site_id` | UUID string. The target site when `op` is `assign`. | The rule is recorded for later families. |
| `mac_addresses.macs` | Unique MAC addresses, at least one. | No pattern is defined (A-09). |
| `site.sitetemplate_id` | UUID string or null. The description names no meaning for null. | Null is refused (D-8). |
| `network.vlan_id` | Numeric VLAN ID from 1 to 4094, or a template variable string. | The integer range is recorded. |
| `gateway_template.type` | `spoke` or `standalone`. Default `standalone`. | The converter uses the same two values (`models.py` line 51). |
| `gateway_template.dns_servers` | Global DNS settings. `ip_config` and `oob_ip_config` DNS settings overwrite this list. | The override is recorded as a limit (A-20). |

## Local Rules

| Rule | Source | Test |
| --- | --- | --- |
| The top-level keys of a request body must appear in the schema properties. | D-6 | Tests 30 |
| A request body must be an object. A list is refused for each write. | D-7 | Test 32 |
| A null `sitetemplate_id` is refused as unassignment. | D-8 | Test 31 |
| A service or service policy body must hold `name`. | D-18 | Test 32 |
| The gateway template body holds only `name`, `type`, and `dns_servers`. | D-12 | Test 20 |

## Planned Synthetic Fixtures

Each fixture uses synthetic values only. The IP addresses use the documentation range 192.0.2.0/24. The UUIDs and MAC addresses are synthetic.

| Fixture ID | Operation | Expectation | Mechanism | Test |
| --- | --- | --- | --- | --- |
| GT-POS-01 | W-05 | accept `name`, `type` `standalone`, and `dns_servers` `192.0.2.53` | schema | Test 20 |
| DP-POS-01 | W-08 | accept a gateway profile with `name` and `type` `gateway` | schema | Test 21 |
| DP-POS-02 | W-08 | accept a switch profile with `name` and `type` `switch` | schema | Test 22 |
| INV-POS-01 | W-03 | accept `op` `assign` with `macs` and a synthetic `site_id` UUID | schema | Test 23 |
| MAC-POS-01 | W-11 | accept `macs` with one synthetic value | schema | Test 24 |
| GT-NEG-01 | W-05 | reject `type` `hub` | schema | Test 25 |
| DP-NEG-01 | W-08 | reject a gateway profile with `type` `switch` | schema | Test 26 |
| DP-NEG-02 | W-08 | reject a switch profile with the gateway-only `ip_configs` key | schema | Test 27 |
| MAC-NEG-01 | W-11 | reject an empty `macs` list and a duplicate `macs` list | schema | Test 28 |
| INV-NEG-01 | W-03 | reject `op` `unknown` | schema | Test 29 |
| ALLOW-01 | W-01 | accept an unknown top-level key by schema and reject it by allowlist | allowlist | Test 30 |
| SITE-NULL-01 | W-02 | accept `sitetemplate_id` null by schema and refuse it by local rule | allowlist | Test 31 |
| BODY-LIST-01 | W-08 | reject a list body by schema | schema | Test 32 |
| SVC-NONAME-01 | W-17 | accept an empty body by schema and refuse it by local rule | allowlist | Test 32 |

Test numbers match the planned test list in `tasks.md`.

## Verified Field Status

| Family | Verified fields (schema evidence) | Fixtures passing | Field status |
| --- | --- | --- | --- |
| F-04 and F-05 (W-05, W-06) | `name`, `type`, `dns_servers` | pending (GT-POS-01, GT-NEG-01) | partial |
| F-06 to F-08 (W-08, W-09, W-11) | `type` discriminator and required fields | pending | partial |
| F-01 and F-02 (W-01, W-02) | `name` | pending | partial |
| F-03 (W-13) | none beyond the object type | pending | partial |
| Not in a family (W-03, W-04, W-14 to W-21) | none beyond the object type | pending | partial |

Field status changes to `verified-present` only after the fixtures for the family pass.
