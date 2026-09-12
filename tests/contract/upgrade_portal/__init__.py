"""Contract tests for the HTTP surface of the ``src.upgrade_portal`` package.

Why:
    These tests drive the Flask test client and check the status code, the
    redirect, and the response body of each route. They prove that every
    route matches the documented contract, and they need no browser.
"""
