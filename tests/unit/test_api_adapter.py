import unittest
from types import SimpleNamespace

from src.ssid_consolidation.api import MistApiAdapter


class DummyResp:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code


def make_mistapi_for_sites(data):
    """Create minimal mistapi-like namespace exposing listOrgSites and get_all."""

    def listOrgSites(apisession, org, limit):
        return DummyResp(data)

    sites_module = SimpleNamespace(listOrgSites=listOrgSites)
    orgs_module = SimpleNamespace(sites=sites_module)
    v1 = SimpleNamespace(orgs=orgs_module)
    api = SimpleNamespace(v1=v1)

    def get_all(response, mist_session=None):
        return response.data

    return SimpleNamespace(api=api, get_all=get_all)


def make_mistapi_for_wlans(data):
    """Create minimal mistapi-like namespace exposing site wlans list function."""

    def listSiteWLANS(apisession, site_id, limit):
        return DummyResp(data)

    wlans = SimpleNamespace(listSiteWLANS=listSiteWLANS)
    sites = SimpleNamespace(wlans=wlans)
    v1 = SimpleNamespace(sites=sites)
    api = SimpleNamespace(v1=v1)

    def get_all(response, mist_session=None):
        return response.data

    return SimpleNamespace(api=api, get_all=get_all)


class TestMistApiAdapter(unittest.TestCase):
    def test_get_sites_returns_sites(self):
        data = [{"id": "s1", "name": "Site One"}]
        mistapi = make_mistapi_for_sites(data)
        adapter = MistApiAdapter(
            apisession=object(),
            mistapi_module=mistapi,
            org_id="org1",
            max_retries=0,
            retry_delay=0.0,
        )
        sites = adapter.get_sites(org_id="org1")
        self.assertEqual(sites, data)

    def test_get_site_wlans_returns_wlans(self):
        data = [{"id": "w1", "name": "MySSID"}]
        mistapi = make_mistapi_for_wlans(data)
        adapter = MistApiAdapter(
            apisession=object(),
            mistapi_module=mistapi,
            org_id="org1",
            max_retries=0,
            retry_delay=0.0,
        )
        wlans = adapter.get_site_wlans("site-1")
        self.assertEqual(wlans, data)

    def test_get_sites_requires_org(self):
        data = [{"id": "s1"}]
        mistapi = make_mistapi_for_sites(data)
        adapter = MistApiAdapter(
            apisession=object(),
            mistapi_module=mistapi,
            org_id=None,
            max_retries=0,
            retry_delay=0.0,
        )
        with self.assertRaises(ValueError):
            adapter.get_sites(org_id=None)


if __name__ == "__main__":
    unittest.main()
