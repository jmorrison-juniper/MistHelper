import unittest

from src.ssid_consolidation.analysis import AnalysisManager


class TestAnalysisManager(unittest.TestCase):
    def setUp(self):
        self.manager = AnalysisManager()

    def test_per_cluster_deviation_counts_parameter_values(self):
        rows = [
            {"edge_cluster_id": "ec-1", "site_name": "A", "target_ssid_name": "Corp"},
            {"edge_cluster_id": "ec-1", "site_name": "A", "target_ssid_name": "Corp"},
            {"edge_cluster_id": "ec-2", "site_name": "B", "target_ssid_name": "Guest"},
        ]

        report = self.manager.per_cluster_deviation(rows, exclude_fields=[])

        self.assertEqual(report["ec-1"]["site_name"]["A"], 2)
        self.assertEqual(report["ec-2"]["target_ssid_name"]["Guest"], 1)

    def test_cross_cluster_drift_returns_only_changed_majorities(self):
        per_cluster = {
            "ec-1": {"site_name": {"A": 2}, "target_ssid_name": {"Corp": 2}},
            "ec-2": {"site_name": {"B": 1}, "target_ssid_name": {"Corp": 1}},
        }

        drift = self.manager.cross_cluster_drift(per_cluster)

        self.assertEqual(drift, {"site_name": {"ec-1": "A", "ec-2": "B"}})


if __name__ == "__main__":
    unittest.main()
