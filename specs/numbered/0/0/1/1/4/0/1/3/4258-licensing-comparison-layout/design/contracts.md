# UI Contract

- The page extends the shared shell and provides feature-local stylesheet and script blocks.
- Organization checkboxes expose names, selection counts, Select All, and Refresh controls.
- Comparison columns show organization, status, APs, switches, gateways, total devices, and license pairs.
- License headers provide accessible descriptions with native tooltips.
- A magenta totals row and four summary cards use the same normalized data.
- Manual rows and purchases use labeled integer fields and stable test selectors.
- Remaining balances show purchased, used, and remaining values. Catalog components remain visible.
- All API values enter the DOM through `textContent`, attribute properties, or input values.
- POST requests retain the shared CSRF token. Export uses the existing shared endpoint.
- Failed discovery, comparisons, and exports show explicit status. Failed endpoints do not become zeros.
- Existing transport and authorization tests must remain green.
