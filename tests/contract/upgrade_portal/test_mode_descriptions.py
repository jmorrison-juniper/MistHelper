"""Read the actual selection pages without cloud or store connections."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from html.parser import HTMLParser
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from tests.contract.upgrade_portal.test_select import choose_org, register_owner, sign_in_client

logger = logging.getLogger(__name__)


class SelectionPage(HTMLParser):
    """Read descriptions and controls from the rendered selection pages."""

    def __init__(self, markup: str) -> None:
        """Parse one complete page with normal HTML character conversion."""
        super().__init__()
        self.elements: dict[str, dict[str, str | None]] = {}
        self.tags: list[tuple[str, dict[str, str | None]]] = []
        self.parts: list[str] = []
        self.descriptions: dict[str, list[str]] = {}
        self._active: str | None = None
        self.feed(markup)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Keep stable selectors and the controls that must not change."""
        attributes = dict(attrs)
        self.tags.append((tag, attributes))
        marker = attributes.get("data-testid")
        if marker:
            self.elements[marker] = attributes
        if tag == "p" and marker and marker.endswith("-description"):
            self._active = marker
            self.descriptions[marker] = []

    def handle_endtag(self, tag: str) -> None:
        """End a description only when its paragraph ends."""
        if tag == "p":
            self._active = None

    def handle_data(self, data: str) -> None:
        """Keep inline route names inside the surrounding description."""
        self.parts.append(data)
        if self._active is not None:
            self.descriptions[self._active].append(data)

    def text(self, marker: str) -> str:
        """Read the paragraph with browser-equivalent space conversion."""
        return " ".join("".join(self.descriptions[marker]).split())


@pytest.fixture
def selection_client(portal_app: Flask, fake_mist_api: Any, fake_org_id: str) -> Iterator[FlaskClient]:
    """Use the existing signed owner helpers with offline selection readers."""
    logger.info("Prepare the offline selection pages")
    portal_app.config.update(
        WTF_CSRF_ENABLED=False,
        MIST_READER=fake_mist_api.read,
        SITE_LOCK_READER=lambda org_id, site_ids: dict.fromkeys(site_ids),
    )
    fake_mist_api.payloads["listOrgSites"] = [
        *fake_mist_api.payloads["listOrgSites"],
        {"id": "33333333-3333-3333-3333-333333333333", "name": "Second Site", "org_id": fake_org_id},
    ]
    with contextmanager(register_owner)(object()) as owner, portal_app.test_client() as client:
        sign_in_client(client, owner)
        choose_org(client, fake_org_id)
        logger.debug("The offline selection client holds one signed organization")
        yield client


class TestModeDescriptions:
    """Check the current features without changing selection controls."""

    descriptions = {
        "mode-single-site-description": (
            "Single-site: Open the inventory of one site. "
            "If no verified pre-check capture exists, take one. "
            "Set the upgrade options for that site. "
            "For each device, select a target version that its model supports. "
            "Access points, switches, and Junos gateways use site routes "
            "(upgradeSiteDevices or upgradeDevice). "
            "Session Smart Router (SSR) gateways use the organization SSR route (upgradeOrgSsrs)."
        ),
        "mode-multi-site-description": (
            "Multi-site: Select one or more sites. "
            "Set the upgrade options for the selected sites. "
            "For each device, select a target version that its model supports. "
            "One portal operation tracks one or more child jobs. "
            "If all selected access points use one target version, they use an organization cloud job "
            "(upgradeOrgDevices). "
            "If access points use different target versions, they use separate site jobs "
            "(upgradeSiteDevices or upgradeDevice). "
            "Switches and Junos gateways use site routes (upgradeSiteDevices or upgradeDevice). "
            "Session Smart Router (SSR) gateways use the organization SSR route (upgradeOrgSsrs)."
        ),
        "mode-capture-description": (
            "Both modes require a verified pre-check capture for each site. "
            "The portal can use each site's newest verified standalone pre-check capture. "
            "In multi-site mode, take missing pre-check captures from the confirmation page. "
            "After the upgrade phases end, automatic post-check mode takes captures "
            "at sites with accepted upgrade jobs. "
            "In manual post-check mode, take those captures yourself. "
            "Compare each verified pre-check and post-check pair."
        ),
    }

    @pytest.mark.parametrize("mode", ("", "single_site", "multi_site"))
    def test_rendered_mode_descriptions(self, selection_client: FlaskClient, mode: str) -> None:
        """Read both descriptions with no selected mode or either saved mode."""
        logger.info("Read the mode descriptions with selected mode %s", mode)
        if mode:
            selected = selection_client.post("/select/mode", json={"mode": mode})
            assert (selected.status_code, selected.get_json()) == (200, {"next": "/select/site"})
        response = selection_client.get("/select/mode")
        assert response.status_code == 200
        page = SelectionPage(response.get_data(as_text=True))
        assert "one organization-level upgrade job" not in " ".join(page.parts)
        assert "no pre-check" not in " ".join(page.parts)
        assert "no comparison" not in " ".join(page.parts)
        for marker, expected in self.descriptions.items():
            assert page.text(marker) == expected
            assert all(len(sentence.split()) <= 25 for sentence in page.text(marker).split("."))
        logger.debug("The mode page states three current descriptions")

    @pytest.mark.parametrize("mode", ("", "single_site", "multi_site"))
    def test_mode_form_controls(self, selection_client: FlaskClient, mode: str) -> None:
        """Keep the existing action, CSRF field, mode values, and checked states."""
        if mode:
            response = selection_client.post("/select/mode", json={"mode": mode})
            assert response.status_code == 200
        response = selection_client.get("/select/mode")
        assert response.status_code == 200
        page = SelectionPage(response.get_data(as_text=True))
        forms = [attrs for tag, attrs in page.tags if (tag, attrs.get("action")) == ("form", "/select/mode")]
        assert [form["method"] for form in forms] == ["post"]
        csrf = [attrs for tag, attrs in page.tags if (tag, attrs.get("name")) == ("input", "csrf_token")]
        assert [field["type"] for field in csrf] == ["hidden", "hidden"]  # The navigation also holds a CSRF field.
        self._check_mode_inputs(page, mode)

    def _check_mode_inputs(self, page: SelectionPage, mode: str) -> None:
        """Keep both radio values, the required field, and the submit control."""
        for marker, value in (("mode-single-site", "single_site"), ("mode-multi-site", "multi_site")):
            control = page.elements[marker]
            assert (control["type"], control["name"], control["value"]) == ("radio", "mode", value)
            assert ("checked" in control) is (mode == value)
        assert "required" in page.elements["mode-single-site"]
        assert page.elements["mode-continue"]["type"] == "submit"

    def test_mode_page_without_an_organization(self, selection_client: FlaskClient) -> None:
        """Keep the organization route when no organization supports the descriptions."""
        with selection_client.session_transaction() as browser_session:
            browser_session.pop("selected_org_id")
        response = selection_client.get("/select/mode")
        assert response.status_code == 200
        page = SelectionPage(response.get_data(as_text=True))
        assert page.descriptions == {}
        assert [attrs["href"] for tag, attrs in page.tags if tag == "a" and attrs.get("href") == "/select/org"] == [
            "/select/org"
        ]
        assert "mode-continue" not in page.elements


