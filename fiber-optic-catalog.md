# Fiber optic transceiver catalog

This catalog covers pluggable Ethernet optics used by Juniper, Mist, and Aruba
network devices. It records the fields that a planner needs to select an optic.

**Important:** A device must support the exact optic part number, speed, coding,
and software release. A matching form factor alone does not prove compatibility.
Use the device vendor hardware guide as the final approval source.

## Planner fields

| Field | Meaning |
|---|---|
| `family` | Optical module family and IEEE Ethernet rate |
| `form_factor` | Host cage size: SFP, SFP+, SFP28, QSFP+, QSFP28, QSFP56, or QSFP-DD |
| `fiber` | MMF, SMF, or direct-attach copper |
| `wavelength_nm` | Nominal optical wavelength |
| `reach_m` | Maximum link length for the stated fiber and speed |
| `connector` | Module-side connector |
| `duplex` | `duplex`, `bi_di`, or `dac` |
| `host_speed` | Required host interface speed |
| `compatibility` | Physical and protocol constraints |

## Transceiver families

Distances are maximum Ethernet channel distances. Loss budget, connector loss,
splice loss, and vendor limits can reduce the usable distance.

| Family | Form factor | Fiber | Wavelength | Reach | Connector | Host speed | Compatibility |
|---|---|---|---:|---:|---|---:|---|
| 1000BASE-SX | SFP | OM1/OM2/OM3/OM4 | 850 nm | 220/550/550/550 m | Duplex LC | 1G | Requires a 1G SFP host. OM1 is 220 m. OM2 or better is 550 m. |
| 1000BASE-LX | SFP | SMF or OM1-OM4 with mode-conditioning cable | 1310 nm | 5 km SMF, 550 m MMF | Duplex LC | 1G | Use SMF for the 5 km rating. MMF requires the vendor-approved mode-conditioning cable. |
| 1000BASE-ZX | SFP | SMF | 1550 nm | 70 km typical | Duplex LC | 1G | Long-reach optic. Confirm minimum receive power and attenuation range. |
| 1000BASE-BX | SFP | SMF | 1310/1490 nm | 10 or 40 km | Simplex LC | 1G | Must be paired with the complementary downstream/upstream wavelength. |
| 10GBASE-SR | SFP+ | OM1/OM2/OM3/OM4 | 850 nm | 33/82/300/400 m | Duplex LC | 10G | OM3 or OM4 is preferred. OM1 and OM2 have short limits. |
| 10GBASE-LRM | SFP+ | OM1/OM2/OM3/OM4 or SMF | 1310 nm | 220 m MMF, 10 km SMF with supported optic | Duplex LC | 10G | Use the specific vendor distance table. Do not assume LX behavior. |
| 10GBASE-LR | SFP+ | SMF | 1310 nm | 10 km | Duplex LC | 10G | Standard single-mode campus and metro optic. |
| 10GBASE-ER | SFP+ | SMF | 1550 nm | 40 km | Duplex LC | 10G | Verify attenuation range. Add an attenuator when the receive level is too high. |
| 10GBASE-ZR | SFP+ | SMF | 1550 nm | 80 km typical | Duplex LC | 10G | Vendor-specific in many platforms. Confirm DOM and coding support. |
| 10GBASE-BX | SFP+ | SMF | 1270/1330 nm or vendor pair | 10/20/40 km | Simplex LC | 10G | Install opposite wavelengths as a matched pair. |
| 25GBASE-SR | SFP28 | OM3/OM4 | 850 nm | 70/100 m | Duplex LC | 25G | Requires a 25G SFP28 host and an 802.3by-capable peer. |
| 25GBASE-LR | SFP28 | SMF | 1310 nm | 10 km | Duplex LC | 25G | Requires a 25G SFP28 host. Some hosts support 10G fallback. |
| 25GBASE-ER | SFP28 | SMF | 1310 nm | 40 km | Duplex LC | 25G | Vendor support is not universal. Confirm the device matrix. |
| 40GBASE-SR4 | QSFP+ | OM3/OM4 | 850 nm | 100/150 m | MPO-12 | 40G | Four parallel lanes. The MPO polarity and fiber cassette must match. |
| 40GBASE-LR4 | QSFP+ | SMF | 1310 nm | 10 km | Duplex LC | 40G | Four wavelengths are multiplexed into a duplex LC pair. |
| 40GBASE-ER4 | QSFP+ | SMF | 1310 nm | 40 km | Duplex LC | 40G | Confirm host support and receive power range. |
| 40GBASE-ESR4 | QSFP+ | OM3/OM4 | 850 nm | 300/400 m | MPO-12 | 40G | Extended SR family. Vendor naming differs. |
| 40GBASE-PLR4 | QSFP+ | SMF | 1310 nm | 10 km | MPO-12 | 40G | Parallel single-mode optic. It is not interchangeable with LR4. |
| 40GBASE-BiDi | QSFP+ | SMF | 1310/1550 nm | 10 km typical | Duplex LC | 40G | Requires a matched wavelength pair and vendor support. |
| 100GBASE-SR4 | QSFP28 | OM3/OM4 | 850 nm | 70/100 m | MPO-12 | 100G | Four 25G lanes. Use OM4 for the 100 m rating. |
| 100GBASE-SRBD | QSFP28 | OM3/OM4 | 850 nm | 70/100 m | Duplex LC | 100G | Two bidirectional 50G lanes. Must pair with the same SRBD family. |
| 100GBASE-LR4 | QSFP28 | SMF | 1310 nm | 10 km | Duplex LC | 100G | Four LAN WDM wavelengths. |
| 100GBASE-ER4 | QSFP28 | SMF | 1310 nm | 40 km | Duplex LC | 100G | Confirm attenuation and receive power limits. |
| 100GBASE-CWDM4 | QSFP28 | SMF | 1310 nm | 2 km | Duplex LC | 100G | Four CWDM wavelengths. Use a 2 km or shorter SMF span. |
| 100GBASE-PSM4 | QSFP28 | SMF | 1310 nm | 2 km | MPO-12 | 100G | Four parallel single-mode fibers. |
| 100GBASE-DR | QSFP28 or QSFP56 | SMF | 1310 nm | 500 m | Duplex duplex LC | 100G | Single 100G PAM4 lane. Peer must support 100G DR. |
| 200GBASE-SR4 | QSFP56 | OM3/OM4 | 850 nm | 70/100 m | MPO-12 | 200G | Four 50G PAM4 lanes. |
| 200GBASE-FR4 | QSFP56 | SMF | 1310 nm | 2 km | Duplex LC | 200G | Four CWDM PAM4 lanes. |
| 200GBASE-DR4 | QSFP56 | SMF | 1310 nm | 500 m | MPO-12 | 200G | Four 50G PAM4 lanes. Use an approved breakout when required. |
| 400GBASE-SR8 | QSFP-DD | OM4 | 850 nm | 70 m | MPO-16 | 400G | Eight 50G PAM4 lanes. MPO-16 polarity is required. |
| 400GBASE-FR4 | QSFP-DD | SMF | 1310 nm | 2 km | Duplex LC | 400G | Four 100G PAM4 wavelengths. |
| 400GBASE-LR4 | QSFP-DD | SMF | 1310 nm | 10 km | Duplex LC | 400G | Four 100G PAM4 wavelengths. |
| 400GBASE-DR4 | QSFP-DD | SMF | 1310 nm | 500 m | MPO-12 | 400G | Four 100G PAM4 lanes. |
| SFP passive DAC | SFP/SFP+ | Twinax copper | n/a | 0.5-5 m | SFP host ends | 1G/10G | A cable assembly, not a fiber optic. Both hosts must support the cable. |
| SFP28 passive DAC | SFP28 | Twinax copper | n/a | 0.5-3 m | SFP28 host ends | 25G | Use only in the supported DAC length and coding range. |
| QSFP+ passive DAC | QSFP+ | Twinax copper | n/a | 1-5 m | QSFP+ host ends | 40G | Both hosts need QSFP+ 40G support. |
| QSFP28 passive DAC | QSFP28 | Twinax copper | n/a | 1-5 m | QSFP28 host ends | 100G | Does not convert to optical 100G. |
| QSFP28-to-4xSFP28 DAC | QSFP28 to SFP28 | Twinax copper | n/a | 1-5 m | Breakout | 100G to 4x25G | The switch must support breakout mode and the stated lane map. |

