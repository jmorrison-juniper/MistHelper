# Feature specification: Load the floor plan image on the Maps page

**Issue**: #3236 | **Branch**: `fix/3236-maps-image-url` | **Status**: Draft

## Problem

The Maps page of the web portal never shows a floor plan image. The image
route calls `mistapi.api.v1.orgs.maps.getOrgMapImage`, and the installed SDK
holds no such function. The call raises `AttributeError`, the route answers
404, and the page shows the device markers on an empty background.

The Mist API has no GET operation for a map image. The map record carries the
image location in its read-only field `url`.

## User stories

### US1. See the floor plan of an image map (P1)

An operator chooses a site and an image floor plan. The page shows the floor
plan image behind the device markers.

Acceptance:

1. If the map holds an image, the page draws the image under the markers.
2. The page asks the portal for the image one time for one map view.

### US2. Read a note for a map with no image (P2)

An operator chooses a floor plan with no image, such as a Google map. The page
shows a clear note, and it still shows the device markers.

Acceptance:

1. If the map holds no image, the page shows the note "This floor plan has no
   image. The map shows the device positions only."
2. The page asks the portal for no image.

### US3. Read a note when the image does not load (P3)

The image download fails. The link can expire, the network can fail, or the
bytes can be something other than an image. The page shows a clear note, and
it still shows the device markers.

Acceptance:

1. If the image does not load, the page shows the note "The portal could not
   load the floor plan image. The map shows the device positions only."

## Functional requirements

- **FR-001**: The map data answer names the portal path
  `/api/maps/site/<site_id>/map/<map_id>/image` only for a map that holds an
  `https` image URL. For every other map, the answer names an empty string.
- **FR-002**: The image path reads the map with
  `mistapi.api.v1.sites.maps.getSiteMap`. It downloads the image from the `url`
  field, and it serves the bytes from the portal origin.
- **FR-003**: The download sends no Mist API token. It follows the redirect to
  the storage host. It stops after 5 seconds to connect or 30 seconds to read,
  and it refuses an image larger than 25 MiB.
- **FR-004**: The portal serves only PNG, JPEG, GIF, or WebP bytes. It reads the
  type from the first bytes of the image, not from the upstream header.
- **FR-005**: The image answer carries `Cache-Control: private, max-age=300`.
- **FR-006**: The site map list sets `has_image` with the same rule as FR-001.
- **FR-007**: The page shows the notes of US2 and US3 with `textContent` only.
- **FR-008**: The image path refuses a site identifier or a map identifier that
  is not a UUID. It answers 404 and makes no API call.
- **FR-009**: The SDK call guard in `tests/unit/web_portal/test_portal_sdk_calls.py`
  holds no exemption for the maps route.
- **FR-010**: The logs hold no link secret. A log filter hides the `jwt` value
  and the storage values `X-Amz-Credential`, `X-Amz-Security-Token`, and
  `X-Amz-Signature`. A failed download logs the error class only.

## Answers of the image path

| Condition | Status | Body |
| --- | --- | --- |
| No API session | 401 | `{"error": "Not authenticated"}` |
| An identifier that is not a UUID | 404 | `{"error": "Map not found"}` |
| The map read fails | 404 | `{"error": "Map not found"}` |
| The map holds no `https` image URL | 404 | `{"error": "This floor plan has no image."}` |
| The download fails, or the bytes are not a known image | 502 | `{"error": "The portal could not download the floor plan image."}` |
| The download succeeds | 200 | The image bytes |

## Out of scope

- The standalone map viewer in `src/maps/`. It has its own image route.
- A server cache of the image bytes.
- The thumbnail image of a map.

## Success criteria

- **SC-001**: A browser journey shows one floor plan image in the image layer of
  the plot. The portal path supplies the image.
- **SC-002**: One map view makes one image request.
- **SC-003**: A local portal with the live cloud shows a real floor plan image.
- **SC-004**: With urllib3 at DEBUG level, the log of the live check holds no
  `jwt` value and no storage signature value.