class TestSiteDescriptions:
    """Check the active mode before and after saved site choices."""

    def _open(self, client: FlaskClient, mode: str, site_ids: tuple[str, ...]) -> SelectionPage:
        """Use the real selection routes and preserve their destinations."""
        logger.info("Read the %s site page with %d selected sites", mode, len(site_ids))
        selected = client.post("/select/mode", json={"mode": mode})
        assert (selected.status_code, selected.get_json()) == (200, {"next": "/select/site"})
        if site_ids:
            selected = client.post("/select/site", json={"site_ids": list(site_ids)})
            assert (selected.status_code, selected.get_json()) == (200, {"next": "/upgrade/org/options"})
        response = client.get("/select/site")
        assert response.status_code == 200
        parsed = SelectionPage(response.get_data(as_text=True))
        logger.debug("The rendered site page holds %d identified elements", len(parsed.elements))
        return parsed

    @pytest.mark.parametrize(
        "mode,count", (("single_site", 0), ("multi_site", 0), ("multi_site", 1), ("multi_site", 2))
    )
    def test_rendered_site_descriptions(
        self, selection_client: FlaskClient, fake_site_id: str, mode: str, count: int
    ) -> None:
        """State the current routes and captures for zero, one, or two saved sites."""
        site_ids = (fake_site_id, "33333333-3333-3333-3333-333333333333")
        page = self._open(selection_client, mode, site_ids[:count])
        assert "one organization-level upgrade job" not in " ".join(page.parts)
        assert "no pre-check" not in " ".join(page.parts)
        assert "no comparison" not in " ".join(page.parts)
        marker = "mode-multi-site-description" if mode == "multi_site" else "mode-single-site-description"
        assert page.text("site-mode-description") == TestModeDescriptions.descriptions[marker]
        assert page.text("site-capture-description") == TestModeDescriptions.descriptions["mode-capture-description"]

    @pytest.mark.parametrize(
        "mode,count", (("single_site", 0), ("multi_site", 0), ("multi_site", 1), ("multi_site", 2))
    )
    def test_site_actions_and_saved_states(
        self, selection_client: FlaskClient, fake_site_id: str, mode: str, count: int
    ) -> None:
        """Keep the site links, selection form, checkbox values, and saved states."""
        site_ids = (fake_site_id, "33333333-3333-3333-3333-333333333333")
        page = self._open(selection_client, mode, site_ids[:count])
        if mode == "single_site":
            assert "multi-site-form" not in page.elements
            for site_id in site_ids:
                assert page.elements[f"site-open-{site_id}"]["href"] == f"/select/site/{site_id}"
            return
        self._check_site_inputs(page, site_ids, count)

    def _check_site_inputs(self, page: SelectionPage, site_ids: tuple[str, ...], count: int) -> None:
        """Keep the multi-site form, its CSRF field, and each checkbox state."""
        form = page.elements["multi-site-form"]
        assert (form["method"], form["action"]) == ("post", "/select/site")
        csrf = [attrs for tag, attrs in page.tags if (tag, attrs.get("name")) == ("input", "csrf_token")]
        assert [field["type"] for field in csrf] == ["hidden", "hidden"]  # The navigation also holds a CSRF field.
        for position, site_id in enumerate(site_ids):
            control = page.elements[f"site-select-{site_id}"]
            assert (control["type"], control["name"], control["value"]) == ("checkbox", "site_ids", site_id)
            assert ("checked" in control) is (position < count)
        assert page.elements["multi-site-continue"]["type"] == "submit"
