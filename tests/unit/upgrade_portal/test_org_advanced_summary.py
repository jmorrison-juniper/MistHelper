"""Unit tests for the reader, the form view, and the summary of the multi-site advanced controls.

Why:
    Issue #3383. The typed confirmation page must list each advanced value
    that a stored child body carries, and no value that a child job drops. A line for a
    dropped value would promise a change that the cloud never receives. These
    tests call the module directly, so they need no route, no cloud, and no
    browser.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.upgrade.options import ORG_OPTION_HELP
from src.upgrade_portal.upgrade.org_advanced_options import (
    ADVANCED_FIELDS,
    OrgAdvancedOptions,
    OrgAdvancedRules,
    OrgAdvancedSummary,
)

SUMMARY_PREFIX = "org-upgrade-summary-"  # The test identifier prefix of each summary line.
RADIO_VIEW = {  # A form view of a radio plan with each radio batch value.
    "strategy": "rrm",
    "rrm_first_batch_percentage": "10",
    "rrm_max_batch_percentage": "30",
    "rrm_node_order": "fringe_to_center",
    "rrm_mesh_upgrade": "sequential",
    "rrm_slow_ramp": "no",
}
DEVICE_ID = "00000000-0000-0000-1000-0011223344b1"  # The device identifier of one switch or one router.
CANARY_FIELDS = {"strategy": "canary", "canary_phases": [1, 10, 50, 100]}  # The canary fields of a batch body.
AP_CANARY_BODY = {"device_type": "ap", **CANARY_FIELDS, "max_failures": [0, 1, 2, 3]}  # The access point body.
SWITCH_CANARY_BODY = {  # The site batch body of one switch in a canary plan with counts.
    "version": "23.4R1.9",
    "device_ids": [DEVICE_ID],
    **CANARY_FIELDS,
    "max_failures": [0, 1, 2, 3],
    "reboot": True,
}
AP_RADIO_BODY = {  # The organization access point body of a radio plan.
    "device_type": "ap",
    "strategy": "rrm",
    "rrm_first_batch_percentage": 10,
    "rrm_max_batch_percentage": 30,
    "rrm_node_order": "fringe_to_center",
    "rrm_mesh_upgrade": "sequential",
    "rrm_slow_ramp": False,
}
PEER_FIELDS = {"enable_p2p": True, "p2p_cluster_size": 20, "p2p_parallelism": 4}  # The peer download of a body.
JUNOS_BODY = {"version": "23.4R1.9", "device_ids": [DEVICE_ID], "reboot": True}  # A batch body with no advanced key.
ROUTER_BODY = {"version": "6.3.0", "device_ids": [DEVICE_ID]}  # A router body of a canary plan, as the build writes it.
PER_DEVICE_BODY = {"version": "23.4R1.9", "reboot": False, "snapshot": False}  # The whole per-device schema.
EVERY_FIELD_BODY = {  # One body that carries each advanced field, to check each label.
    **AP_RADIO_BODY,
    **PEER_FIELDS,
    "max_failures": [0],
    "channel": "stable",
    "version": "stable",
}


def plan(*bodies: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the child jobs of one saved plan, one for each stored body.

    Args:
        bodies: The body that each child job sends to the cloud.

    Returns:
        One child record for each body, in the order of the arguments.
    """
    return [{"body": dict(body)} for body in bodies]  # Detach each body, as the durable store does.


def summary_ids(view: dict[str, Any], children: list[dict[str, Any]]) -> list[str]:
    """Return the field part of each summary line identifier.

    Args:
        view: The form view of the saved options.
        children: The child jobs of the saved plan.

    Returns:
        The field names of the summary lines, in page order.
    """
    lines = OrgAdvancedSummary.lines(view, children)  # Build the summary one time.
    return [line["test_id"].removeprefix(SUMMARY_PREFIX) for line in lines]  # Keep only the field part.


