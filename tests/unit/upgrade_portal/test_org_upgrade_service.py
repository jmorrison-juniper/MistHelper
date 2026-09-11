"""Test the organization AP upgrade contract without a live Mist call.

Why:
    A firmware write must keep its explicit scope and execute once. These
    stand-ins record the SDK boundary. One test also exercises the installed
    SDK retry loop with a stand-in HTTP transport. The package fixture blocks
    every outbound socket.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from copy import deepcopy
from dataclasses import dataclass

import pytest
import requests
from mistapi import APISession
from mistapi.__api_request import APIRequest
from requests.adapters import HTTPAdapter

from src.firmware import org_upgrade_service
from src.firmware.org_upgrade_body import OrgUpgradeBody
from src.firmware.org_upgrade_service import OrgUpgradeService, OrgUpgradeSession

ORG_ID = "22222222-2222-2222-2222-222222222222"
SITE_ID = "11111111-1111-1111-1111-111111111111"
SECOND_SITE_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
UPGRADE_ID = "33333333-3333-3333-3333-333333333333"
SITE_UPGRADE_ID = "44444444-4444-4444-4444-444444444444"
FIRST_MAC = "000000000001"
SECOND_MAC = "000000000002"


@dataclass
class ResponseStandIn:
    """Supply the SDK response fields without a network.

    Why:
        An arbitrary response body lets a test prove that malformed responses
        remain errors rather than empty successful jobs.
    """

    status_code: object = 200
    data: object = None
    headers: Mapping[str, str] | None = None
    raw_data: str = ""


class EndpointStandIn:
    """Record each documented SDK operation and its exact arguments.

    Why:
        The submission method requires a keyword body. A test must fail if the
        service uses the site schema or sends a second write.
    """

    def __init__(self) -> None:
        """Start with one valid job response.

        Why:
            Each test changes only the response behavior that it needs.
        """
        self.calls: list[tuple[str, APISession, str, object]] = []
        self.response = ResponseStandIn(data={"id": UPGRADE_ID})
        self.error: Exception | None = None

    def _record(self, name: str, session: APISession, org_id: str, value: object) -> ResponseStandIn:
        """Record the call before returning or raising.

        Why:
            An exception must not hide the count of attempted writes.
        """
        self.calls.append((name, session, org_id, value))
        if self.error is not None:
            raise self.error
        return self.response

    def submit(self, session: APISession, org_id: str, *, body: dict[str, object]) -> ResponseStandIn:
        """Record a submission with a keyword body.

        Why:
            The service must use the verified organization SDK signature.
        """
        return self._record("upgradeOrgDevices", session, org_id, body)

    def status(self, session: APISession, org_id: str, upgrade_id: str) -> ResponseStandIn:
        """Record the job identifier of a status read.

        Why:
            A site identifier cannot replace the organization job identifier.
        """
        return self._record("getOrgDeviceUpgrade", session, org_id, upgrade_id)

    def cancel(self, session: APISession, org_id: str, upgrade_id: str) -> ResponseStandIn:
        """Record a cancel call with no request body.

        Why:
            Cancellation uses its own documented SDK operation.
        """
        return self._record("cancelOrgDeviceUpgrade", session, org_id, upgrade_id)


@pytest.fixture
def session() -> Iterator[OrgUpgradeSession]:
    """Supply a session identity without loading credentials.

    Why:
        The request base creates no credentials and reads no environment file.
        The API session constructor would load environment values.
    """
    stand_in = object.__new__(OrgUpgradeSession)
    APIRequest.__init__(stand_in)
    try:
        yield stand_in
    finally:
        stand_in._session.close()


@pytest.fixture
def request_body() -> dict[str, object]:
    """Supply a minimal request with an explicit site order.

    Why:
        The reverse lexical order detects sorting at the request boundary.
    """
    return {
        "site_ids": [SECOND_SITE_ID, SITE_ID],
        "versions": [{"firmware_type": "ap", "version": "0.14.29411"}],
    }


@pytest.fixture
def cloud(monkeypatch: pytest.MonkeyPatch) -> EndpointStandIn:
    """Replace all three organization SDK operations.

    Why:
        No test in this fixture can submit a live firmware job.
    """
    stand_in = EndpointStandIn()
    monkeypatch.setattr(org_upgrade_service.org_devices, "upgradeOrgDevices", stand_in.submit)
    monkeypatch.setattr(org_upgrade_service.org_devices, "getOrgDeviceUpgrade", stand_in.status)
    monkeypatch.setattr(org_upgrade_service.org_devices, "cancelOrgDeviceUpgrade", stand_in.cancel)
    return stand_in


class TestOrgUpgradeBody:
    """Check the narrow request schema and its conditional fields.

    Why:
        An invalid field must stop the write before the SDK boundary.
    """

    def test_minimal_body_has_only_explicit_ap_scope(self, request_body: dict[str, object]) -> None:
        """Keep the site order and use the documented versions array.

        Why:
            The organization call does not read site-level device identifiers.
        """
        original = deepcopy(request_body)
        assert OrgUpgradeBody.build(request_body) == {
            **original,
            "all_sites": False,
            "device_type": "ap",
            "strategy": "big_bang",
        }
        assert request_body == original

    @pytest.mark.parametrize("strategy", ("big_bang", "canary", "rrm", "serial"))
    def test_documented_strategies(self, request_body: dict[str, object], strategy: str) -> None:
        """Preserve each supported strategy.

        Why:
            The service must not silently replace the requested orchestration.
        """
        request_body["strategy"] = strategy
        assert OrgUpgradeBody.build(request_body)["strategy"] == strategy

    @pytest.mark.parametrize("force", (False, True))
    def test_canary_options_preserve_false_and_zero(self, request_body: dict[str, object], force: bool) -> None:
        """Preserve explicit booleans, zero values, and ordered phase arrays.

        Why:
            A truth test would remove valid values and change the cloud defaults.
        """
        request_body.update(
            all_sites=False,
            device_type="ap",
            versions=[{"firmware_type": "ap", "version": "stable", "force": force}],
            strategy="canary",
            start_time=0,
            canary_phases=(1, 10, 50, 100),
            max_failure_percentage=0,
        )
        expected = {**request_body, "canary_phases": [1, 10, 50, 100]}
        assert OrgUpgradeBody.build(request_body) == expected

    @pytest.mark.parametrize("strategy", ("canary", "rrm", "serial"))
    def test_failure_limit_and_schedule_bounds(self, request_body: dict[str, object], strategy: str) -> None:
        """Accept the documented upper integer bounds.

        Why:
            Boundary values must not fail because a comparison excludes equality.
        """
        request_body.update(strategy=strategy, max_failure_percentage=100, start_time=2**31 - 1)
        result = OrgUpgradeBody.build(request_body)
        assert result["max_failure_percentage"] == 100
        assert result["start_time"] == 2**31 - 1
        assert "canary_phases" not in result

    def test_body_copies_arrays_and_canonicalizes_sites(self, request_body: dict[str, object]) -> None:
        """Detach nested request values without changing their meaning.

        Why:
            The caller can edit a preview without editing a body already built.
        """
        request_body["site_ids"] = (SECOND_SITE_ID.upper(), SITE_ID)
        request_body.update(strategy="canary", canary_phases=[10, 100])
        built = OrgUpgradeBody.build(request_body)
        assert built["site_ids"] == [SECOND_SITE_ID, SITE_ID]
        assert built["versions"] is not request_body["versions"]
        assert built["canary_phases"] is not request_body["canary_phases"]
        assert OrgUpgradeBody.build(built) == built

    @pytest.mark.parametrize(
        ("field", "value"),
        (
            ("all_sites", True),
            ("all_sites", 0),
            ("all_sites", None),
            ("device_type", "switch"),
            ("device_type", "gateway"),
            ("device_type", None),
            ("site_ids", []),
            ("site_ids", None),
            ("site_ids", SITE_ID),
            ("site_ids", {SITE_ID}),
            ("site_ids", ["not-a-uuid"]),
            ("site_ids", [SITE_ID, SITE_ID]),
            ("site_ids", [SECOND_SITE_ID, SECOND_SITE_ID.upper()]),
            ("versions", []),
            ("versions", None),
            ("versions", {"firmware_type": "ap", "version": "0.14.29411"}),
            ("versions", [{}]),
            ("versions", [None]),
            ("versions", [{"firmware_type": "junos", "version": "23.4R1.9"}]),
            ("versions", [{"firmware_type": "ap", "version": ""}]),
            ("versions", [{"firmware_type": "ap", "version": " \t"}]),
            ("versions", [{"firmware_type": "ap", "version": "bad\x00version"}]),
            ("versions", [{"firmware_type": "ap", "version": None}]),
            ("versions", [{"firmware_type": "ap", "version": 1}]),
            ("versions", [{"firmware_type": "ap", "version": "stable", "force": 1}]),
            ("versions", [{"firmware_type": "ap", "version": "stable", "force": None}]),
            ("versions", [{"firmware_type": "ap", "version": "stable", "model_version": {}}]),
            (
                "versions",
                [{"firmware_type": "ap", "version": "one"}, {"firmware_type": "ap", "version": "two"}],
            ),
            ("strategy", "parallel"),
            ("strategy", ""),
            ("strategy", None),
            ("strategy", True),
            ("start_time", -1),
            ("start_time", 2**31),
            ("start_time", True),
            ("start_time", 1.5),
            ("start_time", "1893456000"),
            ("start_time", None),
            ("canary_phases", [10, 100]),
            ("max_failure_percentage", 0),
        ),
    )
    def test_invalid_requests_never_reach_sdk(
        self,
        session: OrgUpgradeSession,
        cloud: EndpointStandIn,
        request_body: dict[str, object],
        field: str,
        value: object,
    ) -> None:
        """Reject malformed or unsafe requests before any write.

        Why:
            A body builder alone cannot guard callers that bypass the preview.
        """
        request_body[field] = value
        original = deepcopy(request_body)
        with pytest.raises(ValueError):
            OrgUpgradeService.submit(session, ORG_ID, request_body)
        assert cloud.calls == []
        assert request_body == original

    @pytest.mark.parametrize(
        "field",
        (
            "device_ids",
            "version",
            "force",
            "models",
            "rules",
            "snapshot",
            "enable_p2p",
            "download_strategy",
            "reboot_strategy",
            "start_datetime",
            "max_failures",
        ),
    )
    def test_unsupported_fields_do_not_disappear(self, request_body: dict[str, object], field: str) -> None:
        """Reject fields outside the supported subset.

        Why:
            Silent filtering could misrepresent the request that the operator approved.
        """
        request_body[field] = None
        with pytest.raises(ValueError, match="unsupported field"):
            OrgUpgradeBody.build(request_body)

    @pytest.mark.parametrize(
        "phases",
        (
            [],
            None,
            "1,100",
            [0, 100],
            [1, 101],
            [10, 10, 100],
            [50, 10, 100],
            [1, 50],
            [True, 100],
            [1.5, 100],
            ["1", 100],
        ),
    )
    def test_invalid_canary_phases(self, request_body: dict[str, object], phases: object) -> None:
        """Reject incomplete, unordered, or mistyped canary phases.

        Why:
            A phase array represents cumulative device percentages.
        """
        request_body.update(strategy="canary", canary_phases=phases)
        with pytest.raises(ValueError, match="canary_phases"):
            OrgUpgradeBody.build(request_body)

    @pytest.mark.parametrize("percentage", (-1, 101, False, 1.5, "5", None))
    def test_invalid_failure_percentage(self, request_body: dict[str, object], percentage: object) -> None:
        """Reject invalid failure limits even for a supported strategy.

        Why:
            Strategy validation does not validate the value's integer type.
        """
        request_body.update(strategy="serial", max_failure_percentage=percentage)
        with pytest.raises(ValueError, match="max_failure_percentage"):
            OrgUpgradeBody.build(request_body)


class TestOrgUpgradeCalls:
    """Check SDK routing and one-attempt behavior.

    Why:
        Submission and cancellation can disrupt devices. Neither can use a
        guessed endpoint or an implicit retry.
    """

    def test_submit_uses_exact_sdk_arguments(
        self, session: OrgUpgradeSession, cloud: EndpointStandIn, request_body: dict[str, object]
    ) -> None:
        """Pass the caller's session and the validated keyword body.

        Why:
            Organization scope must not become a loop over site upgrade calls.
        """
        result = OrgUpgradeService.submit(session, ORG_ID, request_body)
        assert cloud.calls == [("upgradeOrgDevices", session, ORG_ID, OrgUpgradeBody.build(request_body))]
        assert result.org_id == ORG_ID
        assert result.upgrade_id == UPGRADE_ID
        assert result.raw_status == 200
        assert result.error is None

    @pytest.mark.parametrize(
        ("method", "endpoint"), (("status", "getOrgDeviceUpgrade"), ("cancel", "cancelOrgDeviceUpgrade"))
    )
    def test_job_operations_use_exact_sdk_arguments(
        self, session: OrgUpgradeSession, cloud: EndpointStandIn, method: str, endpoint: str
    ) -> None:
        """Use the organization and job identifiers with no request body.

        Why:
            Both operations share a scope but use different SDK functions.
        """
        result = getattr(OrgUpgradeService, method)(session, ORG_ID, UPGRADE_ID)
        assert cloud.calls == [(endpoint, session, ORG_ID, UPGRADE_ID)]
        assert result.upgrade_id == UPGRADE_ID
        assert result.error is None

    @pytest.mark.parametrize("method", ("submit", "status", "cancel"))
    @pytest.mark.parametrize("status", (202, 400, 401, 403, 404, 409, 429, 500, 502, 503))
    def test_http_errors_remain_errors_without_retry(
        self,
        session: OrgUpgradeSession,
        cloud: EndpointStandIn,
        request_body: dict[str, object],
        method: str,
        status: int,
    ) -> None:
        """Preserve each failed HTTP outcome and its response data.

        Why:
            A refusal is not an empty successful upgrade.
        """
        cloud.response = ResponseStandIn(status, {"detail": "The stand-in refused the request."})
        argument = request_body if method == "submit" else UPGRADE_ID
        result = getattr(OrgUpgradeService, method)(session, ORG_ID, argument)
        assert len(cloud.calls) == 1
        assert result.raw_status == status
        assert result.error == f"The cloud returned HTTP {status}."
        assert result.data == cloud.response.data

    @pytest.mark.parametrize("method", ("submit", "cancel"))
    @pytest.mark.parametrize("error_type", (TimeoutError, requests.exceptions.ConnectionError, RuntimeError))
    def test_exceptions_propagate_without_retry(
        self,
        session: OrgUpgradeSession,
        cloud: EndpointStandIn,
        request_body: dict[str, object],
        method: str,
        error_type: type[Exception],
    ) -> None:
        """Surface an uncertain write or a programming error without repeating it.

        Why:
            Catching every exception could conceal a defect or start duplicate work.
        """
        cloud.error = error_type("The stand-in could not return an answer.")
        argument = request_body if method == "submit" else UPGRADE_ID
        with pytest.raises(error_type) as caught:
            getattr(OrgUpgradeService, method)(session, ORG_ID, argument)
        assert caught.value is cloud.error
        assert len(cloud.calls) == 1

    @pytest.mark.parametrize("method", ("submit", "status", "cancel"))
    @pytest.mark.parametrize("org_id", ("", "not-an-org", "../sites"))
    def test_invalid_organization_never_reaches_sdk(
        self,
        session: OrgUpgradeSession,
        cloud: EndpointStandIn,
        request_body: dict[str, object],
        method: str,
        org_id: str,
    ) -> None:
        """Reject invalid organization path values before any SDK operation.

        Why:
            A malformed path must not select another API scope.
        """
        argument = request_body if method == "submit" else UPGRADE_ID
        with pytest.raises(ValueError, match="org_id"):
            getattr(OrgUpgradeService, method)(session, org_id, argument)
        assert cloud.calls == []

    @pytest.mark.parametrize("method", ("status", "cancel"))
    def test_invalid_job_never_reaches_sdk(
        self, session: OrgUpgradeSession, cloud: EndpointStandIn, method: str
    ) -> None:
        """Reject an invalid job identifier before the status or cancel call.

        Why:
            The endpoint requires the organization job UUID.
        """
        with pytest.raises(ValueError, match="upgrade_id"):
            getattr(OrgUpgradeService, method)(session, ORG_ID, "not-a-job")
        assert cloud.calls == []

    @pytest.mark.parametrize("method", ("submit", "cancel"))
    def test_default_sdk_retry_session_is_refused(
        self, cloud: EndpointStandIn, request_body: dict[str, object], method: str
    ) -> None:
        """Reject the SDK default without changing its shared class setting.

        Why:
            Temporarily changing another session's retry setting is not isolated.
        """
        unsafe_session = object.__new__(APISession)
        original = unsafe_session._MAX_429_RETRIES
        argument = request_body if method == "submit" else UPGRADE_ID
        with pytest.raises(ValueError, match="retries disabled"):
            getattr(OrgUpgradeService, method)(unsafe_session, ORG_ID, argument)
        assert cloud.calls == []
        assert unsafe_session._MAX_429_RETRIES == original
        assert OrgUpgradeSession._MAX_429_RETRIES == 0

    @pytest.mark.parametrize("method", ("submit", "cancel"))
    def test_transport_retries_are_refused(
        self, session: OrgUpgradeSession, cloud: EndpointStandIn, request_body: dict[str, object], method: str
    ) -> None:
        """Reject retries beneath the SDK without changing the transport.

        Why:
            An HTTP adapter can retry a write even when SDK retries are zero.
        """
        session._session.mount("https://", HTTPAdapter(max_retries=3))
        argument = request_body if method == "submit" else UPGRADE_ID
        with pytest.raises(ValueError, match="transport retries disabled"):
            getattr(OrgUpgradeService, method)(session, ORG_ID, argument)
        assert cloud.calls == []
        assert session._session.adapters["https://"].max_retries.total == 3

    @pytest.mark.parametrize("method", ("submit", "cancel"))
    def test_installed_sdk_sends_one_http_attempt(
        self, monkeypatch: pytest.MonkeyPatch, session: OrgUpgradeSession, request_body: dict[str, object], method: str
    ) -> None:
        """Exercise the real SDK retry loop with a stand-in HTTP 429 response.

        Why:
            A mocked endpoint cannot reveal retries inside the SDK.
        """
        session._cloud_uri = "api.example.com"
        response = requests.Response()
        response.status_code = 429
        response.headers.update({"Content-Type": "application/json", "Retry-After": "0"})
        response._content = b'{"detail": "The stand-in reached its request limit."}'
        response.request = requests.Request("POST", "https://api.example.com").prepare()
        calls: list[tuple[str, object]] = []

        def post(url: str, *, json: object = None, headers: object = None) -> requests.Response:
            """Return HTTP 429 without opening a socket.

            Why:
                The recorder counts actual transport attempts inside the SDK.
            """
            calls.append((url, json))
            assert headers == {"Content-Type": "application/json"}
            return response

        monkeypatch.setattr(session._session, "post", post)
        argument = request_body if method == "submit" else UPGRADE_ID
        result = getattr(OrgUpgradeService, method)(session, ORG_ID, argument)
        suffix = "" if method == "submit" else f"/{UPGRADE_ID}/cancel"
        expected_body = OrgUpgradeBody.build(request_body) if method == "submit" else None
        assert calls == [(f"https://api.example.com/api/v1/orgs/{ORG_ID}/devices/upgrade{suffix}", expected_body)]
        assert result.raw_status == 429
        assert result.error is not None


class TestOrgUpgradeResponses:
    """Check response structure without inferring device success.

    Why:
        One organization job can contain different states at different sites.
    """

    @pytest.mark.parametrize("collection", ("site_upgrades", "upgrades"))
    @pytest.mark.parametrize("method", ("submit", "status"))
    def test_preserves_site_entries_and_all_target_arrays(
        self,
        session: OrgUpgradeSession,
        cloud: EndpointStandIn,
        request_body: dict[str, object],
        method: str,
        collection: str,
    ) -> None:
        """Keep site order, array order, duplicate entries, and unknown fields.

        Why:
            Flattening these values loses the cloud's device state evidence.
        """
        targets: dict[str, object] = {
            field: [SECOND_MAC, FIRST_MAC, SECOND_MAC]
            for field in (
                "download_requested",
                "downloaded",
                "downloading",
                "failed",
                "reboot_in_progress",
                "rebooted",
                "scheduled",
                "skipped",
                "upgraded",
            )
        }
        targets.update(total=0, extra_state=[], extra_flag=False)
        entries = [
            {"site_id": SECOND_SITE_ID, "upgrade": {"id": SITE_UPGRADE_ID, "status": "upgrading", "targets": targets}},
            {"site_id": SITE_ID, "upgrade": {"id": UPGRADE_ID, "status": "future_state", "start_time": 0}},
        ]
        payload = {
            "id": UPGRADE_ID,
            collection: entries,
            "force": False,
            "enable_p2p": False,
            "target_version": "stable",
        }
        expected = deepcopy(payload)
        cloud.response = ResponseStandIn(data=payload)
        argument = request_body if method == "submit" else UPGRADE_ID
        result = getattr(OrgUpgradeService, method)(session, ORG_ID, argument)
        assert result.error is None
        assert result.data == expected
        assert json.loads(json.dumps(result.data)) == expected
        targets["reboot_in_progress"] = []
        entries.clear()
        assert result.data == expected
        assert "status" not in result.data

    @pytest.mark.parametrize("collection", ("site_upgrades", "upgrades"))
    @pytest.mark.parametrize("method", ("submit", "status", "cancel"))
    def test_preserves_site_upgrade_references(
        self,
        session: OrgUpgradeSession,
        cloud: EndpointStandIn,
        request_body: dict[str, object],
        method: str,
        collection: str,
    ) -> None:
        """Keep reference entries under their original response field.

        Why:
            The OpenAPI item schema uses site_upgrades. The saved guide uses
            upgrades for the same site_id and upgrade_id reference records.
        """
        first = {"site_id": SECOND_SITE_ID.upper(), "upgrade_id": SITE_UPGRADE_ID}
        entries = [first, {"site_id": SITE_ID, "upgrade_id": UPGRADE_ID}, dict(first)]
        payload = {"id": UPGRADE_ID, collection: entries}
        expected = deepcopy(payload)
        cloud.response = ResponseStandIn(data=payload)
        argument = request_body if method == "submit" else UPGRADE_ID
        result = getattr(OrgUpgradeService, method)(session, ORG_ID, argument)
        assert result.error is None
        assert result.data == expected
        assert len(cloud.calls) == 1
        first.clear()
        entries.clear()
        assert result.data == expected

    @pytest.mark.parametrize("collections", ((), ("site_upgrades",), ("upgrades",), ("site_upgrades", "upgrades")))
    def test_preserves_absent_and_empty_site_collections(
        self, session: OrgUpgradeSession, cloud: EndpointStandIn, collections: tuple[str, ...]
    ) -> None:
        """Keep absent fields distinct from empty arrays.

        Why:
            Normalization must not create an alias or replace an empty field.
        """
        payload: dict[str, object] = {"id": UPGRADE_ID, **{name: [] for name in collections}}
        cloud.response = ResponseStandIn(data=payload)
        result = OrgUpgradeService.status(session, ORG_ID, UPGRADE_ID)
        assert result.error is None
        assert result.data == payload

    def test_preserves_both_site_collections(self, session: OrgUpgradeSession, cloud: EndpointStandIn) -> None:
        """Retain both fields even when their entries differ.

        Why:
            Selecting one field as a preferred source would discard valid data.
        """
        payload = {
            "id": UPGRADE_ID,
            "site_upgrades": [{"site_id": SECOND_SITE_ID, "upgrade_id": SITE_UPGRADE_ID}],
            "upgrades": [
                {"site_id": SITE_ID, "upgrade": {"id": UPGRADE_ID, "targets": {"failed": [SECOND_MAC, FIRST_MAC]}}}
            ],
        }
        cloud.response = ResponseStandIn(data=payload)
        result = OrgUpgradeService.status(session, ORG_ID, UPGRADE_ID)
        assert result.error is None
        assert result.data == payload
        assert result.data["site_upgrades"] is not payload["site_upgrades"]
        assert result.data["upgrades"] is not payload["upgrades"]

    @pytest.mark.parametrize("collection", ("site_upgrades", "upgrades"))
    @pytest.mark.parametrize(
        "entries",
        (
            None,
            {},
            [None],
            [{"site_id": SITE_ID}],
            [{"site_id": "invalid", "upgrade_id": SITE_UPGRADE_ID}],
            [{"site_id": SITE_ID, "upgrade_id": None}],
            [{"site_id": SITE_ID, "upgrade_id": "invalid"}],
            [{"site_id": SITE_ID, "upgrade_id": SITE_UPGRADE_ID, "upgrade": None}],
            [{"site_id": SITE_ID, "upgrade_id": None, "upgrade": {"id": SITE_UPGRADE_ID}}],
        ),
    )
    def test_invalid_site_collections_are_not_ignored(
        self, session: OrgUpgradeSession, cloud: EndpointStandIn, collection: str, entries: object
    ) -> None:
        """Report malformed collections and identifiers under either field.

        Why:
            An unrecognized field name must not bypass site validation.
        """
        payload = {"id": UPGRADE_ID, collection: entries}
        cloud.response = ResponseStandIn(data=payload)
        result = OrgUpgradeService.status(session, ORG_ID, UPGRADE_ID)
        assert result.raw_status == 200
        assert result.error is not None
        assert result.data == payload
        assert len(cloud.calls) == 1

    @pytest.mark.parametrize("invalid_collection", ("site_upgrades", "upgrades"))
    @pytest.mark.parametrize("empty_other_collection", (False, True))
    def test_valid_collection_does_not_hide_an_invalid_collection(
        self, session: OrgUpgradeSession, cloud: EndpointStandIn, invalid_collection: str, empty_other_collection: bool
    ) -> None:
        """Validate both present fields instead of selecting one.

        Why:
            A valid or empty array cannot make a malformed sibling field valid.
        """
        entries = [] if empty_other_collection else [{"site_id": SITE_ID, "upgrade_id": SITE_UPGRADE_ID}]
        payload: dict[str, object] = {"id": UPGRADE_ID, "site_upgrades": entries, "upgrades": entries}
        payload[invalid_collection] = None
        cloud.response = ResponseStandIn(data=payload)
        result = OrgUpgradeService.status(session, ORG_ID, UPGRADE_ID)
        assert result.error is not None
        assert result.data == payload

    @pytest.mark.parametrize(
        "data",
        (None, {}, {"detail": "The request was accepted."}, {"id": UPGRADE_ID}, {"id": UPGRADE_ID, "upgrades": []}),
    )
    def test_cancel_does_not_claim_a_final_device_state(
        self, session: OrgUpgradeSession, cloud: EndpointStandIn, data: object
    ) -> None:
        """Accept an empty cancel response without inventing a stopped device.

        Why:
            The contract provides best-effort cancellation, not rollback.
        """
        cloud.response = ResponseStandIn(data=data)
        result = OrgUpgradeService.cancel(session, ORG_ID, UPGRADE_ID)
        assert result.error is None
        assert result.upgrade_id == UPGRADE_ID
        assert result.data == (data if data is not None else {})
        assert "cancelled" not in result.data
        assert "status" not in result.data

    @pytest.mark.parametrize("raw_text", ("{}", "{ }", " \n{}"))
    def test_empty_json_cancel_body_is_valid(
        self, session: OrgUpgradeSession, cloud: EndpointStandIn, raw_text: str
    ) -> None:
        """Accept an empty JSON object as well as an empty HTTP body.

        Why:
            The SDK records valid JSON text separately from its parsed object.
        """
        cloud.response = ResponseStandIn(200, {}, {"Content-Type": "application/json; charset=utf-8"}, raw_text)
        result = OrgUpgradeService.cancel(session, ORG_ID, UPGRADE_ID)
        assert result.error is None
        assert result.data == {}

    def test_malformed_json_cancel_body_is_not_valid(self, session: OrgUpgradeSession, cloud: EndpointStandIn) -> None:
        """Reject invalid JSON even when the SDK retains an empty object.

        Why:
            A JSON content type does not prove that the body contains JSON.
        """
        cloud.response = ResponseStandIn(200, {}, {"Content-Type": "application/json"}, "{")
        result = OrgUpgradeService.cancel(session, ORG_ID, UPGRADE_ID)
        assert result.error is not None and "invalid JSON" in result.error

    @pytest.mark.parametrize(
        "data",
        (
            None,
            [],
            "not JSON",
            {},
            {"id": None},
            {"id": 1},
            {"id": SITE_UPGRADE_ID},
            {"id": UPGRADE_ID, "upgrades": None},
            {"id": UPGRADE_ID, "upgrades": {}},
            {"id": UPGRADE_ID, "upgrades": [None]},
            {"id": UPGRADE_ID, "upgrades": [{"site_id": "bad", "upgrade": {"id": SITE_UPGRADE_ID}}]},
            {"id": UPGRADE_ID, "upgrades": [{"site_id": SITE_ID, "upgrade": None}]},
        ),
    )
    def test_malformed_status_is_not_an_empty_success(
        self, session: OrgUpgradeSession, cloud: EndpointStandIn, data: object
    ) -> None:
        """Retain HTTP 200 while reporting the invalid response structure.

        Why:
            The transport status and the validity of a job response differ.
        """
        cloud.response = ResponseStandIn(data=data)
        result = OrgUpgradeService.status(session, ORG_ID, UPGRADE_ID)
        assert result.raw_status == 200
        assert result.error is not None
        assert result.upgrade_id == UPGRADE_ID
        if isinstance(data, dict):
            assert result.data == data

    @pytest.mark.parametrize("collection", ("site_upgrades", "upgrades"))
    @pytest.mark.parametrize(
        "state",
        (
            {"status": None},
            {"start_time": False},
            {"start_time": -1},
            {"targets": None},
            {"targets": {"reboot_in_progress": True}},
            {"targets": {"upgraded": 2}},
            {"targets": {"failed": [False]}},
            {"targets": {"total": True}},
        ),
    )
    def test_malformed_target_state_remains_visible(
        self, session: OrgUpgradeSession, cloud: EndpointStandIn, state: dict[str, object], collection: str
    ) -> None:
        """Report malformed site state without removing the source fields.

        Why:
            A boolean or count cannot replace a documented target array.
        """
        data = {
            "id": UPGRADE_ID,
            collection: [{"site_id": SITE_ID, "upgrade": {"id": SITE_UPGRADE_ID, **state}}],
        }
        cloud.response = ResponseStandIn(data=data)
        result = OrgUpgradeService.status(session, ORG_ID, UPGRADE_ID)
        assert result.error is not None
        assert result.data == data

    @pytest.mark.parametrize("code", (None, False, "200", 0, 600))
    def test_missing_http_status_is_unknown(
        self, session: OrgUpgradeSession, cloud: EndpointStandIn, code: object
    ) -> None:
        """Report an unknown request outcome when the SDK has no valid status.

        Why:
            A swallowed transport error must not look like an accepted request.
        """
        cloud.response = ResponseStandIn(code, {"id": UPGRADE_ID})
        result = OrgUpgradeService.status(session, ORG_ID, UPGRADE_ID)
        assert result.raw_status == 0
        assert result.error is not None and "unknown" in result.error

    @pytest.mark.parametrize("method", ("status", "cancel"))
    def test_proxy_html_is_not_a_success(self, session: OrgUpgradeSession, cloud: EndpointStandIn, method: str) -> None:
        """Reject an HTML response that the SDK could not parse.

        Why:
            The SDK leaves an empty object after a JSON parse failure.
        """
        cloud.response = ResponseStandIn(200, {}, {"Content-Type": "text/html"}, "<html>proxy failure</html>")
        result = getattr(OrgUpgradeService, method)(session, ORG_ID, UPGRADE_ID)
        assert result.raw_status == 200
        assert result.error is not None
