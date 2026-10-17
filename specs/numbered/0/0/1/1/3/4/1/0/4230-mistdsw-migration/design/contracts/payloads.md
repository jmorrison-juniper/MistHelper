# Generated Payload Contracts

## Site Variables

CSV header: `name` followed by site names in input order.
Each subsequent row starts with `{{variable_name}}`.
All values are strings. Absent optional values are empty cells.
Do not replace this transposed interchange format with ordinary row-per-store CSV.

For each prefix `sensitive_data`, `trusted`, `untrusted`, and `communications`, produce these seven suffixes:
`vlan_id`, `network`, `cidr`, `mask`, `gw`, `dhcp_start`, and `dhcp_end`.
Also produce `snips_supernet` and seven `guest_wifi_*` variables.
The baseline has 36 variable rows plus the header.
Management adds five `netmgmt_*` rows: VLAN, network, CIDR, mask, and gateway.
WAN adds four `wan1_*` rows: network, CIDR, mask, and gateway.
A mixed batch uses the ordered union of variable names.
The largest supported variable set has 45 rows plus the header.

Four store VLANs use values 101 through 104 and consecutive `/24` subnets.
Defaults use the first usable address as gateway and `.2` through `.254` as the DHCP pool.
For an explicit gateway inside the pool, select the larger contiguous remaining side.
If both sides have equal size, select the upper side.
Reject an empty resulting pool.
Guest values come from the approved profile, not conflicting source constants.
Preserve `{{...}}` syntax without interpreting it as a template language.

## Network and Service Bundle

The ten names are `sensitive`, `trusted`, `untrusted`, `communications`, `guest`, `red`, `aetrex`, `just-retail`, `imbox`, and `realo`.
These are interoperability names, not copied templates.
Each individual network is a JSON object with `name`, `subnet`, `vlan_id`, `gateway`, and access settings.
The first four use variable-reference strings for subnet, VLAN, and gateway.
The six static networks use a literal subnet string, integer VLAN, and gateway string.
Access settings require explicit approved-profile values.
Source examples enable internal and unrestricted internet access. Do not treat that policy as a safe default.

Produce ten `<name>_network.json` files and `all_networks.json`, an array of ten objects.
Produce four `<name>_service.json` files and `all_services.json`, an array of four objects.
Services have `name`, `type`, `addresses`, `specs`, and `traffic_type`.
Source examples use custom services, variable subnet addresses, protocol `any`, and traffic type `default`.
The approved profile must confirm these policies before generation.
Network generation must not print or use the source organization identifier.
The bundle contains 16 network and service files.

## Switch Transformation

Input must be a JSON object with an object-valued `networks` field.
Supported network keys map to the four variable prefixes.
Replace only each supported network's `vlan_id` and `subnet` fields.
Preserve unrelated nonsecret settings, including additional supported subnet fields.
Missing required network keys are validation errors, not successful partial transformations.
Remove top-level `id`, `org_id`, `created_time`, and `modified_time` from export artifacts.
Show these removals in the difference summary.
Unknown credential fields block export until the safe-field rules cover them.

## Gateway Transformation

Input must have object-valued network and port sections and an array-valued service-policy section when present.
Create `ip_configs` with ten network entries.
Each entry contains `type`, `ip`, and `prefix_length`.
Variable networks use reference strings. Static prefix lengths are integers.
Create `dhcpd_config` with Boolean `enabled` and ten matching local DHCP entries.
Each entry has `type`, `ip_start`, `ip_end`, `gateway`, `dns_servers`, `options`, `lease_time`, and `fixed_bindings`.
DNS servers, lease time, and policy choices come from the approved profile.

Require the operator to select the LAN ports that receive the ten-network list.
Preserve all WAN and unselected port settings.
Expand `lan` tenants into the four variable-network names only after review.
Preserve other tenants in order without duplicates.
Do not widen access to the six static networks implicitly.
Remove the same four top-level metadata fields as the switch artifact.
Produce separate `ip_configs.json` and `dhcpd_config.json` objects with their named top-level wrappers.
These two files supplement the complete gateway-template artifact.

## Cross-Artifact Validation

Every variable reference must exist in the CSV variable vocabulary or approved profile.
Network, service, switch, and gateway names must match.
Reject duplicate keys, duplicate VLANs, unintended subnet overlaps, or unresolved profiles.
Compare approved values across artifacts rather than trusting a committed source example.
Treat local Mist schema validation as B4 evidence, not proof of a successful live deployment.
No artifact can contain a credential, customer default, or source organization identifier.
