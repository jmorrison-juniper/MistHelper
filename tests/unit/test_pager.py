from src.export.pager import ListSiteDevicesPager


class MockAPI:
    def __init__(self, n):
        self.n = n

    def listSiteDevices(self, site_id, page_size=2, page_token=None):
        start = int(page_token) if page_token else 0
        end = min(self.n, start + page_size)
        devices = [{'device_id': f'd{i}'} for i in range(start, end)]
        next_token = str(end) if end < self.n else None
        return {'devices': devices, 'next_page_token': next_token}


def test_pager_yields_all():
    api = MockAPI(5)
    pager = ListSiteDevicesPager(api, 'site-1', page_size=2)
    items = list(pager)
    assert len(items) == 5
