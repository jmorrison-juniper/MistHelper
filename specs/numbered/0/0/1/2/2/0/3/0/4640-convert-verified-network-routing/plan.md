# Implementation Plan: Convert Verified Network and Routing Settings

**Branch**: `feat/4640-convert-verified-network-routing` (planned from `main`) | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric record at `specs\numbered\0\0\1\2\2\0\3\0\4640-convert-verified-network-routing\`. The route follows the base-5 rule in `.specify\scripts\powershell\spec-route.ps1`, lines 17 and 18. Decimal 4640 equals `122030` in base 5. Padded to eight levels, it gives `0/0/1/2/2/0/3/0`.

## Summary

Replace the module `conversion.py` with a `conversion/` package. Move the DNS converter into `conversion/common/`. Add verified interface, DHCP, routing, and NTP converters in `conversion/network/`. Write each test family before its code. Make no route change, no shared portal change, and no Mist call.

## Technical Context

**Language/Version**: Python 3.15 or newer. Source: `.github/copilot-instructions.md`, section Language and environment.

**Primary Dependencies**: Standard library only in the converter. The pinned `mistapi` 0.64.1 package stays installed and unused by this record.

**Storage**: None. The conversion holds all values in memory for one request.

**Testing**: pytest under `tests/integration/web_portal/cisco_config_converter/conversion/`. Decision D-2 explains the folder.

**Target Platform**: Windows 11, macOS, Linux, and the Podman image that runs as UID 1000.

**Project Type**: Feature package inside the existing web portal interface package.

**Performance Goals**: None. One request converts one upload. The 16 MiB bound from the existing converter applies.

**Constraints**: No socket, file write, Mist call, or credential in output. No route change. Five children per directory. Five members per class and five top-level names per module.

**Scale/Scope**: Six new modules, one moved module, one entry class in the network package, four test modules, 35 planned test functions, 17 functional requirements.

## Constitution Check

| Rule | Result | Reason |
| --- | --- | --- |
| I. Five-Item Rule, levels | Pass after D-1 | The converter root keeps five children. `conversion/` holds three children after this record. `network/` and `common/` hold five and four children. |
| I. Five-Item Rule, functions | Pass planned | Each method has five parameters or fewer and 25 lines or fewer. T015 runs the complexity gate. |
| I. Five-Item Rule, names | Pass planned | Each module holds five top-level names or fewer. Each class holds five members or fewer. |
| II. Class-based architecture | Pass | Each behavior sits in a named class. No wrapper function is planned. |
| III. Safety-first input | Pass planned | The converter validates each input before use and returns at the first failure. |
| III. Destructive operations | Pass | This record adds no destructive operation. |
| III. Secrets | Pass | Decision D-14 omits credential values. Decision D-18 asks the owner for the later policy. |
| IV. Deployment pipeline | Pass for this record | No code changes here. The pipeline applies to the implementation tasks T-LOCAL-GATES through T-MERGE. |
| V. ASCII output | Pass planned | Reason texts and log templates use ASCII only. |
| V. Structured logs | Fail until owner confirms equivalence | The constitution asks for structured logs. Issue #4636 unresolved item U-2 covers this gap. This record follows the same standard logging. |
| VI. Inline comments | Pass planned | Each new or touched executable line gets a comment. T015 audits the result. |
| VII. Action logging | Pass planned | Each conversion family logs before and after its work. |
| Technology: Python | Pass | Python 3.15 standard library. |
| Technology: mistapi | Pass | No Mist call. The field evidence cites the local OpenAPI file. |
| Technology: owned WebSocket | Not applicable | No WebSocket transport. |
| Technology: UV and requirements | Pass | No dependency change. |
| Technology: Podman | Not applicable | No container change. |
| Technology: file paths | Pass | The converter handles no file path. |
| Technology: export boundary | Pass | This record adds no export. |
| Development: menu operations | Not applicable | No menu change. |
| Development: documentation | Pass | No user-facing change. Decision D-16 explains this. |
| Development: testing | Pass | Tests come before implementation for each family. |
| Escalation | Pass | The change touches more than three files and two classes. This record exists. |
| Multi-agent git: issue first | Pass | Issue #4640 exists. The orchestrator adds the `in-progress` label before the branch. |
| Multi-agent git: overlap | Pass planned | T-PR runs `gh pr list` before the branch. Section Multi-Agent Sequencing lists the shared files. |

## Capacity and Structure Inventory

The inventory uses GitHub `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The remote evidence rows appear in `design\research.md`, section Remote Verification.

