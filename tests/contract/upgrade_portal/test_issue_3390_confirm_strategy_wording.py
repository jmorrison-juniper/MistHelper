"""Contract tests for issue #3390 confirmation strategy wording."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_ROOT = REPO_ROOT / "src" / "interfaces" / "portals" / "upgrade_portal" / "app" / "assets" / "templates"


def render_template(name: str, **context: object) -> str:
    """Render one confirmation template with strict undefined values."""
    environment = Environment(
        loader=FileSystemLoader(str(TEMPLATE_ROOT)),
        autoescape=True,
        undefined=StrictUndefined,
    )
    environment.globals["url_for"] = lambda endpoint, **values: f"/{endpoint}/{values.get('filename', '')}"
    environment.globals["request"] = None
    return environment.get_template(name).render(**context)


def child(family: str, body: Mapping[str, object], site_name: str = "Site One") -> dict[str, object]:
    """Build one durable child summary."""
    return {"device_family": family, "body": dict(body), "site_name": site_name}


def render_org_page(strategy: str, children: list[dict[str, object]]) -> str:
    """Render the organization confirmation page for one strategy plan."""
    return render_template(
        "upgrade/org_confirm.html",
        org_name="Example organization",
        site_count=1,
        device_count=1,
        device_families=["Switches"],
        firmware_summary="EX4100: 23.4R1",
        options={"strategy": strategy, "reboot_at": ""},
        strategy_children=children,
        advanced_summary=[],
        writes_enabled=False,
        prechecks={"sites": [], "missing": [], "ready": False},
    )


def test_all_per_device_children_state_that_the_cloud_applies_no_strategy() -> None:
    """Every per-device body omits the strategy field."""
    children = [child("switch", {"version": "23.4R1", "reboot": False})]
    assert "The cloud applies no strategy." in render_org_page("canary", children)


def test_mixed_children_name_the_group_without_a_strategy() -> None:
    """A mixed plan names the child group whose body omits the strategy field."""
    children = [
        child("switch", {"version": "23.4R1", "reboot": False}),
        child("ap", {"strategy": "canary", "versions": []}),
    ]
    page = render_org_page("canary", children)
    assert (
        "A few devices first, then the rest. " "The cloud applies no strategy to the switch group at Site One."
    ) in page


def test_normal_children_use_the_plain_language_strategy_name() -> None:
    """A grouped body with a strategy uses the shared display name."""
    children = [child("switch", {"strategy": "serial", "version": "23.4R1"})]
    assert "One device at a time" in render_org_page("serial", children)


def test_empty_children_keep_the_plain_language_strategy_name() -> None:
    """An older plan with no child records keeps the selected strategy name."""
    assert "All devices at the same time" in render_org_page("big_bang", [])


def test_single_site_page_states_no_strategy_for_one_per_device_group() -> None:
    """The single-site page applies the same wording to one per-device group."""
    page = render_template(
        "upgrade/confirm.html",
        run_id="run-3390",
        site_name="Site One",
        targets=[
            {
                "device_type": "switch",
                "model": "EX4100",
                "version_target": "23.4R1",
            }
        ],
        options={"strategy": "canary", "reboot": False},
        pre_capture_id="capture-3390",
        pre_capture_verified=True,
        lock_write_allowed=True,
    )
    assert "The cloud applies no strategy." in page


def test_single_site_page_names_the_group_without_a_strategy() -> None:
    """A mixed single-site plan names the group that uses the per-device call."""
    page = render_template(
        "upgrade/confirm.html",
        run_id="run-3390",
        site_name="Site One",
        targets=[
            {
                "device_type": "switch",
                "model": "EX4100",
                "version_target": "23.4R1",
            },
            {
                "device_type": "ap",
                "model": "AP45",
                "version_target": "0.14.29625",
            },
            {
                "device_type": "ap",
                "model": "AP45",
                "version_target": "0.14.29625",
            },
        ],
        options={"strategy": "canary", "reboot": False},
        pre_capture_id="capture-3390",
        pre_capture_verified=True,
        lock_write_allowed=True,
    )
    assert "A few devices first, then the rest. The cloud applies no strategy to the switch group." in page


def test_single_site_page_keeps_plain_language_for_a_normal_group() -> None:
    """A grouped single-site plan uses the same plain strategy name."""
    page = render_template(
        "upgrade/confirm.html",
        run_id="run-3390",
        site_name="Site One",
        targets=[
            {
                "device_type": "switch",
                "model": "EX4100",
                "version_target": "23.4R1",
            },
            {
                "device_type": "switch",
                "model": "EX4100",
                "version_target": "23.4R1",
            },
        ],
        options={"strategy": "serial", "reboot": False},
        pre_capture_id="capture-3390",
        pre_capture_verified=True,
        lock_write_allowed=True,
    )
    assert "One device at a time" in page


def test_single_site_page_keeps_radio_strategy_limits() -> None:
    """A radio plan states that a grouped switch call receives no strategy."""
    page = render_template(
        "upgrade/confirm.html",
        run_id="run-3390",
        site_name="Site One",
        targets=[
            {
                "device_type": "switch",
                "model": "EX4100",
                "version_target": "23.4R1",
            },
            {
                "device_type": "switch",
                "model": "EX4100",
                "version_target": "23.4R1",
            },
            {
                "device_type": "ap",
                "model": "AP45",
                "version_target": "0.14.29625",
            },
            {
                "device_type": "ap",
                "model": "AP45",
                "version_target": "0.14.29625",
            },
        ],
        options={"strategy": "rrm", "reboot": True},
        pre_capture_id="capture-3390",
        pre_capture_verified=True,
        lock_write_allowed=True,
    )
    assert "Access points in radio batches. The cloud applies no strategy to the switch group." in page
