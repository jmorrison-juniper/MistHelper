"""Prove the bounded tenant identifier repair for audit issue #2863."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import pytest
import requests
from hypothesis import given, settings
from hypothesis import strategies as st

from src.api.tenant_fetch import APITenantFetchUtils
from src.websocket.service_ping_discovery import ServicePingDiscoveryMixin


class _PrivateIdentifier:
    """Refuse any attempt to disclose an invalid object's representation."""

    def __str__(self) -> str:
        """Fail if validation tries to print the invalid value."""
        raise RuntimeError("The invalid input representation must stay private.")

    def __repr__(self) -> str:
        """Fail if validation tries to format the invalid value."""
        raise RuntimeError("The invalid input representation must stay private.")


class _TenantCases:
    """Provide exact SDK boundaries and mixed optional payload records."""

    invalid_identifiers = [
        pytest.param(None, id="none"),
        pytest.param("", id="blank"),
        pytest.param(" \t\r\n", id="space"),
        pytest.param(123, id="integer"),
        pytest.param(False, id="boolean"),
        pytest.param(b"private-fixture-metadata", id="bytes"),
        pytest.param([], id="list"),
        pytest.param({"apitoken": "private-fixture-metadata"}, id="mapping"),
        pytest.param(" " * 5000, id="long-space"),
    ]
    org_cases = [
        ("organization_tenants", "api.v1.orgs.networks.listOrgNetworks", None, False),
        (
            "service_policy_tenants",
            "api.v1.orgs.servicepolicies.listOrgServicePolicies",
            "api.v1.sites.servicepolicies.listSiteServicePoliciesDerived",
            False,
        ),
        (
            "gateway_template_tenants",
            "api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates",
            "api.v1.sites.gatewaytemplates.listSiteGatewayTemplatesDerived",
            False,
        ),
        ("_fetch_org_policy_tenants", "api.v1.orgs.servicepolicies.listOrgServicePolicies", None, True),
        ("_fetch_org_template_tenants", "api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates", None, True),
    ]
    site_cases = [
        ("site_tenants", None, "api.v1.sites.networks.listSiteNetworksDerived", False),
        ("_fetch_site_policy_tenants", None, "api.v1.sites.servicepolicies.listSiteServicePoliciesDerived", True),
        ("_fetch_site_template_tenants", None, "api.v1.sites.gatewaytemplates.listSiteGatewayTemplatesDerived", True),
    ]

    @staticmethod
    def response(names: tuple[str, str, str], empty: bool = False) -> SimpleNamespace:
        """Build a response that exercises all three tenant payload formats."""
        first, shared, last = names
        data = [
            None,
            42,
            "unknown",
            {"name": last, "tenants": {**dict.fromkeys(names, {}), None: {}, 7: {}, "": {}}},
            {
                "tenant": first,
                "services": [None, {"tenant": shared}, {"tenant": 7}, {"tenant": ""}],
                "router": {
                    "tenants": [None, {"name": first}, {"name": 7}, {"name": ""}],
                    "tenant_profiles": {shared: {}, None: {}, 7: {}, "": {}},
                },
                "networks": [None, {"tenants": {last: {}, None: {}, 7: {}, "": {}}}],
            },
        ]
        return SimpleNamespace(status_code=200, data=[] if empty else data)

    @staticmethod
    def bind_sdk(
        sdk: MagicMock, empty: bool = False, failure: tuple[int, str] | requests.RequestException | None = None
    ) -> None:
        """Bind every endpoint to a deterministic response without cloud access."""
        org_response = _TenantCases.response(("alpha", "shared", "zulu"), empty)
        site_response = _TenantCases.response(("beta", "shared", "theta"), empty)
        for _, org_endpoint, site_endpoint, _ in _TenantCases.org_cases + _TenantCases.site_cases:
            for endpoint_path in (org_endpoint, site_endpoint):
                if endpoint_path is None:
                    continue
                endpoint = sdk
                for attribute in endpoint_path.split("."):
                    endpoint = getattr(endpoint, attribute)
                endpoint.return_value = org_response if ".orgs." in endpoint_path else site_response
                if isinstance(failure, requests.RequestException):
                    endpoint.side_effect = failure
                elif failure is not None:
                    endpoint.return_value.status_code, endpoint.return_value.raw_data = failure