## Form-factor rules

* SFP ports normally accept SFP and SFP+ modules only when the device permits
  speed fallback. A 1G optic does not become a 10G optic in an SFP+ cage.
* SFP28 ports can often run 10G or 25G. The device release and port profile
  control this behavior.
* QSFP+ is a 40G host. QSFP28 is a 100G host. QSFP56 is a 200G host.
* QSFP-DD is a 400G host. A QSFP-DD module can be mechanically smaller than
  the cage, but the device must explicitly support the module speed.
* MPO-12 and MPO-16 are not interchangeable. Record polarity, key orientation,
  lane count, and cassette type in the path plan.
* UPC and APC connectors must not mate. APC is not a substitute for UPC.
* BiDi modules require the complementary wavelength at the remote end.
* Breakout requires a supported host mode, lane map, and peer optic family.

## Compatibility decision

The planner should accept a path only when all values match:

1. The device port lists the optic form factor.
2. The device supports the optic host speed and breakout mode.
3. Both ends use the same Ethernet family or a documented interoperable pair.
4. Fiber type, connector, lane count, polarity, and wavelength match.
5. The route length is within the optic reach and the calculated loss margin.

## Sources

* IEEE 802.3 Ethernet standards, including 1000BASE-X, 10GBASE-X, 25GBASE-R,
  40GBASE-R, 100GBASE-R, 200GBASE-R, and 400GBASE-R.
* Juniper Networks, *Hardware compatibility and transceiver support*:
  https://www.juniper.net/documentation/us/en/hardware/
* HPE Aruba Networking, *Transceiver guide*:
  https://www.arubanetworks.com/techdocs/hardware/
* FS.com, *Optical transceiver and DAC compatibility guides*:
  https://www.fs.com/products/36735.html
* Fiber Optic Association, `documentation/foa/01-fiber-basics.md` and
  `documentation/foa/04-loss-budget.md`.

