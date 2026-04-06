"""MistHelper_ssid_write.py
Standalone helpers for SSID Template write-phase (prepare and apply).
This module is intentionally light-weight and avoids importing MistHelper at module import
time to prevent circular imports. Runtime imports of MistHelper are performed inside
methods only when needed.
"""
from __future__ import annotations

import glob
import importlib
import json
import logging
import os
import time
from datetime import datetime
from typing import Any


class SSIDTemplateConsolidationManager:
    """Helper class to prepare and apply canonical SSID template requests.

    prepare_templates(dry_run=True):
        - Reads the latest CanonicalTemplates_DRYRUN_*.json (or CanonicalTemplates_*.json)
        - Produces CreateTemplateRequests_DRYRUN_{ts}.json (or CreateTemplateRequests_{ts}.json)

    apply_prepared_templates():
        - Reads the latest CreateTemplateRequests_*.json
        - Requires explicit textual confirmation ("APPLY") via MistHelper.InputUtils.safe_input when available
        - Attempts to create WLAN templates via mistapi, writing a results JSON
    """

    @staticmethod
    def _data_dir() -> str:
        root = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(root, "data")
        os.makedirs(data_dir, exist_ok=True)
        return data_dir

    @staticmethod
    def _find_latest_json(prefix: str) -> str | None:
        data_dir = SSIDTemplateConsolidationManager._data_dir()
        candidates = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.startswith(prefix) and f.endswith(".json")]
        if not candidates:
            return None
        candidates.sort()
        return candidates[-1]

    @staticmethod
    def _is_psk_wlan(wlan: dict[str, Any]) -> bool:
        """Heuristic to detect PSK (pre-shared key) WLANs. Returns True if PSK-like config detected."""
        if not isinstance(wlan, dict):
            return False
        # Common keys that indicate PSK-based WLAN
        psk_indicators = ["psk", "pre_shared_key", "passphrase", "wpa_passphrase", "wpa2_passphrase"]
        for key in psk_indicators:
            if key in wlan:
                return True
        # Some templates embed security under nested keys
        sec = wlan.get("security") or wlan.get("wpa") or wlan.get("auth")
        if isinstance(sec, dict):
            for key in psk_indicators:
                if key in sec:
                    return True
            # Some variants set method/type to 'psk' or 'wpa-psk'
            method = sec.get("method") or sec.get("type") or sec.get("auth_type")
            if isinstance(method, str) and "psk" in method.lower():
                return True
        # Last resort: check SSID profile flags
        if wlan.get("security_mode") and "psk" in str(wlan.get("security_mode")).lower():
            return True
        return False

    @staticmethod
    def prepare_templates(dry_run: bool = True) -> str:
        """Read canonical templates and produce create-template request JSONs.

        Returns the path to the created CreateTemplateRequests JSON file.
        """
        data_dir = SSIDTemplateConsolidationManager._data_dir()
        # Prefer DRYRUN canonical files, then fall back
        src = SSIDTemplateConsolidationManager._find_latest_json("CanonicalTemplates_DRYRUN_")
        if not src:
            src = SSIDTemplateConsolidationManager._find_latest_json("CanonicalTemplates_")
        if not src:
            raise FileNotFoundError("No CanonicalTemplates_*.json found in data/ - run canonicalize dry-run first")

        with open(src, "r", encoding="utf-8") as fh:
            canonical = json.load(fh)

        requests = []
        skipped = []

        for item in canonical:
            group_id = item.get("group_id") or item.get("id")
            wlan = item.get("canonical_wlan") or item.get("wlan") or {}

            # Skip empty or obviously invalid entries
            if not wlan or not isinstance(wlan, dict):
                skipped.append({"group_id": group_id, "reason": "empty_wlan"})
                continue

            if SSIDTemplateConsolidationManager._is_psk_wlan(wlan):
                skipped.append({"group_id": group_id, "reason": "psk_wlan"})
                continue

            # Build request body (API-compatible skeleton)
            body = {"wlan": wlan}

            req = {
                "group_id": group_id,
                "member_count": item.get("member_count", 1),
                "metadata": {
                    "ssids": item.get("ssids"),
                    "template_ids": item.get("template_ids"),
                    "template_names": item.get("template_names"),
                    "applies_site_names": item.get("applies_site_names"),
                    "sample_wlan_id": item.get("sample_wlan_id"),
                },
                "body": body,
            }

            requests.append(req)

        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_name = f"CreateTemplateRequests_{'DRYRUN_' if dry_run else ''}{ts}.json"
        out_path = os.path.join(data_dir, out_name)

        payload = {"created_at": datetime.utcnow().isoformat() + "Z", "requests": requests, "skipped": skipped}
        with open(out_path, "w", encoding="utf-8") as oh:
            json.dump(payload, oh, indent=2, default=str)

        logging.info("Prepared %d template requests (%d skipped) -> %s", len(requests), len(skipped), out_path)
        print(out_path)
        return out_path

    @staticmethod
    def apply_prepared_templates() -> str:
        """Apply a prepared CreateTemplateRequests_*.json to the Mist API.

        Requires explicit operator confirmation by typing 'APPLY'. Uses MistHelper.InputUtils.safe_input when available.
        Returns the path to the results JSON file.
        """
        data_dir = SSIDTemplateConsolidationManager._data_dir()
        # Find a prepared requests file (prefer non-dryrun if present)
        candidates = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.startswith("CreateTemplateRequests_") and f.endswith(".json")]
        if not candidates:
            raise FileNotFoundError("No CreateTemplateRequests_*.json found in data/")
        candidates.sort()
        req_file = candidates[-1]

        with open(req_file, "r", encoding="utf-8") as fh:
            payload = json.load(fh)

        requests = payload.get("requests", [])
        originally_skipped = payload.get("skipped", [])

        # Import MistHelper at runtime to access InputUtils and ConfigUtils and apisession
        mh = None
        InputUtils = None
        ConfigUtils = None
        apisession = None
        try:
            mh = importlib.import_module("MistHelper")
            InputUtils = getattr(mh, "InputUtils", None)
            ConfigUtils = getattr(mh, "ConfigUtils", None)
            apisession = getattr(mh, "apisession", None)
        except Exception:
            # MistHelper may not be importable in some test contexts; fall back to None
            mh = None

        # Get org id
        org_id = None
        if ConfigUtils:
            try:
                org_id = ConfigUtils.get_cached_or_prompted_org_id()
            except Exception:
                org_id = None

        if not org_id:
            # Ask user directly
            if InputUtils:
                org_id = InputUtils.safe_input("Enter organization ID: ", "org_id").strip()
            else:
                org_id = input("Enter organization ID: ").strip()

        if not org_id:
            raise ValueError("Organization ID is required to apply templates")

        # Confirmation
        if InputUtils:
            confirm = InputUtils.safe_input("Type 'APPLY' to proceed: ", "ssid_apply_confirm")
        else:
            confirm = input("Type 'APPLY' to proceed: ")
        if confirm != "APPLY":
            raise PermissionError("Operator did not provide required confirmation 'APPLY'")

        results_created = []
        results_failed = []
        results_skipped = list(originally_skipped)

        # Attempt to import mistapi lazily
        try:
            import mistapi
        except Exception as e:
            raise ImportError(f"mistapi library is required to apply templates: {e}")

        # Discover candidate create functions on mistapi.api.v1.orgs
        orgs_mod = getattr(mistapi.api.v1, "orgs", None)
        candidate_funcs = []
        if orgs_mod is not None:
            for mod_name in ("wlan_templates", "templates"):
                sub_mod = getattr(orgs_mod, mod_name, None)
                if sub_mod is None:
                    continue
                # Common function names
                for fn_name in ("createOrgWlanTemplate", "createOrgTemplate", "createTemplate"):
                    fn = getattr(sub_mod, fn_name, None)
                    if fn:
                        candidate_funcs.append(fn)
                # Also allow a single-argument create method name
                fn = getattr(sub_mod, "create", None)
                if fn:
                    candidate_funcs.append(fn)

        create_fn = candidate_funcs[0] if candidate_funcs else None
        if not create_fn:
            logging.error("No suitable create function found in mistapi.api.v1.orgs (wlan_templates/templates)")
            raise RuntimeError("MistAPI create function not found; cannot apply templates")

        # Apply each request
        for req in requests:
            group_id = req.get("group_id")
            body = req.get("body", {})
            wlan = body.get("wlan", {})

            if not wlan or SSIDTemplateConsolidationManager._is_psk_wlan(wlan):
                results_skipped.append({"group_id": group_id, "reason": "psk_or_empty"})
                continue

            try:
                # Call create function - function signatures vary, attempt (apisession, org_id, body) then (org_id, body)
                resp = None
                try:
                    resp = create_fn(apisession, org_id, body)
                except TypeError:
                    try:
                        resp = create_fn(org_id, body)
                    except TypeError:
                        resp = create_fn(body)

                status_code = getattr(resp, "status_code", None) or getattr(resp, "status", None) or 200
                data = getattr(resp, "data", None) or getattr(resp, "json", None) or None

                if status_code and int(status_code) in (200, 201, 202):
                    created_id = (data or {}).get("id") if isinstance(data, dict) else None
                    results_created.append({"group_id": group_id, "id": created_id, "status": status_code})
                else:
                    results_failed.append({"group_id": group_id, "status": status_code, "data": data})

            except Exception as error:
                logging.exception("Failed to create template for group %s: %s", group_id, error)
                results_failed.append({"group_id": group_id, "error": str(error)})

            # Throttle a little to be gentle with API
            time.sleep(0.3)

        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out_name = f"CreateTemplateResults_{ts}.json"
        out_path = os.path.join(data_dir, out_name)
        out_payload = {
            "applied_at": datetime.utcnow().isoformat() + "Z",
            "created": results_created,
            "failed": results_failed,
            "skipped": results_skipped,
            "source_requests_file": os.path.basename(req_file),
        }

        with open(out_path, "w", encoding="utf-8") as oh:
            json.dump(out_payload, oh, indent=2, default=str)

        logging.info("Apply completed: %d created, %d failed, %d skipped -> %s", len(results_created), len(results_failed), len(results_skipped), out_path)
        print(out_path)
        return out_path