| Directory | Now | After issue 4636 | After this record | Limit | Status |
| --- | --- | --- | --- | --- | --- |
| `src/interfaces/portals/cisco_config_converter/` | 5 | 5. `state/` replaces `models.py`. | 5. `conversion/` replaces `conversion.py`. | 5 | At limit. Count unchanged. |
| `src/interfaces/portals/cisco_config_converter/conversion/` | Not present | Not present | 3: `__init__.py`, `common/`, `network/` | 5 | Two slots remain for issues 4638 and 4639. |
| `src/interfaces/portals/cisco_config_converter/conversion/common/` | Not present | Not present | 4: `__init__.py`, `dns.py`, `fragment.py`, `syntax.py` | 5 | Compliant. |
| `src/interfaces/portals/cisco_config_converter/conversion/network/` | Not present | Not present | 5: `__init__.py`, `dhcp.py`, `interfaces.py`, `ntp.py`, `routing.py` | 5 | At limit. |
| `src/interfaces/portals/` | 6 | 6 | 6 | 5 | Grandfathered. Not touched. |
| `tests/contract/` | 17 | 17 | 17 | 5 | Grandfathered. Not touched. No child added. |
| `tests/integration/web_portal/cisco_config_converter/` | 2 | 3 with `state/` | 4 with `conversion/` | 5 | Compliant. |
| `tests/integration/web_portal/cisco_config_converter/conversion/` | Not present | Not present | 5: `__init__.py`, `test_compat.py`, `test_network.py`, `test_routing.py`, `test_services.py` | 5 | At limit. |
| `tests/unit/marvis/mist/resources/gateway/overrides/` | 5 | 5 | 5 | 5 | At limit. One import line changes. No child added. |

The nested package guard in `tests/guardrails/test_nested_package_structure.py` counts modules and child directories with tracked Python files, not package markers. The converter root has three counted entries after this record, which matches the count that issue #4636 records. The constitution counts five physical children, which includes `__init__.py` and `presentation/`. Both counts appear here.

## Replacement Layout

```text
src/interfaces/portals/cisco_config_converter/
  __init__.py                    unchanged
  presentation/                  unchanged
  routes.py                      one import line changes
  state/                         added by issue 4636
  conversion/                    replaces conversion.py
    __init__.py                  module docstring only
    common/
      __init__.py                module docstring only
      dns.py                     IOSDnsConverter, IOSDomainNameParser
      fragment.py                NetworkFragment, PortAssignment, ConvertedNetwork, UNRESOLVED_REASONS
      syntax.py                  IOSBlockReader, SourceLine
    network/
      __init__.py                IOSNetworkConverter, logger
      dhcp.py                    IOSDhcpConverter, IOSPoolRangeResolver
      interfaces.py              IOSInterfaceConverter, IOSAddressParser, IOSVlanParser, IOSVariableRules
      ntp.py                     IOSNtpConverter
      routing.py                 IOSRouteConverter, IOSVrfConverter, IOSBgpConverter
    hardware/                    reserved for issue 4638
    management/                  reserved for issue 4639

tests/integration/web_portal/cisco_config_converter/
  __init__.py                    unchanged
  test_routes.py                 unchanged
  state/                         added by issue 4636
  conversion/
    __init__.py
    test_compat.py               DNS output, offline guard, mapping register guard
    test_network.py              addresses, roles, VLAN, aggregates, variables
    test_routing.py              static routes, VRF, BGP
    test_services.py             DHCP, NTP, DNS suffix
```

Each module holds five top-level names or fewer. `interfaces.py` holds the maximum of five names, including its `logger`. `network/__init__.py` holds two names and one entry class.

## Symbol Map

The symbol gate reports a removed module when `conversion.py` no longer exists. The record documents this exception, as issue #4636 does for `models.py`.

| Name | Old location | New location |
| --- | --- | --- |
| `IOSDnsConverter` | `conversion.py` line 11 | `conversion/common/dns.py` |
| `logger` | `conversion.py` line 8 | `conversion/common/dns.py` and each new module |

The name `IOSDnsConverter` keeps its spelling and its public method `convert`. The method body changes only for the domain-name line and the known-gap sentence.

## Import Updates

