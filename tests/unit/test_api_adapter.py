import unittest
from types import SimpleNamespace

from src.ssid_consolidation.api import MistApiAdapter, RetryPolicy


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
            retry_policy=RetryPolicy(max_retries=0, retry_delay=0.0),
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
            retry_policy=RetryPolicy(max_retries=0, retry_delay=0.0),
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
            retry_policy=RetryPolicy(max_retries=0, retry_delay=0.0),
        )
        with self.assertRaises(ValueError):
            adapter.get_sites(org_id=None)

    def test_get_site_wlans_returns_empty_for_blank_site_id(self):
        mistapi = make_mistapi_for_wlans([{"id": "w1", "name": "MySSID"}])
        adapter = MistApiAdapter(
            apisession=object(),
            mistapi_module=mistapi,
            org_id="org1",
            retry_policy=RetryPolicy(max_retries=0, retry_delay=0.0),
        )

        wlans = adapter.get_site_wlans("")

        self.assertEqual(wlans, [])

    def test_get_site_wlans_returns_empty_when_endpoint_missing(self):
        mistapi = SimpleNamespace(
            api=SimpleNamespace(v1=SimpleNamespace(sites=SimpleNamespace(wlans=SimpleNamespace()))),
            get_all=lambda response, mist_session=None: response.data,
        )
        adapter = MistApiAdapter(
            apisession=object(),
            mistapi_module=mistapi,
            org_id="org1",
            retry_policy=RetryPolicy(max_retries=0, retry_delay=0.0),
        )

        wlans = adapter.get_site_wlans("site-1")

        self.assertEqual(wlans, [])

    def test_expand_paginated_response_handles_none_and_non_list(self):
        mistapi_none = SimpleNamespace(api=SimpleNamespace(v1=SimpleNamespace()), get_all=lambda **_: None)
        adapter_none = MistApiAdapter(
            apisession=object(),
            mistapi_module=mistapi_none,
            org_id="org1",
            retry_policy=RetryPolicy(max_retries=0, retry_delay=0.0),
        )
        self.assertEqual(adapter_none._expand_paginated_response(object(), "sites"), [])

        mistapi_bad = SimpleNamespace(api=SimpleNamespace(v1=SimpleNamespace()), get_all=lambda **_: {"bad": "shape"})
        adapter_bad = MistApiAdapter(
            apisession=object(),
            mistapi_module=mistapi_bad,
            org_id="org1",
            retry_policy=RetryPolicy(max_retries=0, retry_delay=0.0),
        )
        self.assertEqual(adapter_bad._expand_paginated_response(object(), "sites"), [])


if __name__ == "__main__":
    unittest.main()
