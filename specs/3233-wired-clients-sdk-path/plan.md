# Implementation Plan: Wired clients in the client pick list

## Root cause

`web_portal/routes/operations.py:571` called `mistapi.api.v1.sites.clients.searchSiteWiredClients`. In mistapi 0.64.0 the function lives in `mistapi.api.v1.sites.wired_clients`. Three unit tests mocked the same wrong path, so each test confirmed the defect instead of catching it. A mock accepts any attribute, so no mocked test can catch this class.

## Design

1. Call the real module.
2. Point the three stand-ins at the real module.
3. Add `tests/unit/web_portal/test_portal_sdk_calls.py`. It parses every module under `web_portal/` with `ast`, finds each call whose function is a `mistapi.api...` chain, and requires that the chain resolves in the installed SDK.

## Finding

The guard found a second drift on its first run: `web_portal/routes/maps.py:165` calls `mistapi.api.v1.orgs.maps.getOrgMapImage`, which does not exist. Issue #3236 tracks it. The guard holds it in `KNOWN_DRIFT`, and a companion test fails when that call is repaired, so the exemption cannot outlive the defect.
