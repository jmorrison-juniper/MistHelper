"""Prepare deterministic IPv4 store variables without I/O or cloud access."""

from __future__ import annotations  # WHY: keep public return and input annotations explicit.

import logging  # WHY: report calculation boundaries without logging private addresses.
import re  # WHY: reject malformed variable names before generation.
from dataclasses import dataclass  # WHY: keep prepared output immutable.
from ipaddress import IPv4Address, IPv4Network  # WHY: enforce IPv4-only calculations.

from src.foundation.models.data.mistdsw_addressing import (  # WHY: reuse caller-supplied domain inputs.
    AddressingConfiguration,
    AddressingPolicy,
    StoreAddressingInput,
)


@dataclass(frozen=True, slots=True)
class PreparedStoreVariables:  # WHY: expose one immutable output record for later approved integrations.
    """Hold one validated store name, normalized supernet, and ordered variable values."""

    site_name: str  # WHY: retain the caller's site label for a later output adapter.
    supernet: IPv4Network  # WHY: expose the normalized IPv4 block for review.
    variables: tuple[tuple[str, str], ...]  # WHY: preserve output order and immutable string values.


class AddressingConfigurationValidator:  # WHY: isolate caller configuration checks from calculations.
    """Reject unsafe or inconsistent caller values before address generation."""

    @classmethod
    def validate(
        cls, configuration: AddressingConfiguration
    ) -> None:  # WHY: provide one complete configuration boundary.
        """Run each focused validation rule before preparation begins."""
        cls._validate_prefixes(configuration)  # WHY: confirm the child count and IPv4 sizes.
        cls._validate_names(configuration)  # WHY: prevent malformed or colliding output keys.
        cls._validate_output_keys(configuration)  # WHY: prevent collisions between generated field names.
        cls._validate_vlan_ids(configuration)  # WHY: require unique usable caller VLAN values.
        cls._validate_offsets(configuration.policy)  # WHY: keep default gateways and DHCP pools inside each subnet.

    @staticmethod
    def _validate_prefixes(
        configuration: AddressingConfiguration,
    ) -> None:  # WHY: validate subnet geometry before allocation.
        """Require integer prefix values and one definition per child network."""
        policy = configuration.policy  # WHY: read the explicit caller policy once.
        prefixes = (policy.supernet_prefix, policy.subnet_prefix)  # WHY: reject booleans and non-integer prefix values.
        if (
            any(type(value) is not int for value in prefixes)
            or not 0 <= policy.supernet_prefix < policy.subnet_prefix <= 30
        ):  # WHY: require usable IPv4 prefixes.
            raise ValueError(
                "The configured prefixes must define usable IPv4 child networks."
            )  # WHY: stop invalid geometry.
        expected = 1 << (
            policy.subnet_prefix - policy.supernet_prefix
        )  # WHY: derive child count from explicit prefix values.
        if len(configuration.variable_networks) != expected:  # WHY: require a definition for each generated child.
            raise ValueError(
                "The variable network count must match the configured prefixes."
            )  # WHY: prevent partial output.

    @staticmethod
    def _validate_names(
        configuration: AddressingConfiguration,
    ) -> None:  # WHY: validate keys before they become output names.
        """Require unique lowercase variable prefixes."""
        names = [definition.name for definition in configuration.variable_networks]  # WHY: retain segment input order.
        names.extend(
            definition.name for definition in configuration.supplemental_networks
        )  # WHY: include optional networks.
        names.append(configuration.supernet_variable_name)  # WHY: reserve the caller's supernet key.
        if any(
            not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", name) for name in names
        ):  # WHY: keep every variable prefix unambiguous.
            raise ValueError("A network variable name is invalid.")  # WHY: reject malformed output keys.
        if len(set(names)) != len(names):  # WHY: prevent overwriting values with duplicate prefixes.
            raise ValueError("Network variable names must be unique.")  # WHY: preserve every configured result.

    @staticmethod
    def _validate_output_keys(
        configuration: AddressingConfiguration,
    ) -> None:  # WHY: detect collisions after field suffixes are applied.
        """Require every generated variable key to remain unique."""
        output_keys = [configuration.supernet_variable_name]  # WHY: reserve the caller's supernet key.
        segment_fields = (  # WHY: enumerate each field generated for a child network.
            "vlan_id",
            "network",
            "cidr",
            "mask",
            "gw",
            "dhcp_start",
            "dhcp_end",
        )
        for network_definition in configuration.variable_networks:  # WHY: derive child-network output keys.
            output_keys.extend(  # WHY: include every field emitted for each configured segment.
                f"{network_definition.name}_{field}" for field in segment_fields
            )
        for supplemental_definition in configuration.supplemental_networks:  # WHY: derive optional-network output keys.
            if supplemental_definition.vlan_id is not None:  # WHY: reserve the VLAN key only when supplied.
                output_keys.append(f"{supplemental_definition.name}_vlan_id")  # WHY: match the optional output field.
            output_keys.extend(  # WHY: include every field emitted for the auxiliary network.
                f"{supplemental_definition.name}_{field}" for field in ("network", "cidr", "mask", "gw")
            )
        if len(set(output_keys)) != len(output_keys):  # WHY: refuse values that would overwrite another result.
            raise ValueError("Generated variable names must be unique.")  # WHY: preserve all output values.

    @staticmethod
    def _validate_vlan_ids(
        configuration: AddressingConfiguration,
    ) -> None:  # WHY: check all optional VLAN values together.
        """Require each supplied VLAN to be a unique integer from 1 through 4094."""
        vlan_ids = [
            definition.vlan_id for definition in configuration.variable_networks
        ]  # WHY: include required segment VLAN values.
        vlan_ids.extend(
            definition.vlan_id for definition in configuration.supplemental_networks if definition.vlan_id is not None
        )  # WHY: include only supplied auxiliary VLAN values.
        if any(type(value) is not int or not 1 <= value <= 4094 for value in vlan_ids) or len(set(vlan_ids)) != len(
            vlan_ids
        ):  # WHY: reject booleans, invalid bounds, and duplicates.
            raise ValueError(
                "VLAN IDs must be unique integers from 1 through 4094."
            )  # WHY: refuse invalid network configuration.

    @staticmethod
    def _validate_offsets(
        policy: AddressingPolicy,
    ) -> None:  # WHY: check host offsets against the configured child size.
        """Require a usable default gateway and ordered DHCP host offsets."""
        maximum = (1 << (32 - policy.subnet_prefix)) - 2  # WHY: exclude network and broadcast addresses.
        offsets = (
            policy.default_gateway_host_offset,
            policy.dhcp_start_offset,
            policy.dhcp_end_offset,
        )  # WHY: reject booleans and non-integer offsets.
        if (
            any(type(value) is not int for value in offsets)
            or not 1 <= policy.default_gateway_host_offset <= maximum
            or not 1 <= policy.dhcp_start_offset <= policy.dhcp_end_offset <= maximum
        ):  # WHY: require usable gateway and DHCP hosts.
            raise ValueError(
                "Gateway and DHCP offsets must be ordered usable hosts."
            )  # WHY: prevent invalid default addresses or pools.


