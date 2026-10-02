"""Native SDK page scenarios for the five reader surfaces of issue #3436."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock
from urllib.parse import urlencode, urlsplit

import pytest
from mistapi.__api_response import APIResponse
from requests import Session

from src.config import runtime_settings
from src.firmware import upgrade_service
from src.upgrade_portal.capture import assembly, collector, devices
from tests.support.sdk_pages import HTML_TYPE, JSON_TYPE, PagedSession, build_sdk_answer


@dataclass(frozen=True)
class Endpoint:
    """The exact native endpoint request and its existing source name."""

    name: str
    path: str
    query: dict[str, str]
    mapped: bool
    section: str

    def url(self, page: int = 1) -> str:
        """Build the transport URL from the same query that the SDK sends."""
        query = dict(self.query)
        if page > 1:
            query["page"] = str(page)
        return f"https://api.mist.com{self.path}?{urlencode(query)}"

    def link(self, page: int) -> str:
        """Return the exact relative link that native headers must construct."""
        return self.url(page).removeprefix("https://api.mist.com")

    def answer(self, rows: list[Any], page: int, total: int) -> APIResponse:
        """Build a real SDK answer without inventing a body total for list reads."""
        payload = {"results": rows, "total": total} if self.mapped else rows
        headers = {**JSON_TYPE, "X-Page-Total": str(total), "X-Page-Limit": "1", "X-Page-Page": str(page)}
        return build_sdk_answer(200, json.dumps(payload).encode("utf-8"), headers, self.url(page))


class Cases:
    """Keep endpoint parameters and failure bodies explicit and independent."""

    ORG_ID = "11111111-2222-3333-4444-555555555555"
    SITE_ID = "66666666-7777-8888-9999-000000000000"
    ENDPOINTS = {
        "inventory": Endpoint(
            "inventory",
            f"/api/v1/orgs/{ORG_ID}/inventory",
            {"site_id": SITE_ID, "vc": "True", "limit": "1"},
            False,
            "devices_inventory",
        ),
        "statistics": Endpoint(
            "statistics",
            f"/api/v1/sites/{SITE_ID}/stats/devices",
            {"type": "all", "limit": "1"},
            False,
            "devices_statistics",
        ),
        "fleet": Endpoint(
            "fleet",
            f"/api/v1/orgs/{ORG_ID}/stats/devices",
            {"type": "all", "site_id": SITE_ID, "fields": "mac,version,uptime,last_seen,fwupdate", "limit": "1"},
            False,
            "upgrade_gate_statistics",
        ),
        "wireless": Endpoint(
            "wireless", f"/api/v1/sites/{SITE_ID}/stats/clients", {"limit": "1"}, False, "wireless_statistics"
        ),
        "wired": Endpoint(
            "wired",
            f"/api/v1/sites/{SITE_ID}/wired_clients/search",
            {"limit": "1", "duration": "1h"},
            True,
            "wired_clients",
        ),
        "wireless_search": Endpoint(
            "wireless_search",
            f"/api/v1/sites/{SITE_ID}/clients/search",
            {"limit": "1", "duration": "1h"},
            True,
            "wireless_search",
        ),
        "guest": Endpoint(
            "guest", f"/api/v1/sites/{SITE_ID}/guests/search", {"limit": "1", "duration": "1h"}, True, "wired_clients"
        ),
        "ports": Endpoint(
            "ports", f"/api/v1/sites/{SITE_ID}/stats/ports/search", {"device_type": "all", "limit": "1"}, True, "ports"
        ),
        "tunnels": Endpoint(
            "tunnels",
            f"/api/v1/orgs/{ORG_ID}/stats/tunnels/search",
            {"site_id": SITE_ID, "limit": "1"},
            True,
            "tunnels",
        ),
        "bgp_peers": Endpoint(
            "bgp_peers", f"/api/v1/sites/{SITE_ID}/stats/bgp_peers/search", {"limit": "1"}, True, "bgp_peers"
        ),
        "alarms": Endpoint("alarms", f"/api/v1/sites/{SITE_ID}/alarms/search", {"limit": "1"}, True, "alarms"),
    }
    FAILURES = [
        ("http_403_html", 403, b"<html>Forbidden</html>", HTML_TYPE),
        ("http_404_json", 404, b'{"detail":"Not found"}', JSON_TYPE),
        ("http_429_json", 429, b'{"detail":"Rate limit"}', JSON_TYPE),
        ("http_500_json", 500, b'{"detail":"Server error"}', JSON_TYPE),
        ("http_503_html", 503, b"<html>Unavailable</html>", HTML_TYPE),
        ("http_503_json", 503, b'{"detail":"Unavailable"}', JSON_TYPE),
        ("error_map", 200, b'{"detail":"No records"}', JSON_TYPE),
        ("malformed_json", 200, b'{"results":', JSON_TYPE),
        ("empty_body", 200, b"", JSON_TYPE),
        ("null_body", 200, b"null", JSON_TYPE),
        ("unreadable_results", 200, b'{"results":null}', JSON_TYPE),
        ("absent_status", 0, b"", JSON_TYPE),
    ]

    @staticmethod
    def row(name: str, number: int = 1) -> dict[str, Any]:
        """Return realistic records with stable natural keys and distinct values."""
        mac = f"0011220000{number:02x}"
        device = {
            "mac": mac,
            "type": "switch",
            "name": f"switch-{number}",
            "version": "23.4R2.13",
            "uptime": 45 + number,
            "last_seen": 1000 + number,
            "status": "connected",
        }
        specialized = {
            "wireless": {
                "mac": f"aabbcc0000{number:02x}",
                "ap_mac": "001122000001",
                "hostname": f"client-{number}",
                "rssi": -50 - number,
                "ssid": "Corp",
            },
            "ports": {
                "mac": "001122000001",
                "port_id": f"ge-0/0/{number}",
                "up": True,
                "poe_on": True,
                "power_draw": 12.5 + number,
            },
            "tunnels": {"mac": mac, "wxtunnel_id": f"tunnel-{number}", "up": True},
            "bgp_peers": {"mac": mac, "neighbor_ip": f"192.0.2.{number}", "vrf_name": "default", "up": True},
            "alarms": {"id": f"alarm-{number}", "type": "device_down", "mac": mac},
        }
        return specialized.get(name, device)


class NativePages:
    """Build native page series and keep the failed page's own status."""

    @staticmethod
    def failure(endpoint: Endpoint, fault: tuple[Any, ...], page: int = 2, total: int = 3) -> APIResponse:
        """Use a real absent-response object when no HTTP status exists."""
        _, status, body, content_headers = fault
        if status == 0:
            return APIResponse(response=None, url=endpoint.url(page))
        headers = {**content_headers, "X-Page-Total": str(total), "X-Page-Limit": "1", "X-Page-Page": str(page)}
        return build_sdk_answer(status, body, headers, endpoint.url(page))

    @staticmethod
    def series(endpoint: Endpoint, fault: tuple[Any, ...] | None, good: int = 1) -> list[APIResponse]:
        """Add a planned sentinel page to prove that failure stops the walk."""
        total = good + 2 if fault is not None else good
        pages = [endpoint.answer([Cases.row(endpoint.name, number)], number, total) for number in range(1, good + 1)]
        if fault is not None:
            pages.append(NativePages.failure(endpoint, fault, good + 1, total))
            pages.append(endpoint.answer([Cases.row(endpoint.name, good + 2)], good + 2, total))
        return pages

    @staticmethod
    def reason(section: str, status: int, reason: str = "page_count_mismatch") -> dict[str, Any]:
        """Return the exact persisted reason contract, not a nonempty proxy."""
        return {"section": section, "reason": reason, "http_status": status}


