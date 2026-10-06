"""Guard the budget boundary between the E2E test phases and the session teardown.

Issue #3517 records the defect that this package proves. The guard starts no
portal, no browser, and no container, and it makes no Mist call.
"""