def summary_text(view: dict[str, Any], children: list[dict[str, Any]], field: str) -> str:
    """Return the text of the summary line of one field.

    Args:
        view: The form view of the saved options.
        children: The child jobs of the saved plan.
        field: The field part of the line identifier.

    Returns:
        The text of the line.
    """
    lines = OrgAdvancedSummary.lines(view, children)  # Build the summary one time.
    texts = {line["test_id"]: line["text"] for line in lines}  # Index each line by its identifier.
    return texts[SUMMARY_PREFIX + field]  # A missing line raises, so the test names the gap.


def test_a_canary_plan_lists_the_counts_and_no_radio_value() -> None:
    """A canary plan lists its counts and drops each radio value that its bodies never carry."""
    view = {**RADIO_VIEW, "strategy": "canary", "max_failures": "0,1,2,3"}  # Radio values with a canary plan.
    children = plan(AP_CANARY_BODY, SWITCH_CANARY_BODY)  # The access point child and one switch child.
    assert summary_ids(view, children) == ["max-failures"]  # Only the counts reach a child body.


def test_a_radio_plan_names_each_word_as_the_page_shows_it() -> None:
    """A radio plan names each radio choice with the text of the options page."""
    children = plan(AP_RADIO_BODY)  # The access point child of a radio plan.
    assert summary_ids(RADIO_VIEW, children) == [  # Each radio value, in page order.
        "rrm-first-batch-percentage",
        "rrm-max-batch-percentage",
        "rrm-node-order",
        "rrm-mesh-upgrade",
        "rrm-slow-ramp",
    ]
    assert summary_text(RADIO_VIEW, children, "rrm-node-order") == "Start at the edge of each site"  # The order.
    assert summary_text(RADIO_VIEW, children, "rrm-slow-ramp") == "Grow each batch at the usual rate"  # The growth.


def test_a_radio_plan_with_no_access_point_lists_no_radio_value() -> None:
    """A switch plan drops each radio value, because only an access point body carries it."""
    assert summary_ids(RADIO_VIEW, plan(JUNOS_BODY, JUNOS_BODY)) == []  # No child body carries a radio value.


def test_the_peer_sizes_need_the_peer_download() -> None:
    """The two peer download sizes show only while the peer download is on."""
    sizes = {"strategy": "canary", "p2p_cluster_size": "20", "p2p_parallelism": "4"}  # Two sizes.
    assert summary_ids({**sizes, "enable_p2p": False}, plan(AP_CANARY_BODY)) == []  # The body holds no size.
    shown = summary_ids({**sizes, "enable_p2p": True}, plan({**AP_CANARY_BODY, **PEER_FIELDS}))  # Peer download on.
    assert shown == ["enable-p2p", "p2p-cluster-size", "p2p-parallelism"]  # The choice and both sizes.


def test_the_channel_needs_a_router_body_that_carries_it() -> None:
    """The release train shows only for a plan whose router body carries the train."""
    view = {"strategy": "big_bang", "channel": "beta"}  # A gateway plan with the beta train.
    assert summary_ids(view, plan(JUNOS_BODY)) == []  # A Junos gateway body holds no train.
    children = plan(JUNOS_BODY, {**ROUTER_BODY, "channel": "beta"})  # The router body carries the train.
    assert summary_text(view, children, "channel") == "Beta, the build under test"  # The router reads it.


def test_the_stable_build_needs_a_body_that_names_it() -> None:
    """The stable build shows for each body that names the stable word, and never for an access point alone."""
    view = {"strategy": "big_bang", "stable_version": True}  # A plan with the vendor stable build.
    assert summary_ids(view, plan(AP_CANARY_BODY)) == []  # The access point body names a typed version.
    for body in (JUNOS_BODY, ROUTER_BODY, PER_DEVICE_BODY):  # Each body that can carry the stable word.
        children = plan({**body, "version": "stable"})  # The build writes the stable word into the version.
        assert summary_text(view, children, "stable-version") == "Use the vendor stable build"  # The build line.