class OfflineSession:
    """Run real SDK endpoints and delegate later pages to the existing fixture."""

    def __init__(self) -> None:
        """Start with valid empty answers for every capture endpoint."""
        self.first: dict[str, APIResponse | BaseException] = {}
        self.later: dict[str, PagedSession] = {}
        self.first_calls: list[tuple[str, dict[str, str]]] = []
        self.links: list[str] = []
        self.faults: dict[str, BaseException] = {}
        for endpoint in Cases.ENDPOINTS.values():
            self.install(endpoint, [endpoint.answer([], 1, 0)])

    def install(self, endpoint: Endpoint, pages: list[APIResponse]) -> None:
        """Keep the real first answer and real later-page fixture separate."""
        self.first[endpoint.path] = pages[0]
        self.later[endpoint.path] = PagedSession(pages[1:])

    def mist_get(self, uri: str, query: dict[str, str] | None = None) -> APIResponse:
        """Record exact SDK requests and fail any unplanned page call."""
        if query is not None:
            self.first_calls.append((uri, dict(query)))
            first = self.first[uri]
            if isinstance(first, BaseException):
                raise first
            return first
        self.links.append(uri)
        if uri in self.faults:
            raise self.faults[uri]
        return self.later[urlsplit(uri).path].mist_get(uri)


