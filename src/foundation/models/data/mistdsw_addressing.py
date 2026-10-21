"""Define caller-supplied IPv4 addressing inputs for offline store preparation."""

from __future__ import annotations  # WHY: keep public model annotations explicit and forward-compatible.

from dataclasses import dataclass  # WHY: immutable values keep one calculation input stable.
from ipaddress import IPv4Address, IPv4Network  # WHY: reject IPv6 at the typed model boundary.


@dataclass(frozen=True, slots=True)
class AddressingPolicy:  # WHY: separate caller choices from calculated network values.
    """Carry every prefix and host offset that affects address generation."""

    supernet_prefix: int  # WHY: the caller selects the store address block size.
    subnet_prefix: int  # WHY: the caller selects each generated network size.
    default_gateway_host_offset: int  # WHY: the caller selects the fallback gateway host.
    dhcp_start_offset: int  # WHY: the caller selects the first DHCP host offset.
    dhcp_end_offset: int  # WHY: the caller selects the last DHCP host offset.


@dataclass(frozen=True, slots=True)
class NetworkVariableDefinition:  # WHY: keep each subnet's name, VLAN, and optional gateway together.
    """Describe one caller-named network and its VLAN and optional gateway."""

    name: str  # WHY: the caller controls the output variable prefix.
    vlan_id: int  # WHY: the caller supplies a VLAN without a profile default.
    gateway_address: str | None = None  # WHY: an omitted value uses the configured host offset.

    def variable_values(  # WHY: build one segment's output from its explicit configuration.
        self,
        subnet: IPv4Network,
        policy: AddressingPolicy,
    ) -> tuple[tuple[str, str], ...]:  # WHY: return an ordered immutable set of textual values.
        """Return this network's stable variable values after gateway validation."""
        gateway = (  # WHY: preserve a supplied gateway or use the caller's configured offset.
            IPv4Address(self.gateway_address)
            if self.gateway_address is not None
            else subnet.network_address + policy.default_gateway_host_offset
        )
        if gateway not in subnet or gateway in (
            subnet.network_address,
            subnet.broadcast_address,
        ):  # WHY: only usable in-subnet hosts can route traffic.
            raise ValueError(
                f"The gateway for {self.name} must be a usable host in its subnet."
            )  # WHY: stop invalid output before generation.
        dhcp_start, dhcp_end = self._dhcp_pool(subnet, gateway, policy)  # WHY: exclude an in-pool gateway.
        return (  # WHY: retain a fixed output order for deterministic callers.
            (f"{self.name}_vlan_id", str(self.vlan_id)),  # WHY: serialize the caller-supplied VLAN as text.
            (f"{self.name}_network", str(subnet.network_address)),  # WHY: report the IPv4 network address.
            (f"{self.name}_cidr", str(subnet.prefixlen)),  # WHY: report the configured prefix length.
            (f"{self.name}_mask", str(subnet.netmask)),  # WHY: report the derived IPv4 mask.
            (f"{self.name}_gw", str(gateway)),  # WHY: report the validated gateway address.
            (f"{self.name}_dhcp_start", str(dhcp_start)),  # WHY: report the selected pool start.
            (f"{self.name}_dhcp_end", str(dhcp_end)),  # WHY: report the selected pool end.
        )

    def _dhcp_pool(  # WHY: select one contiguous pool that excludes the gateway.
        self,
        subnet: IPv4Network,
        gateway: IPv4Address,
        policy: AddressingPolicy,
    ) -> tuple[IPv4Address, IPv4Address]:  # WHY: keep pool selection within the subnet model.
        """Return the configured DHCP range after excluding a gateway inside it."""
        maximum_host_offset = subnet.num_addresses - 2  # WHY: exclude the network and broadcast addresses.
        if (
            not 1 <= policy.dhcp_start_offset <= policy.dhcp_end_offset <= maximum_host_offset
        ):  # WHY: require an ordered range of usable hosts.
            raise ValueError(
                f"The DHCP range for {self.name} must contain usable hosts."
            )  # WHY: refuse an empty or invalid pool.
        start = subnet.network_address + policy.dhcp_start_offset  # WHY: apply the caller's lower host offset.
        end = subnet.network_address + policy.dhcp_end_offset  # WHY: apply the caller's upper host offset.
        if not start <= gateway <= end:  # WHY: a gateway outside the pool needs no adjustment.
            return start, end  # WHY: retain the caller's full DHCP range.
        lower_count = int(gateway) - int(start)  # WHY: count usable hosts below the gateway.
        upper_count = int(end) - int(gateway)  # WHY: count usable hosts above the gateway.
        if lower_count == 0 and upper_count == 0:  # WHY: no pool remains when the gateway is the only address.
            raise ValueError(f"The gateway for {self.name} leaves no DHCP addresses.")  # WHY: reject unusable output.
        if lower_count > upper_count:  # WHY: keep the larger side when the lower range is longer.
            return start, IPv4Address(int(gateway) - 1)  # WHY: stop the lower range before the gateway.
        return IPv4Address(int(gateway) + 1), end  # WHY: choose the upper side when it is larger or tied.


@dataclass(frozen=True, slots=True)
class SupplementalNetworkDefinition:  # WHY: carry optional network values without a selected profile.
    """Describe an optional caller-supplied IPv4 network and gateway."""

    name: str  # WHY: the caller controls the auxiliary variable prefix.
    network_cidr: str  # WHY: the caller supplies the network and prefix.
    gateway_address: str  # WHY: the caller supplies the gateway without a profile default.
    vlan_id: int | None = None  # WHY: the caller may supply a VLAN when the auxiliary network needs one.


@dataclass(frozen=True, slots=True)
class AddressingConfiguration:  # WHY: require network and address policy values from each caller.
    """Group generic network values without selecting an organization profile."""

    policy: AddressingPolicy  # WHY: all subnet sizes and host offsets remain explicit.
    variable_networks: tuple[NetworkVariableDefinition, ...]  # WHY: names, VLANs, and gateways remain caller-owned.
    supernet_variable_name: str  # WHY: require the caller to select every output variable name.
    supplemental_networks: tuple[SupplementalNetworkDefinition, ...] = ()  # WHY: optional networks are never invented.


@dataclass(frozen=True, slots=True)
class StoreAddressingInput:  # WHY: bind one host address to its explicit review and configuration choices.
    """Carry one store address, its review choice, and all selected configuration."""

    site_name: str  # WHY: retain the caller's site label without inventing an identifier.
    base_address: str  # WHY: accept an IPv4 host address that may need normalization.
    normalization_acknowledged: bool  # WHY: require review when normalization changes the base.
    configuration: AddressingConfiguration  # WHY: keep every network and policy value caller-supplied.

    def normalized_supernet(self) -> IPv4Network:  # WHY: keep address parsing beside its acknowledgment input.
        """Return the configured supernet only after required normalization review."""
        address = IPv4Address(self.base_address)  # WHY: reject malformed and IPv6 input at the domain boundary.
        supernet = IPv4Network(
            (address, self.configuration.policy.supernet_prefix), strict=False
        )  # WHY: normalize with the caller's prefix.
        if (
            address != supernet.network_address and not self.normalization_acknowledged
        ):  # WHY: require review only when the address changes.
            raise ValueError(
                "Address normalization requires acknowledgment."
            )  # WHY: do not hide a changed network base.
        return supernet  # WHY: provide one validated IPv4 network to the preparer.
