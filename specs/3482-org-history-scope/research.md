# Research: The capture history with no site names every site

**Issue**: #3482 | **Spec**: [spec.md](spec.md)

## Decision 1: The note says "every site" and "The portal holds"

**Decision**: On the page with no site, the note says "The list shows the
stored captures of every site. The portal holds N captures." The caption says
"The stored captures of every site."

**Rationale**: The page with no site reads every capture in the store. The
route passes no organization value to the capture list. The word "organization"
is therefore false today, because the store can hold the captures of more than
one organization. The words "The portal holds" also match the empty rows of the
page, such as "The portal holds no upgrade run yet."

**Alternatives considered**:

- "The organization holds N captures". This text is false until issue #3484
  narrows the list to the selected organization.
- "The list holds N captures". The first sentence already starts with "The
  list shows", so two sentences would then give the list two jobs.

## Decision 2: A new scope class gives the texts

**Decision**: The new frozen class `HistoryScope` in `app/routes/review.py`
holds the site identifier and the site name of the request. The class method
`for_page` builds the scope from the site identifier and the shaped rows. Three
properties give the texts: `capture_lead_text`, `capture_holder_text`, and
`capture_caption_text`.

**Rationale**: The scope is a property of the request, not of the rows. The
view `HistoryPageView` already holds eight fields, and the Pylint default limit
is seven attributes. The compare package owns no request, so its view cannot
know the scope. A separate class keeps the rule in one place, and a unit test
reads the class with no Flask application.

**Alternatives considered**:

- Two new fields of `HistoryPageView`. The view then holds ten fields, and the
  compare view `HistoryView` still does not know the scope.
- A comparison in the template, such as a test of the site value. The history
  template holds no rule, and the unit test `test_the_page_holds_no_rule`
  guards that state.

## Decision 3: The template variable `history_scope` replaces `site_name`

**Decision**: The route passes `history_scope`. The template reads the three
texts from it and no longer reads `site_name`. Each test that renders the
history template with `site_name` passes a scope instead.

**Rationale**: The variable `site_name` cannot tell the page with no site from
a site with no name. The two states need different texts. The project rule
forbids a compatibility path that keeps an old name alive, so the migration
changes each caller.

**Alternatives considered**:

- Keep `site_name` and add a second variable for the scope. Two variables then
  describe one scope, and the two can disagree.

## Decision 4: A page with no scope keeps the old texts

**Decision**: If the route supplies no `history_scope`, the template prints the
texts of a site with no name. These texts are "The list shows the stored
captures.", "The site holds", and "The stored captures of the site."

**Rationale**: The route always supplies a scope. Only a test renders the
template with no scope. The old texts keep each such test valid, and they
match the default texts of #3449.

## Decision 5: The page with no site reads no site name

**Decision**: `HistoryScope.for_page` reads the site name from the rows only
when the request names a site.

**Rationale**: The old route read the name of the first row for each page. On
the page with no site, that name belongs to one of many sites. The docstring of
`read_site_name` claimed that the page with no site shows no name. The new
class makes that claim true, and the docstring states the new call.

## Decision 6: The browser journey reads the count as a pattern

**Decision**: The journey compares the note of the page with no site against a
pattern. The pattern accepts a count of one or more digits and the noun that
agrees with it.

**Rationale**: Many journeys share the browser test server. Some of them store
a capture, so the count of the page with no site depends on the order of the
tests. The pattern still proves every word of the note.
