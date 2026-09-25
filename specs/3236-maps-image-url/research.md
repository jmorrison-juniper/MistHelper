# Research: Load the floor plan image on the Maps page

**Issue**: #3236 | **Spec**: [spec.md](spec.md)

## Facts that the design uses

| Fact | Source |
| --- | --- |
| `mistapi.api.v1.orgs.maps` holds only `importOrgMapsFile`. | The installed SDK, mistapi 0.64.0 |
| `/api/v1/sites/{site_id}/maps/{map_id}/image` supports POST and DELETE only. | `documentation/mist-api-openapi31json.json` |
| The map schema holds `url`: "When type=image, the url". | `documentation/api/sites/GET_sites_site_id_maps_map_id.md` |
| The portal policy is `img-src 'self' data:`. | `web_portal/services/config.py`, `SecurityMiddleware.CSP_POLICY` |
| The page reads `image_url` and `has_image` from the portal answers. | `web_portal/templates/map_viewer.html` |

## The live probe

On 2026-09-25, a read-only probe read one site of the live organization. The
site holds 3 maps of type `image`. The probe printed no URL and no secret.

| Item | Result |
| --- | --- |
| The host of `url` | `api.mist.com` |
| The query parameters of `url` | `jwt` only |
| A GET with no credential | 200 after one redirect |
| The redirect host | `papi-production.s3.us-east-1.amazonaws.com` |
| The content type | `image/png` |
| The size | 140,666 bytes |
| The first bytes | `89504e470d0a1a0a`, the PNG signature |

## Decisions

### D1. The portal serves the image from its own origin

The policy `img-src 'self' data:` blocks an image from `api.mist.com` or from
the storage host. The portal therefore downloads the bytes and serves them. A
policy change is not necessary, and it would widen the policy for every page.

### D2. The download sends no API token

The `jwt` query parameter authenticates the download, and the probe proves that
no token is necessary. The standalone viewer in `src/maps/_flask_viewer.py`
sends `Authorization: Token`. That header does not reach the storage host,
because `requests` removes it at a redirect to a new host. The portal still
sends no token, because a token must not go to a host that does not need it.

### D3. The image path holds the site identifier

`getSiteMap` needs the site identifier, and the SDK has no read for a map by
the map identifier alone. The new path is
`/api/maps/site/<site_id>/map/<map_id>/image`, next to the data path. The old
path `/api/maps/image/<map_id>` never worked, so the change removes it. No
compatibility path stays.

### D4. The first bytes decide the image type

A storage host can send `binary/octet-stream` for a PNG file. The portal reads
the signature of the first bytes instead. The portal serves PNG, JPEG, GIF, and
WebP only. It never serves SVG, because an SVG file can hold script.

### D5. Plotly loads the image, and the page reads the result

Plotly draws the markers at once and loads the image in the background. The
promise of `Plotly.newPlot` waits for the image load. If the load fails, Plotly
removes the image node and shows no sign. The page therefore reads the plot
when the promise ends. If the plot holds no image node, the page shows the
failure note.

`Cache-Control: private, max-age=300` lets a second view of the same map use
the browser cache. The value is short, because the `jwt` link can expire.

### D6. A view counter stops an old draw

The map data answer and the image load both take time. If the operator chooses
a second map before the first answer arrives, the first answer must not replace
the second map. A counter holds the number of the current view. A late answer
of an old view draws nothing and shows no note.

### D7. A log filter hides each link secret

urllib3 writes each request path at DEBUG level. The Mist link holds a `jwt`
value. The redirect goes to a signed storage link. That link holds the values
`X-Amz-Credential`, `X-Amz-Security-Token`, and `X-Amz-Signature`. Each value
grants access to the file until the link expires.

A filter on the `urllib3.connectionpool` logger replaces each of these values
with `***REDACTED***`. The filter keeps the other parameters, such as
`X-Amz-Expires`, because they help triage and grant nothing. The route also
logs only the class name of a download failure, because the exception text
quotes the link.

The live check on 2026-09-25 found the storage secret. The first filter hid the
`jwt` value only. With urllib3 at DEBUG level, the log then held the 3 storage
values of each download. The filter now hides all of them. The second live run
logged 2 `jwt` values and 6 storage values, and it hid all 8.

## Alternatives that the design rejects

| Alternative | Reason for the rejection |
| --- | --- |
| Put the signed URL into the page | The policy blocks it, and the page would show the `jwt` value. |
| Add the storage host to `img-src` | The storage host can change, and the change widens the policy of every page. |
| Keep the old path with a `site_id` query parameter | Two paths for one image is a compatibility path, and the old path never worked. |
| Trust the upstream `Content-Type` header | The header can be generic, and a wrong header can make the portal serve HTML. |
| Allow only a fixed list of download hosts | Each Mist region has its own API host. The Mist cloud writes `url`, and the API marks the field read-only. The raster check of D4 already limits what the portal can serve. |