class OfflineChecks:
    """Block live requests and writes for each concrete acceptance decision."""

    @pytest.fixture(autouse=True)
    def block_operations(self, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
        """Check transport and firmware write counts after each acceptance case."""
        self.http = MagicMock(side_effect=AssertionError("A native page test must not open a live connection."))
        self.upgrade = MagicMock(side_effect=AssertionError("A page read must not submit a firmware operation."))
        monkeypatch.setattr(Session, "request", self.http)
        monkeypatch.setattr(upgrade_service, "invoke_upgrade", self.upgrade)
        monkeypatch.setattr(runtime_settings, "DEFAULT_API_PAGE_LIMIT", 1)
        monkeypatch.setenv("MIST_PAGE_LIMIT", "1")
        yield
        assert self.http.call_count == 0
        assert self.upgrade.call_count == 0

    @staticmethod
    def assert_calls(session: OfflineSession, endpoint: Endpoint, good: int = 1, lost: bool = True) -> None:
        """Check the first query, exact native links, and absence of later calls."""
        assert [call for call in session.first_calls if call[0] == endpoint.path] == [(endpoint.path, endpoint.query)]
        last = good + 1 if lost else good
        assert session.links == [endpoint.link(page) for page in range(2, last + 1)]

    @staticmethod
    def assert_read(result: devices.DeviceRead, endpoint: Endpoint, status: int, good: int = 1) -> None:
        """Use a strong invariant that the unchecked walk demonstrably violates."""
        assert result.records == [Cases.row(endpoint.name, number) for number in range(1, good + 1)]
        assert result.partial_reasons == [
            NativePages.reason(endpoint.section, status)
        ], "page_count_mismatch is required"

    @staticmethod
    def capture(session: OfflineSession, tier: int = 3) -> dict[str, Any]:
        """Build the real final capture and prove that no store callback runs."""
        for name in ("inventory", "statistics"):
            endpoint = Cases.ENDPOINTS[name]
            session.install(endpoint, [endpoint.answer([Cases.row(name, 9)], 1, 1)])
        write = MagicMock(side_effect=AssertionError("The document proof must not write a store."))
        load = MagicMock(side_effect=AssertionError("The document proof must not read a store."))
        kit = collector.CaptureResources(
            session=session,
            report=MagicMock(),
            store=collector.CaptureStore(write, load),
            executor=OfflineChecks.execute,
        )
        job = {
            "capture_id": "cap-34360000000000000000000000000000-01",
            "run_id": "run-34360000000000000000000000000000",
            "ordinal": 1,
            "org_id": Cases.ORG_ID,
            "site_id": Cases.SITE_ID,
            "tier": tier,
        }
        document = collector.build_document(job, session, kit)
        assert write.call_count == 0
        assert load.call_count == 0
        assert assembly.validate_capture(document) == []
        return document

    @staticmethod
    def execute(items: list[Any], worker: Any, description: str) -> tuple[list[Any], list[Any]]:
        """Keep call-group order deterministic without replacing production work."""
        del description
        return [worker(item, threading.Semaphore(1)) for item in items], []
