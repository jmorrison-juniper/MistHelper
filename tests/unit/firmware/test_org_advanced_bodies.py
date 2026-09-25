"""Unit tests for the advanced fields of the organization access point child (issue #3383).

Why:
    The multi-site plan sends every access point of every selected site
    through one organization call. That call now carries the canary counts,
    the peer download, and the radio batch fields that the site call already
    carries. These tests prove three rules with no cloud call. The organization
    child reads each field through the same rule as the site body. The
    organization body accepts each value that the site mapper accepts. The
    organization body refuses each value outside its contract.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.firmware import upgrade_service
from src.firmware.aggregate_upgrade_service import AggregateBuildInput, AggregateUpgradeService
from src.firmware.org_upgrade_body import FAILURE_COUNT_HIGHEST, OrgUpgradeBody
from src.firmware.upgrade_service import (
    CanaryOptions,
    DeviceTarget,
    GatewayFamily,
    PeerToPeerOptions,
    RrmOptions,
    UpgradeOptions,
)

ORG_ID = "11111111-1111-1111-1111-111111111111"  # The organization of every plan.
SITE_ONE = "22222222-2222-2222-2222-222222222222"  # The first selected site.
SITE_TWO = "33333333-3333-3333-3333-333333333333"  # The second selected site.
AP_VERSION = "0.15.1"  # The access point version of every plan.
ORCHESTRATION_FIELDS = (  # The optional fields that both the site body and the organization body can carry.
    "canary_phases",
    "max_failures",
    "max_failure_percentage",
    "enable_p2p",
    "p2p_cluster_size",
    "p2p_parallelism",
    "rrm_first_batch_percentage",
    "rrm_max_batch_percentage",
    "rrm_node_order",
    "rrm_mesh_upgrade",
    "rrm_slow_ramp",
)
PEER_ON = PeerToPeerOptions(enable_p2p=True, p2p_cluster_size=20, p2p_parallelism=4)  # A peer download.
RADIO = RrmOptions(  # One value of each radio batch field.
    rrm_first_batch_percentage=10,
    rrm_max_batch_percentage=30,
    rrm_mesh_upgrade="sequential",
    rrm_node_order="fringe_to_center",
    rrm_slow_ramp=True,
)
PLAN_CHOICES = (  # The option sets that the parity test compares.
    UpgradeOptions(),  # The default plan: one write of every device.
    UpgradeOptions(strategy="canary"),  # The default canary phases and no count.
    UpgradeOptions(strategy="canary", canary=CanaryOptions((1, 50, 100), (0, 1, 2), 10), peer_to_peer=PEER_ON),
    UpgradeOptions(strategy="rrm", canary=CanaryOptions(max_failure_percentage=20), rrm=RADIO, peer_to_peer=PEER_ON),
    UpgradeOptions(strategy="serial", canary=CanaryOptions(max_failure_percentage=0)),
    UpgradeOptions(strategy="canary", peer_to_peer=PeerToPeerOptions(enable_p2p=False, p2p_cluster_size=20)),
)
LARGEST_CHOICES = UpgradeOptions(  # The largest value of each field that the site mapper accepts.
    strategy="canary",
    canary=CanaryOptions((1, 10, 50, 100), (FAILURE_COUNT_HIGHEST,) * 4, 100),
    peer_to_peer=PeerToPeerOptions(enable_p2p=True, p2p_cluster_size=1000, p2p_parallelism=1000),
)
LARGEST_RADIO = UpgradeOptions(  # The largest radio batch values that the site mapper accepts.
    strategy="rrm",
    rrm=RrmOptions(100, 100, "parallel", "center_to_fringe", False),
)
BASE_REQUEST: dict[str, object] = {  # The required fields of one organization access point request.
    "site_ids": [SITE_ONE],
    "versions": [{"firmware_type": "ap", "version": AP_VERSION}],
}
REFUSED_REQUESTS = (  # One request for each rule of the new fields.
    {"strategy": "rrm", "max_failures": [1]},  # A count outside the canary strategy.
    {"strategy": "canary", "max_failures": [1, 1, 1, 1]},  # A count list with no phase list.
    {"strategy": "canary", "canary_phases": [50, 100], "max_failures": [1]},  # One count for two phases.
    {"strategy": "canary", "canary_phases": [100], "max_failures": [FAILURE_COUNT_HIGHEST + 1]},  # Above the limit.
    {"strategy": "canary", "canary_phases": [100], "max_failures": [True]},  # A boolean is not a count.
    {"strategy": "canary", "canary_phases": [100], "max_failures": "1"},  # A text is not an array.
    {"strategy": "canary", "canary_phases": [100], "max_failures": [-1]},  # A negative count.
    {"enable_p2p": "yes"},  # A text is not a boolean.
    {"p2p_cluster_size": 5},  # A size with no peer download.
    {"enable_p2p": False, "p2p_parallelism": 5},  # A size with the peer download off.
    {"enable_p2p": True, "p2p_cluster_size": 1001},  # A size above the limit.
    {"enable_p2p": True, "p2p_parallelism": True},  # A boolean is not a size.
    {"strategy": "canary", "canary_phases": [100], "rrm_node_order": "center_to_fringe"},  # Outside the radio plan.
    {"strategy": "rrm", "rrm_first_batch_percentage": 101},  # A share above 100 percent.
    {"strategy": "rrm", "rrm_max_batch_percentage": "30"},  # A text is not a percentage.
    {"strategy": "rrm", "rrm_node_order": "sideways"},  # A word outside the cloud list.
    {"strategy": "rrm", "rrm_mesh_upgrade": "random"},  # A word outside the cloud list.
    {"strategy": "rrm", "rrm_slow_ramp": "yes"},  # A text is not a boolean.
    {"stable_version": True},  # The organization contract names no stable build.
    {"channel": "beta"},  # Only a router reads a release train.
)


def target(mac: str, site_id: str, device_type: str = "ap", model: str = "AP45") -> DeviceTarget:
    """Build one selected target of the access point version."""
    return DeviceTarget(mac, mac, device_type, model, "0.14.1", AP_VERSION, site_id)  # Keep the rows short.


ACCESS_POINTS = (target("001122334455", SITE_ONE), target("001122334466", SITE_TWO))  # One at each site.


def ap_child_body(options: UpgradeOptions) -> dict[str, Any]:
    """Build one plan of two access points and return the body of its organization child."""
    sites = ({"site_id": SITE_ONE, "name": "One"}, {"site_id": SITE_TWO, "name": "Two"})  # The approved sites.
    request = AggregateBuildInput("owner", ORG_ID, sites, ACCESS_POINTS, options, "nonce")  # Group the values.
    record = AggregateUpgradeService().build(request)  # The production build, which calls no cloud.
    children = [child for child in record["children"] if child["route"] == "upgradeOrgDevices"]  # The AP child.
    assert len(children) == 1  # One organization call serves every access point.
    return dict(children[0]["body"])  # The stored request body.


def orchestration(body: dict[str, Any]) -> dict[str, Any]:
    """Return the optional orchestration fields that one body carries."""
    return {name: body[name] for name in ORCHESTRATION_FIELDS if name in body}  # Drop the route fields.


@pytest.mark.parametrize("options", PLAN_CHOICES)
def test_the_organization_child_reads_each_field_as_the_site_body_does(options: UpgradeOptions) -> None:
    """The organization child carries the same orchestration fields as the site body of the same plan.

    Args:
        options: The choices of the operator.
    """
    site_body = upgrade_service.build_body(ACCESS_POINTS, options, GatewayFamily.JUNOS)  # The site call rule.
    assert orchestration(ap_child_body(options)) == orchestration(dict(site_body))  # One rule for both calls.


@pytest.mark.parametrize("options", (*PLAN_CHOICES, LARGEST_CHOICES, LARGEST_RADIO))
def test_the_organization_body_accepts_each_value_that_the_plan_carries(options: UpgradeOptions) -> None:
    """The submit check accepts each body that the plan stores, so no child fails at submit time.

    Why:
        The aggregate service turns an exception at submit time into an
        unknown outcome. The check of the body therefore must accept each value
        that the plan accepted before the confirmation.

    Args:
        options: The choices of the operator.
    """
    body = ap_child_body(options)  # The stored request of the organization child.
    assert OrgUpgradeBody.build(body) == body  # The submit check keeps every field unchanged.


def test_the_default_child_carries_no_new_field() -> None:
    """A canary plan with no advanced value keeps the body of the earlier release."""
    body = ap_child_body(UpgradeOptions(strategy="canary"))  # The default canary plan.
    assert set(body) == {"all_sites", "device_type", "site_ids", "versions", "strategy", "canary_phases"}
    assert body["canary_phases"] == [1, 10, 50, 100]  # The cloud default phases stay the default.


def test_the_organization_child_refuses_the_stable_build() -> None:
    """The organization access point call names no stable build, so the build refuses the choice."""
    with pytest.raises(ValueError, match="stable build"):  # The plan never reaches the confirmation.
        ap_child_body(UpgradeOptions(stable_version=True))


@pytest.mark.parametrize("fields", REFUSED_REQUESTS)
def test_the_organization_body_refuses_each_value_outside_its_contract(fields: dict[str, object]) -> None:
    """Each value outside the organization contract stops the request before the cloud reads it.

    Args:
        fields: The optional fields of one request.
    """
    with pytest.raises(ValueError):  # A refused field must never vanish from a firmware request.
        OrgUpgradeBody.build({**BASE_REQUEST, **fields})


def test_the_organization_body_copies_each_accepted_value() -> None:
    """Each accepted value reaches the request body unchanged."""
    fields = {"strategy": "canary", "canary_phases": [50, 100], "max_failures": [0, 3], "enable_p2p": True}
    body = OrgUpgradeBody.build({**BASE_REQUEST, **fields, "p2p_cluster_size": 0, "p2p_parallelism": 1000})
    assert body["max_failures"] == [0, 3]  # One count for each phase.
    assert (body["enable_p2p"], body["p2p_cluster_size"], body["p2p_parallelism"]) == (True, 0, 1000)
