# Research: The multi-site options page offers each advanced control

**Issue**: #3383 | **Spec**: [spec.md](spec.md)

## Decision 1: Each field of the organization schema, one at a time

The organization schema is `components.schemas.upgrade_org_devices` in
`documentation/mist-api-openapi31json.json`. The access point child of a
multi-site plan uses that schema. Each switch child and each gateway child uses
the site schema or the router schema, which the single-site run already uses.

| Field | The schema text | The decision |
| - | - | - |
| `max_failures` | An integer array. "If strategy==canary". "Array length should be same as canary_phases". | Send it with the canary strategy only, with one count for each phase. |
| `enable_p2p` | A boolean. "For APs only". | Send it only when the operator chooses yes. |
| `p2p_cluster_size` | An integer with the minimum 0 and the default 10. "For APs only". | Send it only with `enable_p2p` true. |
| `p2p_parallelism` | An integer. "For APs only". | Send it only with `enable_p2p` true. |
| `rrm_first_batch_percentage` | An integer. "For APs only and if strategy==rrm". | Send it with the rrm strategy only. |
| `rrm_max_batch_percentage` | An integer. "For APs only and if strategy==rrm". | Send it with the rrm strategy only. |
| `rrm_mesh_upgrade` | The word `parallel` or `sequential`. | Send it with the rrm strategy only. |
| `rrm_node_order` | The word `center_to_fringe` or `fringe_to_center`. | Send it with the rrm strategy only. |
| `rrm_slow_ramp` | A boolean. The rrm strategy only. | Send it with the rrm strategy only. |

The site schema states that the two size fields apply only "if
enable_p2p==true". The organization schema does not say so. The portal applies
the stricter site rule in both modes.

## Decision 2: The access point child refuses the stable build

The organization schema holds no stable word. The version record
`versions[].version` is "Firmware version to deploy for this entry". The
deprecated top-level `version` field allows `suggested` and `alpha`, but not
`stable`. The site schema `version` allows "Specific version / stable".

The multi-site plan therefore sends the stable build to each switch child and
to each gateway child only. The save refuses the stable build when the plan
holds an access point. The refusal names the control, and it tells the operator
to clear the Access points box or to keep the typed versions.

A second guard in `AggregateUpgradeService._ap_body` refuses the stable build.
The guard stops a later caller that skips the route.

A follow-up issue asks for a live check of the stable word on the organization
route. A live check writes firmware, so this change does not run one.

## Decision 3: The release train control needs a session smart router

Only the router schema holds `channel`. The single-site page shows the control
only when a selected device row names the router family. The multi-site page
reads the device views of each selected site on the server, and it renders the
control only when one row names the router family. The browser then shows the
control only while the Gateways box is checked.

## Decision 4: No shared template partial

The issue proposes one template partial for both pages. The change does not use
one, for three reasons.

1. `filterAdvancedUpgradeControls` in `portal.js` runs on each page. It hides
   each element that carries a `data-requires-*` attribute, and it reads the
   single-site selection to decide. A shared partial would carry those
   attributes into the multi-site form, where no single-site selection exists.

2. The multi-site form sends `FormData`, so each control needs a `name`
   attribute. The single-site page reads each control by its test identifier
   and needs no `name` attribute.

3. The two pages use different test identifiers. The browser tests of each
   page read those identifiers.

The parity contract test is the guard against drift instead. It maps each
advanced test identifier of the single-site page to a control of the
multi-site page.

## Decision 5: One body rule serves both modes

`upgrade_service._add_canary_fields` and `_add_access_point_fields` hold the
canary rule and the access point rule of the site body. The aggregate service
had its own copy of the canary rule, without `max_failures`. The change makes
both functions public and calls them from the access point child builder. The
two modes then share one rule, and no copy can drift. A unit test compares the
two bodies for the same choices.

## Decision 6: The write boundary checks each new field

`OrgUpgradeService.submit` runs `OrgUpgradeBody.build` again before the cloud
call. The change adds the nine access point fields to `OrgUpgradeBody.FIELDS`,
and it adds a check for each field. Each check is at least as strict as the
plan rule, so a plan that the save accepts also passes the write boundary.

The shared reader accepts a failure count of any size. The organization body
accepts a count up to 2147483647, which is the bound of the other integer
fields of that body. The multi-site save refuses a larger count with the
control label. The start therefore never meets a body that the boundary
refuses.

## Decision 7: The visibility attributes of the multi-site page

The new controls use `data-org-requires-type`, `data-org-requires-strategy`,
and `data-org-requires-choice`. The single-site rule in `portal.js` never reads
these names. `updateOrgOptionsVisibility` reads them, and
`setOrgGroupVisibility` disables each control of a hidden group.

## Found during the research

- A digit string longer than 4300 characters makes `int()` raise a
  `ValueError` in the shared readers. The route then shows the Python text of
  the error. A separate issue records that fault.
