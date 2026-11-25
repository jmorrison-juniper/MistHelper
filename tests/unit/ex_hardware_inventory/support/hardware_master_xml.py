"""Helpers for the master XML tests (issue #4933). Every value here is invented."""

from __future__ import annotations

from src.operations.exporting.ex_hardware_inventory.report.builder import TargetResult
from src.operations.exporting.ex_hardware_inventory.run.master_xml import MasterXmlBuilder
from tests.unit.ex_hardware_inventory.support.hardware_replies import HardwareReplies

RUN_UTC = "2026-11-25T18:46:06Z"  # The run time that every test document carries.
ORG_A = "11111111-1111-4111-8111-111111111111"  # An invented organization.
ORG_B = "22222222-2222-4222-8222-222222222222"  # A second invented organization.
SITE_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"  # An invented site.
SITE_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"  # A second invented site.
LIMIT = 10_000_000  # A limit that no test document reaches.
SAME = object()  # Marks "use the standard reply of this switch".


def make_result(
    device: str = "ex-01",
    *,
    state: str = "completed",
    reason: str = "",
    reply: object = SAME,
    org: tuple[str, str] = (ORG_A, "Alpha Org"),
    site: tuple[str, str] = (SITE_A, "Site One"),
) -> TargetResult:
    """Build the result of one switch. A completed switch gets the standard invented reply unless told otherwise."""
    identity = {
        "org_id": org[0],
        "site_id": site[0],
        "site_label": site[1],
        "device_id": f"dev-{device}",
        "label": device,
    }
    text = HardwareReplies.single_switch(device.upper()) if reply is SAME and state == "completed" else reply
    return TargetResult(identity, org[1], state, reason, text if isinstance(text, str) else None)


def make_unread(org: tuple[str, str] = (ORG_B, "Beta Org"), reason: str = "discovery_failed") -> TargetResult:
    """Build the result of an organization that Mist could not read: an identity with an organization only."""
    return TargetResult({"org_id": org[0]}, org[1], "failed", reason, None)


def make_mixed() -> list[TargetResult]:
    """Build one collected switch, one failed switch, one skipped switch, and one unread organization."""
    return [
        make_result("ex-01"),
        make_result("ex-02", state="failed", reason="completion_unproven", reply=None),
        make_result("ex-03", state="skipped", reason="offline", reply=None),
        make_unread(),
    ]


def make_document(results: list[TargetResult] | None = None, scope: str = "organization") -> MasterXmlBuilder.Document:
    """Compile and check a document for the given results, or for the mixed set."""
    return MasterXmlBuilder.compile(make_mixed() if results is None else results, scope, RUN_UTC, LIMIT)


def change(data: bytes, old: str, new: str) -> bytes:
    """Return the bytes with the first ``old`` replaced by ``new``. The text must exist, so no test is vacuous."""
    text = data.decode("utf-8")
    if old not in text:  # A missing anchor would let a test pass without testing anything.
        raise AssertionError(f"The anchor text is not in the document: {old!r}")
    return text.replace(old, new, 1).encode("utf-8")