| File | Current line | New line |
| --- | --- | --- |
| `src/interfaces/portals/cisco_config_converter/routes.py` | Line 11: `from .conversion import IOSDnsConverter` | `from .conversion.common.dns import IOSDnsConverter` |
| `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py` | Import of `IOSDnsConverter` from `src.interfaces.portals.cisco_config_converter.conversion` | Import of `IOSDnsConverter` from `src.interfaces.portals.cisco_config_converter.conversion.common.dns` |

No module keeps `conversion.py` as a re-export. The old-path search must return no match after the change.

## Architecture

The flow for one conversion has two paths.

1. The DNS path. `IOSDnsConverter.convert(source)` reads `ip name-server` and `ip domain name`. The existing preview route calls this path. Its output stays the same except for the known-gap sentence and the new DNS suffix key.
2. The network path. `IOSNetworkConverter.convert(source, assignments)` returns one `NetworkFragment`. The method runs these steps in order.
   - `IOSBlockReader` splits the source into interface, routing, and global blocks with line numbers.
   - `IOSInterfaceConverter` maps interfaces, networks, VLANs, aggregates, and variables. The other converters need its output, so it runs first.
   - `IOSRouteConverter`, `IOSVrfConverter`, and `IOSBgpConverter` map routes, VRF members, and BGP sessions from the networks and subnets that step two found.
   - `IOSDhcpConverter` maps pools after the networks and gateway addresses exist.
   - `IOSNtpConverter` maps NTP servers and needs no other output.

Composition of the DNS output and the network fragment into one proposal belongs to issue #4641. The file `routes.py` keeps calling the DNS path until issue #4641 merges.

## Mapping Rules

The field register in `design\contracts\mist-field-register.md` lists every emitted key. The contract in `design\contracts\proposal-fragment.md` lists the output shape. The rules below summarize the decisions in `design\research.md`.

- A WAN address goes to the port IP configuration. A LAN address goes to the IP configuration keyed by the network name.
- A LAN network comes from a VLAN ID or an SVI. Its name is `VLAN` followed by the VLAN ID.
- A DHCP pool needs a converted network with the same subnet. Its range comes from leading and trailing exclusions only.
- A static route needs an IPv4 destination with a host-bit-free prefix and an IPv4 next hop.
- A VRF instance holds its member network names. Its route distinguisher and its routes stay unresolved.
- A BGP session needs a derived transport from one converted subnet. Its prefixes and credentials stay out of the output.
- An NTP server needs an IPv4 address and no options.

## File-by-File Change Map

| Path | Action | Content |
| --- | --- | --- |
| `src/interfaces/portals/cisco_config_converter/conversion.py` | Delete | Moved to `conversion/common/dns.py`. |
| `src/interfaces/portals/cisco_config_converter/conversion/__init__.py` | Add | Module docstring only. |
| `src/interfaces/portals/cisco_config_converter/conversion/common/__init__.py` | Add | Module docstring only. |
| `src/interfaces/portals/cisco_config_converter/conversion/common/dns.py` | Add | Moved `IOSDnsConverter`. Adds `IOSDomainNameParser` and the revised known-gap sentence. |
| `src/interfaces/portals/cisco_config_converter/conversion/common/fragment.py` | Add | `NetworkFragment`, `PortAssignment`, `ConvertedNetwork`, and the constant `UNRESOLVED_REASONS`. |
| `src/interfaces/portals/cisco_config_converter/conversion/common/syntax.py` | Add | `IOSBlockReader` and `SourceLine`. |
| `src/interfaces/portals/cisco_config_converter/conversion/network/__init__.py` | Add | `IOSNetworkConverter` and `logger`. |
| `src/interfaces/portals/cisco_config_converter/conversion/network/interfaces.py` | Add | Interface, address, role, VLAN, aggregate, shutdown, speed, and variable rules. |
| `src/interfaces/portals/cisco_config_converter/conversion/network/dhcp.py` | Add | DHCP pool mapping and range derivation. |
| `src/interfaces/portals/cisco_config_converter/conversion/network/routing.py` | Add | Static routes, VRF membership, and BGP sessions. |
| `src/interfaces/portals/cisco_config_converter/conversion/network/ntp.py` | Add | IPv4 NTP servers. |
| `src/interfaces/portals/cisco_config_converter/state/proposal.py` | Modify | Adds `NotRequired` keys to `GatewayTemplate`. Owned by issue #4636. |
| `src/interfaces/portals/cisco_config_converter/routes.py` | Modify | One import line. No behavior change. |
| `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py` | Modify | One import line. |
| `tests/integration/web_portal/cisco_config_converter/conversion/__init__.py` | Add | Package marker. |
| `tests/integration/web_portal/cisco_config_converter/conversion/test_network.py` | Add | 17 interface, role, VLAN, aggregate, and variable tests. |
| `tests/integration/web_portal/cisco_config_converter/conversion/test_services.py` | Add | 8 DHCP, NTP, and DNS suffix tests. |
| `tests/integration/web_portal/cisco_config_converter/conversion/test_routing.py` | Add | 7 route, VRF, and BGP tests. |
| `tests/integration/web_portal/cisco_config_converter/conversion/test_compat.py` | Add | 3 DNS, offline, and register tests. |

