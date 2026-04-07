import unittest

from src.ssid_consolidation.collector import Collector


class FakeAdapter:
    def __init__(self):
        self.org_id = "org-1"

    def get_sites(self, org_id=None):
        return [
            {
                "id": "site-1",
                "name": "Site One",
                "template_id": "tmpl-1",
                "edge_cluster_id": "ec-1",
                "edge_cluster_name": "Edge Cluster 1",
            }
        ]

    def get_site_wlans(self, site_id):
        return [
            {"id": "wlan-1", "name": "Corp", "psk": "secret"},
            {"id": "wlan-2", "name": "Guest"},
        ]


class BrokenAdapter:
    org_id = "org-1"

    def get_sites(self, org_id=None):
        raise RuntimeError("boom")


class OddAdapter:
    org_id = "org-1"

    def get_sites(self, org_id=None):
        return {"not": "a-list"}

    def get_site_wlans(self, site_id):
        return "not-a-list"


class TestCollector(unittest.TestCase):
    def test_collect_from_api_returns_matching_rows(self):
        collector = Collector(mist_client=FakeAdapter())

        rows = collector.collect_from_api("Corp")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["site_id"], "site-1")
        self.assertEqual(rows[0]["psk_detected"], 1)

    def test_collect_returns_sample_rows_without_client(self):
        collector = Collector()

        rows = collector.collect("Corp")

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["target_ssid_name"], "Corp")

    def test_collect_falls_back_to_sample_rows_on_adapter_failure(self):
        collector = Collector(mist_client=BrokenAdapter())

        rows = collector.collect("Corp")

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["anomaly_code"], "1_SSID")

    def test_collect_from_api_returns_empty_for_non_list_adapter_payloads(self):
        collector = Collector(mist_client=OddAdapter())

        rows = collector.collect_from_api("Corp")

        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
