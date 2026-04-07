from types import SimpleNamespace

import pytest

from src.ssid_consolidation.api import MistApiAdapter, RetryPolicy


@pytest.fixture
def mock_apisession():
    return object()


@pytest.fixture
def mock_mistapi():
    def listOrgSites(apisession, org, limit):
        return SimpleNamespace(data=[{"id": "site1", "name": "Site One"}], status_code=200)

    def listSiteWLANS(apisession, site_id, limit):
        return SimpleNamespace(data=[{"id": "w1", "name": "MySSID"}], status_code=200)

    api = SimpleNamespace(
        v1=SimpleNamespace(
            orgs=SimpleNamespace(sites=SimpleNamespace(listOrgSites=listOrgSites)),
            sites=SimpleNamespace(wlans=SimpleNamespace(listSiteWLANS=listSiteWLANS)),
        )
    )

    return SimpleNamespace(api=api, get_all=lambda response, mist_session=None: response.data)


@pytest.fixture
def adapter(mock_apisession, mock_mistapi):
    return MistApiAdapter(
        mock_apisession,
        mock_mistapi,
        org_id="org1",
        retry_policy=RetryPolicy(max_retries=0, retry_delay=0.0),
    )
