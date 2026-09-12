"""Unit tests for the standalone capture key of a run-less pre-check.

Why:
    Issue 2096 names a defect. A capture that names no run built the key
    ``cap--01`` and invented a run, so a second run-less capture overwrote the
    first record and left a dangling ``capture_for_run`` edge. The fix reads a
    fresh nonce for each run-less capture, so two such captures never collide.
    The fix also writes no run and no edge for a run-less capture (D1, FR-096).

    These tests prove the nonce key form, the uniqueness of two keys, the empty
    run of the stored document, and the absence of an edge. Every test runs
    offline, because the assembly builder reads no database.
"""

from __future__ import annotations

import re  # WHY: The key form check reads a fixed pattern.

from src.upgrade_portal.capture import assembly, collector, store

# WHY: The key holds the prefix, then 32 hexadecimal digits, then the ordinal.
_KEY_PATTERN = re.compile(r"cap-[0-9a-f]{32}-01")


def _standalone_document() -> dict[str, object]:
    """Return one stored capture that names no run.

    Why:
        Three tests read the same run-less capture, so a difference in a result
        comes from the test and never from the input. The builder threads a
        fresh nonce key through the collector and the assembly, which is the
        real path of a run-less start.

    Returns:
        The stored capture document with an empty run and a nonce key.
    """
    key = assembly.standalone_capture_key()  # A fresh nonce, never a run.
    job = {"capture_id": key, "run_id": "", "ordinal": 1, "actor_email": "operator@example.com"}  # A run-less job.
    identity = collector.capture_identity(job)  # The collector reads the prebuilt key.
    site = assembly.SiteIdentity(org_id="org-1", org_name="Org", site_id="site-1", site_name="Site")  # A named site.
    window = assembly.CaptureWindow("2024-01-01T00:00:00+00:00", "2024-01-01T00:00:01+00:00", 1.0)  # A fixed window.
    return assembly.build_capture(identity, site, window, assembly.CaptureSections())  # The stored document.


def test_standalone_key_matches_the_capture_key_form() -> None:
    """The nonce key reads as a capture key, so a reader sees no new shape."""
    key = assembly.standalone_capture_key()  # One fresh nonce key.
    assert _KEY_PATTERN.fullmatch(key) is not None  # The key holds the prefix, the hex, and the ordinal.


def test_two_standalone_keys_differ() -> None:
    """Two run-less captures hold different keys, so neither overwrites the other."""
    first = assembly.standalone_capture_key()  # The key of the first run-less capture.
    second = assembly.standalone_capture_key()  # The key of the second run-less capture.
    assert first != second  # A fresh nonce for each capture keeps the two records apart.


def test_standalone_capture_carries_the_nonce_key_and_no_run() -> None:
    """The stored document holds the nonce key and an empty run."""
    document = _standalone_document()  # The stored capture of a run-less start.
    assert _KEY_PATTERN.fullmatch(str(document["_key"])) is not None  # The key is a nonce key.
    assert document["capture_id"] == document["_key"]  # The browser reads the same key the store wrote.
    assert document["run_id"] == ""  # A run-less capture names no run, so it builds no edge.


def test_standalone_capture_writes_no_edge() -> None:
    """The store refuses an edge for a run-less capture, so no dangling edge forms."""
    document = _standalone_document()  # The stored capture of a run-less start.
    result = store.write_edge(document)  # The edge write reads the empty run before any database call.
    assert result.verified is False  # The store built no edge for the run-less capture.
    assert result.reason == store.REASON_NO_KEY  # The refusal names the missing run, never a database fault.
