"""Test generic, offline IPv4 store-address preparation with synthetic values."""

from __future__ import annotations  # WHY: keep test annotations consistent with Python 3.13 code.

from dataclasses import replace  # WHY: vary one caller-owned policy value per boundary case.

import pytest  # WHY: parameterized cases and explicit validation failures need pytest helpers.

from src.foundation.models.data.mistdsw_addressing import (  # WHY: build typed inputs without profile defaults.
    AddressingConfiguration,
    AddressingPolicy,
    NetworkVariableDefinition,
    StoreAddressingInput,
    SupplementalNetworkDefinition,
)
from src.foundation.models.data.mistdsw_addressing_preparation import (  # WHY: test the offline domain boundary.
    StoreAddressingPreparer,
)


def sample_configuration(  # WHY: reuse only synthetic network values across focused cases.
    dhcp_start_offset: int = 2,
    dhcp_end_offset: int = 254,
    first_gateway: str | None = None,
) -> AddressingConfiguration:  # WHY: provide complete test-only configuration values.
    """Build a generic synthetic configuration with every required value supplied."""
    return AddressingConfiguration(  # WHY: keep profile values out of production defaults.
        policy=AddressingPolicy(  # WHY: set test-only prefix and host-range choices.
            supernet_prefix=22,  # WHY: exercise four consecutive /24s from an RFC 5737 range.
            subnet_prefix=24,  # WHY: keep each synthetic segment inside the /22.
            default_gateway_host_offset=1,  # WHY: use the first host only as test configuration.
            dhcp_start_offset=dhcp_start_offset,  # WHY: vary pool bounds for tie coverage.
            dhcp_end_offset=dhcp_end_offset,  # WHY: make the pool end explicit.
        ),
        variable_networks=(  # WHY: inject all VLAN labels and IDs instead of selecting a profile.
            NetworkVariableDefinition("alpha", 21, first_gateway),  # WHY: use a neutral test-only name and ID.
            NetworkVariableDefinition("beta", 22, "198.51.101.5"),  # WHY: exercise an explicit synthetic gateway.
            NetworkVariableDefinition("gamma", 23),  # WHY: preserve input order for deterministic output.
            NetworkVariableDefinition("delta", 24),  # WHY: fill the fourth child network.
        ),
        supplemental_networks=(  # WHY: model caller-supplied auxiliary addressing values.
            SupplementalNetworkDefinition(
                "mgmt_lab", "203.0.113.0/27", "203.0.113.1", 31
            ),  # WHY: use synthetic addressing and VLAN values.
            SupplementalNetworkDefinition("wan_lab", "203.0.113.32/29", "203.0.113.33"),  # WHY: avoid overlap.
        ),
        supernet_variable_name="lab_supernet",  # WHY: keep the output variable key caller-selected.
    )


def sample_request(  # WHY: centralize only test data construction.
    base_address: str = "198.51.101.88",
    normalization_acknowledged: bool = True,
    configuration: AddressingConfiguration | None = None,
) -> StoreAddressingInput:  # WHY: create one fully explicit typed input for each case.
    """Build one synthetic store request without organization defaults."""
    return StoreAddressingInput(  # WHY: test the public typed input model.
        site_name="Synthetic Branch",  # WHY: use a non-customer test label.
        base_address=base_address,  # WHY: keep each test input visible at the call site.
        normalization_acknowledged=normalization_acknowledged,  # WHY: model explicit normalization consent.
        configuration=configuration or sample_configuration(),  # WHY: inject complete configuration values.
    )


