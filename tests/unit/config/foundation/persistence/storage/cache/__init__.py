"""Cache-module unit tests package marker.

Why:
    Needed so ``pytest`` collects ``tests/unit/cache/test_*.py`` as a package
    rather than as loose modules, avoiding sys.path shadowing when the cache
    tests grow more than one file.
"""
