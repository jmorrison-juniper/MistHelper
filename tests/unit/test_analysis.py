import unittest
from src.ssid_consolidation.analysis import AnalysisManager


class TestAnalysisManager(unittest.TestCase):
    def setUp(self):
        self.analysis = AnalysisManager()

    def test_per_cluster_and_cross_drift(self):
        rows = [
            {"site_id": "s1", "edge_cluster_id": "c1", "vlan": 10, "auth": "802.1X"},
            {"site_id": "s2", "edge_cluster_id": "c1", "vlan": 10, "auth": "802.1X"},
            {"site_id": "s3", "edge_cluster_id": "c2", "vlan": 20, "auth": "802.1X"},
            {"site_id": "s4", "edge_cluster_id": "c2", "vlan": 30, "auth": "WPA2"},
        ]

        per_cluster = self.analysis.per_cluster_deviation(rows)
        self.assertIn("c1", per_cluster)
        self.assertIn("c2", per_cluster)
        # cluster c1 majority vlan should be 10
        self.assertEqual(per_cluster["c1"]["vlan"].get("10"), 2)

        drift = self.analysis.cross_cluster_drift(per_cluster)
        # vlan differs across clusters (10 vs 20/30 majority) -> should be in drift
        self.assertIn("vlan", drift)
        # verify majority mapping exists for vlan across the clusters
        self.assertEqual(drift["vlan"]["c1"], "10")


if __name__ == "__main__":
    unittest.main()
