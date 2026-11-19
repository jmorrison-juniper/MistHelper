"""Declare the installed SDK organization site-list endpoint."""

from mistapi.__api_response import APIResponse
from mistapi.__api_session import APISession

def listOrgSites(
    mist_session: APISession,
    org_id: str,
    limit: int | None = None,
    page: int | None = None,
) -> APIResponse: ...