Unchanged paths: `web_portal/app.py`, `web_portal/templates/base.html`, `web_portal/services/config.py`, `presentation/`, `compose.yml`, `requirements.txt`, `documentation/`, and `changelog.d/`.

## Dependencies

- Issue #4634 supplies the field evidence rows for each emitted key. The register in this record is the draft of those rows.
- Issue #4636 supplies `state/proposal.py` and the test folder layout. Its pull request must merge before the implementation starts.
- Issue #4637 supplies the review flow. The implementation does not import its code, but issue #4638 depends on it.
- Issue #4638 supplies one `PortAssignment` value for each physical interface. This record defines the type in `common/fragment.py`.
- The `mistapi` package is not called. The `createOrgGatewayTemplate` signature in `.venv` is cited only as the future write boundary.

## Multi-Agent Sequencing

1. Issue #4634 delivers the G2 evidence rows for each emitted key.
2. Issue #4636 merges. Its change to `conversion.py` and `routes.py` lands first.
3. Issue #4637 merges its review flow.
4. Issue #4638 merges its port assignment values and its role contract.
5. This record starts. Its branch comes from `main`.
6. Issue #4639 uses the `management/` slot only. It does not edit files in `conversion/common/` or `conversion/network/`.
7. Issue #4641 composes the DNS output and the network fragment after this record merges.

Before each edit, run `git status` and `gh pr list`. Add files by explicit path only.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| The schema text for `disabled` reverses the meaning of the value. | A port state can point the wrong way. | No `shutdown` value is emitted. Test 14 proves the unresolved result. |
| DHCP range semantics differ from the schema text. | A pool can start or end at the wrong address. | Ranges come from exclusions. A gateway address inside the range is unresolved. Issue #4634 confirms the semantics before apply. |
| Issue #4641 keeps the old second known-gap sentence. | The composed text overstates the scope. | Analysis item E-4 assigns the text to issue #4641. |
| Two open pull requests change `conversion/common/dns.py` or `routes.py`. | A merge conflict or a lost change occurs. | Sequencing step 2 and the overlap check at T-PR. |
| The five-member rule forces many small classes. | Navigation becomes harder. | Each class has one behavior. T015 checks the counts. |
| A Cisco grammar guess misreads a line. | A wrong value could appear in the output. | Each unknown form becomes an unresolved item. No value is inferred. |
| The symbol gate reports `conversion.py` as removed. | The gate fails. | The pull request records the symbol map exception. |
| A reason text or command label shows a credential. | A secret appears in review or logs. | Labels omit values. Test 31 checks each credential form. Test 34 checks the log output. |

## Rollback Steps

1. Revert the squash commit on `main` through a new pull request.
2. Confirm that `conversion.py` returns and that `conversion/` is gone.
3. Run `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py` and confirm the result.
4. No data path exists. No data cleanup is required.

## Complexity Tracking

| Item | Type | Reason | Action |
| --- | --- | --- | --- |
| `src/interfaces/portals/` holds six children. | Grandfathered. Not touched. | Predates this record. | Remediation R-1 in issue #4636. |
| `tests/contract/` holds 17 children. | Grandfathered. Not touched. | Predates this record. | The tests use the integration tree (D-2). Remediation R-2 in issue #4636. |
| `network/__init__.py` holds one class. | New design. | The package needs one entry point without a new child. | T015 checks the name count. |
| Interface rules need several classes. | New design. | The five-member rule limits each class. | T015 checks the member count. |
