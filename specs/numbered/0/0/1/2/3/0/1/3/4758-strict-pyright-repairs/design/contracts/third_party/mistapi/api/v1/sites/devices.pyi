"""Declare the installed SDK listSiteDevices signature without an implementation."""

from mistapi.__api_response import APIResponse
from mistapi.__api_session import APISession

def listSiteDevices(
    mist_session: APISession,
    site_id: str,
    type: str | None = None,
    name: str | None = None,
    limit: int | None = None,
    page: int | None = None,
) -> APIResponse: ...
