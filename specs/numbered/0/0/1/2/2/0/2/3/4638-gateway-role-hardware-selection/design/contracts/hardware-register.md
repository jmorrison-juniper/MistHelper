# Contract: Hardware evidence register

This contract defines the rows of `conversion/hardware/register.py`. Each row cites local evidence. Each row stays blocked until its evidence and its tests pass. Issue 4634 confirms the field semantics before merge.

## Revision and rules

- `CURRENT_REVISION` is `openapi-b7fc2bfb-mistapi-0.64.1`. It names the OpenAPI blob `b7fc2bfb` on `main` and the installed mistapi 0.64.1 package.
- Each row carries a `revision` string. A row with a different revision yields blocker `evidence_revision_stale`.
- A row is `verified` only when it has one inventory line and at least one WAN or LAN port line. Each cited line is a local line in the OpenAPI file or the cabling text in that file.
- Port names follow `^(ge|xe)-[0-9]+/[0-9]+/[0-9]+$`. The LTE name `cl-1/0/0` is not part of the register.
- A port with a documented HA, fxp0, or OOB role is not selectable for WAN or LAN. Those roles appear in the citations below.
- Open-ended ranges, such as `ge-0/0/3-` in the cabling text, are not expanded. A closed range, such as `ge-0/0/1-6` in the device model example, expands to each named port.
- The register holds no VRF support value. Issue 4640 must not enable `vrf_config.enabled` for any model from this register (analysis U-7).

## Rows

| Family | Model | Status | Inventory evidence (OpenAPI line) | Selectable ports and usage | Port evidence and exclusions | Blocker |
| --- | --- | --- | --- | --- | --- | --- |
| srx | SRX300 | verified | Line 48412, device example with `model: SRX300`. | `ge-0/0/7` wan, `ge-0/0/3` lan | Line 29725: `ge-0/0/0` and `ge-0/0/7` are default WAN ports. Line 29729: `ge-0/0/3-` for LAN. Excluded: `ge-0/0/0` (line 29726, OOB after cluster), `ge-0/0/1` (line 29734, ha_control), `ge-0/0/2` (line 29728, ha_data). | none |
| srx | SRX320 | verified | Line 47236, device model example with `model: SRX320`. Line 57027 (`gateway_model`). Line 107665 (stats example). | `ge-0/0/7` wan, `ge-0/0/5` lan, `ge-0/0/6` lan | Lines 47221 and 47223: `lan_ports: ge-0/0/1-6` and `wan_ports: ge-0/0/0,ge-0/0/7`. Excluded: `ha_fxp0_port` `ge-0/0/0` (line 47218), `ha_control_port` `ge-0/0/1` (line 47216), `ha_data_ports` `ge-0/0/2` (line 47217), `ha_wan_ports` `ge-0/0/3` (line 47220), `ha_lan_ports` `ge-0/0/4` (line 47219). LTE `cl-1/0/0` (line 47222) is out of scope. | none |
| srx | SRX340 | blocked | None. Cabling heading only (line 29744). | none | Lines 29746, 29747, and 29750 name WAN and LAN ports. | `model_without_inventory_sample` |
| srx | SRX345 | blocked | None. Cabling heading only (line 29744). | none | Same cabling lines as SRX340. | `model_without_inventory_sample` |
| srx | SRX380 | blocked | None. Cabling heading only (line 29744). | none | Same cabling lines as SRX340. Line 29749 names `xe-0/0/16` for fabric only. | `model_without_inventory_sample` |
| srx | SRX550 | blocked | None. Cabling sections at lines 29750 and 29776. | none | Lines 29755 and 29756 (`ge-0/0/3` WAN, `ge-0/0/4-` LAN). Both sections agree. | `model_without_inventory_sample` |
| srx | SRX1500 | blocked | None. Cabling sections at lines 29757 and 29782. | none | Line 29758 names cluster members `ge-0/0/0,ge-5/0/0`. Line 29784 names `ge-0/0/0,ge-7/0/0`. The sections conflict. | `model_evidence_conflict` |
| srx | SRX1600 | blocked | None. Cabling section at line 29788. | none | Lines 29790 to 29794 name WAN and LAN ports. | `model_without_inventory_sample` |
| srx | SRX4100 | blocked | None. Cabling sections at lines 29763 and 29794. | none | Lines 29765 and 29797 name `xe-0/0/0` WAN and `xe-0/0/1-` LAN. | `model_without_inventory_sample` |
| ssr | SSR120 | blocked | Line 50625, device search example with `model: SSR120`. Line 58160 (version list). | none | No local line names SSR WAN or LAN port roles. | `port_evidence_absent` |

Each family and model not in this table yields blocker `model_unknown`. The VSRX model is not in the table. Lines 29766 to 29771 describe a virtual platform.

## Mistapi and SDK references

These references are evidence only. The converter makes no call to them.

| Reference | Local path | Line |
| --- | --- | --- |
| `listDeviceModels` | `.venv\Lib\site-packages\mistapi\api\v1\const\device_models.py` | 17 |
| `getOrgInventory` with `model` parameter | `.venv\Lib\site-packages\mistapi\api\v1\orgs\inventory.py` | 17 and 21 |
| `listOrgGatewayTemplates` | `.venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py` | 17 |

## Public view

`HardwareRegister.options()` returns the revision and the families. For each model, it returns `status`, `blocker`, and the `ports` map from port name to usage. Blocked rows return an empty `ports` map. The page uses this view to build the model options and the port rows.
