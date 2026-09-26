# Research: The multi-site options page states the correct site noun

**Issue**: #3447 | **Spec**: [spec.md](spec.md)

## R1: The source of the count

The route `options_page` in `src/upgrade_portal/app/routes/org_upgrade.py`
passes one row for each selected site as `sites`. The template
`org_options.html` sets `rows = sites | default([], true)` on line 2. The note
on line 27 prints `rows | length`, and then the fixed word "sites".

The route answers status 404 with the code `sites_not_chosen` when no row
remains. The page thus never opens with zero sites.

A retry changes the selection to the sites of the retry devices (#3247). The
route then passes one row for each site of the retry. The note then prints the
count of the retry sites with the same fixed word.

## R2: The plural rule of the portal

**Decision**: Set the noun with a Jinja `set` statement and the rule
`'site' if site_count == 1 else 'sites'`.

**Rationale**: The portal uses the same inline rule in these places.

| File | Line | Text |
| - | - | - |
| `upgrade/confirm.html` | 107 | `device_noun` |
| `upgrade/org_options.html` | 54 | The retry banner |
| `upgrade/org_progress.html` | 217 and 249 | The retry count and the child job count |
| `app/routes/review.py` | 1276 | A Python helper of the review page |
| `static/js/portal.js` | 4512 | The count of the selected runs |

**Alternatives considered**:

- A shared Jinja filter. We did not use this. Five places use the inline
  rule, so a filter for one line adds a second style. Issue #3449 can decide
  on a shared filter for each template.
- The text "site(s)". We did not use this. The text is harder to read, and
  the house style uses the correct noun.

## R3: The test identifier

**Decision**: Add `data-testid="org-upgrade-site-count"` to the paragraph of
the note.

**Rationale**: The paragraph has no identifier. The class `portal-card-note`
occurs on other paragraphs of the page. A test that finds the note by its
position fails when the layout changes.

## R4: The test harness

**Decision**: A new contract file drives the real options route through a
signed multi-site client. Stand-ins replace each cloud read. The file builds
its own fixture from the shared helpers of
`tests/contract/upgrade_portal/test_org_child_controls_routes.py`. The retry
tests use `settled_record` from that file.

**Rationale**: Ruff reports F811 when a test file imports a pytest fixture and
a test names that fixture as a parameter. The contract file of #3439 uses the
same pattern.

A browser journey in `tests/e2e/upgrade_portal/` selects one site and then two
sites through the real site picker. The journey saves one screenshot of each
note.

## R5: Other pages with the same defect

A scan of the templates found the same defect on two more pages:
`select/orgs.html` line 138 and `review/history.html` line 429. Issue #3449
holds them.

The notes at `capture/capture.html` line 340 and `review/compare.html` lines
178 and 238 show only when the portal limits the rows of a table. Such a table
holds many rows, so the plural noun is correct there.

The scan also read `static/js/portal.js` and the Python routes. The one count
in `portal.js` already uses the rule. The stop messages in
`upgrade/stop.py` already use the rule.
