# Research: The multi-site texts name one site with a singular noun

**Issue**: #3462 | **Spec**: [spec.md](spec.md)

## Decision 1: The place words are "this site" and "these sites"

**Decision**: A text that names one site says "this site" before the name. A
text that names two or more sites says "these sites" before the names.

**Rationale**: The issue asks for "at this site: Site A". The single-site
texts already say "this site", so the two modes then use the same words. The
colon points from the noun to the list of names.

**Alternatives considered**:

- "At 1 site: Site A". This text repeats the count, and the list of names
  already shows the count.
- "At the site: Site A". The name of a site often holds the word "Site", so
  the text reads "the site: Site A". The demonstrative "this" points at the
  name more clearly.

## Decision 2: One class method holds the rule of the Python texts

**Decision**: The static method `OrgSiteRefusal.place_text(count)` returns
the place words for a count. The three save refusals and the start refusal
call it.

**Rationale**: Four texts in two modules share one rule. One method keeps the
rule in one place, and a unit test reads it with no Flask application. The
module `org_site_records.py` imports no route module, so the route module can
import the class with no import cycle. The route module already imports two
names from that module.

**Alternatives considered**:

- A second copy of the rule in the route module. Two copies can drift.
- A new module for the rule. One method does not need a module.

## Decision 3: The template holds the rule of the banner

**Decision**: The template sets one Boolean value from the length of
`partial_site_names`. The banner reads that value for both nouns.

**Rationale**: The fix of #3447 uses the same rule on the same page. The fix
of #3452 uses it on the confirm page. The route already passes the list, so
no route value changes.

**Alternatives considered**:

- A route value for the place words. This change moves page text into Python
  code, and it adds a route value for one banner.

## Decision 4: The start refusal gets a new second sentence

**Decision**: The second sentence of the start refusal changes from "These
sites hold no pre-check capture: {names}." to "The portal found no pre-check
capture for {place}: {names}."

**Rationale**: The old sentence has the subject "These sites", so the verb
must also change for one site. The new sentence has the subject "The
portal", so only the place words change. The preposition "for" fits a
capture, because the portal stores the capture and not the site.

**Alternatives considered**:

- "This site holds" and "These sites hold". This text needs two values for
  one rule.

## Decision 5: The count of the labels decides the noun

**Decision**: The noun follows the count of all refused sites, not the count
of the shown names.

**Rationale**: A refusal shows 10 names at most, and then "and N more". Such
a refusal always names 11 or more sites, so the plural noun is correct. A
count of zero takes the plural noun, as in #3447. No refusal names zero
sites, so that count is a guard only.
