import time
from src.cache.site_cache import SiteCache


def test_site_cache_set_get():
    cache = SiteCache(ttl_seconds=1)
    cache.set("k1", [{"id": "s1", "name": "A"}])
    assert cache.get("k1") == [{"id": "s1", "name": "A"}]
    assert cache.is_fresh("k1")
    time.sleep(1.1)
    assert not cache.is_fresh("k1")