def test_a_router_child_lists_no_failure_count() -> None:
    """A canary plan of routers lists no count, because the router body holds no canary field."""
    view = {"strategy": "canary", "max_failures": "0,0,0,0"}  # The operator set a count for each phase.
    assert summary_ids(view, plan(ROUTER_BODY)) == []  # No stored body carries the counts.


def test_the_per_device_call_lists_no_failure_count() -> None:
    """A plan of per-device calls lists no count, because that schema holds no orchestration field."""
    view = {"strategy": "canary", "max_failures": "0,0,0,0"}  # One switch at each site, with reboot off.
    assert summary_ids(view, plan(PER_DEVICE_BODY, PER_DEVICE_BODY)) == []  # Neither body carries the counts.


def test_a_damaged_child_makes_no_line() -> None:
    """A child with no readable body makes no line, and a readable body still counts."""
    view = {"strategy": "canary", "max_failures": "0,1,2,3"}  # The operator set a count for each phase.
    damaged = [{}, {"body": None}, {"body": ["max_failures"]}]  # No child holds a body mapping.
    assert summary_ids(view, damaged) == []  # A damaged plan makes no promise.
    assert summary_ids(view, [*damaged, *plan(SWITCH_CANARY_BODY)]) == ["max-failures"]  # One body is enough.


def test_an_unset_value_makes_no_line() -> None:
    """The default form view makes no summary line, so the page shows no empty promise."""
    view = OrgAdvancedOptions.form_values({"strategy": "canary"})  # Every control keeps the cloud default.
    assert OrgAdvancedSummary.lines({**view, "strategy": "canary"}, plan(EVERY_FIELD_BODY)) == []  # No line at all.


@pytest.mark.parametrize("field", ADVANCED_FIELDS)
def test_each_line_names_the_label_of_the_options_page(field: str) -> None:
    """Each summary line names the label that the multi-site options page paints.

    Args:
        field: The cloud field name under test.
    """
    view = {**RADIO_VIEW, "enable_p2p": True, "stable_version": True, "channel": "stable"}  # Each value set.
    view.update(max_failures="0", p2p_cluster_size="20", p2p_parallelism="4")  # The rest of the values.
    lines = OrgAdvancedSummary.lines(view, plan(EVERY_FIELD_BODY))  # One body carries each field.
    labels = {line["test_id"]: line["label"] for line in lines}  # Index each label by its identifier.
    identifier = SUMMARY_PREFIX + field.replace("_", "-")  # The identifier of the line under test.
    assert labels[identifier] == ORG_OPTION_HELP[field][0]  # The confirm page and the options page agree.


def test_the_reader_drops_an_empty_control_and_keeps_a_value() -> None:
    """The reader drops an empty control and keeps each value without its spaces."""
    values = OrgAdvancedOptions.read({"max_failures": " 0,1 ", "rrm_node_order": "", "channel": None})
    assert values == {"max_failures": "0,1"}  # Only the set value remains, and the spaces go.


@pytest.mark.parametrize(
    ("value", "expected"),
    [(True, True), (False, False), ("yes", True), (" Yes ", True), ("no", False), ("", False), (None, False)],
)
def test_the_radio_reader_reads_each_yes_word(value: object, expected: bool) -> None:
    """The radio reader reads a boolean or a yes word, and every other value means no.

    Args:
        value: The radio value under test.
        expected: The reading that the page must show.
    """
    assert OrgAdvancedOptions.chosen(value) is expected  # One reading for each value.


def test_the_router_rule_reads_the_family_of_each_row() -> None:
    """The router rule finds a router row at any selected site."""
    junos = {"targets": [{"gateway_family": "junos"}]}  # A site with a Junos gateway only.
    router = {"targets": [{"gateway_family": "ssr"}]}  # A site with a session smart router.
    assert OrgAdvancedRules.holds_router([junos]) is False  # No router, so no release train control.
    assert OrgAdvancedRules.holds_router([junos, router]) is True  # One router is enough.
