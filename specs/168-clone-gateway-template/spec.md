# Feature Specification: Clone Device Config to New Gateway Template (Menu 194)

## 1. Problem & Goal

### Problem
Operators frequently configure gateway devices (SRX/SSR) with local device-level overrides
in Mist — not via a gateway template. When the same configuration needs to be applied across
multiple sites or devices, there is no automated way to "promote" a device's local config into
a reusable gateway template. Engineers must manually reverse-engineer the device config and
recreate the template from scratch.

### Goal
Provide a **Clone Device Config to Gateway Template** menu operation (Menu 194) that:
1. Lets the user select a **site** from the org's site list
2. Shows all **gateways/routers** at that site and lets the user select one
3. Fetches the selected **device's local configuration** via the Mist API
   (`getSiteDevice` — returns device-level overrides, not template-inherited config)
4. Prompts for the new template's **type** (`standalone` or `spoke`)
5. Prompts for the new template's **name**
6. Prompts whether to use the **same hardware platform** (device model, for
   `gateway_matching`) as the source device, or to specify a different target model
7. Extracts the relevant config fields from the device, strips device-specific metadata,
   and calls `createOrgGatewayTemplate` to create the new template
8. Confirms success with the new template's ID and name

### Key Design Principle: Device Config, Not Template Config
The source of truth is the **device record** returned by `getSiteDevice`. This contains
the full configuration including all locally-applied overrides. Fields that belong to the
device record (MAC, serial, connected status, stats, site_id, etc.) are stripped before
creating the template payload. Configuration fields (port_config, ip_configs, dhcpd_config,
bgp_config, etc.) are preserved and become the template body.

### Non-Goals
- Cloning from an existing gateway template (use the existing template operations)
- Applying the new template to any sites or devices (separate operation)
- Bulk cloning (one device at a time)
- Merging multiple device configs into one template

---

## 2. Interfaces & Behavior

### Menu Number
**Menu 194** (extends Destructive range 154-193; first available slot beyond 193)

### Menu Category
**Destructive** (range 154-193) — because it creates a new configuration object that must be cleaned up if unwanted.

### User Prompts & Interaction Flow

```text
=== Clone Gateway Template ===

1. User selects Menu 168
   → Display: "Preparing to clone a gateway template..."
   → Fetch list of org gateway templates via listOrgGatewayTemplates()

2. System presents template selection menu:
   → "Select source template to clone:"
   → Display table: ID | Template Name | Type (spoke/standalone) | Created
   → Numbered list for quick selection
   → Include "Cancel" option

3. User selects a template
   → System fetches full template details via getOrgGatewayTemplate(template_id)
   → Display confirmation:
     "Source Template: {name}"
     "Type: {spoke|standalone}"
     "Gateway Matching: {match_model and/or match_role if present}"

4. Prompt for new template name:
   → "Enter new template name: "
   → Validate non-empty, unique (no duplicate names in org)
   → Suggest default: "{source_name}_clone" or "{source_name}_{YYYYMMDD}"

5. Prompt to modify hardware platform (if source has model-specific matching):
   → "Source template matches model: {source_model}"
   → "Modify hardware platform for cloned template? (y/N): "
   → If yes:
       - Show list of supported models (SRX3000-series, SRX5000-series, SSR320, SSR380, etc.)
       - Allow user to select new model or keep same
   → If no:
       - Preserve source model in gateway_matching rules

6. Confirm before creation:
   → Display summary:
     "Creating new template:"
     "Name: {new_name}"
     "Type: {spoke|standalone}"
     "Model matching: {model or 'same as source'}"
     "Proceed? (y/N): "

7. On confirmation:
   → Call createOrgGatewayTemplate(org_id, cloned_template_payload)
   → Log the API call and response
   → Display success/failure:
     "✓ Template cloned successfully!"
     "New Template ID: {template_id}"
     "New Template Name: {template_name}"
   → Export CSV with template details (optional post-creation)

8. On cancellation or failure:
   → Log reason
   → Display error message with remediation steps
```

### Error Handling

