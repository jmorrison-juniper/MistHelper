"""Contract tests for issue #3390 confirmation strategy wording."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from src.interfaces.portals.upgrade_portal.app.routes.org_upgrade import strategy_summary

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


def test_all_per_device_children_state_that_the_cloud_applies_no_strategy() -> None:
    """Every per-device body omits the strategy field."""
    children = [child("switch", {"version": "23.4R1", "reboot": False})]
    assert strategy_summary({"strategy": "canary"}, children) == "The cloud applies no strategy."


def test_mixed_children_name_the_group_without_a_strategy() -> None:
    """A mixed plan names the child group whose body omits the strategy field."""
    children = [
        child("switch", {"version": "23.4R1", "reboot": False}),
        child("ap", {"strategy": "canary", "versions": []}),
    ]
    summary = strategy_summary({"strategy": "canary"}, children)
    assert summary == ("A few devices first, then the rest. " "The cloud applies no strategy to the switch group.")


def test_normal_children_use_the_plain_language_strategy_name() -> None:
    """A grouped body with a strategy uses the shared display name."""
    children = [child("switch", {"strategy": "serial", "version": "23.4R1"})]
    assert strategy_summary({"strategy": "serial"}, children) == "One device at a time"


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