class TestStoreAddressingPreparation:  # WHY: keep valid calculation behavior together.
    """Verify deterministic addressing output and generic configuration use."""

    def test_normalizes_and_derives_four_ordered_networks(
        self,
    ) -> None:  # WHY: cover normalization and stable child order.
        """A host address maps to the configured supernet and its ordered children."""
        result = StoreAddressingPreparer.prepare(sample_request())  # WHY: prepare a synthetic non-aligned address.
        variables = dict(result.variables)  # WHY: inspect the immutable ordered variable pairs by key.
        assert str(result.supernet) == "198.51.100.0/22"  # WHY: verify acknowledged /22 normalization.
        assert variables["lab_supernet"] == "198.51.100.0/22"  # WHY: verify the caller-supplied output key.
        assert tuple(
            variables[f"{name}_network"] for name in ("alpha", "beta", "gamma", "delta")
        ) == (  # WHY: verify child order.
            "198.51.100.0",  # WHY: expect the first /24 child.
            "198.51.101.0",  # WHY: expect the second /24 child.
            "198.51.102.0",  # WHY: expect the third /24 child.
            "198.51.103.0",  # WHY: expect the fourth /24 child.
        )
        assert tuple(
            variables[f"{name}_vlan_id"] for name in ("alpha", "beta", "gamma", "delta")
        ) == (  # WHY: preserve caller VLAN IDs.
            "21",  # WHY: verify the first explicit test VLAN.
            "22",  # WHY: verify the second explicit test VLAN.
            "23",  # WHY: verify the third explicit test VLAN.
            "24",  # WHY: verify the fourth explicit test VLAN.
        )
        assert result == StoreAddressingPreparer.prepare(
            sample_request()
        )  # WHY: require deterministic output for equal inputs.

    def test_requires_acknowledgment_for_normalization(self) -> None:  # WHY: prove normalization fails closed.
        """An unaligned source address cannot normalize without acknowledgment."""
        with pytest.raises(ValueError, match="acknowledgment"):  # WHY: the caller must review a changed base.
            StoreAddressingPreparer.prepare(
                sample_request(normalization_acknowledged=False)
            )  # WHY: omit required acknowledgment.

    def test_excludes_explicit_gateway_and_uses_upper_side_for_a_tie(
        self,
    ) -> None:  # WHY: cover pool selection boundaries.
        """The gateway leaves the larger contiguous DHCP side, with upper-side tie selection."""
        configuration = sample_configuration(2, 6, "198.51.100.4")  # WHY: create equal two-address pool sides.
        variables = dict(
            StoreAddressingPreparer.prepare(sample_request(configuration=configuration)).variables
        )  # WHY: inspect generated values.
        assert variables["alpha_dhcp_start"] == "198.51.100.5"  # WHY: the equal-size tie selects the upper side.
        assert variables["alpha_dhcp_end"] == "198.51.100.6"  # WHY: the upper side excludes the gateway.
        assert variables["beta_dhcp_start"] == "198.51.101.2"  # WHY: select the larger lower pool side.
        assert variables["beta_dhcp_end"] == "198.51.101.4"  # WHY: stop the pool before its explicit gateway.

    def test_emits_caller_supplied_auxiliary_network_values(self) -> None:  # WHY: cover optional network configuration.
        """Auxiliary network CIDRs and gateways come only from the request."""
        variables = dict(
            StoreAddressingPreparer.prepare(sample_request()).variables
        )  # WHY: inspect the generated immutable values.
        assert variables["mgmt_lab_cidr"] == "27"  # WHY: preserve the caller's management prefix.
        assert variables["mgmt_lab_mask"] == "255.255.255.224"  # WHY: derive the mask from the supplied CIDR.
        assert variables["mgmt_lab_gw"] == "203.0.113.1"  # WHY: preserve the explicit usable gateway.
        assert variables["mgmt_lab_vlan_id"] == "31"  # WHY: preserve the caller-supplied optional VLAN.
        assert variables["wan_lab_network"] == "203.0.113.32"  # WHY: derive the WAN network address.