| Scenario | Response |
|----------|----------|
| No templates in org | "No gateway templates found in this organization" |
| User cancels template selection | "Operation cancelled" → return to main menu |
| Invalid new template name (empty) | "Template name cannot be empty. Please try again." |
| New name already exists | "Template name '{name}' already exists. Please choose a different name." |
| Fetch source template fails | "Failed to fetch source template details: {error}" + retry logic |
| Clone API call fails (validation error) | "Failed to create template: {api_error_message}" |
| Clone API call fails (network error) | Retry up to 3 times with exponential backoff; then fail |
| Unexpected exception | "An unexpected error occurred. Please check logs and contact support." |

### Output Format

**CSV Export** (optional, after successful clone):
```csv
field,source_value,cloned_value
template_id,{old_id},{new_id}
template_name,{old_name},{new_name}
template_type,{type},{type}
gateway_model_match,{model},{model_or_new_model}
ports_count,{count},{count}
ip_configs_count,{count},{count}
dhcp_pools_count,{count},{count}
bgp_rules_count,{count},{count}
ospf_rules_count,{count},{count}
extra_routes_count,{count},{count}
created_time,{epoch},{epoch}
```

**Logging:**
- `DEBUG`: Intermediate steps (template fetch, API call details)
- `INFO`: Success messages, template ID, cloned template details
- `ERROR`: Failures with full context for troubleshooting

---

## 3. Constraints & Performance

### Rate Limiting
- Single API calls: `listOrgGatewayTemplates()` (list), `getOrgGatewayTemplate()` (fetch detail), `createOrgGatewayTemplate()` (create)
- **Expected latency**: < 3 seconds for the entire workflow (source fetch + clone creation)
- **Retry logic**: 3 retries on transient failures with 5s exponential backoff (5s, 10s, 20s)
- **Timeout**: 120s per API call (use `API_REQUEST_TIMEOUT` global)

### Data Volume
- Template JSON can be large (~500KB for complex templates with many ports/policies)
- All data is in-memory during clone (no streaming)
- No pagination needed for templates (org typically has <50 templates)

### Resource Constraints
- Works in standard and fast modes
- Fast mode: Reduces retries to 2 (no backoff, fail faster)
- CPU/Memory: Negligible (single-threaded JSON serialization)

### Scalability Notes
- Linear with template complexity (larger templates take slightly longer to serialize/deserialize)
- No impact on site device assignment

---

## 4. Security & Secrets

### Authentication
- Uses existing `apisession` (module-level global) — no new auth needed
- Requires org-level privilege to create templates (same as existing "Create Template" operations)

### Data Handling
- **Secrets in payload**: Gateway templates may contain credentials (e.g., SNMP community strings, tunnel pre-shared keys)
  - **Policy**: Never log secrets to console or CSV
  - **Implementation**: Redact secrets in any debug/info output using a helper function `_redact_secrets(payload)`
  - **CSV export**: Exclude sensitive fields (PSK, SNMP keys) or replace with `[REDACTED]`
- **Logs**: Standard Python logging with `logging` module
  - Do NOT log the full template JSON (too noisy, contains secrets)
  - DO log field counts, template IDs, names, and API metadata
- **Environment Variables**: Only standard Mist API token (`MIST_APITOKEN`) — no new env vars

### Rate Limit Tokens
- No API token consumption concern beyond standard Mist API quotas
- Single org query (listOrgGatewayTemplates) + template fetch (getOrgGatewayTemplate) + create (createOrgGatewayTemplate) = 3 API calls

---

## 5. Data Model & API Calls

### Primary Key Strategy

```python
"createOrgGatewayTemplate": {
    "type": "natural_pk",
    "primary_key": ["id"],
    "indexes": ["org_id", "name", "type"],
    "unique_constraints": [],
    "description": "Gateway template clone results with stable UUID"
}
```

### API Calls Required

| Call | Method | Purpose | Input | Output |
|------|--------|---------|-------|--------|
| List templates | `mistapi.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates(apisession, org_id, limit=DEFAULT_API_PAGE_LIMIT)` | Get all templates in org | org_id | List of template summaries (id, name, type) |
| Fetch template | `mistapi.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate(apisession, org_id, template_id)` | Get full template details for cloning | org_id, template_id | Full template object (all config fields) |
| Create template | `mistapi.api.v1.orgs.gatewaytemplates.createOrgGatewayTemplate(apisession, org_id, body=template_payload)` | Create the cloned template | org_id, template_payload (JSON) | New template object (id, name, created_time) |

