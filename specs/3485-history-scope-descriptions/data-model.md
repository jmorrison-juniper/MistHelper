# Data model: History scope descriptions

## Existing history scope

`HistoryScope` retains its two existing fields.

| Field | Type | Source |
| --- | --- | --- |
| `site_id` | `str` | The existing optional filter inside the authorized history request. |
| `site_name` | `str` | The existing name from the scoped capture rows. |

The Captures card properties and `for_page` contract remain unchanged.
An organization page never adopts a site's name from its first row.

## Dedicated card scope

`HistoryCardScope` receives the existing validated `site_id` and `site_name`.
Its only computed properties are `runs`, `operations`, and `audit`.
Each property returns a frozen `HistoryCardDescription`.

## Description record

`HistoryCardDescription` contains three string fields and one shared subject formatter.

| Key | Meaning |
| --- | --- |
| `note` | The scope-specific first sentence of the card note. |
| `caption` | The scope-specific first sentence of the accessible caption. |
| `empty` | The scope-specific statement for an empty visible page. |

The common subject is the stored site name, "the selected site", or "the selected organization".
The multi-site group uses "that include" for a site filter.
The organization group uses "of" or "for" the selected organization.

## Validation and state

Use no raw query name or site identifier as display text.
Keep Jinja's automatic escaping.
Add no persisted field, schema, primary key, or state transition.
Do not read a cloud source to complete a missing display name.
