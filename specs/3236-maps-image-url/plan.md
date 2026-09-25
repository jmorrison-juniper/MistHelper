# Implementation plan: Load the floor plan image on the Maps page

**Issue**: #3236 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

The Maps route reads the map record, downloads the image from its `url` field,
and serves the bytes from the portal origin. Plotly draws the markers at once
and loads the image. The page shows a note when the map has no image or when
the image does not load.

## Technical context

- Python 3.13, Flask, `mistapi` 0.64.0, and `requests`.
- The change adds no dependency.
- The web portal owns port 8055. The operations portal agent deploys a change
  there. This change does not restart or reload a server.

## Files

| File | Change |
| --- | --- |
| `web_portal/routes/maps.py` | Add the classes `MapImageSource` and `MapImageDownloader`. Replace the image route. Change the map data and the map list. |
| `web_portal/templates/map_viewer.html` | Add the note. Read the image result when the Plotly promise ends. Ignore a late answer of an old view. |
| `tests/unit/web_portal/test_map_image_route.py` | New route tests with a fake SDK and a fake download. |
| `tests/e2e/test_map_viewer_image.py` | New browser journeys with a fake SDK. |
| `tests/unit/web_portal/test_portal_sdk_calls.py` | Remove the exemption for #3236. |
| `specs/005-web-portal/contracts/rest-api.md` | Name the new image path and its answers. |
| `changelog.d/issue-3236-maps-image-url.md` | The release note. |

## The two classes

The work splits into two classes, so that each class holds five members or
fewer. The route builds the portal image path with `url_for`, so no class needs
a path method.

`MapImageSource` reads the map record and decides the answer of the path.

| Member | Purpose |
| --- | --- |
| `image_url_of(map_record)` | Return the `https` image URL of a map record, or an empty string. |
| `read_record(apisession, site_id, map_id)` | Read one map. Return `None` if the read fails or finds no map. |
| `fetch(apisession, site_id, map_id)` | Read the map and download its image. Return the answer of the path. |

`MapImageDownloader` downloads the bytes and proves the image type.

| Member | Purpose |
| --- | --- |
| `download(url)` | Download the bytes with the limits of FR-003. Return `None` on a failure. |
| `read_body(answer)` | Read a streamed answer up to `MAX_BYTES`. Return `None` on a failure status. |
| `image_type_of(content)` | Return the MIME type of the first bytes, or an empty string. |

## Test approach

1. Write the route tests first, and run them red.
2. Write the browser journeys, and run them red.
3. Change the route and the template. Run both test files green.
4. Run a local portal with the live cloud on a port from 9600 to 9699. Read the
   screenshot of a real floor plan.

## Constitution checks

- The change calls no destructive operation.
- The logs name the site and the map, and they never name the URL. A log
  filter hides the `jwt` value and the storage signature values that urllib3
  writes at DEBUG level. See research D7.
- The page writes each note with `textContent`.
