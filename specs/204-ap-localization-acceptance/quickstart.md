# Quickstart: AP Localization Acceptance (Menu 204)

**Audience**: Developer implementing or reviewing this feature.

---

## What This Feature Does

Adds menu operation 204 to MistHelper. Operators can accept or reject
pending AP localization data (placement or orientation) for a specific
site map by calling the Mist `confirmSiteApLocalizationData` endpoint.

The operation follows the MistHelper destructive-operation safety model:
validate inputs → display elevated warning → require typed confirmation →
execute API call → export audit record.

---

## Files to Change

| File | Change |
|------|--------|
| `MistHelper.py` | Add `ApLocalizationManager` class (~80 lines); add `'204': confirm_site_ap_localization_data` to dispatch dict; add `'confirmSiteApLocalizationData'` to `ENDPOINT_PRIMARY_KEY_STRATEGIES` |
| `README.md` | Increment operation count 203 → 204; add row to Destructive menu table |
| `CHANGELOG.md` | New entry under `[Unreleased]` |
| `tests/unit/test_menu_204_ap_localization.py` | New test file (see Test Cases below) |

---

## API Reference

```python
import mistapi.api.v1.sites.maps as maps_api

response = maps_api.confirmSiteApLocalizationData(
    apisession,           # mistapi.APISession
    site_id,              # str: site UUID
    map_id,               # str: map UUID
    {
        "accept": True,           # bool: True=accept, False=reject
        "for": "placement",       # str: "placement" or "orientation"
        "macs": [],               # list[str]: AP MACs; empty = full map
    }
)
success = getattr(response, "status_code", None) == 200
```

---

## Implementation Skeleton

```python
class ApLocalizationManager:
    """Manages AP localization acceptance/rejection workflow for Menu 204."""

    ALLOWED_FOR_TYPES = frozenset({"placement", "orientation"})  # Valid localization types
    ACCEPT_PHRASE = "ACCEPT-LOCALIZATION"    # Typed phrase to accept
    REJECT_PHRASE = "REJECT-LOCALIZATION"    # Typed phrase to reject

    def confirm_site_ap_localization(self):
        """Entry point: full accept/reject workflow including safety gates and audit export."""
        logging.info("Starting Menu 204 - AP Localization Acceptance")  # Workflow start log
        inputs = self._prompt_inputs()  # Collect all required inputs from operator
        if not self._validate_inputs(inputs):  # Block on any validation failure
            self._export_audit_record(inputs, "cancelled", "validation_failed", "n/a")
            return
        action_label = "accept" if inputs["accept"] else "reject"  # Human-readable action name
        confirm_phrase = self.ACCEPT_PHRASE if inputs["accept"] else self.REJECT_PHRASE
        print(f"\n[!] DESTRUCTIVE: This will {action_label} AP localization data on the Mist cloud.")
        typed = safe_input(f"Type '{confirm_phrase}' to proceed: ", context="menu_204_confirmation")
        if typed.strip() != confirm_phrase:  # Confirmation gate - no API call without exact phrase
            print("  Cancelled - confirmation phrase did not match.")
            logging.info("Menu 204 cancelled - confirmation failed")  # Cancellation log
            self._export_audit_record(inputs, "cancelled", "confirmation_failed", "n/a")
            return
        if getattr(globals(), "TEST_MODE", False):  # Skip real call during automated test run
            print("[TEST MODE] Skipping confirmSiteApLocalizationData call")
            return
        import mistapi.api.v1.sites.maps as _maps_api  # Local import to avoid circular deps
        body = {"accept": inputs["accept"], "for": inputs["for_type"]}  # Build request body
        if inputs["macs"]:  # Only include macs field when operator provided specific APs
            body["macs"] = inputs["macs"]
        logging.info("Menu 204: calling confirmSiteApLocalizationData site=%s map=%s", inputs["site_id"], inputs["map_id"])
        try:
            response = _maps_api.confirmSiteApLocalizationData(  # Execute the acceptance action
                apisession, inputs["site_id"], inputs["map_id"], body
            )
            status = getattr(response, "status_code", "n/a")  # Extract HTTP status
        except Exception as api_err:  # Network or API error - record failure in audit log
            logging.error("Menu 204 API call failed: %s", api_err)
            status = "n/a"
        logging.debug("Menu 204 API response status=%s", status)  # Post-call result log
        success = (status == 200)  # 200 is the only success signal (empty body)
        print(f"  {action_label.capitalize()} {inputs['for_type']}: HTTP {status} ({'OK' if success else 'FAILED'})")
        self._export_audit_record(inputs, "executed", "", str(status))  # Always write audit record

    def _prompt_inputs(self):
        """Collect site_id, map_id, for_type, accept flag, and optional MACs from operator."""
        site_id = safe_input("Enter site ID: ", context="menu_204_site_id").strip()  # Site UUID
        map_id = safe_input("Enter map ID: ", context="menu_204_map_id").strip()  # Map UUID
        for_type = safe_input("Localization type (placement/orientation): ", context="menu_204_for_type").strip().lower()
        choice = safe_input("Accept or reject? (a/r): ", context="menu_204_choice").strip().lower()
        accept = (choice == "a")  # Any input other than 'a' is treated as reject
        macs_raw = safe_input("AP MACs to scope (comma-separated, blank=full map): ", context="menu_204_macs")
        macs = [m.strip() for m in macs_raw.split(",") if m.strip()]  # Split and strip MAC list
        return {"site_id": site_id, "map_id": map_id, "for_type": for_type, "accept": accept, "macs": macs}

    def _validate_inputs(self, inputs):
        """Return True when all required inputs pass validation; print guidance on failure."""
        if not inputs["site_id"]:  # site_id is mandatory
            print("  [ERROR] Site ID is required.")
            return False
        if not inputs["map_id"]:  # map_id is mandatory
            print("  [ERROR] Map ID is required.")
            return False
        if inputs["for_type"] not in self.ALLOWED_FOR_TYPES:  # for_type must be in allowed set
            print(f"  [ERROR] Localization type must be 'placement' or 'orientation', got: {inputs['for_type']!r}")
            return False
        return True  # All validation gates passed

    def _export_audit_record(self, inputs, outcome, cancel_reason, http_status):
        """Write a single audit record dict to the DataExporter for this action attempt."""
        from datetime import datetime  # Local import - only needed here
        macs_scope = ",".join(inputs.get("macs", [])) or "full_map"  # Normalise scope label
        record = [{  # Wrap in list - DataExporter expects a list of dicts
            "timestamp": datetime.utcnow().isoformat(),  # UTC timestamp for audit traceability
            "menu_operation": "204",  # Literal menu number for audit log filtering
            "site_id": inputs.get("site_id", ""),  # From operator input
            "map_id": inputs.get("map_id", ""),  # From operator input
            "for_type": inputs.get("for_type", ""),  # "placement" or "orientation"
            "action": "accept" if inputs.get("accept") else "reject",  # Human-readable action
            "macs_scope": macs_scope,  # Full MAC list or "full_map"
            "http_status": http_status,  # Response code or "n/a"
            "outcome": outcome,  # "executed" or "cancelled"
            "cancel_reason": cancel_reason,  # Reason code or empty string
        }]
        logging.info("Menu 204: exporting audit record outcome=%s", outcome)  # Pre-export log
        DataExporter.write_with_format_selection(  # Write to configured output backend
            record, "confirmSiteApLocalizationData", api_function_name="confirmSiteApLocalizationData"
        )
        logging.debug("Menu 204: audit record exported")  # Post-export log


def confirm_site_ap_localization_data():  # Menu 204: AP localization acceptance
    """Accept or reject pending AP localization data for a site map (Menu 204)."""
    ApLocalizationManager().confirm_site_ap_localization()  # Delegate to manager class
```

