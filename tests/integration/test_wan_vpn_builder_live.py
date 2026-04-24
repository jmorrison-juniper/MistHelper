"""Integration tests for Menu 164 -- WAN Hub-Spoke VPN Builder.

Exercises the real Mist API:
  - Read-only: fetch profiles, fetch VPNs
  - CRUD: create VPN -> verify -> delete -> verify removed
  - E2E smoke: replay full interactive workflow with scripted input

Requires MIST_APITOKEN + MIST_ORG_ID in .env.
Run with:  pytest tests/integration/test_wan_vpn_builder_live.py -m integration -v
"""

import uuid

import mistapi
import mistapi.api.v1.orgs.vpns
import pytest

from src.wan_vpn_builder import WanVpnBuilder

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TEST_VPN_PREFIX = "INTTEST_"


def _unique_vpn_name() -> str:
    """Generate a unique VPN name that won't collide with production VPNs."""
    short_id = uuid.uuid4().hex[:8]
    return f"{TEST_VPN_PREFIX}{short_id}"


def _find_vpn_by_name(session, org: str, name: str) -> dict | None:
    """Search org VPNs for one matching *name* (case-sensitive)."""
    response = mistapi.api.v1.orgs.vpns.listOrgVpns(session, org)
    vpns = mistapi.get_all(response=response, mist_session=session)
    for vpn in vpns:
        if vpn.get("name") == name:
            return vpn
    return None


def _delete_vpn(session, org: str, vpn_id: str) -> None:
    """Delete a VPN by ID (cleanup helper)."""
    mistapi.api.v1.orgs.vpns.deleteOrgVpn(session, org, vpn_id)


def _cleanup_stale_test_vpns(session, org: str) -> None:
    """Remove any leftover VPNs from prior interrupted test runs."""
    response = mistapi.api.v1.orgs.vpns.listOrgVpns(session, org)
    vpns = mistapi.get_all(response=response, mist_session=session)
    for vpn in vpns:
        if vpn.get("name", "").startswith(TEST_VPN_PREFIX):
            vpn_id = vpn.get("id", "")
            if vpn_id:
                _delete_vpn(session, org, vpn_id)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True, scope="module")
def cleanup_stale_vpns(mist_api_session, org_id):
    """Remove leftover test VPNs before *and* after the module runs."""
    _cleanup_stale_test_vpns(mist_api_session, org_id)
    yield
    _cleanup_stale_test_vpns(mist_api_session, org_id)


@pytest.fixture()
def builder(mist_api_session, org_id):
    """Create a WanVpnBuilder wired to the real API."""
    return WanVpnBuilder(mist_api_session, org_id)


# ===================================================================
# Read-Only Tests
# ===================================================================


class TestFetchProfiles:
    """Verify we can read gateway device profiles from the live API."""

    def test_fetch_profiles_returns_list(self, builder):
        profiles = builder._fetch_profiles()
        assert isinstance(profiles, list)

    def test_profiles_have_required_keys(self, builder):
        profiles = builder._fetch_profiles()
        if not profiles:
            pytest.skip("No gateway profiles in this org")
        for profile in profiles:
            assert "id" in profile
            assert "name" in profile


class TestFetchExistingVpns:
    """Verify we can read VPN definitions from the live API."""

    def test_fetch_existing_vpns_returns_list(self, builder):
        vpns = builder._fetch_existing_vpns()
        assert isinstance(vpns, list)

    def test_vpns_have_required_keys(self, builder):
        vpns = builder._fetch_existing_vpns()
        if not vpns:
            pytest.skip("No VPNs defined in this org")
        for vpn in vpns:
            assert "id" in vpn
            assert "name" in vpn


# ===================================================================
# CRUD Tests (Create / Verify / Delete / Verify Removed)
# ===================================================================


