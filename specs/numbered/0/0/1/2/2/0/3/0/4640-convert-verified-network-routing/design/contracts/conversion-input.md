# Contract: Conversion Input

## Scope

This contract defines the input of the network conversion and the DNS conversion. Issue #4638 supplies the port assignments. Issue #4636 supplies the source type.

## Source Configuration

The source value comes from `state/intake.py` after issue #4636 merges. Today the same class is in `models.py` at line 38.

| Field | Type | Rule |
| --- | --- | --- |
| `content` | `str` | UTF-8 text with no null character. Size is at most 16 MiB. |
| `name` | `str` | One to 120 visible characters. No control character. |
| `kind` | `str` | `standalone` or `spoke`, until issue #4638 changes the role contract (D-17). |

The validation rules of `SourceConfiguration.read` do not change.

## Port Assignment

The type `PortAssignment` is a `TypedDict` in `conversion/common/fragment.py`. Issue #4638 produces values of this type.

| Field | Type | Rule |
| --- | --- | --- |
| `cisco_interface` | `str` | The exact IOS interface name, such as `GigabitEthernet0/0`. Unique in the list. |
| `mist_port` | `str` | The form `ge-<fpc>/<pic>/<port>`. Unique in the list. See Unverified UV-11. |
| `role` | `str` | The value `wan` or `lan`. Lowercase. |
| `family` | `str` | The value `SRX` or `SSR`. Used only for the untagged network rule (D-4 and test 13). |

## Boundary Errors

- Raise `ValueError` for a missing field, an empty `cisco_interface`, an invalid `mist_port` form, an invalid `role`, an invalid `family`, or a duplicate `cisco_interface`.
- Each error message names the field and the rule. The message does not echo the rejected value.
- A duplicate `mist_port` raises no error. Each interface that uses that port becomes an unresolved item with the reason key `PORT_CONFLICT`.

## Operation

The network entry point has this signature.

```text
IOSNetworkConverter.convert(source: SourceConfiguration, assignments: list[PortAssignment]) -> NetworkFragment
```

The method runs these steps in order.

1. Split the source into blocks with line numbers.
2. Validate the assignments and mark duplicate ports.
3. Map interfaces, networks, VLANs, aggregates, and variables.
4. Map static routes, VRF members, and BGP sessions from the converted subnets.
5. Map DHCP pools from the converted networks and gateway addresses.
6. Map NTP servers.

The method performs no input or output operation. It opens no socket and writes no file.

## DNS Operation

The DNS entry point keeps its signature.

```text
IOSDnsConverter.convert(source: SourceConfiguration) -> ConversionProposal
```

## Logging

- Write one info line before the network conversion. Its template is `Preparing network conversion with %d assignments.`
- Write one debug line after the conversion. Its template is `Prepared %d emitted keys and %d unresolved items.`
- Write one info line before each family converter and one debug line after it.
- Write an error line with the exception type on each raised error. Do not include the rejected value.
- Logs use ASCII only. Logs never include a source value, a description, or a credential.