---

## Test Cases

```python
# tests/unit/test_menu_204_ap_localization.py
from unittest.mock import patch, MagicMock
import pytest
from MistHelper import ApLocalizationManager

class TestApLocalizationValidation:
    def test_empty_site_id_blocked(self):
        mgr = ApLocalizationManager()
        assert mgr._validate_inputs({"site_id": "", "map_id": "uuid", "for_type": "placement"}) is False

    def test_empty_map_id_blocked(self):
        mgr = ApLocalizationManager()
        assert mgr._validate_inputs({"site_id": "uuid", "map_id": "", "for_type": "placement"}) is False

    def test_invalid_for_type_blocked(self):
        mgr = ApLocalizationManager()
        assert mgr._validate_inputs({"site_id": "a", "map_id": "b", "for_type": "unknown"}) is False

    def test_valid_inputs_pass(self):
        mgr = ApLocalizationManager()
        assert mgr._validate_inputs({"site_id": "a", "map_id": "b", "for_type": "orientation"}) is True

class TestApLocalizationCallWiring:
    @patch("MistHelper.mistapi.api.v1.sites.maps.confirmSiteApLocalizationData")
    @patch("MistHelper.DataExporter.write_with_format_selection")
    @patch("MistHelper.safe_input")
    def test_accept_confirmation_invokes_api(self, mock_input, mock_export, mock_api):
        mock_input.side_effect = ["site-1", "map-1", "placement", "a", ""]
        mock_input.return_value = ApLocalizationManager.ACCEPT_PHRASE  # confirmation step
        mock_api.return_value = MagicMock(status_code=200)
        ApLocalizationManager().confirm_site_ap_localization()
        mock_api.assert_called_once()

    @patch("MistHelper.DataExporter.write_with_format_selection")
    @patch("MistHelper.safe_input")
    def test_wrong_confirmation_cancels(self, mock_input, mock_export):
        # All prompts return valid values except the confirmation phrase
        mock_input.side_effect = ["site-1", "map-1", "placement", "a", "", "WRONG"]
        mgr = ApLocalizationManager()
        with patch("mistapi.api.v1.sites.maps.confirmSiteApLocalizationData") as mock_api:
            mgr.confirm_site_ap_localization()
            mock_api.assert_not_called()
        # Audit record must still be written with outcome=cancelled
        mock_export.assert_called_once()
        args = mock_export.call_args[0][0][0]
        assert args["outcome"] == "cancelled"
        assert args["cancel_reason"] == "confirmation_failed"
```

---

## Deployment Checklist

After implementation:

- [ ] `python -m py_compile MistHelper.py` passes  
- [ ] `python -m ruff check MistHelper.py` passes  
- [ ] `python -m black --check MistHelper.py` passes  
- [ ] `pytest tests/unit/test_menu_204_ap_localization.py -v` all green  
- [ ] README operation count updated: 203 → 204  
- [ ] CHANGELOG entry added under `[Unreleased]`  
- [ ] Git commit: `version YY.MM.DD.HH.MM - add menu 204 AP localization acceptance`  
- [ ] Push to `main`, wait for CI, pull image, restart container  