class TestStoreAddressingValidation:  # WHY: keep invalid input behavior together.
    """Reject malformed, unsafe, or inconsistent synthetic inputs."""

    @pytest.mark.parametrize(  # WHY: test invalid IPv4 prefix bounds and child counts.
        ("supernet_prefix", "subnet_prefix"),
        [(-1, 24), (23, 24), (24, 23), (22, 31)],
    )
    def test_rejects_invalid_prefix_geometry(
        self, supernet_prefix: int, subnet_prefix: int
    ) -> None:  # WHY: require valid parent and child network sizes.
        """The supplied prefix values must define the supplied child networks."""
        base_configuration = sample_configuration()  # WHY: retain valid names and network definitions.
        configuration = AddressingConfiguration(  # WHY: replace only the invalid prefix values.
            policy=replace(  # WHY: preserve all unrelated caller-owned policy values.
                base_configuration.policy,
                supernet_prefix=supernet_prefix,
                subnet_prefix=subnet_prefix,
            ),
            variable_networks=base_configuration.variable_networks,  # WHY: retain four synthetic child definitions.
            supernet_variable_name="lab_supernet",  # WHY: keep the output key valid.
            supplemental_networks=base_configuration.supplemental_networks,  # WHY: retain valid auxiliary networks.
        )
        with pytest.raises(ValueError):  # WHY: reject invalid geometry before generation.
            StoreAddressingPreparer.prepare(
                sample_request(configuration=configuration)
            )  # WHY: validate the same public input boundary.

    @pytest.mark.parametrize(  # WHY: test invalid DHCP offset ordering and subnet bounds.
        ("dhcp_start_offset", "dhcp_end_offset"),
        [(0, 2), (3, 2), (255, 255)],
    )
    def test_rejects_invalid_dhcp_offsets(
        self, dhcp_start_offset: int, dhcp_end_offset: int
    ) -> None:  # WHY: require ordered DHCP hosts inside each child subnet.
        """The DHCP range must use ordered host offsets within the subnet."""
        base_configuration = sample_configuration()  # WHY: retain valid synthetic network definitions.
        configuration = AddressingConfiguration(  # WHY: replace only the invalid DHCP offsets.
            policy=replace(  # WHY: preserve valid prefixes and gateway offset.
                base_configuration.policy,
                dhcp_start_offset=dhcp_start_offset,
                dhcp_end_offset=dhcp_end_offset,
            ),
            variable_networks=base_configuration.variable_networks,  # WHY: retain four valid child definitions.
            supernet_variable_name="lab_supernet",  # WHY: keep the output key valid.
            supplemental_networks=base_configuration.supplemental_networks,  # WHY: retain valid auxiliary networks.
        )
        with pytest.raises(ValueError, match="offsets"):  # WHY: reject invalid host bounds before generation.
            StoreAddressingPreparer.prepare(
                sample_request(configuration=configuration)
            )  # WHY: validate the same public input boundary.

    def test_rejects_generated_variable_key_collisions(self) -> None:  # WHY: require an unambiguous output mapping.
        """A supernet key cannot overwrite a generated segment field."""
        base_configuration = sample_configuration()  # WHY: retain valid synthetic network definitions.
        configuration = AddressingConfiguration(  # WHY: collide with the first segment's network key.
            policy=base_configuration.policy,  # WHY: preserve valid prefixes and host offsets.
            variable_networks=base_configuration.variable_networks,  # WHY: retain unique segment names.
            supernet_variable_name="alpha_network",  # WHY: duplicate one generated output key.
            supplemental_networks=base_configuration.supplemental_networks,  # WHY: keep valid auxiliary values.
        )
        with pytest.raises(ValueError, match="Generated variable names"):  # WHY: reject ambiguous output.
            StoreAddressingPreparer.prepare(
                sample_request(configuration=configuration)
            )  # WHY: validate before any values are returned.

    @pytest.mark.parametrize("address", ["not-an-ip", "2001:db8::1"])  # WHY: reject malformed and IPv6 inputs.
    def test_rejects_non_ipv4_base_addresses(self, address: str) -> None:  # WHY: enforce the IPv4-only input contract.
        """The store base accepts only a valid IPv4 address."""
        with pytest.raises(ValueError):  # WHY: invalid input must stop before generation.
            StoreAddressingPreparer.prepare(
                sample_request(base_address=address)
            )  # WHY: pass the invalid value at the boundary.

    @pytest.mark.parametrize(  # WHY: exercise network, broadcast, and cross-subnet gateway rejection.
        "gateway",
        ["198.51.100.0", "198.51.100.255", "198.51.101.1"],
    )
    def test_rejects_invalid_explicit_segment_gateways(
        self, gateway: str
    ) -> None:  # WHY: reject network, broadcast, and remote gateways.
        """A segment gateway must be a usable host in its own subnet."""
        configuration = sample_configuration(
            first_gateway=gateway
        )  # WHY: inject one invalid address into segment alpha.
        with pytest.raises(ValueError, match="gateway"):  # WHY: report the invalid segment field.
            StoreAddressingPreparer.prepare(
                sample_request(configuration=configuration)
            )  # WHY: validate before returning values.

    @pytest.mark.parametrize(  # WHY: validate caller-supplied VLAN uniqueness and bounds.
        "definitions",
        [
            (
                NetworkVariableDefinition("alpha", 21),
                NetworkVariableDefinition("beta", 21),
                NetworkVariableDefinition("gamma", 23),
                NetworkVariableDefinition("delta", 24),
            ),
            (
                NetworkVariableDefinition("alpha", 0),
                NetworkVariableDefinition("beta", 22),
                NetworkVariableDefinition("gamma", 23),
                NetworkVariableDefinition("delta", 24),
            ),
        ],
    )
    def test_rejects_duplicate_or_out_of_range_vlan_values(
        self,
        definitions: tuple[NetworkVariableDefinition, ...],
    ) -> None:  # WHY: enforce unique caller-supplied VLAN values.
        """The caller must provide unique VLAN IDs from the valid range."""
        configuration = AddressingConfiguration(  # WHY: retain the synthetic policy while replacing its VLAN values.
            policy=sample_configuration().policy,  # WHY: keep prefixes and host offsets unchanged.
            variable_networks=definitions,  # WHY: inject the invalid VLAN sequence.
            supernet_variable_name="lab_supernet",  # WHY: retain the explicit test-only supernet key.
            supplemental_networks=sample_configuration().supplemental_networks,  # WHY: retain valid auxiliary networks.
        )
        with pytest.raises(ValueError, match="VLAN"):  # WHY: reject malformed configuration before address generation.
            StoreAddressingPreparer.prepare(
                sample_request(configuration=configuration)
            )  # WHY: use the same boundary as valid requests.

    def test_rejects_overlapping_or_invalid_auxiliary_gateways(
        self,
    ) -> None:  # WHY: prove auxiliary values fail closed.
        """Auxiliary networks must not overlap and each gateway must be usable."""
        invalid_gateway_configuration = AddressingConfiguration(  # WHY: supply an unusable auxiliary gateway.
            policy=sample_configuration().policy,  # WHY: keep the variable-network policy valid.
            variable_networks=sample_configuration().variable_networks,  # WHY: retain four valid segment definitions.
            supernet_variable_name="lab_supernet",  # WHY: retain the explicit test-only variable name.
            supplemental_networks=(
                SupplementalNetworkDefinition(
                    "mgmt_lab", "203.0.113.0/27", "203.0.113.0"
                ),  # WHY: use the network address as an invalid gateway.
            ),
        )
        with pytest.raises(ValueError, match="gateway"):  # WHY: reject a network address as a gateway.
            StoreAddressingPreparer.prepare(
                sample_request(configuration=invalid_gateway_configuration)
            )  # WHY: validate before returning values.
        overlapping_configuration = AddressingConfiguration(  # WHY: test overlap with valid gateways.
            policy=sample_configuration().policy,  # WHY: keep the variable-network policy valid.
            variable_networks=sample_configuration().variable_networks,  # WHY: retain four valid segment definitions.
            supernet_variable_name="lab_supernet",  # WHY: retain the explicit test-only variable name.
            supplemental_networks=(
                SupplementalNetworkDefinition(
                    "mgmt_lab", "203.0.113.0/27", "203.0.113.1"
                ),  # WHY: use a valid synthetic gateway.
                SupplementalNetworkDefinition(
                    "wan_lab", "203.0.113.0/29", "203.0.113.2"
                ),  # WHY: overlap while keeping a valid gateway.
            ),
        )
        with pytest.raises(ValueError, match="overlaps"):  # WHY: reject ambiguous auxiliary ranges.
            StoreAddressingPreparer.prepare(
                sample_request(configuration=overlapping_configuration)
            )  # WHY: validate the complete request.
