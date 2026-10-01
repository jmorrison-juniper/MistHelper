# Contract: Selected-Organization History

**Feature**: [spec.md](../spec.md)

This contract narrows existing reads.
It creates no route, persisted field, or authentication policy.

## 1. Existing Request Forms

| Request | Successful scope | Existing response |
| --- | --- | --- |
| `GET /history` | Selected organization, across its sites. | Existing HTML with Captures, Runs, Multi-site upgrades, and Audit log cards. |
| `GET /history?site_id=<site_id>` | Selected organization intersected with the requested site. | Existing HTML with the same cards. |
| `GET /api/sites/<site_id>/history` | Selected organization intersected with the requested site. | `200` JSON with `captures` and `total`. |
| `GET /api/sites/<site_id>/runs/history` | Selected organization intersected with the requested site. | `200` JSON with `runs` and `total`. |

Capture and run requests retain `limit` and `offset`.
The default limit is 25.
The limit bounds remain 1 through 200.
The default offset is zero.
The offset bounds remain zero through 1,000,000.
Nonnumeric values retain the existing default behavior.
Out-of-range integers retain the existing clamp behavior.

Pagination links retain the site restriction.
They do not carry another organization as authorization.
Each request reads and authorizes the current signed selection again.

## 2. Authorization Order and Refusals

The current sign-in guard acts first.
Next, the route reads the saved signed selection and normalizes it.
Next, the existing organization refusal authority decides.
Only an accepted decision permits history readers to run.

| Condition | Required result | History source calls |
| --- | --- | --- |
| No active sign-in, JSON or default request | Existing `401 not_authenticated` envelope. | Zero. |
| No active sign-in, HTML-preferring request | Existing sign-in redirect behavior. | Zero. |
| Missing, blank, whitespace-only, or incorrectly typed selection | Existing `400 org_not_chosen` envelope. | Zero. |
| Selection outside known privileges | Existing `403 org_not_permitted` envelope. | Zero. |
| Known empty privileges | Existing `403 org_not_permitted` envelope. | Zero. |
| Explicit selection with unavailable privileges permitted by current policy | Normal scoped history response. | Matching scope only. |

Existing refusal messages remain unchanged.
The error envelope remains `{"error": {"code": "...", "message": "..."}}`.

Zero calls means zero capture, run, operation, and audit reads.
This rule also applies when every store is empty or unavailable.
Do not infer an organization from returned rows.
Do not select the first permitted organization.
Do not use request-supplied organization values.

## 3. Data and Pagination Scope

Organization matching uses the validated signed selection.
If the request names a site, matching also requires that site.

For captures and runs, both restrictions precede count and page queries.
The returned total counts every matching record before `offset` and `limit`.
Foreign records consume no page positions.

Preserve existing capture ordering by descending `started_at`.
Preserve existing run ordering by descending `created_at`.
Preserve the current run exclusion for aggregate operation records.

An offset beyond matching history returns an empty page with the correct scoped total.
An empty selected organization retains the existing empty states.
Populated foreign history cannot supply replacement rows or totals.

A foreign or unknown site returns the existing successful empty intersection.
Capture and run totals are zero.
The response does not identify a foreign organization or confirm its stored history.

The complete response must contain no foreign stored identifier, site label, moment, count, operator label, account label, digest, or link.
This includes HTML attributes, embedded values, and JSON fields.
Unattributed records do not match.

A site value from the request remains request context, not returned stored history.
Keep existing scope attributes that repeat that requested value.
Compare foreign-site and unknown-site empty results without requiring removal of their request context.

## 4. Real Adapter and Injected Reader Boundaries

These existing call forms remain unchanged:

```text
CAPTURE_LISTER(site_id)
CAPTURE_LISTER(site_id, limit=limit, offset=offset)
RUN_LISTER(site_id)
RUN_LISTER(site_id, limit=limit, offset=offset)
```

The trusted real adapters derive and authorize the organization from the signed request context.
They must construct:

