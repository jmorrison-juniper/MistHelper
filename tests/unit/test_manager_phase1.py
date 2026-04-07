import unittest
import os
from src.ssid_consolidation.manager import SSIDTemplateConsolidationManager
from src.ssid_consolidation.collector import Collector
from src.ssid_consolidation.cache import CacheManager
from src.ssid_consolidation.exporter import Exporter


class DummyCollector(Collector):
    def collect(self, target_ssid: str):
        return [
            {
                "site_id": "sX",
                "site_name": "SiteX",
                "template_id": "tX",
                "template_name": "T",
                "target_ssid_name": target_ssid,
                "target_ssid_id": "ssidx",
                "psk_detected": 0,
                "edge_cluster_id": "ec",
                "edge_cluster_name": "EC",
                "anomaly_code": None,
                "collected_at": "2026-04-07T00:00:00",
            }
        ]


class TestManagerPhase1(unittest.TestCase):
    def setUp(self):
        self.cache_db = "data/ssid-consolidation/test_manager_cache.db"
        try:
            os.remove(self.cache_db)
        except Exception:
            pass
        self.cache = CacheManager(db_path=self.cache_db)
        self.cache.clear()
        self.collector = DummyCollector()
        self.exporter = Exporter()
        self.mgr = SSIDTemplateConsolidationManager(collector=self.collector, cache=self.cache, exporter=self.exporter, cache_minutes=60)

    def test_phase1_collect_and_cache(self):
        rows, meta = self.mgr.phase1_collect("TestSSID", force_refresh=True)
        self.assertIsInstance(rows, list)
        self.assertFalse(meta.get("cached"))
        # second call should use cache
        rows2, meta2 = self.mgr.phase1_collect("TestSSID", force_refresh=False)
        self.assertTrue(meta2.get("cached"))

    def tearDown(self):
        try:
            os.remove(self.cache_db)
        except Exception:
            pass
        try:
            os.remove("data/ssid-consolidation/matrix.csv")
        except Exception:
            pass
        try:
            os.remove("data/ssid-consolidation/matrix.db")
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()
