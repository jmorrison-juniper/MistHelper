# Contract: Site snapshot interface

This contract defines the Python interface of the change. It covers the new module, the constructor and method signatures, the log events, and the errors.

## Module

`src/mist/realtime/websocket_streams/web/services/pickers/site_snapshot.py` (new)

## Constant

- `SITE_SNAPSHOT_LIFETIME_SECONDS: float = 300.0`
- Meaning: a snapshot with an age of 300 seconds or less is fresh.
- The value equals `ScopeRouter.TTL_SECONDS` in `src/operations/exporting/ex_hardware_inventory/run/routing.py`, line 37.

## Class `OrganizationSiteSnapshot`

| Member | Signature | Behavior |
| - | - | - |
| constructor | `__init__(self, picker: Any) -> None` | Stores the picker. The snapshot starts in the absent state. |
| refresh | `refresh(self) -> dict[str, object]` | Calls `picker.sites()` once. Stores copies of the rows and the read time. Returns the picker payload unchanged. On any exception, clears the rows, logs an error, and raises the same exception. |
| rows | `rows(self) -> list[dict[str, object]]` | Returns copies of the stored rows. Calls `refresh` first when the snapshot is absent or expired. |

- The class uses one `threading.Lock`. The lock covers `refresh` and `rows`.
- The class uses `time.monotonic` for the read time. A wall clock change cannot change the age.

## Log events

| Order | Level | Event name | Fields | Written when |
| - | - | - | - | - |
| 1 | info | `web.batch.sites.snapshot.read` | none | Before the organization read starts. |
| 2 | debug | `web.batch.sites.snapshot.stored` | `count` only | After the rows are stored. |
| 3 | error | `web.batch.sites.snapshot.failed` | `detail` with the exception type name | When the read raises. |

- No event carries an identifier, a label, or a token.
- Event names use ASCII only.

## Changed signatures in `related.py`

| Class | Member | Before | After |
| - | - | - | - |
| `BatchTargetResolver` | `__init__` | `(picker, catalog)` | `(picker, catalog, sites: OrganizationSiteSnapshot)` |
| `BatchTargetPickerService` | `sites` | Calls `self._picker.sites()` directly. | Calls `self._sites.refresh()` and returns its payload with `complete` and `scope` set. |
| `BatchTargetPickerService` | `targets` | Builds `BatchTargetResolver(self._picker, self._catalog)`. | Builds `BatchTargetResolver(self._picker, self._catalog, self._sites)`. |
| `BatchTargetResolver` | `_site_rows` | Calls `self._picker.sites()["rows"]`. | Calls `self._sites.rows()`. |

- `BatchTargetPickerService.__init__` keeps its signature `(picker, catalog, reason)`. It adds the attribute `_sites`.
- No compatibility shim keeps the old `BatchTargetResolver` signature. `BatchTargetResolver(` appears once in the source tree, at `related.py`, line 63.

## Errors

- The snapshot adds no new error code.
- The picker raises the existing codes: `picker_request_failed`, `picker_service_failed`, `picker_incomplete`, and `picker_unavailable`.
- A site check that finds no matching site raises `bad_request` with the existing sentence.
