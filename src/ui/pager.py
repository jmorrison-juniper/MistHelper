"""Interactive pager for presenting device pages in terminal."""
from typing import List, Dict
from ..export.pager import ListSiteDevicesPager

DEFAULT_PAGE_SIZE = 50
TRUNCATE_LIMIT = 120
TRUNCATE_SHOW = 100


class InteractivePager:
    def __init__(self, api_client, site_id, page_size=DEFAULT_PAGE_SIZE, columns=None):
        self.api_client = api_client
        self.site_id = site_id
        self.page_size = page_size
        self.columns = columns or ['device_id', 'hostname', 'ip', 'os', 'model', 'status', 'last_seen']

    def get_page(self, page_index: int) -> List[Dict]:
        pager = ListSiteDevicesPager(api_client=self.api_client, site_id=self.site_id, page_size=500)
        page = []
        cur_page = 0
        for device in pager:
            page.append(device)
            if len(page) >= self.page_size:
                if cur_page == page_index:
                    return self._format_page(page)
                cur_page += 1
                page = []
        if page and cur_page == page_index:
            return self._format_page(page)
        return []

    def _format_page(self, rows: List[Dict]) -> List[Dict]:
        def trunc(s):
            s = '' if s is None else str(s)
            if len(s) > TRUNCATE_LIMIT:
                return s[:TRUNCATE_SHOW] + '…'
            return s
        formatted = [{k: trunc(r.get(k, '')) for k in self.columns} for r in rows]
        return formatted
