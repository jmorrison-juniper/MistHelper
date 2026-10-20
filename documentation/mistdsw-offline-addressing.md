# Offline MistDSW Addressing

Issue #4288 adds a typed IPv4 addressing core for offline store preparation.
The core returns ordered variables from one explicit request.
It does not read or write files, call Mist, or select an organization profile.

## Input Values

Supply a store name, an IPv4 base address, and an acknowledgment choice.
Supply the supernet and child prefixes, gateway offset, and DHCP offsets.
Supply each network name, VLAN ID, optional gateway, and output variable key.
Supply each optional network CIDR, gateway, name, and optional VLAN ID.
The core does not set organization values or profile approvals.

## Calculation Rules

The core normalizes the base address with the supplied supernet prefix.
It requires acknowledgment when normalization changes the network address.
It creates one ordered child network for each supplied network definition.
It rejects invalid IPv4 addresses, VLAN IDs, names, prefixes, and overlaps.
It accepts a gateway only when that address is a usable host in its network.
It excludes an in-pool gateway from DHCP and selects the larger remaining range.
It selects the upper range when both sides have equal size.
It returns immutable string pairs in deterministic input order.

## Scope Limits

All labels, VLAN IDs, prefixes, gateways, host offsets, and output keys come from the request.
No Guest or Realo value is selected.
B2 and all profile approvals remain unresolved.
This core does not prepare CSV, transform templates, or create network payloads.
It does not add a portal, command, menu operation, storage, or Mist API request.
The broader migration still needs its documented release approvals.

The [migration plan](../specs/numbered/0/0/1/1/3/4/1/0/4230-mistdsw-migration/plan.md)
records the approved boundary.
The [migration tasks](../specs/numbered/0/0/1/1/3/4/1/0/4230-mistdsw-migration/tasks.md)
keep the remaining work open.
