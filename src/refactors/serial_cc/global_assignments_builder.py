"""Global assignment map builder extracted from high-complexity import manager method."""

import logging
from collections.abc import Callable
from typing import Any


class GlobalAssignmentsBuilderService:
    """Build global name-to-object assignments from imported modules."""

    @staticmethod
    def execute(imports: dict[str, Any], add_fallbacks_fn: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
        """Build and return global assignments dictionary using existing fallback handler."""
        global_vars: dict[str, Any] = {}

        for module_name, module_obj in imports.items():
            global_vars[module_name] = module_obj

            if module_name == "datetime":
                global_vars["timezone"] = getattr(module_obj, "timezone", None)
                global_vars["timedelta"] = getattr(module_obj, "timedelta", None)
            elif module_name == "concurrent.futures":
                global_vars["ThreadPoolExecutor"] = getattr(module_obj, "ThreadPoolExecutor", None)
                global_vars["as_completed"] = getattr(module_obj, "as_completed", None)
                global_vars["concurrent"] = module_obj
            elif module_name == "prettytable":
                global_vars["PrettyTable"] = getattr(module_obj, "PrettyTable", None)
            elif module_name == "numpy":
                global_vars["np"] = module_obj
            elif module_name == "tqdm":
                global_vars["tqdm"] = module_obj
            elif module_name == "collections":
                global_vars["defaultdict"] = getattr(module_obj, "defaultdict", None)
            elif module_name == "difflib":
                global_vars["SequenceMatcher"] = getattr(module_obj, "SequenceMatcher", None)
            elif module_name == "usaddress-scourgify":
                if module_obj:
                    try:
                        normalize_func = getattr(module_obj, "normalize_address_record", None)
                        if normalize_func:
                            global_vars["normalize_address_record"] = normalize_func
                        else:
                            from scourgify import normalize_address_record

                            global_vars["normalize_address_record"] = normalize_address_record
                    except (ImportError, AttributeError):
                        logging.debug("Could not import normalize_address_record from scourgify, using fallback")
            elif module_name == "rapidfuzz":
                if module_obj:
                    try:
                        fuzz_module = getattr(module_obj, "fuzz", None)
                        if fuzz_module:
                            global_vars["fuzz"] = fuzz_module
                        else:
                            from rapidfuzz import fuzz

                            global_vars["fuzz"] = fuzz
                    except (ImportError, AttributeError):
                        logging.debug("Could not import fuzz from rapidfuzz, using fallback")
            elif module_name == "mistapi":
                if module_obj:
                    global_vars["mistapi"] = module_obj
                    logging.debug("Added mistapi to global namespace")
            elif module_name == "paramiko":
                if module_obj:
                    global_vars["paramiko"] = module_obj
                    logging.debug("Added paramiko to global namespace")
            elif module_name == "redexpect":
                if module_obj:
                    global_vars["redexpect"] = module_obj
                    logging.debug("Added redexpect to global namespace")

        add_fallbacks_fn(global_vars)
        return global_vars
