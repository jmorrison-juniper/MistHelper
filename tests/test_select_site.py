from src.prompt_utils import select_site_with_logging
from src.cache.site_cache import SiteCache
from src.utils import input_utils


def test_select_by_index(monkeypatch):
    sites = [{'id': 's1', 'name': 'Alpha'}, {'id': 's2', 'name': 'Beta'}]
    def fetcher():
        return sites
    cache = SiteCache(ttl_seconds=3600)
    # monkeypatch InputUtils.safe_input to simulate choosing index 1
    monkeypatch.setattr('src.utils.input_utils.InputUtils.safe_input', lambda prompt, **kwargs: '1')
    selected = select_site_with_logging(fetcher, cache, interactive=True)
    assert selected == 's1'
