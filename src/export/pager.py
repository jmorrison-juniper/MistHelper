"""ListSiteDevicesPager - paginated iterator over listSiteDevices responses."""
import time
from typing import Any, Optional


class ListSiteDevicesPager:
    def __init__(self, api_client: Any, site_id: str, page_size: int = 500, max_retries: int = 3):
        self.api_client = api_client
        self.site_id = site_id
        self.page_size = page_size
        self.max_retries = max_retries

    def __iter__(self):
        page_token = None
        while True:
            attempt = 0
            while True:
                try:
                    resp = self.api_client.listSiteDevices(site_id=self.site_id, page_size=self.page_size, page_token=page_token)
                    break
                except Exception:
                    attempt += 1
                    if attempt >= self.max_retries:
                        raise
                    time.sleep(2 ** attempt)
            items = resp.get('devices', [])
            for d in items:
                yield d
            page_token = resp.get('next_page_token')
            if not page_token:
                break