### Payload Construction

**Source Template Fields to Clone** (all nested objects):
```python
fields_to_clone = [
    "name",                    # Will be overwritten with user-provided name
    "type",                    # spoke or standalone
    "gateway_matching",        # Device model matching rules
    "port_config",             # All port definitions (ge-0/0/0, etc.)
    "ip_configs",              # Static/DHCP IP configurations per network
    "oob_ip_config",           # Out-of-band management IP
    "dhcpd_config",            # DHCP pool definitions
    "dnsOverride",             # Boolean flag
    "dns_servers",             # List of DNS servers
    "dns_suffix",              # List of DNS suffixes
    "ntpOverride",             # Boolean flag
    "ntp_servers",             # List of NTP servers
    "extra_routes",            # Static route definitions
    "extra_routes6",           # IPv6 static routes
    "router_id",               # BGP/OSPF router ID (auto-assigned if omitted)
    "bgp_config",              # BGP peer configurations
    "ospf_config",             # OSPF area configurations
    "vrf_config",              # VRF settings
    "vrf_instances",           # VRF instance definitions
    "path_preferences",        # Service path preferences
    "tunnel_configs",          # Tunnel configurations
    "tunnel_provider_options", # Provider-specific tunnel options
    "routing_policies",        # Custom routing policies
    "service_policies",        # QoS and security policies
    "idp_profiles",            # IDP profile references
    "additional_config_cmds"   # Custom Junos CLI commands
]
```

**Payload Structure for API Call**:
```python
cloned_payload = {
    "name": user_provided_name,  # NEW: User-specified name
    "type": source_template["type"],
    # All other fields copied exactly from source
    "gateway_matching": (
        {
            "enable": source_template.get("gateway_matching", {}).get("enable", True),
            "rules": adjust_model_matching_if_user_changed_platform(...)
        }
        if "gateway_matching" in source_template
        else None
    ),
    # ... all other nested fields ...
}
```

### Optional Platform Adjustment

If user chooses to change hardware platform:

```python
# Source template has:
#   gateway_matching.rules[0].match_model = "srx3000"
# User selects:
#   new_model = "ssr380"
# Cloned template will have:
#   gateway_matching.rules[0].match_model = "ssr380"

def adjust_model_matching(source_rules, old_model, new_model):
    """Replace model in gateway_matching rules if user changed platform."""
    adjusted_rules = []
    for rule in source_rules:
        adjusted_rule = dict(rule)  # Shallow copy
        if old_model and new_model and "match_model" in adjusted_rule:
            # Replace old model with new model in the match_model property
            adjusted_rule["match_model"] = new_model
        adjusted_rules.append(adjusted_rule)
    return adjusted_rules
```

---

## 6. Acceptance Criteria

### Functional Requirements
- [x] User can select an existing gateway template from the org inventory
- [x] User receives clear feedback on template selection (show template name, type, model matching)
- [x] User can enter a new template name (validated for empty and uniqueness)
- [x] User can optionally change the hardware platform (device model) matching criteria
- [x] System clones the template with all configuration fields preserved
- [x] Cloned template is immediately queryable via `listOrgGatewayTemplates()`
- [x] Cloned template has a unique UUID ID (generated by API)
- [x] Cloned template has creation timestamp set correctly
- [x] Operator receives success confirmation with new template ID and name
- [x] Operator can export clone details to CSV (optional)

### Error Handling
- [x] Gracefully handle "no templates in org" case
- [x] Validate new template name is non-empty
- [x] Validate new template name is unique within the org
- [x] Retry on transient API failures (up to 3 times)
- [x] Display clear error messages with context for troubleshooting

### Logging & Observability
- [x] Log template selection decision at INFO level
- [x] Log full API request/response (template details) at DEBUG level
- [x] Log API errors with full context at ERROR level
- [x] Do NOT log secrets (PSK, SNMP keys, etc.) to console or logs
- [x] Record operation timing (elapsed time for the entire workflow)

