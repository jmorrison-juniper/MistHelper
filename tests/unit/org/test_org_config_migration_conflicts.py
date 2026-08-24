"""Tests for the org config migration conflict detection and the ID remapping.

Why:
    ``src/org/org_config_migration_manager.py`` drives menus 176 and 177. The
    import path writes into a live org, so the conflict detection is the last
    guard before a duplicate network or an overlapping subnet reaches the Mist
    cloud. The ID remapping is the second guard, because a stale reference from
    the source org points a gateway template at an object that does not exist
    in the destination. This module covers both guards and the boundary cases
    that a malformed bundle produces. No test reaches the Mist API.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.org import org_config_migration_manager as ocm
from src.org.org_config_migration_manager import OrgConfigMigrationManager


@pytest.fixture
def manager() -> OrgConfigMigrationManager:
    """Return a manager with mock collaborators and an empty cache.

    Why:
        The conflict checks and the remapping read only instance state. Mock
        collaborators keep the constructor from reaching the network.
    """
    # WHY: the session, the org resolver, and the input wrapper stay unused here.
    return OrgConfigMigrationManager(MagicMock(), MagicMock(), MagicMock())


class TestNormalizedName:
    """Cover the name reader that every name conflict check depends on."""

    def test_a_name_is_lowercased(self) -> None:
        """Mist treats two names that differ only in case as two objects."""
        # WHY: a case-sensitive compare would let a near-duplicate through.
        assert OrgConfigMigrationManager._normalized_name({"name": "Corp-LAN"}) == "corp-lan"

    def test_a_missing_name_becomes_an_empty_string(self) -> None:
        """A bundle can hold an unnamed object, and a None would raise on lower."""
        assert OrgConfigMigrationManager._normalized_name({}) == ""

    def test_a_null_name_becomes_an_empty_string(self) -> None:
        """The Mist API returns a null name for a partially built object."""
        assert OrgConfigMigrationManager._normalized_name({"name": None}) == ""


class TestCheckNameConflict:
    """Cover the first guard, which stops a duplicate name before the create call."""

    def test_a_matching_name_is_reported(self, manager: OrgConfigMigrationManager) -> None:
        """A duplicate name would fail the create call or shadow a live object."""
        existing = [{"name": "Corp-LAN", "id": "dest-1"}]  # WHY: one object already in the org.
        conflict = manager._check_name_conflict({"name": "Corp-LAN"}, existing)
        assert conflict is not None  # WHY: the guard must report, not stay silent.
        assert conflict["reason"] == "name_match"  # WHY: the report groups by this reason.

    def test_the_match_ignores_the_case(self, manager: OrgConfigMigrationManager) -> None:
        """A case-only difference is still a duplicate to the operator."""
        existing = [{"name": "corp-lan", "id": "dest-1"}]  # WHY: the stored name is lowercase.
        conflict = manager._check_name_conflict({"name": "CORP-LAN"}, existing)
        assert conflict is not None  # WHY: the compare must fold the case.

    def test_the_existing_identifier_is_preserved(self, manager: OrgConfigMigrationManager) -> None:
        """The remap table needs the destination identifier to fix later references."""
        existing = [{"name": "Corp-LAN", "id": "dest-1"}]  # WHY: one object already in the org.
        conflict = manager._check_name_conflict({"name": "Corp-LAN"}, existing)
        assert conflict is not None  # WHY: guard the index below.
        # WHY: without this identifier a later VPN reference would keep the source value.
        assert conflict["existing_id"] == "dest-1"

    def test_a_unique_name_reports_no_conflict(self, manager: OrgConfigMigrationManager) -> None:
        """A clean name must not be blocked, or the import stalls on every object."""
        existing = [{"name": "Corp-LAN", "id": "dest-1"}]  # WHY: a different existing object.
        assert manager._check_name_conflict({"name": "Guest-LAN"}, existing) is None

    def test_an_unnamed_new_object_reports_no_conflict(self, manager: OrgConfigMigrationManager) -> None:
        """An empty name would match every other unnamed object in the org."""
        existing = [{"name": None, "id": "dest-1"}]  # WHY: an unnamed existing object.
        assert manager._check_name_conflict({}, existing) is None

    def test_an_empty_org_reports_no_conflict(self, manager: OrgConfigMigrationManager) -> None:
        """A first import into a fresh org must not be blocked."""
        assert manager._check_name_conflict({"name": "Corp-LAN"}, []) is None


class TestCheckNetworkSubnetOverlap:
    """Cover the subnet guard, which stops an overlapping route from reaching the org."""

    def test_an_overlapping_subnet_is_reported(self, manager: OrgConfigMigrationManager) -> None:
        """Two overlapping subnets create a routing ambiguity in the gateway."""
        # WHY: the existing block contains the whole new block.
        existing = [{"name": "Corp", "subnet": "10.0.0.0/16"}]
        conflict = manager._check_network_subnet_overlap({"subnet": "10.0.1.0/24"}, existing)
        assert conflict is not None  # WHY: the guard must report the overlap.
        assert conflict["reason"] == "subnet_overlap"  # WHY: the report groups by this reason.

    def test_an_adjacent_subnet_reports_no_conflict(self, manager: OrgConfigMigrationManager) -> None:
        """Two touching blocks share no address, so they must both import.

        Why:
            This is the boundary case. An off-by-one in the overlap test would
            block every legitimate adjacent network.
        """
        # WHY: 10.0.1.0/24 ends at 10.0.1.255 and 10.0.2.0/24 starts at 10.0.2.0.
        existing = [{"name": "Corp", "subnet": "10.0.1.0/24"}]
        assert manager._check_network_subnet_overlap({"subnet": "10.0.2.0/24"}, existing) is None

    def test_an_identical_subnet_is_reported(self, manager: OrgConfigMigrationManager) -> None:
        """An exact repeat is the most common real overlap."""
        existing = [{"name": "Corp", "subnet": "10.0.1.0/24"}]  # WHY: the same block.
        assert manager._check_network_subnet_overlap({"subnet": "10.0.1.0/24"}, existing) is not None

    def test_a_new_supernet_is_reported(self, manager: OrgConfigMigrationManager) -> None:
        """A wider new block that swallows an existing one is still an overlap."""
        # WHY: the new block contains the existing block, which is the reverse direction.
        existing = [{"name": "Corp", "subnet": "10.0.1.0/24"}]
        assert manager._check_network_subnet_overlap({"subnet": "10.0.0.0/8"}, existing) is not None

    def test_a_missing_new_subnet_reports_no_conflict(self, manager: OrgConfigMigrationManager) -> None:
        """A network without a subnet has no address range to compare."""
        existing = [{"name": "Corp", "subnet": "10.0.1.0/24"}]  # WHY: a valid existing block.
        assert manager._check_network_subnet_overlap({"name": "No-Subnet"}, existing) is None

    def test_an_invalid_new_subnet_reports_no_conflict(self, manager: OrgConfigMigrationManager) -> None:
        """A malformed bundle value must not crash the whole import."""
        existing = [{"name": "Corp", "subnet": "10.0.1.0/24"}]  # WHY: a valid existing block.
        # WHY: a /99 prefix is out of range, so the parser raises ValueError.
        assert manager._check_network_subnet_overlap({"subnet": "10.0.1.0/99"}, existing) is None

    def test_host_bits_are_tolerated(self, manager: OrgConfigMigrationManager) -> None:
        """Operators write a host address with a prefix, and strict parsing would reject it."""
        existing = [{"name": "Corp", "subnet": "10.0.1.0/24"}]  # WHY: the same block, canonical.
        # WHY: 10.0.1.5/24 has host bits set, which only a non-strict parse accepts.
        assert manager._check_network_subnet_overlap({"subnet": "10.0.1.5/24"}, existing) is not None

    def test_an_existing_entry_without_a_subnet_is_skipped(self, manager: OrgConfigMigrationManager) -> None:
        """A partially built existing object must not stop the scan."""
        # WHY: the first entry has no subnet, so the loop must reach the second.
        existing = [{"name": "Empty"}, {"name": "Corp", "subnet": "10.0.1.0/24"}]
        conflict = manager._check_network_subnet_overlap({"subnet": "10.0.1.0/24"}, existing)
        assert conflict is not None  # WHY: the real overlap must still be found.

    def test_an_invalid_existing_subnet_is_skipped(self, manager: OrgConfigMigrationManager) -> None:
        """One corrupt existing record must not hide a real overlap behind it."""
        # WHY: the first entry fails to parse, so the loop must reach the second.
        existing = [{"name": "Bad", "subnet": "not-a-cidr"}, {"name": "Corp", "subnet": "10.0.1.0/24"}]
        conflict = manager._check_network_subnet_overlap({"subnet": "10.0.1.0/24"}, existing)
        assert conflict is not None  # WHY: the real overlap must still be found.

    def test_the_detail_names_both_networks(self, manager: OrgConfigMigrationManager) -> None:
        """The operator needs both names to decide which object to keep."""
        existing = [{"name": "Corp", "subnet": "10.0.0.0/16"}]  # WHY: the blocking object.
        conflict = manager._check_network_subnet_overlap({"subnet": "10.0.1.0/24"}, existing)
        assert conflict is not None  # WHY: guard the index below.
        assert "10.0.1.0/24" in conflict["detail"]  # WHY: the new block must be named.
        assert "Corp" in conflict["detail"]  # WHY: the blocking object must be named.


class TestCheckServiceAddressOverlap:
    """Cover the address guard, which scans a list of addresses on both sides."""

    def test_an_overlapping_address_is_reported(self, manager: OrgConfigMigrationManager) -> None:
        """Two services that share an address create an ambiguous policy match."""
        existing = [{"name": "Web", "addresses": ["10.0.0.0/16"]}]  # WHY: a wide existing block.
        new_obj = {"addresses": ["10.0.1.5/32"]}  # WHY: a host inside that block.
        conflict = manager._check_service_address_overlap(new_obj, existing)
        assert conflict is not None  # WHY: the guard must report the overlap.
        assert conflict["reason"] == "address_overlap"  # WHY: the report groups by this reason.

    def test_an_empty_address_list_reports_no_conflict(self, manager: OrgConfigMigrationManager) -> None:
        """A service defined by a port alone has no address to compare."""
        existing = [{"name": "Web", "addresses": ["10.0.0.0/16"]}]  # WHY: a valid existing block.
        assert manager._check_service_address_overlap({"addresses": []}, existing) is None

    def test_a_missing_address_field_reports_no_conflict(self, manager: OrgConfigMigrationManager) -> None:
        """A bundle can omit the field entirely, and a None would break the loop."""
        existing = [{"name": "Web", "addresses": ["10.0.0.0/16"]}]  # WHY: a valid existing block.
        assert manager._check_service_address_overlap({"name": "Ports-Only"}, existing) is None

    def test_the_scan_reaches_every_new_address(self, manager: OrgConfigMigrationManager) -> None:
        """Stopping at the first clean address would miss a later overlap."""
        existing = [{"name": "Web", "addresses": ["192.168.5.0/24"]}]  # WHY: matches the third.
        # WHY: only the third address overlaps, so the loop must reach it.
        new_obj = {"addresses": ["10.0.0.0/24", "172.16.0.0/24", "192.168.5.10/32"]}
        assert manager._check_service_address_overlap(new_obj, existing) is not None

    def test_an_invalid_new_address_is_skipped(self, manager: OrgConfigMigrationManager) -> None:
        """A hostname in an address field must not crash the whole import."""
        existing = [{"name": "Web", "addresses": ["10.0.0.0/16"]}]  # WHY: a valid existing block.
        # WHY: the first value fails to parse, so the loop must reach the second.
        new_obj = {"addresses": ["not-an-ip", "10.0.1.5/32"]}
        assert manager._check_service_address_overlap(new_obj, existing) is not None

    def test_an_invalid_existing_address_is_skipped(self, manager: OrgConfigMigrationManager) -> None:
        """One corrupt existing address must not hide a real overlap beside it."""
        # WHY: the first existing address fails to parse, so the scan must continue.
        existing = [{"name": "Web", "addresses": ["bad-value", "10.0.0.0/16"]}]
        new_obj = {"addresses": ["10.0.1.5/32"]}  # WHY: a host inside the second block.
        assert manager._check_service_address_overlap(new_obj, existing) is not None

    def test_an_existing_service_without_addresses_is_skipped(self, manager: OrgConfigMigrationManager) -> None:
        """A port-only existing service has nothing to compare against."""
        existing = [{"name": "Ports-Only"}]  # WHY: no address field at all.
        new_obj = {"addresses": ["10.0.1.5/32"]}  # WHY: a valid new address.
        assert manager._check_service_address_overlap(new_obj, existing) is None

    def test_the_detail_names_both_services(self, manager: OrgConfigMigrationManager) -> None:
        """The operator needs both names to decide which object to keep."""
        existing = [{"name": "Web", "addresses": ["10.0.0.0/16"]}]  # WHY: the blocking service.
        conflict = manager._check_service_address_overlap({"addresses": ["10.0.1.5/32"]}, existing)
        assert conflict is not None  # WHY: guard the index below.
        assert "10.0.1.5/32" in conflict["detail"]  # WHY: the new address must be named.
        assert "Web" in conflict["detail"]  # WHY: the blocking service must be named.


class TestNeedsSubnetCheck:
    """Cover the metadata lookup that gates the IP overlap scan."""

    def test_networks_need_the_check(self, manager: OrgConfigMigrationManager) -> None:
        """Networks carry a subnet, so an overlap is possible."""
        assert manager._needs_subnet_check("networks") is True

    def test_services_need_the_check(self, manager: OrgConfigMigrationManager) -> None:
        """Services carry an address list, so an overlap is possible."""
        assert manager._needs_subnet_check("services") is True

    def test_vpns_do_not_need_the_check(self, manager: OrgConfigMigrationManager) -> None:
        """A VPN holds no address field, so an IP scan would waste time."""
        assert manager._needs_subnet_check("vpns") is False

    def test_an_unknown_type_does_not_need_the_check(self, manager: OrgConfigMigrationManager) -> None:
        """An unknown key must return False rather than raise on the lookup."""
        assert manager._needs_subnet_check("no_such_type") is False


class TestDetectConflicts:
    """Cover the guard that runs the name check before the address check."""

    def test_a_name_conflict_short_circuits_the_subnet_check(self, manager: OrgConfigMigrationManager) -> None:
        """A named duplicate blocks the import, so an extra IP scan is wasted work."""
        # WHY: the object matches by name and would also overlap by subnet.
        manager._existing = {"networks": [{"name": "Corp", "subnet": "10.0.0.0/16", "id": "d1"}]}
        conflict = manager._detect_conflicts({"name": "Corp", "subnet": "10.0.1.0/24"}, "networks")
        assert conflict is not None  # WHY: guard the index below.
        assert conflict["reason"] == "name_match"  # WHY: the name check must win the race.

    def test_a_subnet_conflict_is_found_when_the_name_is_clean(self, manager: OrgConfigMigrationManager) -> None:
        """A renamed object with the same range is the case the subnet guard exists for."""
        # WHY: the names differ, so only the subnet scan can catch this one.
        manager._existing = {"networks": [{"name": "Corp", "subnet": "10.0.0.0/16", "id": "d1"}]}
        conflict = manager._detect_conflicts({"name": "Branch", "subnet": "10.0.1.0/24"}, "networks")
        assert conflict is not None  # WHY: guard the index below.
        assert conflict["reason"] == "subnet_overlap"  # WHY: the subnet guard must catch it.

    def test_a_type_without_an_ip_field_skips_the_subnet_check(self, manager: OrgConfigMigrationManager) -> None:
        """A VPN with a clean name must import without an IP scan."""
        manager._existing = {"vpns": [{"name": "Hub", "id": "d1"}]}  # WHY: a different name.
        assert manager._detect_conflicts({"name": "Spoke"}, "vpns") is None

    def test_an_unseen_type_reports_no_conflict(self, manager: OrgConfigMigrationManager) -> None:
        """A type the cache never loaded must not raise on the dictionary read."""
        manager._existing = {}  # WHY: the cache is empty, as it is before the fetch.
        assert manager._detect_conflicts({"name": "Corp"}, "networks") is None


class TestStripSourceFields:
    """Cover the field filter that prevents a source identifier from reaching the create call."""

    def test_the_source_identifiers_are_removed(self, manager: OrgConfigMigrationManager) -> None:
        """Sending a source identifier makes the create call fail or overwrite an object."""
        obj = {
            "id": "src-1",  # WHY: belongs to the source org.
            "org_id": "src-org",  # WHY: belongs to the source org.
            "created_time": 1,  # WHY: the destination sets its own timestamp.
            "modified_time": 2,  # WHY: the destination sets its own timestamp.
            "for_site": True,  # WHY: a site scope does not carry across orgs.
            "name": "Corp-LAN",  # WHY: this field must survive.
        }
        assert manager._strip_source_fields(obj) == {"name": "Corp-LAN"}

    def test_the_original_object_is_not_changed(self, manager: OrgConfigMigrationManager) -> None:
        """The caller still needs the source identifier to build the remap entry."""
        obj = {"id": "src-1", "name": "Corp-LAN"}  # WHY: the identifier must survive the call.
        manager._strip_source_fields(obj)  # WHY: drive the filter.
        assert obj["id"] == "src-1"  # WHY: an in-place delete would break the remap table.

    def test_an_empty_object_stays_empty(self, manager: OrgConfigMigrationManager) -> None:
        """An empty object must return cleanly rather than raise on the loop."""
        assert manager._strip_source_fields({}) == {}


class TestRemapping:
    """Cover the reference repair that keeps a bundle self-consistent after import."""

    def test_a_remap_entry_is_recorded(self, manager: OrgConfigMigrationManager) -> None:
        """A missing entry leaves every later reference pointing at the source org."""
        manager._build_remap_entry("source-object-id", "dest-object-id")  # WHY: drive the record.
        assert manager._remap_table["source-object-id"] == "dest-object-id"

    def test_a_vpn_network_identifier_is_swapped(self, manager: OrgConfigMigrationManager) -> None:
        """A stale network identifier points the VPN at an object the org does not hold."""
        manager._remap_table = {"src-net": "dest-net"}  # WHY: the mapping the import built.
        obj: dict[str, Any] = {"networks": {"corp": {"id": "src-net"}}}  # WHY: one reference.
        manager._remap_vpn_networks(obj)  # WHY: drive the swap.
        assert obj["networks"]["corp"]["id"] == "dest-net"

    def test_an_unmapped_vpn_identifier_is_left_alone(self, manager: OrgConfigMigrationManager) -> None:
        """Blanking an unmapped reference would silently drop a network from the VPN."""
        manager._remap_table = {}  # WHY: no mapping exists for this reference.
        obj: dict[str, Any] = {"networks": {"corp": {"id": "src-net"}}}  # WHY: one reference.
        manager._remap_vpn_networks(obj)  # WHY: drive the fallback branch.
        assert obj["networks"]["corp"]["id"] == "src-net"  # WHY: the original must survive.

    def test_a_vpn_entry_without_an_identifier_survives(self, manager: OrgConfigMigrationManager) -> None:
        """Dropping an entry without an identifier would lose part of the VPN config."""
        manager._remap_table = {"src-net": "dest-net"}  # WHY: the mapping the import built.
        obj: dict[str, Any] = {"networks": {"corp": {"vlan_id": 10}}}  # WHY: no identifier.
        manager._remap_vpn_networks(obj)  # WHY: drive the preserve branch.
        assert obj["networks"]["corp"] == {"vlan_id": 10}  # WHY: the entry must survive intact.

    def test_a_malformed_vpn_networks_value_is_ignored(self, manager: OrgConfigMigrationManager) -> None:
        """A list where a dictionary belongs must not crash the whole import."""
        obj: dict[str, Any] = {"networks": ["not-a-dict"]}  # WHY: reproduce the bad shape.
        manager._remap_vpn_networks(obj)  # WHY: the call must return, not raise.
        assert obj["networks"] == ["not-a-dict"]  # WHY: the guard must not rewrite the value.

    def test_a_gateway_template_network_identifier_is_swapped(self, manager: OrgConfigMigrationManager) -> None:
        """A gateway template references networks by identifier, same as a VPN."""
        manager._remap_table = {"src-net": "dest-net"}  # WHY: the mapping the import built.
        obj: dict[str, Any] = {"networks": {"corp": {"id": "src-net"}}}  # WHY: one reference.
        manager._remap_gateway_template_refs(obj)  # WHY: drive the swap.
        assert obj["networks"]["corp"]["id"] == "dest-net"

    def test_a_malformed_gateway_template_value_is_ignored(self, manager: OrgConfigMigrationManager) -> None:
        """A list where a dictionary belongs must not crash the whole import."""
        obj: dict[str, Any] = {"networks": ["not-a-dict"]}  # WHY: reproduce the bad shape.
        manager._remap_gateway_template_refs(obj)  # WHY: the call must return, not raise.
        assert obj["networks"] == ["not-a-dict"]  # WHY: the guard must not rewrite the value.

    def test_a_device_profile_template_identifier_is_swapped(self, manager: OrgConfigMigrationManager) -> None:
        """A device profile points at one gateway template by identifier."""
        manager._remap_table = {"src-tpl": "dest-tpl"}  # WHY: the mapping the import built.
        obj: dict[str, Any] = {"gateway_template_id": "src-tpl"}  # WHY: one reference.
        manager._remap_device_profile_refs(obj)  # WHY: drive the swap.
        assert obj["gateway_template_id"] == "dest-tpl"

    def test_an_unmapped_device_profile_identifier_is_left_alone(self, manager: OrgConfigMigrationManager) -> None:
        """Blanking an unmapped reference would detach the profile from its template."""
        manager._remap_table = {}  # WHY: no mapping exists for this reference.
        obj: dict[str, Any] = {"gateway_template_id": "src-tpl"}  # WHY: one reference.
        manager._remap_device_profile_refs(obj)  # WHY: drive the guard.
        assert obj["gateway_template_id"] == "src-tpl"  # WHY: the original must survive.

    def test_a_device_profile_without_a_template_is_untouched(self, manager: OrgConfigMigrationManager) -> None:
        """A standalone profile has no template reference to repair."""
        obj: dict[str, Any] = {"name": "Branch-GW"}  # WHY: no template reference.
        manager._remap_device_profile_refs(obj)  # WHY: the call must return, not raise.
        assert obj == {"name": "Branch-GW"}  # WHY: the guard must not add a key.

    def test_a_service_policy_identifier_is_swapped(self, manager: OrgConfigMigrationManager) -> None:
        """A service policy references services by identifier in a list."""
        manager._remap_table = {"src-svc": "dest-svc"}  # WHY: the mapping the import built.
        obj: dict[str, Any] = {"services": [{"id": "src-svc"}]}  # WHY: one reference.
        manager._remap_service_policy_refs(obj)  # WHY: drive the swap.
        assert obj["services"][0]["id"] == "dest-svc"

    def test_every_service_policy_entry_is_visited(self, manager: OrgConfigMigrationManager) -> None:
        """Stopping at the first entry would leave a later reference stale."""
        manager._remap_table = {"a": "dest-a", "c": "dest-c"}  # WHY: the first and the third map.
        # WHY: the middle entry has no mapping, so it proves the loop does not stop there.
        obj: dict[str, Any] = {"services": [{"id": "a"}, {"id": "b"}, {"id": "c"}]}
        manager._remap_service_policy_refs(obj)  # WHY: drive the whole loop.
        assert [entry["id"] for entry in obj["services"]] == ["dest-a", "b", "dest-c"]

    def test_a_malformed_service_policy_value_is_ignored(self, manager: OrgConfigMigrationManager) -> None:
        """A dictionary where a list belongs must not crash the whole import."""
        obj: dict[str, Any] = {"services": {"not": "a-list"}}  # WHY: reproduce the bad shape.
        manager._remap_service_policy_refs(obj)  # WHY: the call must return, not raise.
        assert obj["services"] == {"not": "a-list"}  # WHY: the guard must not rewrite the value.

    def test_the_dispatcher_routes_each_type_to_its_repair(self, manager: OrgConfigMigrationManager) -> None:
        """A wrong route would leave every reference of that type stale."""
        manager._remap_table = {"src": "dest"}  # WHY: one mapping serves every case below.
        # WHY: each pair holds the type key and the object shape that type uses.
        cases = [
            ("vpns", {"networks": {"n": {"id": "src"}}}),
            ("gateway_templates", {"networks": {"n": {"id": "src"}}}),
            ("service_policies", {"services": [{"id": "src"}]}),
        ]
        for type_key, obj in cases:  # WHY: one loop keeps the three routes in one assertion.
            manager._remap_object_references(obj, type_key)  # WHY: drive the dispatcher.
        assert cases[0][1]["networks"]["n"]["id"] == "dest"  # WHY: the VPN route must fire.
        assert cases[1][1]["networks"]["n"]["id"] == "dest"  # WHY: the template route must fire.
        assert cases[2][1]["services"][0]["id"] == "dest"  # WHY: the policy route must fire.

    def test_the_dispatcher_returns_a_type_it_does_not_repair(self, manager: OrgConfigMigrationManager) -> None:
        """A network holds no outward reference, so it passes through unchanged."""
        obj: dict[str, Any] = {"name": "Corp-LAN", "subnet": "10.0.1.0/24"}  # WHY: no reference.
        assert manager._remap_object_references(obj, "networks") is obj


class TestResolveApiFn:
    """Cover the dotted-path walker that turns a config entry into a callable."""

    def test_a_dotted_path_resolves_to_the_endpoint(self, manager: OrgConfigMigrationManager) -> None:
        """A wrong walk would call the wrong Mist endpoint against a live org."""
        # WHY: the real SDK path proves the walk works against the shipped package.
        resolved = manager._resolve_api_fn("mistapi.api.v1.orgs.networks.listOrgNetworks")
        assert callable(resolved)  # WHY: the caller invokes the result directly.

    def test_every_configured_list_path_resolves(self, manager: OrgConfigMigrationManager) -> None:
        """A typo in one path breaks that type at run time, not at import time."""
        for config_type in OrgConfigMigrationManager.CONFIG_TYPES:  # WHY: check all six types.
            # WHY: a broken path raises AttributeError here rather than in a live import.
            assert callable(manager._resolve_api_fn(str(config_type["list_fn"])))

    def test_every_configured_create_path_resolves(self, manager: OrgConfigMigrationManager) -> None:
        """A broken create path fails only after the operator confirms the import."""
        for config_type in OrgConfigMigrationManager.CONFIG_TYPES:  # WHY: check all six types.
            assert callable(manager._resolve_api_fn(str(config_type["create_fn"])))

    def test_an_unknown_segment_raises(self, manager: OrgConfigMigrationManager) -> None:
        """A silent None would fail later with a confusing not-callable error."""
        with pytest.raises(AttributeError):  # WHY: fail fast at the resolve step.
            manager._resolve_api_fn("mistapi.api.v1.orgs.networks.noSuchEndpoint")


class TestExtractCreatedId:
    """Cover the response reader that feeds the remap table."""

    def test_an_identifier_is_read_from_the_data_dictionary(self, manager: OrgConfigMigrationManager) -> None:
        """Without the new identifier every later reference stays stale."""
        response = MagicMock()  # WHY: stand in for the SDK response wrapper.
        response.data = {"id": "dest-1", "name": "Corp-LAN"}  # WHY: the documented shape.
        assert manager._extract_created_id(response) == "dest-1"

    def test_a_missing_identifier_returns_an_empty_string(self, manager: OrgConfigMigrationManager) -> None:
        """A partial response must not raise inside the create loop."""
        response = MagicMock()  # WHY: stand in for the SDK response wrapper.
        response.data = {"name": "Corp-LAN"}  # WHY: the identifier is absent.
        assert manager._extract_created_id(response) == ""

    def test_a_list_payload_returns_an_empty_string(self, manager: OrgConfigMigrationManager) -> None:
        """A list payload is the wrong shape, and indexing it would raise."""
        response = MagicMock()  # WHY: stand in for the SDK response wrapper.
        response.data = [{"id": "dest-1"}]  # WHY: reproduce the wrong shape.
        assert manager._extract_created_id(response) == ""


class TestExtractResponseData:
    """Cover the payload reader that both the export and the conflict cache use."""

    def test_a_list_payload_is_returned_directly(self, manager: OrgConfigMigrationManager) -> None:
        """A direct list needs no paging call, which saves a round trip."""
        response = MagicMock()  # WHY: stand in for the SDK response wrapper.
        response.data = [{"id": "a"}, {"id": "b"}]  # WHY: the single-page shape.
        assert manager._extract_response_data(response) == [{"id": "a"}, {"id": "b"}]

    def test_a_paged_payload_goes_through_the_sdk_helper(self, manager: OrgConfigMigrationManager) -> None:
        """A truncated first page would silently shrink the conflict cache."""
        response = MagicMock()  # WHY: stand in for the SDK response wrapper.
        response.data = {"results": []}  # WHY: a dictionary means the reply is paged.
        with patch.object(ocm.mistapi, "get_all", return_value=[{"id": "a"}]) as paging_spy:
            assert manager._extract_response_data(response) == [{"id": "a"}]
        paging_spy.assert_called_once()  # WHY: the helper must follow the remaining pages.

    def test_a_none_paging_result_becomes_an_empty_list(self, manager: OrgConfigMigrationManager) -> None:
        """The SDK returns None for an empty reply, which callers must not index."""
        response = MagicMock()  # WHY: stand in for the SDK response wrapper.
        response.data = {"results": []}  # WHY: a dictionary means the reply is paged.
        with patch.object(ocm.mistapi, "get_all", return_value=None):
            assert manager._extract_response_data(response) == []


class TestFetchConfigType:
    """Cover the fetch that both the export and the conflict cache depend on."""

    def test_the_call_carries_the_page_limit(self, manager: OrgConfigMigrationManager) -> None:
        """A default page size would truncate a large org and hide a conflict."""
        endpoint = MagicMock()  # WHY: stand in for the resolved SDK endpoint.
        with (
            patch.object(manager, "_resolve_api_fn", return_value=endpoint),
            patch.object(manager, "_extract_response_data", return_value=[]),
        ):
            manager._fetch_config_type(dict(OrgConfigMigrationManager.CONFIG_TYPES[0]))
        _, kwargs = endpoint.call_args  # WHY: read the endpoint keywords.
        assert kwargs["limit"] == 1000  # WHY: the large page keeps the fetch to one round trip.

    def test_the_configured_filter_reaches_the_call(self, manager: OrgConfigMigrationManager) -> None:
        """Device profiles must be filtered to gateways, or the import pulls access points."""
        endpoint = MagicMock()  # WHY: stand in for the resolved SDK endpoint.
        # WHY: the device profile entry is the only one that declares extra keywords.
        profile_type = next(ct for ct in OrgConfigMigrationManager.CONFIG_TYPES if ct["key"] == "device_profiles")
        with (
            patch.object(manager, "_resolve_api_fn", return_value=endpoint),
            patch.object(manager, "_extract_response_data", return_value=[]),
        ):
            manager._fetch_config_type(dict(profile_type))
        _, kwargs = endpoint.call_args  # WHY: read the endpoint keywords.
        assert kwargs["type"] == "gateway"  # WHY: an unfiltered call returns the wrong profiles.

    def test_a_failure_returns_an_empty_list(self, manager: OrgConfigMigrationManager, caplog: Any) -> None:
        """One dead endpoint must not abandon the other five config types."""
        caplog.set_level("ERROR")  # WHY: the handler reports the failure at ERROR level.
        with patch.object(manager, "_resolve_api_fn", side_effect=RuntimeError("api down")):
            assert manager._fetch_config_type(dict(OrgConfigMigrationManager.CONFIG_TYPES[0])) == []
        assert "api down" in caplog.text  # WHY: the operator needs the cause to triage.


class TestExecuteImport:
    """Cover the import driver, which must respect the dependency order."""

    def test_the_types_are_imported_in_dependency_order(self, manager: OrgConfigMigrationManager) -> None:
        """A VPN created before its networks references an object that does not exist."""
        # WHY: the bundle lists the dependent types first, so insertion order cannot win.
        bundle = {
            "device_profiles": [{"name": "P"}],  # WHY: import order 2.
            "vpns": [{"name": "V"}],  # WHY: import order 1.
            "networks": [{"name": "N"}],  # WHY: import order 0.
        }
        seen: list[str] = []  # WHY: record the order the batches actually ran in.
        with patch.object(
            manager,
            "_import_type_batch",
            side_effect=lambda ct, *_args: seen.append(str(ct["key"])),
        ):
            manager._execute_import(bundle, dry_run=True)
        assert seen == ["networks", "vpns", "device_profiles"]  # WHY: order must follow the rank.

    def test_an_empty_type_is_skipped(self, manager: OrgConfigMigrationManager) -> None:
        """A batch call for zero objects prints a misleading empty heading."""
        bundle = {"networks": [], "vpns": [{"name": "V"}]}  # WHY: one empty and one populated.
        seen: list[str] = []  # WHY: record which batches actually ran.
        with patch.object(
            manager,
            "_import_type_batch",
            side_effect=lambda ct, *_args: seen.append(str(ct["key"])),
        ):
            manager._execute_import(bundle, dry_run=True)
        assert seen == ["vpns"]  # WHY: the empty type must not produce a batch.

    def test_an_empty_bundle_returns_no_results(self, manager: OrgConfigMigrationManager) -> None:
        """A bundle with only metadata must return cleanly, not raise."""
        assert manager._execute_import({"metadata": {}}, dry_run=True) == []


class TestProcessImportObject:
    """Cover the per-object decision, which is the last guard before a write."""

    @staticmethod
    def _network_type() -> dict[str, Any]:
        """Return the networks config entry, which every test in this class uses.

        Why:
            Networks are the simplest type, because they hold no outward
            reference that the remapping would rewrite.
        """
        # WHY: a copy keeps a test from mutating the shared class constant.
        return dict(OrgConfigMigrationManager.CONFIG_TYPES[0])

    def test_a_conflict_blocks_the_create_call(self, manager: OrgConfigMigrationManager) -> None:
        """The conflict guard exists to stop a duplicate reaching the live org."""
        manager._existing = {"networks": [{"name": "Corp", "id": "dest-1"}]}  # WHY: a duplicate.
        results: list[dict[str, Any]] = []  # WHY: the accumulator the report reads.
        with patch.object(manager, "_create_and_record") as create_spy:
            manager._process_import_object(self._network_type(), {"name": "Corp", "id": "src-1"}, False, results)
        create_spy.assert_not_called()  # WHY: a blocked object must never reach the API.
        assert results[0]["status"] == "skipped"  # WHY: the report must show the skip.

    def test_a_dry_run_never_calls_the_api(self, manager: OrgConfigMigrationManager) -> None:
        """A preview that writes would defeat the whole purpose of the dry run."""
        manager._existing = {"networks": []}  # WHY: no conflict blocks this object.
        results: list[dict[str, Any]] = []  # WHY: the accumulator the report reads.
        with patch.object(manager, "_create_and_record") as create_spy:
            manager._process_import_object(self._network_type(), {"name": "Corp", "id": "src-1"}, True, results)
        create_spy.assert_not_called()  # WHY: a dry run must make no write call.
        assert results[0]["status"] == "would_import"  # WHY: the preview label must differ.

    def test_a_clean_object_reaches_the_create_call(self, manager: OrgConfigMigrationManager) -> None:
        """A clean object is the whole point of the import, so it must not be blocked."""
        manager._existing = {"networks": []}  # WHY: no conflict blocks this object.
        results: list[dict[str, Any]] = []  # WHY: the accumulator the report reads.
        with patch.object(manager, "_create_and_record") as create_spy:
            manager._process_import_object(self._network_type(), {"name": "Corp", "id": "src-1"}, False, results)
        create_spy.assert_called_once()  # WHY: the object must reach the API.

    def test_the_source_fields_are_stripped_before_the_create_call(self, manager: OrgConfigMigrationManager) -> None:
        """A source identifier in the body makes the create call fail on the server."""
        manager._existing = {"networks": []}  # WHY: no conflict blocks this object.
        results: list[dict[str, Any]] = []  # WHY: the accumulator the report reads.
        obj = {"name": "Corp", "id": "src-1", "org_id": "src-org"}  # WHY: two source fields.
        with patch.object(manager, "_create_and_record") as create_spy:
            manager._process_import_object(self._network_type(), obj, False, results)
        cleaned = create_spy.call_args[0][1]  # WHY: read the body the create call received.
        assert "id" not in cleaned  # WHY: the source identifier must not reach the server.
        assert "org_id" not in cleaned  # WHY: the source org must not reach the server.

    def test_an_unnamed_object_is_reported_under_a_placeholder(self, manager: OrgConfigMigrationManager) -> None:
        """A blank line in the report tells the operator nothing."""
        manager._existing = {"networks": []}  # WHY: no conflict blocks this object.
        results: list[dict[str, Any]] = []  # WHY: the accumulator the report reads.
        with patch.object(manager, "_create_and_record"):
            manager._process_import_object(self._network_type(), {"id": "src-1"}, True, results)
        assert results[0]["name"] == "unnamed"  # WHY: the placeholder keeps the row readable.


class TestRecordConflict:
    """Cover the skip record, which also seeds the remap table."""

    def test_the_skip_is_recorded_with_its_reason(self, manager: OrgConfigMigrationManager) -> None:
        """A skip without a reason leaves the operator unable to act on the report."""
        results: list[dict[str, Any]] = []  # WHY: the accumulator the report reads.
        conflict = {"detail": "already exists", "existing_id": "dest-1"}  # WHY: a name match.
        manager._record_conflict("networks", "Corp", "src-1", conflict, results)
        assert results[0]["status"] == "skipped"  # WHY: the report groups by status.
        assert results[0]["reason"] == "already exists"  # WHY: the reason drives the fix.

    def test_a_skipped_object_still_maps_to_the_existing_one(self, manager: OrgConfigMigrationManager) -> None:
        """A later VPN must point at the object that is already in the destination.

        Why:
            Without this entry the VPN keeps the source identifier and breaks.
        """
        results: list[dict[str, Any]] = []  # WHY: the accumulator the report reads.
        conflict = {"detail": "already exists", "existing_id": "dest-1"}  # WHY: a name match.
        manager._record_conflict("networks", "Corp", "src-1", conflict, results)
        assert manager._remap_table["src-1"] == "dest-1"  # WHY: the reference must be repairable.

    def test_a_subnet_conflict_adds_no_mapping(self, manager: OrgConfigMigrationManager) -> None:
        """A subnet overlap names no single existing object to map onto."""
        results: list[dict[str, Any]] = []  # WHY: the accumulator the report reads.
        conflict = {"detail": "10.0.1.0/24 overlaps"}  # WHY: no existing identifier is given.
        manager._record_conflict("networks", "Corp", "src-1", conflict, results)
        assert manager._remap_table == {}  # WHY: a guessed mapping would corrupt the import.


class TestCreateAndRecord:
    """Cover the single write call and the failure path that keeps the import alive."""

    @staticmethod
    def _network_type() -> dict[str, Any]:
        """Return the networks config entry used by every test in this class."""
        # WHY: a copy keeps a test from mutating the shared class constant.
        return dict(OrgConfigMigrationManager.CONFIG_TYPES[0])

    def test_the_body_is_sent_to_the_resolved_endpoint(self, manager: OrgConfigMigrationManager) -> None:
        """A body sent positionally would land in the org identifier slot."""
        endpoint = MagicMock()  # WHY: stand in for the resolved SDK endpoint.
        endpoint.return_value.data = {"id": "dest-1"}  # WHY: the documented reply shape.
        manager.org_id = "org-9"  # WHY: the destination org the write targets.
        results: list[dict[str, Any]] = []  # WHY: the accumulator the report reads.
        with patch.object(manager, "_resolve_api_fn", return_value=endpoint):
            manager._create_and_record(self._network_type(), {"name": "Corp"}, "Corp", "src-1", results)
        args, kwargs = endpoint.call_args  # WHY: read the call the endpoint received.
        assert args[1] == "org-9"  # WHY: the destination org must be the second argument.
        assert kwargs["body"] == {"name": "Corp"}  # WHY: the body must go by keyword.

    def test_a_success_records_the_new_mapping(self, manager: OrgConfigMigrationManager) -> None:
        """A later object references this one, so the new identifier must be stored."""
        endpoint = MagicMock()  # WHY: stand in for the resolved SDK endpoint.
        endpoint.return_value.data = {"id": "dest-1"}  # WHY: the documented reply shape.
        results: list[dict[str, Any]] = []  # WHY: the accumulator the report reads.
        with patch.object(manager, "_resolve_api_fn", return_value=endpoint):
            manager._create_and_record(self._network_type(), {"name": "Corp"}, "Corp", "src-1", results)
        assert manager._remap_table["src-1"] == "dest-1"  # WHY: the reference must be repairable.
        assert results[0]["status"] == "imported"  # WHY: the report must show the success.

    def test_a_response_without_an_identifier_adds_no_mapping(self, manager: OrgConfigMigrationManager) -> None:
        """An empty mapping is safer than one that points at nothing."""
        endpoint = MagicMock()  # WHY: stand in for the resolved SDK endpoint.
        endpoint.return_value.data = {"name": "Corp"}  # WHY: the identifier is absent.
        results: list[dict[str, Any]] = []  # WHY: the accumulator the report reads.
        with patch.object(manager, "_resolve_api_fn", return_value=endpoint):
            manager._create_and_record(self._network_type(), {"name": "Corp"}, "Corp", "src-1", results)
        assert manager._remap_table == {}  # WHY: an empty target would blank a later reference.

    def test_a_failure_is_recorded_and_not_raised(self, manager: OrgConfigMigrationManager, caplog: Any) -> None:
        """One rejected object must not abandon the rest of the import batch."""
        caplog.set_level("ERROR")  # WHY: the handler reports the failure at ERROR level.
        results: list[dict[str, Any]] = []  # WHY: the accumulator the report reads.
        with patch.object(manager, "_resolve_api_fn", side_effect=RuntimeError("400 bad body")):
            manager._create_and_record(self._network_type(), {"name": "Corp"}, "Corp", "src-1", results)
        assert results[0]["status"] == "failed"  # WHY: the report must show the failure.
        assert results[0]["reason"] == "400 bad body"  # WHY: the reason drives the fix.
        assert "400 bad body" in caplog.text  # WHY: the operator needs the cause to triage.

    def test_a_failure_adds_no_mapping(self, manager: OrgConfigMigrationManager) -> None:
        """A mapping to an object that was never created would corrupt every reference."""
        endpoint = MagicMock()  # WHY: stand in for the resolved SDK endpoint.
        endpoint.side_effect = RuntimeError("409 conflict")  # WHY: the server rejects the write.
        results: list[dict[str, Any]] = []  # WHY: the accumulator the report reads.
        with patch.object(manager, "_resolve_api_fn", return_value=endpoint):
            manager._create_and_record(self._network_type(), {"name": "Corp"}, "Corp", "src-1", results)
        assert manager._remap_table == {}  # WHY: no object exists, so no mapping may exist.


class TestImportTypeBatch:
    """Cover the batch loop, which must visit every object in the type."""

    def test_every_object_is_processed(self, manager: OrgConfigMigrationManager) -> None:
        """A dropped object would silently miss part of the migration."""
        config_type = dict(OrgConfigMigrationManager.CONFIG_TYPES[0])  # WHY: the networks entry.
        objects = [{"name": "A"}, {"name": "B"}, {"name": "C"}]  # WHY: three objects to import.
        results: list[dict[str, Any]] = []  # WHY: the accumulator the report reads.
        with patch.object(manager, "_process_import_object") as process_spy:
            manager._import_type_batch(config_type, objects, True, results)
        assert process_spy.call_count == 3  # WHY: the loop must reach every object.

    def test_an_empty_batch_processes_nothing(self, manager: OrgConfigMigrationManager) -> None:
        """An empty list must return cleanly rather than raise on the loop."""
        config_type = dict(OrgConfigMigrationManager.CONFIG_TYPES[0])  # WHY: the networks entry.
        results: list[dict[str, Any]] = []  # WHY: the accumulator the report reads.
        with patch.object(manager, "_process_import_object") as process_spy:
            manager._import_type_batch(config_type, [], True, results)
        process_spy.assert_not_called()  # WHY: no object means no call.


class TestPartitionImportResults:
    """Cover the report grouping that the operator reads after an import."""

    def test_each_status_lands_in_its_own_bucket(self, manager: OrgConfigMigrationManager) -> None:
        """A mixed bucket would hide a failure among the successes."""
        # WHY: one row of each status proves the grouping separates all four.
        results = [
            {"type": "networks", "name": "A", "status": "imported"},
            {"type": "networks", "name": "B", "status": "skipped", "reason": "dup"},
            {"type": "networks", "name": "C", "status": "failed", "reason": "400"},
            {"type": "networks", "name": "D", "status": "would_import"},
        ]
        buckets = manager._partition_import_results(results)  # WHY: drive the grouping.
        # WHY: each bucket must hold exactly the one row that carries its status.
        assert len(buckets["imported"]) == 1
        assert len(buckets["skipped"]) == 1
        assert len(buckets["failed"]) == 1
        assert len(buckets["would_import"]) == 1

    def test_an_empty_result_list_yields_empty_buckets(self, manager: OrgConfigMigrationManager) -> None:
        """A dry run over an empty bundle must not raise on the report."""
        buckets = manager._partition_import_results([])  # WHY: drive the empty path.
        # WHY: every bucket must exist so the printer can read it without a guard.
        assert all(not rows for rows in buckets.values())
