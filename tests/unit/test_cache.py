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

    def tearDown(self):
        try:
            os.remove(self.db)
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()
