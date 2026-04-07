import unittest
from types import SimpleNamespace

from src.ssid_consolidation.api import MistApiAdapter


class DummyResp:
    def __init__(self, data=None, status_code: int | None = 200):
        self.data = data
        self.status_code = status_code


def make_flaky_mistapi_sequence(responses):
    """Create a minimal mistapi-like object whose listOrgSites returns sequential responses."""
    counter = {"i": 0}

    def listOrgSites(apisession, org, limit):
        idx = min(counter["i"], len(responses) - 1)
        resp = responses[idx]
        counter["i"] += 1
        if isinstance(resp, Exception):
            raise resp
        return resp

    sites_module = SimpleNamespace(listOrgSites=listOrgSites)
    orgs_module = SimpleNamespace(sites=sites_module)
    v1 = SimpleNamespace(orgs=orgs_module)
    api = SimpleNamespace(v1=v1)
    def get_all(response, mist_session=None):
        return response.data

    return SimpleNamespace(api=api, get_all=get_all)


class TestMistApiAdapterRetries(unittest.TestCase):
    def test_retry_succeeds_after_initial_none_status(self):
        # First response has status_code None -> treated as failure, second succeeds
        responses = [
            DummyResp(data=None, status_code=None),
            DummyResp(data=[{"id": "s1", "name": "Site1"}], status_code=200),
        ]

        mistapi = make_flaky_mistapi_sequence(responses)
        adapter = MistApiAdapter(
            apisession=object(),
            mistapi_module=mistapi,
            org_id="org1",
            max_retries=2,
            retry_delay=0.0,
        )

        sites = adapter.get_sites(org_id="org1")
        self.assertEqual(sites, [{"id": "s1", "name": "Site1"}])

    def test_persistent_5xx_returns_empty(self):
        # Always return 500 -> adapter should ultimately return [] from get_sites
        responses = [
            DummyResp(data=None, status_code=500),
            DummyResp(data=None, status_code=500),
        ]

        mistapi = make_flaky_mistapi_sequence(responses)
        adapter = MistApiAdapter(
            apisession=object(),
            mistapi_module=mistapi,
            org_id="org1",
            max_retries=1,
            retry_delay=0.0,
        )

        sites = adapter.get_sites(org_id="org1")
        self.assertEqual(sites, [])


if __name__ == "__main__":
    unittest.main()
