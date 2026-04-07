import os
import unittest

from src.ssid_consolidation.logging import OperationsLog
from src.ssid_consolidation.models import OperationLogEntry


class TestOperationsLog(unittest.TestCase):
    def setUp(self):
        self.db_path = "data/ssid-consolidation/test_operations.db"
        try:
            os.remove(self.db_path)
        except OSError:
            pass
        self.operations_log = OperationsLog(db_path=self.db_path)

    def test_append_and_query_by_phase(self):
        entry = OperationLogEntry(
            phase=1,
            site_id="site-1",
            action="collect",
            status="ok",
            message="done",
            timestamp="2026-04-07T00:00:00+00:00",
        )

        self.operations_log.append(entry)
        rows = self.operations_log.query_by_phase(1)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].action, "collect")
        self.assertEqual(rows[0].status, "ok")

    def tearDown(self):
        self.operations_log.close()
        try:
            os.remove(self.db_path)
        except OSError:
            pass


if __name__ == "__main__":
    unittest.main()
