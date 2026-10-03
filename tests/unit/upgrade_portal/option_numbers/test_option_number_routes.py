"""Prove named refusals through native single-site and multi-site routes."""

from __future__ import annotations

import logging
from unittest.mock import Mock, patch

import pytest

from src.upgrade_portal.api import numeric_input
from src.upgrade_portal.app.routes import org_upgrade
from src.upgrade_portal.runtime import identity
from src.upgrade_portal.upgrade import options
from tests.support.sdk_pages import HTML_TYPE, build_sdk_answer
from tests.unit.upgrade_portal.option_numbers.option_number_harness import SITE_ID, RouteHarness

FIELDS = (
    "max_failure_percentage",
    "canary_phases",
    "max_failures",
    "p2p_cluster_size",
    "p2p_parallelism",
    "rrm_first_batch_percentage",
    "rrm_max_batch_percentage",
    "reboot_at",
)


@pytest.mark.parametrize("mode", ("single_site", "multi_site"))
@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("token", ("5²", "7" * 5000), ids=("superscript", "5000-digits"))
def test_native_routes_refuse_without_plan_or_worker(
    mode: str, field: str, token: str, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The actual route returns the page label and performs zero prohibited actions."""
    harness = RouteHarness(monkeypatch)
    caplog.set_level(logging.DEBUG)
    with harness.app.test_client() as client:
        owner = harness.sign_in(client, mode)
        try:
            if mode == "single_site":
                response = client.post(f"/api/sites/{SITE_ID}/runs", json={})
                assert response.status_code == 201
                run_id = response.get_json()["run_id"]
                path = f"/api/runs/{run_id}/options"
                harness.store.writes = 0
            else:
                path = "/api/org-upgrades/options"
            value = token + "s" if field == "reboot_at" else token
            response = client.post(path, json=harness.payload(field, value))
            assert response.status_code == 400
            answer = response.get_json()
            text = str(answer)
            labels = options.ORG_OPTION_HELP if mode == "multi_site" else options.OPTION_HELP
            assert labels[field][0] in text
            assert token not in text
            assert token not in caplog.text
            assert "invalid literal" not in text
            assert "sys.set_int_max_str_digits" not in text
            harness.assert_no_actions()
            with client.session_transaction() as session:
                assert "org_upgrade_options" not in session
        finally:
            identity.SESSION_REGISTRY.drop(owner.key)


def test_current_renderer_contains_the_safe_numeric_labels(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each actual options page paints the labels used by numeric refusals."""
    harness = RouteHarness(monkeypatch)
    with harness.app.test_client() as client:
        owner = harness.sign_in(client, "single_site")
        try:
            response = client.post(f"/api/sites/{SITE_ID}/runs", json={})
            assert response.status_code == 201
            run_id = response.get_json()["run_id"]
            page = client.get(f"/runs/{run_id}/options")
            assert page.status_code == 200
            text = " ".join(page.get_data(as_text=True).split())
            for field in FIELDS:
                assert options.OPTION_HELP[field][0] in text
            with client.session_transaction() as session:
                session["selected_upgrade_mode"] = "multi_site"
            page = client.get("/upgrade/org/options")
            assert page.status_code == 200
            text = " ".join(page.get_data(as_text=True).split())
            for field in FIELDS:
                assert options.ORG_OPTION_HELP[field][0] in text
        finally:
            identity.SESSION_REGISTRY.drop(owner.key)


def test_http_502_inventory_refuses_before_plan_persistence(monkeypatch: pytest.MonkeyPatch) -> None:
    """The actual inventory failure cannot become a stored option plan."""
    harness = RouteHarness(monkeypatch)
    failed = build_sdk_answer(502, b"<html>Bad Gateway</html>", HTML_TYPE, "https://api.example.invalid/inventory")
    assert failed.status_code == 502
    harness.fail_inventory(monkeypatch, failed)
    with harness.app.test_client() as client:
        owner = harness.sign_in(client, "multi_site")
        try:
            answer = client.post("/api/org-upgrades/options", json=harness.payload("max_failures", "0"))
            assert answer.status_code == 400
            assert answer.get_json()["error"]["code"] == "org_upgrade_options_invalid"
            harness.assert_no_actions()
        finally:
            identity.SESSION_REGISTRY.drop(owner.key)


@pytest.mark.parametrize("field", ("max_failure_percentage", "canary_phases"))
@pytest.mark.parametrize("token", ("５", "٧", "5²", "7" * 5000, "0000", "101"))
def test_organization_boundary_refuses_before_mapper_with_measured_calls(
    field: str, token: str, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The real route measures lexical refusal before normalization or plan mapping."""
    harness = RouteHarness(monkeypatch)
    method = Mock(wraps=org_upgrade.OrgOptionRefusal.whole_number)
    mapper = Mock(wraps=org_upgrade.build_options)
    conversion = Mock(wraps=int)
    monkeypatch.setattr(org_upgrade.OrgOptionRefusal, "whole_number", method)
    monkeypatch.setattr(org_upgrade, "build_options", mapper)
    monkeypatch.setattr(numeric_input, "int", conversion, raising=False)
    original = numeric_input.AsciiWholeNumberReader.read
    caplog.set_level(logging.DEBUG)
    with patch.object(numeric_input.AsciiWholeNumberReader, "read", autospec=True, side_effect=original) as helper:
        with harness.app.test_client() as client:
            owner = harness.sign_in(client, "multi_site")
            try:
                answer = client.post("/api/org-upgrades/options", json=harness.payload(field, token))
                assert answer.status_code == 400
                text = str(answer.get_json())
                assert options.ORG_OPTION_HELP[field][0] in text
                assert token not in text
                assert token not in caplog.text
                assert "sys.set_int_max_str_digits" not in text
                assert "checked=1" in caplog.text
                preceding = 1 if field == "canary_phases" else 0
                assert method.call_count == preceding + 1
                assert helper.call_count == preceding + (1 if token == "101" else 0)
                assert conversion.call_count == preceding
                mapper.assert_not_called()
                harness.assert_no_actions()
            finally:
                identity.SESSION_REGISTRY.drop(owner.key)


@pytest.mark.parametrize("field", ("max_failure_percentage", "canary_phases"))
@pytest.mark.parametrize("value", ("0", "1", "100", " 10 ", "001"))
def test_organization_boundary_keeps_supported_integer_values(field: str, value: str) -> None:
    """The early reader preserves zero, maximum, whitespace, and supported leading zeros."""
    assert org_upgrade.OrgOptionRefusal.whole_number(value, field) == int(value)


@pytest.mark.parametrize("field", ("max_failure_percentage", "canary_phases"))
def test_organization_conversion_failure_keeps_its_named_safe_refusal(
    field: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An actual helper conversion failure cannot disclose its raw exception text."""
    conversion = Mock(side_effect=ValueError("invalid literal: sensitive entered value"))
    monkeypatch.setattr(numeric_input, "int", conversion, raising=False)
    with pytest.raises(options.BadOptionError) as failure:
        org_upgrade.OrgOptionRefusal.whole_number("7", field)
    assert failure.value.field == field
    assert options.ORG_OPTION_HELP[field][0] in str(failure.value)
    assert "sensitive entered value" not in str(failure.value)
    assert failure.value.__suppress_context__ is True
    conversion.assert_called_once_with("7")
