# Research: The portal pages use American spelling

**Issue**: #3384 | **Spec**: [spec.md](spec.md)

## Decision 1: Change the five lines, and keep every identifier

**Evidence**: a search of `src/upgrade_portal/app/assets/templates` found five
lines with "neighbour" or "neighbourhood". Four lines are visible text:

- `options.html`: the legend of the peer-to-peer group.

- `options.html`: the label of the yes choice of that group.

- `options.html`: the hint of the radio node order control.

- `confirm.html`: the row name of the peer-to-peer choice.

The fifth line is inside a Jinja comment of `options.html`. The browser never
receives it, but STE covers code comments.

**Decision**: change the five lines to "neighbor" or "neighborhood".

## Decision 2: Guard the templates and the portal script

**Evidence**: a wider search for 40 British spellings found no other hit in the
templates or in `static/js/portal.js`. The only other match was the attribute
`aria-labelledby` in `review/history.html`. The ARIA standard fixes that name.

**Decision**: add a contract test with a short list of British word stems. The
list omits `labelled`, because of `aria-labelledby`. The list omits
`cancelled`, because the state model uses that identifier. The list omits
`analyses`, because the word is also the American plural of "analysis".

**Why a guard**: no current test reads the five texts. A guard stops the next
British spelling at review time, and it costs less than one second.

## Decision 3: Prove the guard decision without the files

**Evidence**: the project guard rule asks for a red proof. A direct test of the
decision needs no network and no environment.

**Decision**: add one test that feeds British samples to the pattern and one
test that feeds the allowed identifiers. The file guard also states the count
of files that it read, and it fails if it reads no file.
