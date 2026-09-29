# Feature Specification: Site Variable Audit

**Feature Branch**: `feat/3556-site-variable-audit`

**Created**: 2026-09-29

**Status**: Draft

**Input**: User description: "Menu 275 site variable coverage audit. A gateway template, a network template, or a WLAN can reference a site variable with the {{name}} syntax. A site that lacks that variable renders a broken configuration, and Mist rolls the device back after the five-minute check. Menu 149 checks one variable, wan2_interface. No operation checks every variable that every assigned template needs. SiteVariableAudit.csv: one row per site and missing variable with site name, template type, template name, variable name, and the field path where the template uses it. SiteVariableSummary.csv: one row per site with assigned templates, required variable count, defined variable count, missing count, and unused variable count. A console summary prints the site count with at least one missing variable."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find Sites With Missing Variables (Priority: P1)

A NOC engineer runs Menu 275 to audit all assigned gateway templates, network templates, and WLANs. The engineer receives a CSV file that lists each site and each variable that is required by an assigned template but is not defined for that site.

**Why this priority**: Missing site variables can make Mist roll back device configuration after the five-minute check. Operators need a full missing-variable list before they change templates or sites.

**Independent Test**: Run the operation in `--test` mode with fixture data that has at least one site missing a variable. Confirm that the operation does not prompt, writes `data/SiteVariableAudit.csv`, and lists the expected site, template, variable, and field path.

**Acceptance Scenarios**:

1. **Given** a site has an assigned template that references `{{wan_interface}}` and the site variable list does not include `wan_interface`, **When** Menu 275 runs, **Then** `SiteVariableAudit.csv` contains one row for that site and missing variable.
2. **Given** three sites are missing at least one required variable, **When** Menu 275 finishes, **Then** the console summary reports a missing-variable site count of three.
3. **Given** the operation runs in `--test`, **When** fixture data is available, **Then** the operation completes without an interactive prompt and writes both required CSV files under `data/`.

---

### User Story 2 - Trace Variable Use in Templates (Priority: P2)

A NOC engineer reviews where a missing variable is used. The audit identifies the template type, template name, variable name, and JSON field path for each missing variable. The scanner finds variables at any depth in a template body, including inside lists.

**Why this priority**: Operators must know which template field needs the variable so they can repair the correct site variable or template field.

**Independent Test**: Use a fixture template with `{{variable}}` tokens in nested objects and inside a list. Confirm that each token is found and that the audit row reports the correct JSON path for the field that uses the token.

**Acceptance Scenarios**:

1. **Given** a template contains `{{vlan_id}}` inside a nested list item, **When** the scanner runs, **Then** the scanner records the variable and the JSON path to that list item field.
2. **Given** a template contains multiple `{{name}}` tokens in different fields, **When** the scanner runs, **Then** each field path is available for reporting.
3. **Given** a template has no `{{name}}` token, **When** the scanner runs, **Then** the template adds no required variables for any site.

---

### User Story 3 - Summarize Required, Defined, Missing, and Unused Variables (Priority: P3)

A NOC engineer receives one summary row per site. The row shows assigned templates, required variable count, defined variable count, missing count, unused variable count, and unused variable names.

**Why this priority**: The summary helps operators find sites that need cleanup, not only sites that are broken. Unused variables can confuse future template work.

**Independent Test**: Use fixture data for a site that defines one variable that no assigned template uses. Confirm that `SiteVariableSummary.csv` counts that variable as unused and includes its name.

**Acceptance Scenarios**:

1. **Given** a site defines `old_vlan` and no assigned template uses `{{old_vlan}}`, **When** Menu 275 runs, **Then** the site summary counts `old_vlan` as unused and names it.
2. **Given** a site has assigned templates and all required variables are defined, **When** Menu 275 runs, **Then** the site has no audit rows and has a missing count of zero in the summary.
3. **Given** a site has no assigned gateway template, network template, or WLAN, **When** Menu 275 runs, **Then** the summary still includes the site with zero required variables and all defined variables counted as unused.

### Edge Cases

