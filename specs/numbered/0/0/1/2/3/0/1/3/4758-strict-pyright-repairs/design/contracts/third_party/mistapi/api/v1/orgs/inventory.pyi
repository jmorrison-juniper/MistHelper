"""Declare the installed SDK organization inventory endpoint."""

from mistapi.__api_response import APIResponse
from mistapi.__api_session import APISession

def getOrgInventory(
    mist_session: APISession,
    org_id: str,
    serial: str | None = None,
    model: str | None = None,
    type: str | None = None,
    mac: str | None = None,
    site_id: str | None = None,
    vc_mac: str | None = None,
    vc: bool | None = None,
    unassigned: bool | None = None,
    modified_after: int | None = None,
    disconnected_before: int | None = None,
    limit: int | None = None,
    page: int | None = None,
) -> APIResponse: ...
