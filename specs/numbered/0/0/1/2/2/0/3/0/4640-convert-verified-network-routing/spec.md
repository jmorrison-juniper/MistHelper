# Feature Specification: Convert Verified Network and Routing Settings

**Feature Branch**: `feat/4640-convert-verified-network-routing` (planned, not created)

**Created**: 2026-11-26

**Status**: Draft. Implementation waits for the prerequisites in `plan.md`.

**Issue**: [#4640](https://github.com/jmorrison-juniper/MistHelper/issues/4640), "[Spec]: Convert verified network and routing settings". Labels: `feature`, `web-portal`. Created 2026-11-07. No comments. No linked pull request.

**Parent**: [#4224](https://github.com/jmorrison-juniper/MistHelper/issues/4224), "Integrate Mist Cisco config converter".

**Input**: User description: "Complete T013–T014. Add synthetic conversion tests and implement only verified interface addressing, WAN/LAN, VLAN and aggregation, DHCP pools and exclusions, static routes, VRFs, BGP, DNS, NTP, and variable behavior."

**Record path**: `specs\numbered\0\0\1\2\2\0\3\0\4640-convert-verified-network-routing`

## Scope

This record covers tasks T013 and T014 of the full-parity map in merged PR #4596. It also covers the package change that T014 needs. The change adds no cloud call, no route, and no shared portal file.

The DNS behavior of the existing offline component stays in place. Its values, its review, and its export rules do not change.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Convert interface addresses with explicit roles (Priority: P1)

An engineer assigns each physical Cisco interface to one Mist port and one role, WAN or LAN. The converter places each verified address in the port or network that the role selects.

**Why this priority**: Addresses and roles define every other network setting. A wrong role changes the whole port mapping.

**Independent Test**: Use synthetic IOS text and explicit assignments. No role comes from a hostname, a comment, or a source hint.

**Acceptance Scenarios**:

1. **Given** a WAN assignment and a contiguous IPv4 mask, **When** the converter runs, **Then** the WAN port holds the address and prefix.
2. **Given** an SVI with an IPv4 address, **When** the converter runs, **Then** the network address configuration holds that address and its prefix length.
3. **Given** an interface without an assignment, **When** the converter runs, **Then** the proposal lists an unresolved item and emits no value for that interface.
4. **Given** an interface with an assignment but no role, **When** the converter runs, **Then** the proposal lists an unresolved item for the missing role.

---

### User Story 2 - Convert VLANs and aggregates (Priority: P1)

An engineer maps access VLANs, trunk VLAN lists, WAN VLANs, and port channels to Mist ports. The converter validates each VLAN ID and each member port.

**Why this priority**: VLAN and aggregation errors can move traffic into the wrong broadcast domain.

**Independent Test**: Use synthetic access, trunk, subinterface, and port-channel input with invalid VLAN IDs and conflicting members.

**Acceptance Scenarios**:

1. **Given** access and trunk VLANs from 1 to 4094, **When** the converter runs, **Then** each VLAN appears as a named network with its VLAN ID.
2. **Given** VLAN ID 0, VLAN ID 4095, or a reversed range, **When** the converter runs, **Then** the proposal lists an unresolved item.
3. **Given** a port channel whose members share one role, **When** the converter runs, **Then** one aggregate port key holds all members and the LACP mode.
4. **Given** a port channel whose members have different roles, **When** the converter runs, **Then** the proposal lists an unresolved item for the aggregate.

---

### User Story 3 - Convert DHCP pools with verified ranges (Priority: P1)

An engineer reviews DHCP pools that exist for converted networks. The converter emits a pool only when its range follows from leading or trailing exclusions.

**Why this priority**: A wrong DHCP range can hand out addresses that belong to a gateway or a server.

**Independent Test**: Use synthetic pools with no exclusions, leading exclusions, trailing exclusions, middle exclusions, overlaps, invalid masks, and invalid lease times.

**Acceptance Scenarios**:

1. **Given** a leading exclusion covers the gateway address, **When** the converter runs, **Then** the pool starts after that exclusion.
2. **Given** a middle exclusion in a pool, **When** the converter runs, **Then** the proposal lists an unresolved item and no pool.
3. **Given** two pools whose ranges overlap, **When** the converter runs, **Then** the proposal lists an unresolved item for both pools.

---

### User Story 4 - Convert static routes, VRFs, and BGP (Priority: P2)

An engineer reviews static routes, VRF membership, and BGP sessions. The converter emits only the fields with verified Mist contracts.

**Why this priority**: Routing settings change the path of every connected host. The converter must not invent a next hop, a transport, or a prefix.

**Independent Test**: Use synthetic routes, VRF members, and BGP neighbors with unsupported forms and credentials.

**Acceptance Scenarios**:

1. **Given** a static route with an IPv4 next hop, **When** the converter runs, **Then** the extra route list holds the CIDR and next hop.
2. **Given** a route with a distance, a name, or an interface next hop, **When** the converter runs, **Then** the proposal lists an unresolved item.
3. **Given** an interface in a VRF with a converted network, **When** the converter runs, **Then** the VRF instance lists that network as a member.
4. **Given** a BGP neighbor with a password, **When** the converter runs, **Then** the proposal emits no password and lists an unresolved item for it.

---

### User Story 5 - Convert NTP, DNS suffix, and variables (Priority: P2)

An engineer reviews NTP servers, the DNS domain name, and variable tokens. The converter emits only IPv4 NTP servers, valid domain names, and variable tokens in fields that accept variables.

**Why this priority**: NTP and DNS errors affect every device that uses the converted template.

**Independent Test**: Use synthetic NTP servers with hostnames and options, a domain name with conflicting values, and variable tokens in allowed and unallowed fields.

**Acceptance Scenarios**:

1. **Given** IPv4 NTP servers, **When** the converter runs, **Then** the template holds each server once in input order.
2. **Given** an NTP hostname or a server with an option, **When** the converter runs, **Then** the proposal lists an unresolved item for that line.
3. **Given** a variable token in an allowed field, **When** the converter runs, **Then** the token stays and its name is listed as required.
4. **Given** a variable token in an unlisted field, **When** the converter runs, **Then** the proposal lists an unresolved item.

---

### Edge Cases

- A WAN address on a DHCP client line has no verified Mist field, so the converter lists it as unresolved.
- A physical interface with no assignment and a Loopback or Tunnel interface both produce unresolved items.
- Two Cisco interfaces assigned to one Mist port produce unresolved items for both interfaces.
- A `shutdown` line has a property name, but the schema text reverses its meaning. The converter lists it as unresolved.
- A speed or duplex value has no verified format, so the converter lists it as unresolved.
- A SRX-only untagged network on an SSR assignment produces an unresolved item.
- A DHCP pool whose network matches no converted network produces an unresolved item.
- Caution: A reviewer can miss an unresolved item when the list is short. The proposal must list every unresolved item with its line number.
- A variable token in a VLAN ID produces an unresolved item, because the network name rule needs a fixed VLAN ID.
- Secret-bearing lines never appear in an unresolved reason. The command label omits each value.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The DNS converter MUST keep `ip name-server` values, review rules, and export rules unchanged.
- **FR-002**: The converter MUST emit a WAN address in the port IP configuration and a LAN address in the network IP configuration.
- **FR-003**: The converter MUST take each WAN or LAN role from the explicit port assignment only.
- **FR-004**: The converter MUST accept VLAN IDs from 1 to 4094 and reject other VLAN values with an unresolved item.
- **FR-005**: The converter MUST map each aggregate to one port key with one role and one LACP mode.
- **FR-006**: The converter MUST emit a DHCP pool only when its range follows from leading or trailing exclusions and no overlap exists.
- **FR-007**: The converter MUST emit static routes only as IPv4 destination CIDR keys with IPv4 next hops.
- **FR-008**: The converter MUST map VRF members to VRF instances and MUST list each unsupported VRF field as unresolved.
- **FR-009**: The converter MUST emit BGP sessions only with a derived transport and verified fields, and MUST omit prefixes and credentials.
- **FR-010**: The converter MUST emit only IPv4 NTP servers without options.
- **FR-011**: The converter MUST map `ip domain name` to the DNS suffix list and MUST reject invalid or conflicting domain names.
- **FR-012**: The converter MUST keep variable tokens only in fields that accept variables and MUST list each required variable name without a value.
- **FR-013**: The converter MUST emit a key only when the mapping register holds a row for that key with an OpenAPI line.
- **FR-014**: The converter MUST show each unresolved item with its source line, a secret-free command label, and a reason text.
- **FR-015**: The converter MUST run offline. It MUST NOT open a socket, write a file, or call Mist. It MUST NOT place a credential or a source description in output or logs.
- **FR-016**: Each implemented family MUST have positive and negative tests written before its implementation.
- **FR-017**: The change MUST replace `conversion.py` with a `conversion/` package. The converter root MUST keep five children. The change MUST add only one import line to `routes.py`.

### Mist Cloud Transport Requirements

This record makes no Mist REST call. The emitted objects use the gateway template field names that the OpenAPI document defines. The future write path uses the mistapi method `orgs.gatewaytemplates.createOrgGatewayTemplate`, which accepts `body: dict | list`. That method is outside this record. The field evidence appears in `design\contracts\mist-field-register.md`.

### Key Entities

- **Port assignment**: One Cisco interface, one Mist port, one role, and one family. Owned as a type by this record and produced by issue #4638.
- **Network fragment**: The partial gateway template emitted for network and routing families. Holds verified keys, required variable names, and unresolved items.
- **Unresolved item**: One source line, one secret-free command label, and one reason text.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each implemented family has at least one positive test and one negative test.
- **SC-002**: The DNS output for inputs without a domain name changes only in the first known-gap sentence.
- **SC-003**: The conversion tests record zero socket connections, zero file writes, and zero Mist calls.
- **SC-004**: A guard test proves that every emitted key has a mapping register row with an OpenAPI line.
- **SC-005**: Each applicable local gate passes, and the pull request lists each exact result.
- **SC-006**: The converter root holds five children. The `conversion/` root holds three children after this record. No class holds more than five members.

## Assumptions

- The input uses IOS-style text with one command per line. Banner handling follows the existing DNS converter.
- The 16 MiB upload bound and UTF-8 rule stay unchanged.
- Issue #4638 supplies one port assignment for each physical interface that the converter uses.
- Mist `ae_idx` values are strings that hold integers from 0 to 127, as the schema text states.
- The schema field `disabled` has an unverified meaning, so no `shutdown` value is emitted.
- Generated network names use the form `VLAN` followed by the VLAN ID.
- Each fixture is synthetic and original. The observed source code, tests, mapping prose, and assets are not reused.

## Out of Scope

- Changes to `routes.py` beyond one import line, to the presentation files, and to `web_portal/`.
- The composed proposal and its known-gap text. Issue #4641 owns that work.
- Hardware selection, model inventory, and the Branch, Hub, and Standalone role mapping. Issue #4638 owns that work.
- Management, security, cellular, and flow-export families. Issue #4639 owns that work.
- IPv6, DHCP relay, DHCP fixed bindings, DHCP options, and VRF route distinguishers.
- BGP prefix advertisement, BGP authentication keys, and BGP options other than the verified fields.
- Interface speed, duplex, MTU, descriptions, and redundancy.
- Cloud discovery, apply, backup, restore, and administration.
- Changelog fragments and documentation changes. Decision D-16 explains this.

## Clarifications

### Session 2026-11-26

- Q: Which source defines the WAN or LAN role? Recorded answer: The explicit port assignment from issue #4638 defines the role. Hints in the source never set a role.
- Q: How does a DHCP pool get its range? Recorded answer: The range follows from leading and trailing exclusions. Middle exclusions and overlaps are unresolved.
- Q: Which name does a generated VLAN network use? Recorded answer: The name is `VLAN` followed by the VLAN ID. A variable VLAN ID is unresolved.
- Q: Does the DNS known-gap text change? Recorded answer: The first sentence changes to include the domain name. Decision D-10 records this change.
- Q: How does the converter treat credentials? Recorded answer: The converter omits every credential value and lists the line as unresolved. Decision D-18 asks the owner for the later credential policy.