- A template field contains more than one token, such as `{{primary}}-{{backup}}`; each token is evaluated separately.
- The same variable appears more than once in the same assigned template; the required variable count counts the variable once per site, while audit rows keep the field path evidence for each missing use.
- A variable token appears inside a list, a nested object, a string with other text, or a repeated structure; the scanner still reports the JSON path of the field that contains the token.
- A site has no assigned templates; the site has zero required variables, zero missing variables, and all defined variables are unused.
- A site has assigned templates but no variables returned by the site variable search; every required variable for that site is missing.
- A template references a variable with surrounding spaces, such as `{{ name }}`; the scanner normalizes the variable name to `name`.
- A template has malformed brace text that is not a complete `{{name}}` token; the scanner ignores it and does not report a false variable.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Menu 275 MUST audit site variable coverage for assigned gateway templates, assigned network templates, and assigned WLANs.
- **FR-002**: The operation MUST run in `--test` with no prompt and write both output files under `data/`.
- **FR-003**: The operation MUST write `data/SiteVariableAudit.csv` with one row per site and missing variable use.
- **FR-004**: Each `SiteVariableAudit.csv` row MUST include site name, template type, template name, variable name, and the JSON field path where the assigned template uses the variable.
- **FR-005**: The operation MUST write `data/SiteVariableSummary.csv` with one row per site.
- **FR-006**: Each `SiteVariableSummary.csv` row MUST include site name, assigned templates, required variable count, defined variable count, missing count, unused variable count, and unused variable names.
- **FR-007**: The scanner MUST find a `{{variable}}` token at any depth of a gateway template, network template, or WLAN body.
- **FR-008**: The scanner MUST find a `{{variable}}` token inside a list and report the JSON path of the field that contains it.
- **FR-009**: A site whose assigned template needs a variable that the site variable search does not return for that site MUST appear in `SiteVariableAudit.csv`.
- **FR-010**: A variable that a site defines and that no assigned template uses MUST count as unused in the summary, and the summary MUST name it.
- **FR-011**: The operation MUST read each unique template one time per run.
- **FR-012**: The operation MUST NOT call per-site settings retrieval for each site as part of the audit.
- **FR-013**: The console summary MUST print the count of sites that have at least one missing variable.
- **FR-014**: The wiring manifest `specs/3556-site-variable-audit/wiring.md` MUST exist and include every section of the contract.
- **FR-015**: The release note fragment `changelog.d/issue-3556-site-variable-audit.md` MUST exist.
- **FR-016**: Output records MUST be deterministic so repeated runs with the same input produce the same rows and counts.
- **FR-017**: The operation MUST show clear user-facing errors when required organization or site data is unavailable.

### Acceptance Criteria from Issue 3556

- The operation runs in --test with no prompt and writes both files under data/.
- The scanner finds a {{variable}} token at any depth of a template body, including inside a list, and reports the JSON path of the field.
- A site whose assigned template needs a variable that searchOrgVars does not return for that site appears in SiteVariableAudit.csv.
- A variable that a site defines and that no assigned template uses counts as unused in the summary, and the summary names it.
- The scanner reads templates one time each and never calls getSiteSetting for each site.
- The wiring manifest specs/3556-site-variable-audit/wiring.md exists with every section of the contract.
- The release note fragment changelog.d/issue-3556-site-variable-audit.md exists.

### Key Entities *(include if feature involves data)*

- **Site**: A Mist site that can have assigned templates and site variables. Key attributes are site name, assigned template references, and defined site variable names.
- **Assigned Template**: A gateway template, network template, or WLAN that applies to a site. Key attributes are template type, template name, template body, and site assignments.
- **Variable Token**: A `{{name}}` reference found inside a template body. Key attributes are normalized variable name and JSON field path.
- **Missing Variable Finding**: Evidence that a site lacks a variable required by an assigned template. Key attributes are site name, template type, template name, variable name, and field path.
- **Site Variable Summary**: Per-site aggregate data. Key attributes are assigned templates, required variable count, defined variable count, missing count, unused variable count, and unused variable names.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In `--test`, the operation completes with zero interactive prompts and creates `SiteVariableAudit.csv` and `SiteVariableSummary.csv` under `data/`.
- **SC-002**: Fixture tests with variables in nested objects and lists find 100% of valid `{{variable}}` tokens and report the expected JSON field paths.
- **SC-003**: For fixture sites with missing required variables, 100% of expected missing variable uses appear in `SiteVariableAudit.csv` with site, template, variable, and field path evidence.
- **SC-004**: For fixture sites with unused variables, 100% of unused variable names appear in `SiteVariableSummary.csv` and the unused count matches the named variables.
- **SC-005**: The console missing-site count equals the number of distinct sites in `SiteVariableAudit.csv` for every test fixture.
- **SC-006**: Each unique template is read no more than one time per run, and the audit does not perform a per-site settings retrieval for every site.
- **SC-007**: The feature is ready for implementation only when `specs/3556-site-variable-audit/wiring.md` and `changelog.d/issue-3556-site-variable-audit.md` are present in the planned change set.

## Assumptions

- Menu 275 is the new menu entry for this audit.
- The audit scope is limited to gateway templates, network templates, and WLANs assigned to sites.
- The audit does not change Mist configuration. It only reads data, writes CSV reports, and prints a console summary.
- Site variables returned for a site are the source of truth for defined variables.
- Required variable count is the count of unique variable names required by all templates assigned to a site.
- Missing count is the count of unique required variable names that are not defined for the site.
- Audit rows can include more than one row for the same missing variable when different assigned template fields use that variable. This preserves the field path evidence.
- Unused variable count is the count of defined site variables that no assigned template uses.
- JSON paths use a consistent, human-readable format that identifies object fields and list positions.
