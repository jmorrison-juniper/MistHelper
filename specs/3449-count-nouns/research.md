# Research: The picker note and the history note make the noun agree with the count

**Issue**: #3449 | **Spec**: [spec.md](spec.md)

## Decision 1: The noun replaces the words "of them"

**Decision**: The second sentence says "This page starts after 1 organization"
and "This page starts after 1 capture". The words "of them" go away.

**Rationale**: The word "them" is plural, so it cannot refer to one
organization or to one capture. The noun agrees with each count, and the
reader does not have to find the word that "them" refers to.

**Alternatives considered**:

- "This page starts after row 1". This text changes the meaning, because the
  offset counts the rows before the page.
- Keep "of them" for each count except 1. This text needs two sentence shapes
  for one idea.

## Decision 2: The view model settles each text

**Decision**: Each view model gives three texts: `total_text`, `offset_text`,
and `page_size_text`. The template prints the three texts and holds no rule.

**Rationale**: The two templates hold no rule. The unit tests
`test_the_page_holds_no_rule` guard that state for each page. The docstrings of
the two view models say that the page prints a value and never compares a
number. The fix of #3447 put a comparison into the options template. That
template has no such guard, but these two templates do.

**Alternatives considered**:

- A comparison in each template. The guard does not find `==`, but the
  comparison breaks the stated intent of the two view models.
- A Jinja filter for the count. A filter adds a rule to the template layer,
  and a unit test then needs a template to test the rule.

## Decision 3: One mixin serves the two history views

**Decision**: The new class `HistoryNoteText` in `compare/render.py` holds the
three properties and one static rule. `HistoryView` and the route view
`HistoryPageView` both inherit it.

**Rationale**: The route prints `HistoryPageView`, and the unit tests print
`HistoryView`. One mixin keeps the note of the two views in step. The mixin
holds `__slots__ = ()`, so the two slots views get no `__dict__`. A property is
not a field, so `asdict` and each JSON body do not change. A scratch proof ran
the mixin under a frozen slots dataclass. The fields stayed the same, the view
stayed frozen, and mypy reported no issue.

**Alternatives considered**:

- Three properties in each view. Two copies of the texts can drift.
- Three new fields that the builder fills. A view built with a count and no
  text then prints a text that does not agree with the count.

## Decision 4: The picker view holds its own rule

**Decision**: `OrgPickerView` in `select.py` holds the three properties and a
static rule of its own.

**Rationale**: `select.py` imports nothing from the compare package. An import
would join the organization picker to the capture comparison. The rule is one
line, and a unit test reads each copy.

**Alternatives considered**:

- A new shared module for the rule. One line does not need a module, and the
  portal holds no shared text module now.

## Decision 5: The page size also agrees with its count

**Decision**: Each note prints `page_size_text`, which says "1 row" or
"N rows".

**Rationale**: The history page size can be 1, because the query value `limit`
accepts each value from 1 to 200. The picker page size is fixed at 25, but the
two notes then use one pattern.

## Decision 6: Each note gets a test identifier

**Decision**: The picker note gets `data-testid="org-search-note"`, which is
the same value as its `id`. The history note gets
`data-testid="history-count-note"`. The contract file `ui-testids.md` names
both identifiers.

**Rationale**: A browser journey must find each note with no text search and
no position rule. A text search would find the old text and the new text
through different paths.
