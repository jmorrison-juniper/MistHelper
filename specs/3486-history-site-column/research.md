# Research: The Site column of the Captures table

**Issue**: #3486 | **Spec**: [spec.md](spec.md)

## R1. The source of the site text

**Decision**: Read the site text from the stored capture record of each row.

**Evidence**:

- `capture/assembly.py` writes `site_name` on each capture record. The
  collector job carries the same name. Each record also holds `site_id`.
- `review.history_row` copies each stored field into the shaped row. The
  shaped row therefore holds both fields.
- `compare.render.HistoryRow` holds no site field, and the class is frozen.
  `review.page_rows` copies each compare row. It adds the device types from
  the stored row with the same capture identifier. The site text can join at
  the same place.

**Alternatives**:

- A new field on `HistoryRow`. Rejected, because the compare package owns the
  class, and the route already adds the device types beside it.
- A cloud read of the site name. Rejected, because the record holds the name,
  and the spec forbids a new read.

## R2. One rule for the site text of a run and of a capture

**Decision**: Rename `run_site_label` to `record_site_label`. Call it for a
run row and for a capture row.

**Evidence**: `run_site_label` returns the site name, then the site
identifier, then an empty text. One call site uses it, in
`run_history_identity_fields`. No test names it.

**Alternative**: A second function for the capture row. Rejected, because two
copies of one rule can drift apart.

## R3. The owner of the column rule

**Decision**: Add the class `HistoryCaptureColumns`. The route gives one
instance to the template as the value `history_columns`.

| Property | The page with no site | The page of one site |
| - | - | - |
| `shows_site_column` | True | False |
| `column_count` | 10 | 9 |
| `row_values_text` | The sentence of today, with "the site," first. | The sentence of today. |

**Evidence**: The template prints the values and holds no rule. The guard
`test_the_page_holds_no_rule` rejects arithmetic in a Jinja expression, so the
route must give the column count.

**Alternatives**:

- Three new properties on the class `HistoryScope` of issue #3482. Rejected.
  That class already holds two fields, one class method, and three
  properties. Three more members break the five-item rule. The new class
  holds one field and three properties.
- One property on `HistoryScope` that returns the new class. Rejected. The
  template reads the scope with a default, because a render can give no
  scope. The template uses `StrictUndefined`, so a chained read of an absent
  scope stops the render. A separate template value takes one default for
  each property.

## R4. The column widths

**Decision**: Add the class `history-table-sites` to the table when it shows
the Site column. Add ten width rules under `.history-table.history-table-sites`.
Raise the minimum width of that table from 58rem to 60rem.

**Evidence**: `portal.css` states the width of each of the nine columns with
an `nth-child` rule. A new second column moves each later column to the next
rule. Each selector of the new set carries two classes, so it wins over the
rule of the nine-column set.

The first plan held a floor of 66rem, and each share was near the share of
today. A browser proved two faults in that plan.

1. At 1024 pixels, the page gives the table 982 pixels. A floor of 66rem is
   1056 pixels, so the table scrolled sideways. The Open control then sat
   past the edge of the window.
2. A Role share of 5 percent broke the word `post` over two lines. That row
   stood 61 pixels high, and the budget of issue #2106 is 48 pixels.

A temporary probe then measured each column in Microsoft Edge. The probe
measured the text with a range and added the cell padding. A cell with a
visible overflow does not report the overflow in `scrollWidth`, so the range
is necessary. The need of a cell is the largest need of the five seed rows. A
seed capture identifier holds 27 characters.

| Column | Cell need | Header need | Nine columns | Ten columns | At 1024 pixels | At 1280 pixels |
| - | - | - | - | - | - | - |
| Capture | 234 pixels | 82 pixels | 20 percent | 12 percent | 118 pixels | 149 pixels |
| Site | 160 pixels | 52 pixels | None | 13 percent | 128 pixels | 161 pixels |
| Started | 182 pixels | 77 pixels | 14 percent | 14 percent | 137 pixels | 173 pixels |
| Role | 55 pixels | 56 pixels | 6 percent | 7 percent | 69 pixels | 87 pixels |
| State | 98 pixels | 61 pixels | 9 percent | 9 percent | 88 pixels | 111 pixels |
| Devices | 33 pixels | 80 pixels | 7 percent | 7 percent | 69 pixels | 87 pixels |
| Device types | 131 pixels | 116 pixels | 18 percent | 12 percent | 118 pixels | 149 pixels |
| Clients | 33 pixels | 73 pixels | 7 percent | 7 percent | 69 pixels | 87 pixels |
| Stored size | 67 pixels | 103 pixels | 9 percent | 9 percent | 88 pixels | 111 pixels |
| Action | 88 pixels | 72 pixels | 10 percent | 10 percent | 98 pixels | 124 pixels |

The header need includes the sort arrow of `portal.js`. The two right columns
give the width of each column of the ten-column table, with the padding.

The shares obey five rules.

1. The start moment, the state, the three number columns, and the action keep
   the shares of the table of one site.
2. The Role column gets 1 more percent. The Linux font of the test runner is
   wider than the Windows font, so the word `post` needs a margin.
3. The Site column gets 13 percent. At 1280 pixels, the name
   `E2E Stored Poll Site` fits.
4. The Site column and the Role percent come from the capture column and the
   device type column. A real capture identifier holds 39 characters, and it
   clips at every width in the two tables. The `title` attribute holds the
   whole identifier.
5. At 1280 pixels, each header shows its text and its sort arrow. At 1024
   pixels, the Devices, Clients, and Stored size headers hide the arrow. The
   table of one site hides the same three arrows at 1024 pixels, because the
   three shares do not change.

The floor of 60rem is 960 pixels. At that floor, the Role column holds 67
pixels, and the Action column holds 96 pixels.

The rule `.portal-table td` holds `word-break: break-word`. A word that does
not fit its cell then breaks at a character, and the row grows. The Site cell
therefore holds `white-space: nowrap` and clips a long name with an ellipsis,
in the same way as the device type cell.
The guard `test_the_stylesheet_scopes_every_new_rule_to_the_history_table`
reads the rules of the cell classes, and each new rule names `.history-table`.

**Alternative**: The Site column before the Action column. Rejected, because
the operator reads the capture and then its site. The Runs table also shows
its Site column beside the run identifier.

**Alternative**: A fixed pixel limit for each header in the browser journey.
Rejected, because the header width follows the font of the browser. The
journey instead compares the two tables in one browser at 1280 pixels. Each
header that fits in the table of one site must also fit in the table of every
site.

## R5. The sort

**Evidence**: The function `sortTableByColumn` of `portal.js` reads the header
and each cell by one index. The new header and the new cell share one index,
so the sort needs no script change. The function `compareCells` compares two
site texts as text.

## R6. The test identifier

**Decision**: Use `history-site-{capture_id}`. Add the constant
`SITE_TEST_ID_PREFIX` beside `DEVICE_TYPE_TEST_ID_PREFIX`. Add one row to
`specs/1823-upgrade-capture-portal/contracts/ui-testids.md`.

**Evidence**: No identifier of the portal starts with `history-site-`.

## R7. The render with no column value

**Decision**: The template reads each new value with a default. The column
default is false, the count default is 9, and the caption default is the
sentence of today. A render with no `history_columns` value then prints the
table of today.

**Evidence**: The unit tests of the layout and of the history view render the
template with no scope and no column value. One of them asserts the class
list `portal-table history-table`.
