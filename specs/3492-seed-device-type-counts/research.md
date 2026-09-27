# Research: The browser seed captures hold the counts of a real capture

**Issue**: #3492
**Date**: 2026-09-27

## R1. The shipped writer of the count map

**Decision**: The seed builds its count map with the shipped function
`build_counts`. The seed gives the function one `CaptureSections` value with
the device index, the device records, and the client lists of the seed.

**Evidence**:

1. The function `_body_fields` in `src/upgrade_portal/capture/assembly.py`
   writes `"counts": build_counts(sections)`. No other code in the capture
   package writes the count map.
2. The function `build_counts` returns the nine keys of `COUNT_KEYS`, in the
   order of that tuple.
3. The function `_device_counts` counts the devices by state and by type. It
   reads the `status` field and the `type` field of each index entry.
4. The function `_type_counts` maps each type through `DEVICE_TYPE_COUNTS`.
   The map holds `gateway`, `switch`, and `ap`.
5. The dataclass `CaptureSections` holds four fields: `device_index`,
   `devices`, `clients`, and `extras`. The function `build_counts` reads the
   device index and the three client groups only.

A probe on 2026-09-27 built the count map of each seed with the builder. Each
of the five seeds gave 3 devices in total, 0 connected devices, and 3
disconnected devices. Each seed also gave 1 gateway, 1 switch, 1 access
point, 0 wired clients, and 3 wireless clients. The Tier 3 seed also gave 1
guest client. The other four seeds gave 0 guest clients.

**Alternatives**:

- Write the three type counts by hand. The seed then drifts from the builder
  again, and that drift is the defect of this issue. Rejected.
- Call the private function `_type_counts`. A private name can change without
  notice. The public builder is the contract of the stored shape. Rejected.

## R2. The Tier 3 seed adds a guest client after the base seed

**Decision**: The function `stand_in_tier3_capture` builds the count map
again after it sets the guest list.

**Evidence**:

1. The function `stand_in_tier3_capture` calls `stand_in_capture` first. It
   then replaces the guest list with one record.
2. The base count map comes from the base lists, so it counts no guest
   client.
3. The function `row_counts` in `src/upgrade_portal/app/routes/review.py`
   adds the three keys of `CLIENT_COUNT_KEYS` for the Clients cell of the
   history page. The cell of the Tier 3 row therefore reads 3 today. The real
   capture of the same lists reads 4.

**Alternatives**:

- Give the guest list to `stand_in_capture` as a new parameter. That function
  already has five parameters, which is the project limit. Four other seeds
  also call it. Rejected.
- Add the guest count by hand after the base map. That is a hand-written
  count, so it breaks FR-002. Rejected.

One helper in the seed file builds the count map from a capture document.
Both seed builders call it. The helper reads the builder through the module
name at call time, so a direct test can replace the builder with a marker.

## R3. The readers of the count map

**Decision**: No reader changes. The browser tests of each reader run after
the change.

| Reader | The value that it reads | The effect on the seeds |
| - | - | - |
| `device_type_text` in `review.py` | The three type counts | Each seed row reads "1 gateway, 1 switch, 1 access point". |
| `row_counts` in `review.py` | The total and the three client counts | The Tier 3 row reads 4 clients. The other rows keep 3. |
| The count list of `capture/capture.html` | The nine counts of the status record | A seed on the capture page shows the six device counts too. |
| `_counts_map` in `compare/render.py` | The total and the three client counts | A comparison of the Tier 3 seed adds the guest client. |

The inventory page reads the live device read of the site, and not a stored
capture. Its counts do not change.

The phrase of `device_type_text` joins the words of `DEVICE_TYPE_WORDS` with
a comma and a space. The phrase of one device of each type holds 35
characters: "1 gateway, 1 switch, 1 access point". The fallback text "No
device type" holds 14 characters.

## R4. The width of the real phrase

**Decision**: The CSS rule of the cell does not change in this issue. The
journey measures the fit and records the numbers. Issue #3495 holds the
finding.

**Evidence**:

1. The rule `.history-table .cell-device-type` in `portal.css` sets
   `overflow: hidden`, `text-overflow: ellipsis`, and `white-space: nowrap`.
   The row budget of issue #2106 needs this rule. A long phrase therefore
   clips on one line, and it never adds a line.
2. The `title` attribute of the cell holds the whole phrase.
3. The page with no site holds ten columns, and the Device types column gets
   12 percent of the width. Issue #3486 set that share.
4. The page of one site holds nine columns, and the Device types column gets
   18 percent of the width.

**Result**: The journey measured each seed row on 2026-09-27 in Microsoft
Edge. The phrase needs 268 pixels in each row. Each row stood 48 pixels or
less on each page at each width.

| Page | Window width | Cell width | Visible text |
| - | - | - | - |
| No site | 1024 pixels | 118 pixels | `1 gateway, ...` |
| No site | 1280 pixels | 149 pixels | `1 gateway, 1 sw...` |
| No site | 1440 pixels | 168 pixels | `1 gateway, 1 switc...` |
| One site | 1024 pixels | 177 pixels | `1 gateway, 1 switch,...` |
| One site | 1280 pixels | 223 pixels | `1 gateway, 1 switch, 1 acc...` |
| One site | 1440 pixels | 252 pixels | `1 gateway, 1 switch, 1 access ...` |

The phrase clips in each seed row on each page at each width. The old
fallback text "No device type" needed 130 pixels. It clipped on the page
with no site at 1024 pixels only.

A keyboard user and a touch user cannot reach a `title` attribute, so the
clipped words stay hidden from those users. Issue #3495 holds this finding.
At 1024 pixels on the page with no site, the capture identifier, the site
name, and the Started moment also clip. Issue #3495 names those cells too.
