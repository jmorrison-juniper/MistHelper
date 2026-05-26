"""Unit tests for extracted Marvis troubleshooting utilities."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.troubleshooting.marvis_troubleshoot_utils import MarvisTroubleshootDeps
from src.troubleshooting.marvis_troubleshoot_utils import MarvisTroubleshootUtils


def _make_deps() -> MarvisTroubleshootDeps:
    """Build minimal dependency container with mocks for unit tests."""
    mock_prompt_client_utils = SimpleNamespace(select_client=MagicMock(return_value=(None, None, None)))
    mock_prompt_utils = SimpleNamespace(select_site=MagicMock(return_value=None), select_device=MagicMock(return_value=None))
    mock_config_utils = SimpleNamespace(get_cached_or_prompted_org_id=MagicMock(return_value="org-1"))
    mock_data_exporter = SimpleNamespace(save_data_to_output=MagicMock())
    mock_marvis_data_utils = SimpleNamespace(format_for_csv=MagicMock(return_value=[{"site_id": "site-1"}]))
    mock_data_processing_utils = SimpleNamespace(
        flatten_nested_fields=MagicMock(return_value=[{"flattened": True}]),
        escape_multiline=MagicMock(return_value=[{"flattened": True}]),
    )

    mock_mistapi = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    troubleshoot=SimpleNamespace(troubleshootOrg=MagicMock()),
                    orgs=SimpleNamespace(getOrg=MagicMock()),
                    insights=SimpleNamespace(getOrgSitesSle=MagicMock()),
                ),
                sites=SimpleNamespace(devices=SimpleNamespace(getSiteDevice=MagicMock())),
            )
        )
    )

    return MarvisTroubleshootDeps(
        apisession=object(),
        mistapi=mock_mistapi,
        config_utils=mock_config_utils,
        prompt_client_utils=mock_prompt_client_utils,
        prompt_utils=mock_prompt_utils,
        data_exporter=mock_data_exporter,
        marvis_data_utils=mock_marvis_data_utils,
        data_processing_utils=mock_data_processing_utils,
    )


def test_client_connectivity_returns_when_no_client_selected() -> None:
    """client_connectivity exits safely when guided selection returns no client."""
    deps = _make_deps()
    MarvisTroubleshootUtils.client_connectivity(deps)
    deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg.assert_not_called()


def test_process_insight_response_sites_uses_marvis_formatter() -> None:
    """Sites SLE response path uses injected Marvis formatter and exporter."""
    deps = _make_deps()
    payload = {"results": [{"site_id": "site-1"}]}

    result = MarvisTroubleshootUtils._process_insight_response("Organization Sites SLE", payload, deps)

    assert result is True
    deps.marvis_data_utils.format_for_csv.assert_called_once_with(payload, "sites")
    deps.data_exporter.save_data_to_output.assert_called_once()


def test_view_insights_fetches_org_and_attempts_insights() -> None:
    """view_insights fetches org details and then requests org SLE insights."""
    deps = _make_deps()
    deps.mistapi.api.v1.orgs.orgs.getOrg.return_value = SimpleNamespace(
        data={"name": "Test Org", "features": ["marvis"]}
    )
    deps.mistapi.api.v1.orgs.insights.getOrgSitesSle.return_value = SimpleNamespace(data=[])

    MarvisTroubleshootUtils.view_insights(deps)

    deps.mistapi.api.v1.orgs.orgs.getOrg.assert_called_once()
    deps.mistapi.api.v1.orgs.insights.getOrgSitesSle.assert_called_once()
