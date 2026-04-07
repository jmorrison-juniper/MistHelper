import os
import unittest

from src.ssid_consolidation.cache import CacheManager
from src.ssid_consolidation.collector import Collector
from src.ssid_consolidation.exporter import Exporter
from src.ssid_consolidation.manager import SSIDTemplateConsolidationManager


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


class FaultyExporter(Exporter):
    def write(self, rows, outdir="data/ssid-consolidation", basename="matrix"):
        raise OSError("export failed")


class FaultyCache(CacheManager):
    def save_rows(self, rows, collected_at=None):
        raise OSError("cache failed")


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
        self.mgr = SSIDTemplateConsolidationManager(
            collector=self.collector,
            cache=self.cache,
            exporter=self.exporter,
            cache_minutes=60,
        )

    def test_phase1_collect_and_cache(self):
        rows, meta = self.mgr.phase1_collect("TestSSID", force_refresh=True)
        self.assertIsInstance(rows, list)
        self.assertFalse(meta.get("cached"))
        # second call should use cache
        rows2, meta2 = self.mgr.phase1_collect("TestSSID", force_refresh=False)
        self.assertTrue(meta2.get("cached"))

    def test_phase1_collect_handles_invalid_cache_timestamp_and_export_failure(self):
        self.cache.save_rows(self.collector.collect("TestSSID"), collected_at="not-a-timestamp")
        mgr = SSIDTemplateConsolidationManager(
            collector=self.collector,
            cache=self.cache,
            exporter=FaultyExporter(),
            cache_minutes=60,
        )

        rows, meta = mgr.phase1_collect("TestSSID", force_refresh=False)

        self.assertEqual(len(rows), 1)
        self.assertFalse(meta["cached"])
        self.assertIsNone(meta["out"])

    def test_phase1_collect_handles_invalid_cache_minutes_and_save_failure(self):
        original_value = os.environ.get("SSID_CONSOLIDATION_CACHE_MINUTES")
        os.environ["SSID_CONSOLIDATION_CACHE_MINUTES"] = "invalid"
        faulty_cache_db = "data/ssid-consolidation/test_faulty_cache.db"
        faulty_cache = None
        try:
            faulty_cache = FaultyCache(db_path=faulty_cache_db)
            mgr = SSIDTemplateConsolidationManager(
                collector=self.collector,
                cache=faulty_cache,
                exporter=self.exporter,
                cache_minutes=15,
            )
            rows, meta = mgr.phase1_collect("TestSSID", force_refresh=True)
            mgr.clear_cache()
        finally:
            if original_value is None:
                os.environ.pop("SSID_CONSOLIDATION_CACHE_MINUTES", None)
            else:
                os.environ["SSID_CONSOLIDATION_CACHE_MINUTES"] = original_value
            if faulty_cache is not None:
                faulty_cache.close()
            try:
                os.remove(faulty_cache_db)
            except Exception:
                pass

        self.assertEqual(mgr.cache_minutes, 15)
        self.assertEqual(len(rows), 1)
        self.assertFalse(meta["cached"])

    def tearDown(self):
        self.cache.close()
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