### User Experience
- [x] Menu display is clear (option 168 appears in Destructive menu)
- [x] Prompts are unambiguous and use consistent capitalization/formatting
- [x] Error messages suggest remediation steps
- [x] Confirmation prompts use "y/N" format (default = No)

### Data Integrity
- [x] Source template is not modified
- [x] All nested configuration objects are deep-copied (not referenced)
- [x] CSV export matches the expected schema (from Section 2)

---

## 7. Implementation Notes (AI Hints)

### Pseudocode / Algorithm

```python
def clone_gateway_template():
    # Step 1: List and select source template
    templates = fetch_all_templates(org_id)  # listOrgGatewayTemplates
    if not templates:
        print("No templates available")
        return False
    
    source_template = user_selects_template(templates)
    if not source_template:
        return False  # User cancelled
    
    # Step 2: Fetch full template details
    full_template = fetch_template_details(org_id, source_template["id"])
    
    # Step 3: Prompt for new name
    while True:
        new_name = user_input("Enter new template name: ")
        if not new_name:
            print("Name cannot be empty")
            continue
        if name_exists_in_org(new_name):
            print("Name already exists")
            continue
        break
    
    # Step 4: Optional model change
    if has_model_matching(full_template):
        if user_wants_to_change_model():
            new_model = user_selects_model()
            adjust_gateway_matching(full_template, old_model=..., new_model=new_model)
    
    # Step 5: Confirm
    if not user_confirms_clone(full_template, new_name):
        return False
    
    # Step 6: Clone via API
    cloned_payload = build_clone_payload(full_template, new_name)
    result = create_template(org_id, cloned_payload)  # createOrgGatewayTemplate
    
    # Step 7: Report success
    print(f"✓ Cloned! New ID: {result['id']}")
    export_csv_if_requested(result)
    return True
```

### Class Structure (No Wrappers)

Add to existing `<main class handling templates>` or create new class:

```python
class GatewayTemplateCloner:
    """Encapsulates gateway template cloning logic."""
    
    def __init__(self, apisession, org_id, safe_input=None, output_manager=None):
        self.apisession = apisession
        self.org_id = org_id
        self.safe_input = safe_input or InputUtils.safe_input
        self.output_manager = output_manager  # For CSV export
    
    def list_templates(self):
        """Fetch all templates in the org."""
        logging.info("Fetching gateway templates for org %s", self.org_id)
        # Call listOrgGatewayTemplates
        # Return list sorted by name
    
    def get_template_details(self, template_id):
        """Fetch full template config."""
        logging.info("Fetching template details for %s", template_id)
        # Call getOrgGatewayTemplate
    
    def prompt_for_new_name(self, source_name):
        """Get and validate new template name."""
        # Interactive loop until valid name entered
        # Check uniqueness via existing name list
    
    def adjust_platform_matching(self, template, old_model, new_model):
        """Modify gateway_matching rules for new platform."""
        # Adjust match_model property in gateway_matching.rules
    
    def build_clone_payload(self, source_template, new_name, new_model=None):
        """Construct payload for createOrgGatewayTemplate."""
        # Deep copy all fields
        # Set name to new_name
        # Optionally adjust model matching
        # Return JSON-safe dict
    
    def clone(self):
        """Main workflow."""
        # 1. List, select
        # 2. Confirm
        # 3. Clone
        # 4. Report
```

### Files to Modify

