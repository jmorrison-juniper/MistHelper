# Research: The multi-site confirm page names one site for a plan of one site

**Issue**: #3452 | **Spec**: [spec.md](spec.md)

## Decision 1: The texts do not repeat the count

**Decision**: The Warning says "at each selected site" for two or more sites.
The button of a full pre-check says "Take a new pre-check for each site".

**Rationale**: The issue states that the text "each selected site" is correct
for each count. A text with the count reads badly for two sites, as in "for
all 2 sites". The line "Sites" above the Warning already states the count.

**Alternatives considered**:

- "At each of the N selected sites". This text repeats the count, and it is
  longer. The operator reads the count in the line above.
- One text, "each selected site", for each count. This text is correct for
  one site too. The issue asks that the page name one site for a plan of one
  site, so the page uses "the selected site" there.

## Decision 2: The button of the missing pre-checks follows the site count

**Decision**: The button says "Take the missing pre-check" for a plan of one
site. For two or more sites, it keeps "Take the missing pre-checks".

**Rationale**: A plan of one site can miss one capture at most. The singular
form is therefore always exact there. For two or more sites, the count of the
missing captures changes after each capture. The plural form then names the
kind of work, and the label stays stable.

**Alternatives considered**:

- A label that follows the count of the missing captures. The page loads
  again after each capture, so the label would change during one task. The
  issue does not ask for this change.

## Decision 3: The template holds the rule

**Decision**: The template sets one Boolean value from the count of the saved
sites. Each of the three texts reads that value.

**Rationale**: The fix of #3447 uses the same rule in the options page. The
route already passes the count as `site_count`. No Python code changes.

**Alternatives considered**:

- A route value for each text. This change adds three values to the route and
  moves page text into Python code.

## Decision 4: The Warning gets a test identifier

**Decision**: The Warning gets the test identifier `org-upgrade-scope-warning`.

**Rationale**: The page holds more than one alert. A stable identifier lets
the contract tests and the browser journeys read the whole Warning. The
buttons already have stable identifiers.