class TestTenantIdentifierRefusal:
    """Prove named required-input refusals at the real SDK boundary."""

    @pytest.mark.parametrize("case", _TenantCases.org_cases, ids=lambda case: case[0])
    @pytest.mark.parametrize("identifier", _TenantCases.invalid_identifiers)
    def test_missing_org(
        self, case: tuple[str, str | None, str | None, bool], identifier: object, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Every organization boundary refuses an invalid resolver result."""
        method_name, _, _, private = case
        resolver = MagicMock(return_value=identifier)
        utils = APITenantFetchUtils(object(), resolver)
        with patch("src.api.tenant_fetch.mistapi") as sdk, caplog.at_level(logging.INFO):
            _TenantCases.bind_sdk(sdk, empty=True)
            try:
                with pytest.raises(ValueError, match=r"^org_id must be a non-empty string\.$") as refusal:
                    if private:
                        getattr(utils, method_name)(identifier)
                    else:
                        getattr(utils, method_name)()
            finally:
                print(f"Checked 1 org_id refusal case. SDK calls: {len(sdk.mock_calls)}.")
            assert sdk.mock_calls == []
            assert str(refusal.value) == "org_id must be a non-empty string."
        assert resolver.call_count == (0 if private else 1)
        errors = [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR]
        assert errors == [
            "Cannot fetch tenants: org_id must be a non-empty string. checked_identifiers=1 refused_identifiers=1"
        ]
        assert "No org" not in caplog.text

    @pytest.mark.parametrize("case", _TenantCases.site_cases, ids=lambda case: case[0])
    @pytest.mark.parametrize("identifier", _TenantCases.invalid_identifiers)
    def test_missing_required_site(
        self, case: tuple[str, str | None, str | None, bool], identifier: object, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Every required site boundary refuses an invalid direct argument."""
        resolver = MagicMock(return_value="org-1")
        utils = APITenantFetchUtils(object(), resolver)
        with patch("src.api.tenant_fetch.mistapi") as sdk, caplog.at_level(logging.INFO):
            _TenantCases.bind_sdk(sdk, empty=True)
            try:
                with pytest.raises(ValueError, match=r"^site_id must be a non-empty string\.$") as refusal:
                    getattr(utils, case[0])(identifier)
            finally:
                print(f"Checked 1 site_id refusal case. SDK calls: {len(sdk.mock_calls)}.")
            assert sdk.mock_calls == []
            assert str(refusal.value) == "site_id must be a non-empty string."
        resolver.assert_not_called()
        errors = [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR]
        assert errors == [
            "Cannot fetch tenants: site_id must be a non-empty string. checked_identifiers=1 refused_identifiers=1"
        ]
        assert "No site" not in caplog.text

    @pytest.mark.parametrize("case", _TenantCases.org_cases[1:3], ids=lambda case: case[0])
    @pytest.mark.parametrize("identifier", _TenantCases.invalid_identifiers[1:])
    def test_invalid_optional_site(
        self, case: tuple[str, str | None, str | None, bool], identifier: object, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A supplied invalid site refuses before even the organization call."""
        resolver = MagicMock(return_value="org-1")
        utils = APITenantFetchUtils(object(), resolver)
        with patch("src.api.tenant_fetch.mistapi") as sdk, caplog.at_level(logging.INFO):
            _TenantCases.bind_sdk(sdk, empty=True)
            try:
                with pytest.raises(ValueError, match=r"^site_id must be a non-empty string\.$"):
                    getattr(utils, case[0])(identifier)
            finally:
                print(f"Checked 1 optional site_id refusal case. SDK calls: {len(sdk.mock_calls)}.")
            assert sdk.mock_calls == []
        resolver.assert_called_once_with()
        errors = [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR]
        assert errors == [
            "Cannot fetch tenants: site_id must be a non-empty string. checked_identifiers=1 refused_identifiers=1"
        ]
        assert "No org" not in caplog.text

    @settings(max_examples=40, derandomize=True)
    @given(identifier=st.text(alphabet=" \t\r\n\v\f\u00a0\u2003", max_size=5000))
    def test_blank_string_corpus_refuses_before_sdk(self, identifier: str) -> None:
        """Generated whitespace values cannot reach any required boundary."""
        for method_name, org_endpoint, _, private in _TenantCases.org_cases + _TenantCases.site_cases:
            field = "org_id" if org_endpoint else "site_id"
            resolver = MagicMock(return_value=identifier)
            utils = APITenantFetchUtils(object(), resolver)
            with patch("src.api.tenant_fetch.mistapi") as sdk, patch("src.api.tenant_fetch.logger") as logs:
                with pytest.raises(ValueError, match=rf"^{field} must be a non-empty string\.$"):
                    if private or field == "site_id":
                        getattr(utils, method_name)(identifier)
                    else:
                        getattr(utils, method_name)()
                assert sdk.mock_calls == []
                logs.error.assert_called_once_with(
                    "Cannot fetch tenants: %s must be a non-empty string. checked_identifiers=1 refused_identifiers=1",
                    field,
                )

    @settings(max_examples=40, derandomize=True)
    @given(identifier=st.one_of(st.none(), st.booleans(), st.integers(), st.binary(), st.lists(st.integers())))
    def test_nonstring_corpus_refuses_before_sdk(self, identifier: object) -> None:
        """Generated non-string inputs cannot masquerade as identifiers."""
        for method_name, org_endpoint, _, private in _TenantCases.org_cases + _TenantCases.site_cases:
            field = "org_id" if org_endpoint else "site_id"
            utils = APITenantFetchUtils(object(), lambda: identifier)
            with patch("src.api.tenant_fetch.mistapi") as sdk, patch("src.api.tenant_fetch.logger") as logs:
                with pytest.raises(ValueError, match=rf"^{field} must be a non-empty string\.$"):
                    if private or field == "site_id":
                        getattr(utils, method_name)(identifier)
                    else:
                        getattr(utils, method_name)()
                assert sdk.mock_calls == []
                logs.error.assert_called_once_with(
                    "Cannot fetch tenants: %s must be a non-empty string. checked_identifiers=1 refused_identifiers=1",
                    field,
                )


class TestTenantIdentifierSuccess:
    """Preserve exact SDK calls, valid empty results, and tenant-name filtering."""

    @pytest.mark.parametrize("case", _TenantCases.org_cases + _TenantCases.site_cases, ids=lambda case: case[0])
    @pytest.mark.parametrize("empty", [False, True], ids=["records", "empty"])
    def test_valid_sdk_boundary(self, case: tuple[str, str | None, str | None, bool], empty: bool) -> None:
        """Opaque identifiers keep exact arguments and exact tenant results."""
        method_name, org_endpoint, site_endpoint, private = case
        session = object()
        resolver = MagicMock(return_value="org-1")
        utils = APITenantFetchUtils(session, resolver)
        with patch("src.api.tenant_fetch.mistapi") as sdk:
            _TenantCases.bind_sdk(sdk, empty)
            if org_endpoint:
                result = getattr(utils, method_name)("org-1") if private else getattr(utils, method_name)()
                expected_call = getattr(call, org_endpoint)(session, "org-1", limit=1000)
                names = ["alpha", "shared", "zulu"]
            else:
                result = getattr(utils, method_name)("site-1")
                expected_call = getattr(call, site_endpoint)(session, "site-1")
                names = ["beta", "shared", "theta"]
            assert sdk.mock_calls == [expected_call]
            expected_names = [] if empty else names
            assert result == (set(expected_names) if private else expected_names)
        assert resolver.call_count == (1 if org_endpoint and not private else 0)

    @pytest.mark.parametrize("case", _TenantCases.org_cases[1:3], ids=lambda case: case[0])
    @pytest.mark.parametrize("omit_site", [False, True], ids=["explicit-none", "default-none"])
    def test_none_keeps_organization_only(
        self, case: tuple[str, str | None, str | None, bool], omit_site: bool
    ) -> None:
        """Both forms of absent optional site produce exactly one org call."""
        session = object()
        resolver = MagicMock(return_value="org-1")
        utils = APITenantFetchUtils(session, resolver)
        with patch("src.api.tenant_fetch.mistapi") as sdk:
            _TenantCases.bind_sdk(sdk)
            result = getattr(utils, case[0])() if omit_site else getattr(utils, case[0])(None)
            assert result == ["alpha", "shared", "zulu"]
            assert sdk.mock_calls == [getattr(call, case[1])(session, "org-1", limit=1000)]
        resolver.assert_called_once_with()

    @pytest.mark.parametrize("case", _TenantCases.org_cases[1:3], ids=lambda case: case[0])
    def test_valid_site_keeps_sorted_union(self, case: tuple[str, str | None, str | None, bool]) -> None:
        """A valid supplied site preserves both contributions and ordering."""
        session = object()
        resolver = MagicMock(return_value="org-1")
        utils = APITenantFetchUtils(session, resolver)
        with patch("src.api.tenant_fetch.mistapi") as sdk:
            _TenantCases.bind_sdk(sdk)
            result = getattr(utils, case[0])("site-1")
            assert result == ["alpha", "beta", "shared", "theta", "zulu"]
            assert sdk.mock_calls == [
                getattr(call, case[1])(session, "org-1", limit=1000),
                getattr(call, case[2])(session, "site-1"),
            ]
        resolver.assert_called_once_with()

    @settings(max_examples=40, derandomize=True)
    @given(identifier=st.text(min_size=1, max_size=80).filter(lambda value: bool(value.strip())))
    def test_valid_opaque_string_reaches_sdk_unchanged(self, identifier: str) -> None:
        """A format-free contract neither normalizes nor replaces valid IDs."""
        session = object()
        utils = APITenantFetchUtils(session, lambda: identifier)
        with patch("src.api.tenant_fetch.mistapi") as sdk:
            _TenantCases.bind_sdk(sdk)
            assert utils.organization_tenants() == ["alpha", "shared", "zulu"]
            assert utils.site_tenants(identifier) == ["beta", "shared", "theta"]
            assert sdk.mock_calls == [
                call.api.v1.orgs.networks.listOrgNetworks(session, identifier, limit=1000),
                call.api.v1.sites.networks.listSiteNetworksDerived(session, identifier),
            ]

    @pytest.mark.parametrize("case", _TenantCases.org_cases[:3], ids=lambda case: case[0])
    def test_optional_payload_names_keep_separate_rules(self, case: tuple[str, str | None, str | None, bool]) -> None:
        """Optional payload names retain their original nonempty-string rule."""
        session = object()
        utils = APITenantFetchUtils(session, lambda: "org-1")
        with patch("src.api.tenant_fetch.mistapi") as sdk:
            _TenantCases.bind_sdk(sdk)
            endpoint = sdk
            for attribute in case[1].split("."):
                endpoint = getattr(endpoint, attribute)
            endpoint.return_value = _TenantCases.response((" ", "shared", "zulu"))
            assert getattr(utils, case[0])() == [" ", "shared", "zulu"]
            assert sdk.mock_calls == [getattr(call, case[1])(session, "org-1", limit=1000)]


class TestTenantFailureContracts:
    """Preserve existing failure contracts and operator-visible refusal."""

    @pytest.mark.parametrize("case", _TenantCases.org_cases[:3], ids=lambda case: case[0])
    def test_resolver_runtime_error_propagates(self, case: tuple[str, str | None, str | None, bool]) -> None:
        """A resolver fault propagates as the original exception object."""
        failure = RuntimeError("The organization resolver failed.")
        resolver = MagicMock(side_effect=failure)
        utils = APITenantFetchUtils(object(), resolver)
        with patch("src.api.tenant_fetch.mistapi") as sdk:
            with pytest.raises(RuntimeError, match="The organization resolver failed") as caught:
                getattr(utils, case[0])()
            assert caught.value is failure
            assert sdk.mock_calls == []
        resolver.assert_called_once_with()

    @pytest.mark.parametrize("site_scope", [False, True], ids=["org", "site"])
    @pytest.mark.parametrize(
        ("status_code", "raw_body"),
        [
            pytest.param(403, "", id="HTTP-4xx"),
            pytest.param(503, "", id="HTTP-5xx"),
            pytest.param(200, "private-fixture-unparsed-body", id="malformed-json"),
        ],
    )
    def test_cloud_failure_keeps_existing_contract(
        self, site_scope: bool, status_code: int, raw_body: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """HTTP and parse failures remain explicit empty results."""
        session = object()
        utils = APITenantFetchUtils(session, lambda: "org-1")
        endpoint_path = _TenantCases.site_cases[0][2] if site_scope else _TenantCases.org_cases[0][1]
        with patch("src.api.tenant_fetch.mistapi") as sdk, caplog.at_level(logging.INFO):
            _TenantCases.bind_sdk(sdk, empty=True, failure=(status_code, raw_body))
            result = utils.site_tenants("site-1") if site_scope else utils.organization_tenants()
            assert result == []
            expected = (
                getattr(call, endpoint_path)(session, "site-1")
                if site_scope
                else (getattr(call, endpoint_path)(session, "org-1", limit=1000))
            )
            assert sdk.mock_calls == [expected]
        errors = [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR]
        assert len(errors) == 1
        assert ("did not parse" if status_code == 200 else f"HTTP {status_code}") in errors[0]
        assert "private-fixture-unparsed-body" not in caplog.text
        assert "No " not in caplog.text

    @pytest.mark.parametrize("case", _TenantCases.org_cases + _TenantCases.site_cases, ids=lambda case: case[0])
    @pytest.mark.parametrize(
        "failure",
        [
            pytest.param(requests.Timeout("fixture transport failure"), id="connection-timeout"),
            pytest.param(requests.ConnectionError("fixture transport failure"), id="connection-error"),
        ],
    )
    def test_transport_failures_keep_existing_contract(
        self,
        case: tuple[str, str | None, str | None, bool],
        failure: requests.RequestException,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Each transport failure keeps exact arguments and one failure report."""
        method_name, org_endpoint, site_endpoint, private = case
        session = object()
        utils = APITenantFetchUtils(session, lambda: "org-1")
        endpoint_path = org_endpoint or site_endpoint
        with patch("src.api.tenant_fetch.mistapi") as sdk, caplog.at_level(logging.INFO):
            _TenantCases.bind_sdk(sdk, empty=True, failure=failure)
            identifier = "org-1" if org_endpoint else "site-1"
            method = getattr(utils, method_name)
            result = method(identifier) if private or not org_endpoint else method()
            assert result == (set() if private else [])
            expected = getattr(call, endpoint_path)(session, identifier)
            if org_endpoint:
                expected = getattr(call, endpoint_path)(session, identifier, limit=1000)
            assert sdk.mock_calls == [expected]
        errors = [record.getMessage() for record in caplog.records if record.levelno >= logging.WARNING]
        assert len(errors) == 1
        assert "fixture transport failure" in errors[0]

    @pytest.mark.parametrize(
        ("method_name", "field"),
        [
            ("_fetch_org_tenants", "org_id"),
            ("_fetch_site_tenants", "site_id"),
            ("_fetch_policy_tenants", "site_id"),
            ("_fetch_template_tenants", "site_id"),
        ],
    )
    def test_discovery_receives_refusal_before_empty_source(
        self, method_name: str, field: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The read-only caller never stores or reports a false empty source."""
        utils = APITenantFetchUtils(object(), lambda: "" if field == "org_id" else "org-1")
        discovery = MagicMock(spec=ServicePingDiscoveryMixin)
        discovery.site_id = ""
        discovery._tenant_utils.return_value = utils
        with patch("src.api.tenant_fetch.mistapi") as sdk, caplog.at_level(logging.INFO):
            with pytest.raises(ValueError, match=rf"^{field} must be a non-empty string\.$"):
                getattr(ServicePingDiscoveryMixin, method_name)(discovery)
            assert sdk.mock_calls == []
        discovery._store_tenant_source.assert_not_called()
        errors = [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR]
        assert errors == [
            f"Cannot fetch tenants: {field} must be a non-empty string. checked_identifiers=1 refused_identifiers=1"
        ]

    @pytest.mark.parametrize(
        "identifier",
        [
            pytest.param(_PrivateIdentifier(), id="private-representation"),
            pytest.param({"apitoken": "private-fixture-metadata"}, id="private-mapping"),
            pytest.param(b"private-fixture-metadata", id="private-bytes"),
            pytest.param(" " * 5000, id="long-space"),
        ],
    )
    def test_invalid_metadata_stays_private(self, identifier: object, caplog: pytest.LogCaptureFixture) -> None:
        """Refusals neither format private values nor print oversized inputs."""
        utils = APITenantFetchUtils(object(), lambda: identifier)
        with patch("src.api.tenant_fetch.mistapi") as sdk, caplog.at_level(logging.INFO):
            with pytest.raises(ValueError, match=r"^org_id must be a non-empty string\.$") as refusal:
                utils.organization_tenants()
            assert sdk.mock_calls == []
            assert str(refusal.value) == "org_id must be a non-empty string."
        assert "private-fixture-metadata" not in caplog.text
        assert "apitoken" not in caplog.text
        assert len(caplog.text) < 600
        errors = [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR]
        assert errors == [
            "Cannot fetch tenants: org_id must be a non-empty string. checked_identifiers=1 refused_identifiers=1"
        ]
