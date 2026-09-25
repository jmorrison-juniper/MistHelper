# Research: The options page shows a real note under each type control

**Issue**: #3381 | **Spec**: [spec.md](spec.md)

## Decision 1: Repair the template, not the selector

**Evidence**:

- `TypedVersionSelector.select` in `src/upgrade_portal/upgrade/options.py`
  writes `"warning": _type_warning(...)`. `_type_warning` returns `None` when a
  type has no warning.

- `build_options_view` puts the selections into the view under
  `type_selections`. The route `options_page` in
  `src/upgrade_portal/app/routes/upgrade.py` passes them to the template.

- `options.html` line 60 sets `typed_selections`, and line 195 prints
  `selection.get('warning', <default>)`.

- A dictionary `get` returns the stored value when the key exists. The stored
  value is `None`, so Jinja prints the word `None`.

**Decision**: change line 195 to `selection.get('warning') | default(<text>,
true)`. The second argument `true` makes the filter treat `None` and an empty
text as absent.

**Why this repair**: the templates of the portal use `default(..., true)` in
more than 200 places for the same reason. A value of `None` is a correct
answer of the selector. The template is the one place that turns it into text.

**Alternatives rejected**:

- Drop the key from the selector when the value is `None`. Other code reads the
  selection shape, and a missing key changes that shape.

- Write an empty text in the selector. An empty text still reaches the
  template, and the template then prints an empty note.

## Decision 2: The same defect exists nowhere else

**Evidence**: a search of every template under
`src/upgrade_portal/app/assets/templates` found one printed `.get(key,
'<text>')` call, which is line 195. A second search found one printed
`default(...)` call without `true`: `org_options.html` line 233, the failure
limit field. The multi-site `options_view` in
`src/upgrade_portal/app/routes/org_upgrade.py` answers
`options.get("max_failure_percentage", 5)`. The stored options come from
`read_options`, which omits the key for a big-bang plan and stores a number for
the other plans. So that field never receives `None`.

**Decision**: change line 195 only.

## Decision 3: Test the shipped selection shape

**Evidence**: the stand-in `StandInOptionsView` of
`tests/contract/upgrade_portal/test_upgrade_options.py` answers no
`type_selections` field. The template then reads an empty selection, and the
default text shows. So no current contract test renders the value `None`.

**Decision**: add a stand-in that builds `type_selections` with the shipped
`TypedVersionSelector`, from the inventory row of the test file. The test
reads the note of each device type by its identifier.
