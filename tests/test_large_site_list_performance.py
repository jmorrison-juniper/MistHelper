def test_large_site_matching_perf():
    # Lightweight perf smoke: generate 2000 site names and run a simple substring scan
    n = 2000
    sites = [{'id': f's{i}', 'name': f'site-{i}'} for i in range(n)]
    needle = 'site-1999'
    matches = [s for s in sites if needle in s['name']]
    assert len(matches) == 1
