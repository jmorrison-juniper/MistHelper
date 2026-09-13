# Network node device catalog

This catalog gives the planner the optic host constraints for common network
nodes. It is a planning index, not a release-specific hardware support list.
The exact switch SKU, port profile, firmware release, and vendor part number
must be checked before procurement.

| Vendor | Device family | Node role | Optic host ports | Supported host classes | Device-side limits |
|---|---|---|---|---|---|
| Juniper | EX2300-C, EX2300, EX3400 | access switch | SFP/SFP+ uplinks, model dependent | 1G SFP and 10G SFP+ | Uplink speed and stacking use vary by model. |
| Juniper | EX4100, EX4100-F | access switch | SFP28 and SFP+ uplinks, model dependent | 10G SFP+ and 25G SFP28 | Confirm port profile and VC role before using 25G. |
| Juniper | EX4400 | access switch | SFP28 uplinks and QSFP28 uplinks, model dependent | 10G, 25G, and 100G families | Breakout and VC support depend on the uplink module and release. |
| Juniper | EX4650 | aggregation switch | SFP28 and QSFP28 | 10G, 25G, 40G, and 100G families | QSFP breakout requires a supported port mode. |
| Juniper | QFX5120 | data-center leaf | SFP28 and QSFP28 | 10G, 25G, 40G, and 100G families | Confirm the front-panel port group and breakout map. |
| Juniper | QFX5200 | data-center leaf | SFP28 and QSFP28 | 10G, 25G, 40G, and 100G families | Optic coding and speed profile are release dependent. |
| Juniper | QFX5700 | data-center spine/leaf | QSFP28 and QSFP-DD, model dependent | 40G, 100G, 200G, and 400G families | Confirm the exact chassis and line-card port type. |
| Juniper | MX204 | edge router | SFP/SFP+, QSFP28 | 1G, 10G, 40G, and 100G families | Use the MX204 supported transceiver table for each port. |
| Juniper | MX304, MX480, MX960 | edge router | MIC and MPC ports | SFP+, SFP28, QSFP+, QSFP28, model dependent | The installed MPC or MIC controls the host cage. |
| Juniper | PTX1000, PTX10000 | core router | QSFP28, QSFP56, QSFP-DD, model dependent | 100G, 200G, and 400G families | Line-card and PIC support controls the optic list. |
| Mist | EX cloud-managed switches | access and aggregation | Inherited Juniper EX port cages | Same as the underlying EX model | Mist management does not expand the hardware optic matrix. |
| Mist | WAN Edge appliance | branch gateway | Model-specific SFP/SFP+ ports | Usually 1G or 10G optics listed for the model | Confirm the appliance data sheet and port speed profile. |
| HPE Aruba Networking | CX 6100/6200 | access switch | SFP or SFP+ uplinks, model dependent | 1G and 10G families | Verify the exact model suffix and uplink speed. |
| HPE Aruba Networking | CX 6300 | access and aggregation switch | SFP28 and QSFP28, model dependent | 10G, 25G, 40G, and 100G families | VSF and breakout modes limit available ports. |
| HPE Aruba Networking | CX 8320/8360 | data-center leaf | SFP28 and QSFP28 | 10G, 25G, 40G, and 100G families | Use the Aruba transceiver guide for supported coding. |
| HPE Aruba Networking | CX 9300 | data-center spine/leaf | QSFP28 and QSFP-DD, model dependent | 100G, 200G, and 400G families | Exact port group and release determine supported optics. |

## Planner compatibility keys

Use these keys when joining a device record to `fiber-optic-catalog.json`:

* `device_vendor`
* `device_family`
* `device_model`
* `port_id`
* `host_form_factor`
* `host_speed_gbps`
* `breakout_mode`
* `supported_optic_part_numbers`
* `firmware_release`

Reject a match when the device does not list the optic part number. If the part
number is unknown, return the match as `needs_vendor_validation`, not as
compatible.

## Sources

* Juniper Networks hardware documentation:
  https://www.juniper.net/documentation/us/en/hardware/
* HPE Aruba Networking hardware documentation:
  https://www.arubanetworks.com/techdocs/hardware/
* Mist switch documentation:
  https://www.mist.com/documentation/

