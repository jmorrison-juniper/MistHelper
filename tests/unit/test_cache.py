import os
import unittest

from src.ssid_consolidation.cache import CacheManager


class TestCacheManager(unittest.TestCase):
    def setUp(self):
        self.db = "data/ssid-consolidation/test_cache.db"
        if os.path.exists(self.db):
            try:
                os.remove(self.db)
            except Exception:
                pass
        self.cache = CacheManager(db_path=self.db)

    def test_save_and_get(self):
        self.cache.clear()
        rows = [{"site_id": "s1", "site_name": "Site 1"}]
        self.cache.save_rows(rows)
        allrows = self.cache.get_all()
        self.assertEqual(len(allrows), 1)
        self.assertEqual(allrows[0]["data"]["site_id"], "s1")

    def test_get_all_skips_invalid_and_non_dict_payloads(self):
        self.cache.clear()
        self.cache._conn.execute(
            "INSERT OR REPLACE INTO phase1_cache (site_id, row_json, collected_at) VALUES (?, ?, ?)",
            ("bad-json", "{", "2026-04-07T00:00:00+00:00"),
        )
        self.cache._conn.execute(
            "INSERT OR REPLACE INTO phase1_cache (site_id, row_json, collected_at) VALUES (?, ?, ?)",
            ("bad-shape", "[]", "2026-04-07T00:00:00+00:00"),
        )
        self.cache._conn.commit()

        allrows = self.cache.get_all()

        self.assertEqual(allrows, [])

    def tearDown(self):
        self.cache.close()
        try:
            os.remove(self.db)
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()