1. **MistHelper.py**:
   - Add `GatewayTemplateCloner` class (or integrate into existing template handler)
   - Add Menu 168 dispatcher in main menu loop
   - Call `clone_gateway_template()` function
   - Add to `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict entry for "createOrgGatewayTemplate"

2. **README.md**:
   - Update menu operation count: 193 (no change, just confirming)
   - Add Menu 168 to the Destructive (154-193) section:
     ```
     168 | Clone Gateway Template | Duplicate gateway template with new name | Click
     ```

3. **CHANGELOG.md**:
   - Add entry with version YY.MM.DD.HH.MM format:
     ```
     ### Added
     - Menu 168: Clone Gateway Template - duplicate existing gateway template with optional platform change
     ```

### Risk Hotspots

1. **Secrets in Logs**: Ensure PSK, SNMP keys are redacted using `_redact_secrets()` helper
2. **Deep Copy Semantics**: Nested dicts must be truly independent (use `copy.deepcopy()` if needed)
3. **Model Matching Logic**: Verify `gateway_matching.rules` structure matches API schema
4. **API Rate Limiting**: Multiple listOrgGatewayTemplates calls on retry could hit limits
5. **Name Collision**: Check uniqueness before sending to API (API will reject duplicate names)

### Testing Strategy

**Unit Tests** (pytest):
- Test `build_clone_payload()` with various template structures
- Test model adjustment logic with different rule configurations
- Test name validation (empty, duplicate, valid)

**Integration Tests**:
- Clone a real template in a test org
- Verify cloned template is identical except for name/ID
- Change platform and verify gateway_matching is updated
- Export CSV and verify schema

**Manual E2E Test**:
- Run Menu 168 against live org
- Clone a simple template
- Clone a complex template with BGP/OSPF
- Attempt duplicate name (should fail)
- Verify cloned template is queryable in Menu 12 (List Templates)

---

## 8. UI/UX Notes

### Menu Display
```
================  DESTRUCTIVE OPERATIONS (163-167, 168)  ================
163 - Create/Update Gateway Template
164 - Delete Gateway Template
165 - Import Org Bulk Config
166 - Test Firmware on Device
167 - Export Inventory for Firmware Upgrade
**168 - Clone Gateway Template**  ← NEW
================================================================================
```

### Selection Table Format
```
─────────────────────────────────────────────────────────────────────────────
 ID │ Template Name           │ Type         │ Model Match         │ Updated
─────────────────────────────────────────────────────────────────────────────
  1 │ Corporate-Core-SRX      │ spoke        │ srx3000-series      │ 2025-05-20
  2 │ Branch-Basic            │ standalone   │ ssr380              │ 2025-05-18
  3 │ Remote-Office-HighAvail │ spoke        │ srx5000-series      │ 2025-05-15
─────────────────────────────────────────────────────────────────────────────
Enter selection (1-3 or 0 to cancel): _
```

### Confirmation Prompt Format
```
===============================================================================
CONFIRM: Clone Gateway Template
===============================================================================
Source:              Corporate-Core-SRX (spoke)
New Name:            Corporate-Core-SRX_clone
Platform Model:      srx3000-series (unchanged)
New Org:             Production (org_id: abc1234...)

This will create a new template with identical configuration.
Proceed? (y/N): _
```

---

## 9. External Resources

- Mist API Docs (OpenAPI): `documentation/mist-api-openapi3json.json`
  - Schema: `gateway_template` (line ~416404)
  - Schema: `gateway_matching_rule` (line ~415440)
  - Operation: `createOrgGatewayTemplate` (POST /orgs/{org_id/gatewaytemplates)

- Code References:
  - Similar template operations: Menu 163-167 in MistHelper.py
  - Example listing: `listOrgGatewayTemplates()` call pattern
  - Example creation: `createOrgGatewayTemplate()` call pattern

---

## Checklist for Implementation

- [ ] Class `GatewayTemplateCloner` created in MistHelper.py
- [ ] Menu 168 dispatcher added to main menu loop
- [ ] `clone_gateway_template()` function implemented
- [ ] User prompts match spec exactly (wording, format, defaults)
- [ ] Error messages include remediation steps
- [ ] Secrets redacted in logs (PSK, SNMP keys, tunnel PSKs)
- [ ] CSV export schema matches section 2
- [ ] All API calls use retry logic (3 retries, exponential backoff)
- [ ] Logging levels correct (DEBUG for details, INFO for progress, ERROR for failures)
- [ ] README.md updated with Menu 168 description
- [ ] CHANGELOG.md entry added (YY.MM.DD.HH.MM format)
- [ ] ENDPOINT_PRIMARY_KEY_STRATEGIES updated (if not already present)
- [ ] Unit tests written (payload building, name validation, model adjustment)
- [ ] Integration test passes (clone real template in test org)
- [ ] Manual E2E test passes (all scenarios)
- [ ] Code review: no new global variables, no wrappers, follows 5-item rule
- [ ] Type hints added for all function signatures
- [ ] Inline comments on every line of generated code
- [ ] Action logging before/after API calls
- [ ] All quality gates pass (pytest, mypy, black, ruff)
