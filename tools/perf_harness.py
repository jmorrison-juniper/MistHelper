"""Performance harness to exercise streaming exporter with a mock API."""
import time
import tracemalloc
import os
import argparse

from src.export.streaming_exporter import stream_site_devices_to_csv


class MockAPI:
    def __init__(self, n):
        self.n = n

    def listSiteDevices(self, site_id, page_size=500, page_token=None):
        start = int(page_token) if page_token else 0
        end = min(self.n, start + page_size)
        devices = [{'device_id': f'd{i}', 'hostname': f'h{i}', 'ip': f'10.0.0.{i%255}', 'os': 'linux', 'model': 'X', 'status': 'online', 'last_seen': None} for i in range(start, end)]
        next_token = str(end) if end < self.n else None
        return {'devices': devices, 'next_page_token': next_token}


def run_harness(n):
    api = MockAPI(n)
    out_path = f'./perf_output_{n}.csv'
    tracemalloc.start()
    start = time.time()
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        cols = ['device_id', 'hostname', 'ip', 'os', 'model', 'status', 'last_seen']
        rows = stream_site_devices_to_csv(api, 'site-1', f, cols, page_size=500, force_refresh=True)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    duration = (time.time() - start) * 1000.0
    csv_size = os.path.getsize(out_path)
    return {'rows': rows, 'duration_ms': duration, 'peak_memory_bytes': peak, 'csv_size_bytes': csv_size}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--devices', type=int, default=10000)
    args = parser.parse_args()
    print(run_harness(args.devices))