class TestVpnCrud:
    """Full create-verify-delete lifecycle against the real API."""

    def test_create_and_delete_vpn(self, mist_api_session, org_id):
        """Create a minimal VPN, confirm it exists, delete it, confirm removal."""
        vpn_name = _unique_vpn_name()
        vpn_body = {
            "name": vpn_name,
            "type": "hub_spoke",
            "path_selection": {"strategy": "simple"},
            "paths": {
                "TEST-ge-0/0/0": {"pod": 1},
            },
        }

        # -- Create --
        response = mistapi.api.v1.orgs.vpns.createOrgVpn(mist_api_session, org_id, body=vpn_body)
        created = response.data if hasattr(response, "data") else response
        vpn_id = created.get("id", "")
        assert vpn_id, "API did not return a VPN ID after creation"
        assert created.get("name") == vpn_name

        try:
            # -- Verify exists --
            found = _find_vpn_by_name(mist_api_session, org_id, vpn_name)
            assert found is not None, f"VPN '{vpn_name}' not found after creation"
            assert found["id"] == vpn_id

            # -- Delete --
            _delete_vpn(mist_api_session, org_id, vpn_id)

            # -- Verify removed --
            gone = _find_vpn_by_name(mist_api_session, org_id, vpn_name)
            assert gone is None, f"VPN '{vpn_name}' still exists after deletion"
        except Exception:
            # Ensure cleanup even if assertions fail mid-test
            try:
                _delete_vpn(mist_api_session, org_id, vpn_id)
            except Exception:
                pass
            raise

    def test_create_vpn_via_builder_method(self, builder, org_id, mist_api_session):
        """Use the builder's _create_vpn method (same path the menu uses)."""
        vpn_name = _unique_vpn_name()
        vpn_body = {
            "name": vpn_name,
            "type": "hub_spoke",
            "path_selection": {"strategy": "simple"},
            "paths": {
                "TEST-wan0": {"pod": 42},
                "TEST-wan0-wan0": {"pod": 42},
            },
        }

        created = builder._create_vpn(vpn_body)
        assert created is not None, "_create_vpn returned None"
        vpn_id = created.get("id", "")
        assert vpn_id

        try:
            found = _find_vpn_by_name(mist_api_session, org_id, vpn_name)
            assert found is not None
            assert found["id"] == vpn_id
        finally:
            _delete_vpn(mist_api_session, org_id, vpn_id)


# ===================================================================
# E2E Smoke Test -- replay the full interactive flow
# ===================================================================


class TestEndToEndSmoke:
    """Replay the full Menu 164 workflow with scripted input.

    This test simulates a user creating a VPN through the interactive
    menu, then verifies the VPN was created and cleans it up.
    """

    def test_full_workflow_with_scripted_input(self, mist_api_session, org_id, capsys):
        """Simulate the full interactive flow:
        1. Enter VPN name
        2. Assign first profile as Hub
        3. Accept default pod
        4. Confirm CREATE
        5. Decline profile updates
        """
        vpn_name = _unique_vpn_name()

        # Pre-check: we need at least one gateway profile
        builder_check = WanVpnBuilder(mist_api_session, org_id)
        profiles = builder_check._fetch_profiles()
        if not profiles:
            pytest.skip("No gateway profiles available for E2E test")

        # Build input sequence:
        #   1. VPN name
        #   2. Role for profile 1 = Hub (H)
        #   3..N. Role for remaining profiles = Skip (K)
        #   N+1. Accept default pod (empty = enter)
        #   N+2. Type CREATE to confirm
        #   N+3. Decline profile updates (N)
        input_sequence = [vpn_name]
        input_sequence.append("H")  # First profile = Hub
        for _ in range(1, len(profiles)):
            input_sequence.append("K")  # Skip remaining profiles
        input_sequence.append("")  # Accept default pod for the hub
        input_sequence.append("CREATE")  # Confirm
        input_sequence.append("N")  # Skip profile updates

        call_index = 0

        def scripted_input(prompt, **kwargs):
            nonlocal call_index
            if call_index < len(input_sequence):
                answer = input_sequence[call_index]
                call_index += 1
                return answer
            return "q"

        # Run the full workflow
        builder = WanVpnBuilder(mist_api_session, org_id, scripted_input)
        builder.run()

        # Verify the VPN was created
        created_vpn = _find_vpn_by_name(mist_api_session, org_id, vpn_name)
        try:
            assert created_vpn is not None, (
                f"VPN '{vpn_name}' not found after E2E workflow. " f"Captured output:\n{capsys.readouterr().out}"
            )
            assert created_vpn.get("type") == "hub_spoke"
            assert "paths" in created_vpn
            assert len(created_vpn["paths"]) > 0

            # capsys already consumed above for the assertion message
        finally:
            # Always clean up
            vpn_id = created_vpn.get("id", "") if created_vpn else ""
            if vpn_id:
                _delete_vpn(mist_api_session, org_id, vpn_id)