```text
CaptureQuery(org_id=chosen, site_id=site_id, limit=limit, offset=offset)
RunQuery(org_id=chosen, site_id=site_id, limit=limit, offset=offset)
```

`chosen` is never empty on a source-read path.
It never comes from the request body, the first record, or the first privilege.

The existing signature introspection handles window arguments only.
Do not introduce an organization-dropping retry.
Do not retain an unrestricted adapter path.

Injected readers remain trusted test or application configuration, not user-controlled request input.
Single-organization formatting stand-ins are not isolation evidence.
Isolation evidence must exercise the real adapters and query types.

The comparison picker retains its site-only capture call.
If the signed selection fails, the real capture adapter must refuse before any store read.
Existing comparison loaders and exports are outside this contract's repair surface.

## 5. Operation History

The operation section receives the validated organization.
The existing lister still receives `org_id`, optional `site_id`, and `limit`.

An operation must match the selected organization.
If the request names a site, the operation must include it in `site_ids`.
Preserve the existing descending creation and update ordering.

The existing browser-session ownership rule controls progress links.
A same-organization operation from another session remains visible without that link.
No owner key reaches the response.

## 6. Audit Reader

The intended reader signature is:

```text
read_audit_rows(limit=DEFAULT_AUDIT_LIMIT, path=None, site_id="", *, org_id)
```

The caller must supply `org_id`.
An empty or incorrectly typed value fails before a trail read.
There is no unrestricted default or compatibility overload.

`site_id=""` means every matching site in that organization.
The default audit limit remains 200.
The route does not replace that limit with its capture page limit.

For both reader paths:

1. Read the complete trail in its stored order.
2. Exclude records outside the organization-and-site scope before inference.
3. Keep independent holder state for each `(org_id, site_id)`.
4. Insert inferred rows through the existing transition rules.
5. Apply the existing result limit and newest-first output order.

A bounded result equals the newest matching events from an unrestricted-size scoped result.
Earlier matching actions remain available for inference outside the visible window.
Foreign events consume no result positions and change no matching inference state.

Keep the legacy final slice behavior on the non-positive or unbounded path.
Zero returns an empty slice.
Negative values keep the existing negative-slice meaning.
`None` keeps the existing full-slice meaning.

An inferred expiry uses the earlier matching hold's organization, site, and actor digest.
It uses the later matching take's moment.
A release prevents the corresponding expiry.
A takeover creates no expiry by itself.
A later take after an unreleased takeover does create an expiry.

Audit output retains its current fields and digests.
It contains no stored audit address, credential, or owner key.
Missing files, damaged lines, and legacy missing actions retain their current handling.

## 7. Preserved Behavior and Availability

History remains read-only.
It requires no site-lock ownership, lock lookup, or typed confirmation.

Keep existing source availability behavior.
An unavailable source must not trigger an unrestricted retry.

Keep existing empty states, row fields, page bounds, stale-run displays, operation links, and device-type cells.
Keep bulk confirmation context tied to the validated selected organization.
Do not change confirmation words, firmware choices, menus, JavaScript, unrelated history text, or styles.

## 8. Verification Contract

Use at least two synthetic organizations and two sites in the selected organization.
Exercise all four request forms.
Inspect the complete responses.

The synthetic database must evaluate the query's actual filters.
Check organization binds in both count and page calls.
Check that organization and optional site filters precede count and page-limit clauses.

Prove exact rows and totals for populated, empty, site-specific, later-page, and beyond-end cases.
Add, remove, or reorder foreign records.
Confirm that matching rows, totals, and page boundaries stay unchanged.
Prove zero source calls for every refused selection.

Audit evidence must cover both limit paths, both opening actions, release suppression, takeover behavior, missing attribution, and reused site text.
Use explicit expected event order and attribution.

Do not replace this evidence with an injected lister signature assertion.
Do not add browser duplication when direct response contracts prove the changed behavior.
