"""Verify menu dispatch, real SDK pagination, and CSV output without cloud writes."""

import argparse
import csv
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import mistapi
import pytest
from requests import PreparedRequest, Response

import MistHelper
from src.operations.exporting.export.data_exporter import DataExporter

ORG_ID = "00000000-0000-0000-0000-000000000001"


class SdkScenario:
    """Supply controlled HTTP bytes while retaining the actual SDK and writers."""

    def __init__(self) -> None:
        """Include both connection states, excluded APs, and an unmatched statistic."""
        self.payloads: dict[str, list[dict[str, Any]]] = {
            "ap_led_status": [
                {"code": "03", "key": "NO_IP_ADDRESS", "name": "No IP Address", "description": "No DHCP lease"}
            ],
            "sites": [{"id": "site-one", "name": "First site"}, {"id": "site-two", "name": "Second site"}],
            "inventory": [
                {"mac": "000000000001", "type": "ap", "site_id": "site-one", "connected": True},
                {"mac": "000000000002", "type": "ap", "site_id": "site-two", "connected": False},
                {"mac": "000000000003", "type": "ap", "connected": True},
                {"mac": "000000000004", "type": "ap", "connected": False},
            ],
            "devices": [
                {"mac": "000000000001", "status": "connected", "last_trouble": {"code": 3}},
                {"mac": "000000000002", "status": "disconnected", "last_trouble": {"code": "99"}},
                {"mac": "000000000003", "last_trouble": {"code": "00"}},
                {"mac": "000000000004"},
                {"mac": "000000000005", "last_trouble": {"code": "51"}},
            ],
        }
        self.requests: list[PreparedRequest] = []
        self.failure: tuple[str, int, int | str] | None = None

    def send(self, request: PreparedRequest, **kwargs: Any) -> Response:
        """Reject unexpected requests and return real HTTP responses with page headers."""
        self.requests.append(request)
        url = urlsplit(str(request.url))
        subject = url.path.rsplit("/", 1)[-1]
        query = parse_qs(url.query)
        page = int(query.get("page", ["1"])[0])
        assert request.method == "GET"
        assert url.hostname == "api.mist.com"
        assert url.path == (
            "/api/v1/const/ap_led_status"
            if subject == "ap_led_status"
            else f"/api/v1/orgs/{ORG_ID}/{'stats/devices' if subject == 'devices' else subject}"
        )
        if subject != "ap_led_status":
            assert query["limit"] == ["1"]
        if subject in ("inventory", "devices"):
            assert query["type"] == ["ap"]
        if subject == "devices":
            assert query["status"] == ["all"]
        return self._response(request, subject, page)

    def _response(self, request: PreparedRequest, subject: str, page: int) -> Response:
        """Encode fixtures as bytes so SDK body parsing and cursor creation remain real."""
        response = Response()
        response.request = request
        response.url = str(request.url)
        response.status_code = 200
        response.encoding = "utf-8"
        records = self.payloads[subject]
        response._content = json.dumps(records[page - 1 : page]).encode("utf-8")
        response.headers.update({"X-Page-Total": str(len(records)), "X-Page-Limit": "1", "X-Page-Page": str(page)})
        if self.failure is not None and (subject, page) == self.failure[:2]:
            failure = self.failure[2]
            response.status_code = failure if isinstance(failure, int) else 200
            response._content = b'{"error":"controlled failure"}' if isinstance(failure, int) else failure.encode()
        return response

    def dispatch(self) -> None:
        """Execute the actual CLI dispatcher with no endpoint or writer substitutions."""
        session = mistapi.APISession(host="api.mist.com", show_cli_notif=False, console_log_level=50)
        runtime = SimpleNamespace(
            ConfigUtils=SimpleNamespace(get_cached_or_prompted_org_id=lambda: ORG_ID),
            apisession=session,
            DataExporter=DataExporter,
        )
        arguments = argparse.Namespace(
            menu="307",
            port=None,
            debug=False,
            delay=None,
            fast=False,
            dry_run=None,
            address_check=False,
            skip_ssl_verify=False,
        )
        try:
            with (
                patch("requests.sessions.Session.send", side_effect=self.send),
                patch("src.operations.exporting.ap_warning_report.operation.SourceDependencyResolver", runtime),
                patch(
                    "src.operations.exporting.ap_warning_report.operation.runtime_settings.DEFAULT_API_PAGE_LIMIT", 1
                ),
                patch(
                    "src.operations.exporting.export.data_exporter.SourceDependencyResolver",
                    SimpleNamespace(OUTPUT_FORMAT="csv"),
                ),
            ):
                MistHelper._dispatch_cli_menu_action(arguments, None, None)
        finally:
            session._session.close()


def test_menu_dispatch_through_sdk_to_csv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify exact saved rows after real SDK pagination and successful CLI termination."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MISTHELPER_STANDALONE", "true")
    scenario = SdkScenario()
    with pytest.raises(SystemExit) as completed:
        scenario.dispatch()
    assert completed.value.code == 0
    with (tmp_path / "data" / f"ApWarningReport_{ORG_ID}.csv").open(encoding="utf-8", newline="") as output:
        rows = list(csv.DictReader(output))
    assert len(scenario.requests) == 12
    assert [(row["mac"], row["code"], row["connection_status"]) for row in rows] == [
        ("000000000001", "03", "connected"),
        ("000000000002", "99", "disconnected"),
    ]
    assert [row["site_name"] for row in rows] == ["First site", "Second site"]
    assert [row["definition_status"] for row in rows] == ["known", "unknown"]
    assert rows[0]["code_key"] == "NO_IP_ADDRESS"
    assert all(row["reported_at"].endswith("+00:00") for row in rows)


@pytest.mark.parametrize("subject,page", [("ap_led_status", 1), ("sites", 2), ("inventory", 3), ("devices", 5)])
@pytest.mark.parametrize("failure", [403, 503, "", "bad json"])
def test_sdk_failure_never_reports_cli_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, subject: str, page: int, failure: int | str
) -> None:
    """Invalidate failed or partial reads before any CSV or successful CLI exit exists."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MISTHELPER_STANDALONE", "true")
    scenario = SdkScenario()
    scenario.failure = (subject, page, failure)
    with pytest.raises(RuntimeError, match="The AP warning report failed"):
        scenario.dispatch()
    assert not (tmp_path / "data").exists()
    assert len(scenario.requests) > 0
    final_request = urlsplit(str(scenario.requests[-1].url))
    assert final_request.path.rsplit("/", 1)[-1] == subject
    assert int(parse_qs(final_request.query).get("page", ["1"])[0]) == page