class StoreAddressingPreparer:  # WHY: keep deterministic calculations offline and independent of storage.
    """Calculate store variables from explicit input without file or network access."""

    @classmethod
    def prepare(
        cls, request: StoreAddressingInput
    ) -> PreparedStoreVariables:  # WHY: expose one deterministic calculation boundary.
        """Validate one request and return its ordered network variables."""
        logger = logging.getLogger(__name__)  # WHY: keep each log record scoped to this module.
        logger.info(
            "Preparing offline store addressing values."
        )  # WHY: record the data transform without exposing inputs.
        try:  # WHY: log validation failures without logging the supplied network values.
            cls._validate_site_name(request.site_name)  # WHY: block unsafe spreadsheet labels before output.
            AddressingConfigurationValidator.validate(
                request.configuration
            )  # WHY: reject invalid caller settings before parsing addresses.
            supernet = request.normalized_supernet()  # WHY: require valid IPv4 and normalization review.
            values = cls._segment_values(request, supernet)  # WHY: derive only configured child networks.
            values.extend(cls._supplemental_values(request, supernet))  # WHY: include only explicit auxiliary networks.
            result = PreparedStoreVariables(
                request.site_name, supernet, tuple(values)
            )  # WHY: freeze the deterministic result.
        except ValueError as error:  # WHY: report known input failures and preserve the original error.
            logger.error(
                "Offline store addressing failed with %s.", type(error).__name__
            )  # WHY: avoid logging caller addresses or names.
            raise  # WHY: callers must handle invalid input explicitly.
        logger.debug(
            "Prepared %s addressing values.", len(result.variables)
        )  # WHY: report result size without private values.
        return result  # WHY: return only validated IPv4 values.

    @staticmethod
    def _validate_site_name(site_name: str) -> None:  # WHY: isolate safe label checks from address calculations.
        """Reject blank, oversized, control, and formula-prefixed site labels."""
        if (
            not site_name or site_name != site_name.strip() or len(site_name) > 128
        ):  # WHY: enforce a stable bounded label.
            raise ValueError(
                "The site name must contain 1 through 128 trimmed characters."
            )  # WHY: stop invalid labels early.
        if any(
            ord(character) < 32 or ord(character) == 127 for character in site_name
        ):  # WHY: reject terminal and record controls.
            raise ValueError("The site name cannot contain control characters.")  # WHY: prevent unsafe output labels.
        if site_name.lstrip().startswith(("=", "+", "-", "@")):  # WHY: reject spreadsheet formula prefixes.
            raise ValueError(
                "The site name cannot start with a formula character."
            )  # WHY: prevent unsafe future CSV output.

    @staticmethod
    def _segment_values(
        request: StoreAddressingInput, supernet: IPv4Network
    ) -> list[tuple[str, str]]:  # WHY: preserve caller segment order.
        """Build values for every child network inside the normalized supernet."""
        configuration = request.configuration  # WHY: read only values supplied by the caller.
        children = tuple(
            supernet.subnets(new_prefix=configuration.policy.subnet_prefix)
        )  # WHY: divide the network by its explicit prefix.
        values = [(configuration.supernet_variable_name, str(supernet))]  # WHY: use the caller's supernet output key.
        for definition, subnet in zip(
            configuration.variable_networks, children, strict=True
        ):  # WHY: pair each explicit definition with one ordered child.
            values.extend(
                definition.variable_values(subnet, configuration.policy)
            )  # WHY: validate gateway and DHCP values per subnet.
        return values  # WHY: preserve stable input and field order.

    @staticmethod
    def _supplemental_values(
        request: StoreAddressingInput, supernet: IPv4Network
    ) -> list[tuple[str, str]]:  # WHY: keep optional networks separate.
        """Validate caller-supplied auxiliary networks and return their variables."""
        values: list[tuple[str, str]] = []  # WHY: collect only validated auxiliary values.
        prior_networks: list[IPv4Network] = []  # WHY: detect overlap without changing caller order.
        for (
            definition
        ) in request.configuration.supplemental_networks:  # WHY: process only explicitly supplied networks.
            network = IPv4Network(
                definition.network_cidr, strict=True
            )  # WHY: reject host bits instead of normalizing a profile value.
            gateway = IPv4Address(definition.gateway_address)  # WHY: reject malformed and IPv6 gateway values.
            if gateway not in network or gateway in (
                network.network_address,
                network.broadcast_address,
            ):  # WHY: require a usable in-network gateway.
                raise ValueError(
                    f"The gateway for {definition.name} must be a usable host in its network."
                )  # WHY: stop invalid auxiliary output.
            if network.overlaps(supernet) or any(
                network.overlaps(prior) for prior in prior_networks
            ):  # WHY: prevent overlaps with store and auxiliary networks.
                raise ValueError(
                    f"The network {definition.name} overlaps another configured network."
                )  # WHY: refuse an ambiguous plan.
            prior_networks.append(network)  # WHY: compare later caller networks with this validated block.
            if definition.vlan_id is not None:  # WHY: emit an auxiliary VLAN only when the caller supplies one.
                values.append(
                    (f"{definition.name}_vlan_id", str(definition.vlan_id))
                )  # WHY: retain the explicit VLAN as text.
            values.extend(  # WHY: retain the same field order for every auxiliary network.
                (
                    (
                        f"{definition.name}_network",
                        str(network.network_address),
                    ),  # WHY: report its derived network address.
                    (f"{definition.name}_cidr", str(network.prefixlen)),  # WHY: report its explicit prefix.
                    (f"{definition.name}_mask", str(network.netmask)),  # WHY: report its derived mask.
                    (f"{definition.name}_gw", str(gateway)),  # WHY: report its validated gateway.
                )
            )
        return values  # WHY: return only non-overlapping auxiliary values.
