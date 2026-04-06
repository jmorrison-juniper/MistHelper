from src.export.streaming_exporter import stream_site_devices_to_csv


class MockAPI:
    def __init__(self, n):
        self.n = n

    def listSiteDevices(self, site_id, page_size=500, page_token=None):
        start = int(page_token) if page_token else 0
        end = min(self.n, start + page_size)
        devices = [{"device_id": f"d{i}", "hostname": f"h{i}"} for i in range(start, end)]
        next_token = str(end) if end < self.n else None
        return {"devices": devices, "next_page_token": next_token}


def test_stream_export_counts(tmp_path):
    api = MockAPI(50)
    out = tmp_path / "out.csv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        cols = ["device_id", "hostname"]
        rows = stream_site_devices_to_csv(api, "site-1", f, cols, page_size=20)
    assert rows == 50
