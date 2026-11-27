# Contract: Batch target routes (unchanged)

The HTTP routes of the Multi Site batch target discovery do not change. This contract records their shape, so a reviewer can confirm that the response stays the same.

## Routes

| Route | Handler | Purpose |
| - | - | - |
| `GET /api/websockets/batches/sites` with `kind` and `key` | `OrganizationPickerRoutes.sites` (`routes/pickers.py`, line 95) | Lists the complete site rows of the organization. |
| `GET /api/websockets/batches/sites/<site_id>/targets` with `kind`, `key`, `device_id`, and `map_id` | `BatchTargetPickerRoutes.site_targets` (`routes/pickers.py`, line 113) | Lists the targets of one verified site. |
| `GET /api/websockets/batches/targets` with `kind` and `key` | `BatchTargetPickerRoutes.organization_targets` (`routes/pickers.py`, line 124) | Lists the targets of an organization-scoped operation. |

- The browser builds the two `targets` URLs in `websockets.js`, line 514.
- The handler for the organization sites list calls `services.pickers.batch.sites`. The URL pattern is in the blueprint, which this change does not edit.

## Response fields of a target discovery

The discovery response keeps these fields. `BatchTargetResponseBuilder.build` returns them (`related.py`, lines 269 to 276).

| Field | Meaning |
| - | - |
| `rows` | The deduplicated, sorted target rows. |
| `total_count` | The number of rows. |
| `complete` | `True` only after every picker read succeeds. |
| `reason` | The sentence for an empty result, or `None`. |
| `excluded` | The count of rows excluded by family, as `{"incompatible_family": n}`. |
| `scope` | `{"site_id": <site identifier>}` for a site, or `{"organization": True}` for an organization. |

## Error codes

The routes keep these error codes, which the picker and the resolver raise.

- `bad_request`: an unknown field, a repeated control, a foreign site, or a map outside the site.
- `not_ready`: the portal engine is not ready.
- `picker_request_failed`: Mist refused a request with an HTTP 4xx status.
- `picker_service_failed`: Mist failed with a server error or an unclassified exception.
- `picker_incomplete`: Mist returned an invalid page cursor, a repeated cursor, or no page.
- `picker_unavailable`: Mist returned an unsupported response shape.

## Compatibility rule

A client that works before the change must work after the change without a new field. The change adds no field and removes no field.
