"""PK Strategy Probe for MistHelper.

Makes live API calls against the Mist API for a list of operationIds that are
NOT yet in ENDPOINT_PRIMARY_KEY_STRATEGIES, inspects the first real response
record, and recommends the correct strategy entry.

Usage:
    python scripts/probe_pk_strategy.py --limit 1 listOrgDevices listOrgWlans ...

    # Or read operationIds from a file (one per line):
    python scripts/probe_pk_strategy.py --from-file missing_ops.txt

    # Pipe directly from gap report:
    python scripts/probe_pk_strategy.py --all-library-funcs

Output:
    Prints a ready-to-paste Python dict block for ENDPOINT_PRIMARY_KEY_STRATEGIES
    and writes it to scripts/pk_strategy_suggestions.py for review.

How PK strategy is determined from a live response record:
    1. Has 'id' field AND no 'timestamp'             -> natural_pk  (stable entity)
    2. Has 'id' AND 'timestamp'                      -> composite_pk (event/log record)
    3. Has 'timestamp' but no 'id'                   -> composite_pk (time-series, pick stable fields)
    4. Has numeric-dominant top-level fields          -> timeseries_pk
    5. None of the above                             -> auto_increment_with_unique
"""

import argparse
import importlib
import inspect
import json
import logging
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: ensure project root is on sys.path so MistHelper dotenv loads
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent  # navigate up from scripts/ to repo root
sys.path.insert(0, str(REPO_ROOT))  # prepend repo root so local imports work

# ---------------------------------------------------------------------------
# Load .env early — before argparse evaluates os.environ.get() defaults
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv as _load_dotenv  # type: ignore[import-untyped]

    _load_dotenv(REPO_ROOT / ".env")  # load project .env into os.environ NOW
except ImportError:
    pass  # dotenv optional — env vars may already be set

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Field-presence heuristics for strategy classification
# ---------------------------------------------------------------------------

# Fields that indicate this record is a stable entity with a UUID primary key
_NATURAL_PK_SIGNALS = {"id"}

# Fields that strongly suggest time-series / event data
_TIMESERIES_SIGNALS = {
    "timestamp",
    "ts",
    "time",
}  # created_time/modified_time are metadata on entities, not event timestamps

# Numeric-heavy field name patterns suggesting Redis TimeSeries routing
_NUMERIC_FIELD_PATTERNS = {
    "bytes",
    "packets",
    "errors",
    "util",
    "rate",
    "latency",
    "jitter",
    "loss",
    "rssi",
    "snr",
    "uptime",
    "count",
}

# Fields that are reliable index candidates in entity records
_GOOD_INDEX_CANDIDATES = {
    "org_id",
    "site_id",
    "mac",
    "serial",
    "model",
    "type",
    "name",
    "hostname",
    "status",
    "version",
}


# ---------------------------------------------------------------------------
# ResponseAnalyzer
# ---------------------------------------------------------------------------


class ResponseAnalyzer:
    """Inspect one response record and classify the recommended PK strategy."""

    def classify(self, record: dict, op_id: str) -> dict:
        """Return a complete strategy dict for one inspected response record."""
        logging.info("Classifying response record for %s ...", op_id)  # log before analysis
        fields = set(record.keys())  # top-level keys in the real API response
        strategy = self._choose_strategy(fields)  # pick strategy type based on heuristics
        pk_fields = self._pick_pk_fields(fields, strategy)  # decide which fields form the PK
        indexes = sorted(fields & _GOOD_INDEX_CANDIDATES)  # common useful index candidates
        description = self._build_description(op_id, strategy, fields)  # human-readable desc
        logging.debug(
            "Classified %s as %s with pk=%s",
            op_id,
            strategy,
            pk_fields,
        )  # log classification result
        return {
            "type": strategy,
            "primary_key": pk_fields,
            "indexes": indexes,
            "unique_constraints": [],
            "description": description,
            "_probe_fields": sorted(fields),  # diagnostic: full field list from live response
        }

    def _choose_strategy(self, fields: set) -> str:
        """Apply heuristics to select the right strategy type string."""
        has_id = bool(fields & _NATURAL_PK_SIGNALS)  # check for stable UUID field
        has_ts = bool(fields & _TIMESERIES_SIGNALS)  # check for timestamp-like fields
        numeric_hits = sum(  # count numeric-pattern field hits
            1 for f in fields if any(pat in f.lower() for pat in _NUMERIC_FIELD_PATTERNS)
        )
        if has_ts and numeric_hits >= 2:
            return "timeseries_pk"  # Redis TimeSeries: has timestamp + multiple numeric metrics
        if has_id and has_ts:
            return "composite_pk"  # event/log record: has both UUID and timestamp
        if has_id:
            return "natural_pk"  # stable entity: UUID present, no timestamp
        if has_ts:
            return "composite_pk"  # time-series without id: use timestamp + stable fields
        return "auto_increment_with_unique"  # no stable key found: fall back to internal id

    def _pick_pk_fields(self, fields: set, strategy: str) -> list[str]:
        """Choose which fields form the composite or natural primary key."""
        if strategy == "natural_pk":
            return ["id"]  # UUID is always sufficient alone
        if strategy in ("composite_pk", "timeseries_pk"):
            pk = []  # build ordered composite key
            if "id" in fields:
                pk.append("id")  # id first if present
            ts_field = next(  # pick first timestamp-like field
                (f for f in ("timestamp", "ts", "time") if f in fields), None
            )
            if ts_field:
                pk.append(ts_field)  # add timestamp to composite key
            # Add one stable discriminator if id is missing
            if "id" not in fields:
                for candidate in ("mac", "device_id", "site_id", "org_id"):
                    if candidate in fields:
                        pk.insert(0, candidate)  # prepend stable discriminator
                        break
            return pk if pk else ["misthelper_internal_id"]  # final fallback
        return ["misthelper_internal_id"]  # auto-increment: internal id only

    @staticmethod
    def _build_description(op_id: str, strategy: str, fields: set) -> str:
        """Generate a one-line description string for the strategy entry."""
        field_sample = ", ".join(sorted(fields)[:5])  # first 5 fields as sample
        type_labels = {
            "natural_pk": "stable UUID entities",
            "composite_pk": "event/log time-series records",
            "timeseries_pk": "numeric metrics for Redis TimeSeries",
            "auto_increment_with_unique": "no stable key — internal id assigned",
        }
        label = type_labels.get(strategy, strategy)  # human-readable strategy label
        return f"{op_id} — {label} (sample fields: {field_sample})"


# ---------------------------------------------------------------------------
# MistApiProbe
# ---------------------------------------------------------------------------


class MistApiProbe:
    """Call the mistapi SDK for a given operationId and return the first record.

    SAFETY: Only read-only (GET) operationIds are allowed. Any operationId whose
    name starts with a mutating verb is refused before a network call is made.
    """

    # Verb prefixes that unambiguously indicate a mutating API call
    _MUTATING_PREFIXES = (
        "create",
        "update",
        "delete",
        "add",
        "remove",
        "set",
        "enable",
        "disable",
        "import",
        "upload",
        "send",
        "start",
        "stop",
        "cancel",
        "apply",
        "clear",
        "replace",
        "upgrade",
        "reboot",
        "assign",
        "unassign",
        "invite",
        "revoke",
    )

    def __init__(self, mist_session) -> None:
        self.session = mist_session  # authenticated mistapi APISession

    @classmethod
    def is_read_only(cls, op_id: str) -> bool:
        """Return True only if the operationId verb indicates a safe read operation."""
        name_lower = op_id[0].lower() + op_id[1:]  # normalise first char to lowercase
        return not any(name_lower.startswith(p) for p in cls._MUTATING_PREFIXES)

    def fetch_first_record(self, op_id: str, context: dict) -> dict | None:
        """Find, call, and return the first record from a mistapi function."""
        if not self.is_read_only(op_id):
            logging.warning(
                "SKIPPED %s — mutating operationId refused (read-only probe only)", op_id
            )  # refuse to call any write/delete/mutating operation
            return None  # hard stop: no network call made

        logging.info("Probing %s ...", op_id)  # log before API call
        func = self._resolve_function(op_id)  # locate SDK function by name
        if func is None:
            logging.warning("Could not locate mistapi function for %s", op_id)
            return None  # skip unknown operationIds

        kwargs = self._build_kwargs(func, context)  # build minimal call arguments
        logging.debug("Calling %s with kwargs %s", op_id, list(kwargs.keys()))

        try:
            response = func(**kwargs)  # invoke the SDK function
        except Exception as exc:
            logging.error("API call failed for %s: %s", op_id, exc)
            return None  # skip on any API error

        logging.debug("Got response type %s", type(response).__name__)
        return self._extract_first_record(response, op_id)  # pull first record from response

    def _resolve_function(self, op_id: str):
        """Walk mistapi.api.v1 to find the function matching op_id."""
        import pkgutil  # local import — only needed here

        import mistapi.api.v1 as v1  # mistapi SDK root package  # noqa: I001

        for module_info in pkgutil.walk_packages(v1.__path__, v1.__name__ + "."):
            try:
                mod = importlib.import_module(module_info.name)  # dynamic import of sub-module
                func = getattr(mod, op_id, None)  # look up function by exact name
                if func is not None and callable(func):
                    return func  # return first match found
            except Exception:
                continue  # skip un-importable modules
        return None  # not found in any module

    def _build_kwargs(self, func, context: dict) -> dict:
        """Build the minimal kwargs needed to call a mistapi function."""
        sig = inspect.signature(func)  # inspect function signature
        kwargs: dict = {"mist_session": self.session}  # always required first argument

        for param_name, param in sig.parameters.items():
            if param_name == "mist_session":
                continue  # already added above
            if param_name in context:
                kwargs[param_name] = context[param_name]  # inject from caller-provided context
            elif param.default is inspect.Parameter.empty:
                # Required param not in context: try to look up from env
                env_key = f"MIST_{param_name.upper()}"
                env_val = os.environ.get(env_key)
                if env_val:
                    kwargs[param_name] = env_val  # use env var fallback
                else:
                    logging.warning(
                        "Required param '%s' for %s not in context or env (%s)",
                        param_name,
                        func.__name__,
                        env_key,
                    )  # warn but continue
            elif param_name in ("limit", "page"):
                kwargs[param_name] = 1  # always request minimal page size

        return kwargs  # return assembled kwargs dict

    @staticmethod
    def _extract_first_record(response, op_id: str) -> dict | None:
        """Pull the first dict record out of a mistapi APIResponse."""
        data = None
        if hasattr(response, "data"):
            data = response.data  # standard mistapi .data accessor
        elif isinstance(response, dict):
            data = response  # direct dict response
        elif isinstance(response, (list, tuple)) and response:
            data = response[0]  # list response: take first item

        if isinstance(data, dict):
            # Many list endpoints wrap results in a 'results' key
            if "results" in data and isinstance(data["results"], list) and data["results"]:
                logging.debug("Unwrapping 'results' array for %s", op_id)
                return data["results"][0]  # return first item in results[]
            return data  # return the dict itself

        if isinstance(data, list) and data:
            return data[0] if isinstance(data[0], dict) else None  # first item if list

        logging.warning("No usable record found in response for %s", op_id)
        return None  # no usable record found


# ---------------------------------------------------------------------------
# SuggestionWriter
# ---------------------------------------------------------------------------


class SuggestionWriter:
    """Format and write the probed strategy suggestions as Python source."""

    OUTPUT_PATH = REPO_ROOT / "scripts" / "pk_strategy_suggestions.py"  # output file path

    def write(self, suggestions: dict[str, dict]) -> None:
        """Write all suggestions to pk_strategy_suggestions.py for review."""
        logging.info(
            "Writing %d strategy suggestions to %s",
            len(suggestions),
            self.OUTPUT_PATH,
        )  # log before file write
        lines = [
            '"""Auto-generated PK strategy suggestions from probe_pk_strategy.py.',
            "",
            "Review each entry, adjust indexes/pk fields as needed,",
            "then paste into ENDPOINT_PRIMARY_KEY_STRATEGIES in MistHelper.py.",
            '"""',
            "",
            "SUGGESTED_PK_STRATEGIES = {",
        ]
        for op_id, strategy in sorted(suggestions.items()):
            probe_fields = strategy.pop("_probe_fields", [])  # remove diagnostic field before output
            lines.append(f"    # Live response fields: {probe_fields}")
            lines.append(f"    {json.dumps(op_id)}: {{")
            for key, value in strategy.items():
                lines.append(f"        {json.dumps(key)}: {json.dumps(value)},")
            lines.append("    },")
        lines.append("}")
        lines.append("")
        self.OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")  # write to disk
        logging.info("Written to %s — review before pasting into MistHelper.py", self.OUTPUT_PATH)

    def print_summary(self, suggestions: dict[str, dict]) -> None:
        """Print a console summary table of strategy type counts."""
        counts: dict[str, int] = {}  # count per strategy type
        for strategy in suggestions.values():
            stype = strategy.get("type", "unknown")  # get type string from strategy
            counts[stype] = counts.get(stype, 0) + 1  # increment count
        print("\n--- PK Strategy Suggestion Summary ---")
        for stype, count in sorted(counts.items()):
            print(f"  {stype:35s}: {count:3d}")  # print aligned summary row
        print(f"  {'TOTAL':35s}: {sum(counts.values()):3d}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _load_mist_session():
    """Create an authenticated mistapi session (dotenv already loaded at module level)."""
    try:
        import mistapi  # type: ignore[import]

        mist_session = mistapi.APISession()  # create session from env/config
        mist_session.login()  # authenticate with Mist API
        logging.info("Authenticated mistapi session established")
        return mist_session
    except Exception as exc:
        logger.error("Could not create mistapi session: %s", exc)
        sys.exit(1)  # abort: can't probe without auth


def _unwrap_list(data) -> list:
    """Normalize a mistapi response data value into a plain list of records."""
    if isinstance(data, list):
        return data  # already a flat list
    if isinstance(data, dict):
        return data.get("results", [])  # unwrap paginated results array
    return []  # nothing usable


def _mod_call(module_path: str, func_name: str, *args, **kwargs):
    """Import a mistapi module by dotted path and call one function from it."""
    mod = importlib.import_module(module_path)  # dynamic import by full dotted path
    func = getattr(mod, func_name)  # look up the function by name
    return func(*args, **kwargs)  # call and return the raw APIResponse


def _detect_org_id(context: dict, mist_session) -> None:
    """Fill context['org_id'] from the authenticated session's first org privilege."""
    if context.get("org_id"):
        return  # already set, skip
    try:
        resp = _mod_call("mistapi.api.v1.self.self", "getSelf", mist_session)  # fetch /api/v1/self
        data = getattr(resp, "data", resp)  # unwrap response object
        privs = data.get("privileges", []) if isinstance(data, dict) else []  # get privilege list
        if privs:
            context["org_id"] = privs[0].get("org_id", "")  # use first org in privileges
            logging.info("Auto-detected org_id: %s", context["org_id"])  # log resolved value
    except Exception as exc:
        logging.warning("Could not auto-detect org_id: %s", exc)  # non-fatal, warn and continue


def _detect_site_id(context: dict, mist_session) -> None:
    """Fill context['site_id'], preferring any site named 'morrison' for richer device data."""
    if context.get("site_id") or not context.get("org_id"):
        return  # already set or no org_id to query from
    try:
        resp = _mod_call("mistapi.api.v1.orgs.sites", "listOrgSites", mist_session, context["org_id"])
        sites = _unwrap_list(getattr(resp, "data", resp))  # normalize to list
        target = next((s for s in sites if "morrison" in s.get("name", "").lower()), None)  # prefer morrison house
        target = target or (sites[0] if sites else None)  # fallback to first site
        if target:
            context["site_id"] = target.get("id", "")  # store site UUID
            logging.info("Auto-detected site_id: %s (%s)", context["site_id"], target.get("name", ""))
    except Exception as exc:
        logging.warning("Could not auto-detect site_id: %s", exc)  # non-fatal


def _detect_site_resources(context: dict, mist_session) -> None:
    """Fill device_id, device_mac, map_id, wlan_id, client_mac from the site."""
    site_id = context.get("site_id")
    if not site_id:
        return  # can't query site resources without site_id

    _discover_from_site(context, mist_session, site_id)  # devices, maps, wlans, clients
    _discover_clients(context, mist_session, site_id)  # wireless clients (may be empty)


def _discover_from_site(context: dict, mist_session, site_id: str) -> None:
    """Fetch device_id/mac, map_id, and wlan_id from one site."""
    _fetch_first(
        context,
        mist_session,
        "device_id",
        "mistapi.api.v1.sites.devices",
        "listSiteDevices",
        site_id,
        type="all",
        limit=1,
    )  # first device (any type)
    if context.get("device_id"):
        context.setdefault("device_mac", "")  # device_mac already set by _fetch_first below
    _fetch_first(
        context, mist_session, "map_id", "mistapi.api.v1.sites.maps", "listSiteMaps", site_id
    )  # first floor plan map
    _fetch_first(
        context, mist_session, "wlan_id", "mistapi.api.v1.sites.wlans", "listSiteWlans", site_id
    )  # first WLAN/SSID


def _discover_clients(context: dict, mist_session, site_id: str) -> None:
    """Try to find a connected wireless client MAC for use as client_mac."""
    if context.get("client_mac"):
        return  # already set
    try:
        resp = _mod_call(
            "mistapi.api.v1.sites.wireless_clients", "searchSiteWirelessClients", mist_session, site_id, limit=1
        )
        clients = _unwrap_list(getattr(resp, "data", resp))  # normalize response
        if clients:
            context["client_mac"] = clients[0].get("mac", "")  # use first connected client
            logging.info("Auto-detected client_mac: %s", context["client_mac"])
    except Exception as exc:
        logging.warning("Could not auto-detect client_mac: %s", exc)  # no clients online is normal


def _detect_org_resources(context: dict, mist_session) -> None:
    """Fill mxedge_id, webhook_id, and sso_id from the org."""
    org_id = context.get("org_id")
    if not org_id:
        return  # can't query org resources without org_id

    _fetch_first(
        context, mist_session, "mxedge_id", "mistapi.api.v1.orgs.mxedges", "listOrgMxEdges", org_id, limit=1
    )  # first MxEdge
    _fetch_first(
        context, mist_session, "webhook_id", "mistapi.api.v1.orgs.webhooks", "listOrgWebhooks", org_id
    )  # first org webhook
    _fetch_first(context, mist_session, "sso_id", "mistapi.api.v1.orgs.sso", "listOrgSso", org_id)  # first SSO config


def _fetch_first(context: dict, mist_session, key: str, module_path: str, func_name: str, *args, **kwargs) -> None:
    """Generic helper: call one API list function and store the first record's id in context."""
    if context.get(key):
        return  # already populated, skip API call
    try:
        resp = _mod_call(module_path, func_name, mist_session, *args, **kwargs)  # dynamic call
        records = _unwrap_list(getattr(resp, "data", resp))  # normalize to list
        if records and isinstance(records[0], dict):
            first = records[0]  # first record from the list
            context[key] = first.get("id", "")  # store the UUID id
            if key == "device_id" and first.get("mac"):
                context["device_mac"] = first["mac"]  # devices carry mac alongside id
            logging.info("Auto-detected %s: %s", key, context[key])  # log what we found
    except Exception as exc:
        logging.warning("Could not auto-detect %s (%s.%s): %s", key, module_path, func_name, exc)


def _enrich_context_from_session(context: dict, mist_session) -> dict:
    """Auto-populate all discoverable resource IDs from the live session."""
    _detect_org_id(context, mist_session)  # org_id from /self privileges
    _detect_site_id(context, mist_session)  # site_id preferring morrison house
    _detect_site_resources(context, mist_session)  # device_id, device_mac, map_id, wlan_id
    _detect_org_resources(context, mist_session)  # mxedge_id, webhook_id, sso_id
    return context  # return fully enriched context dict


def _load_op_ids_from_args(args) -> list[str]:
    """Collect the list of operationIds to probe from CLI arguments."""
    op_ids: list[str] = list(args.op_ids)  # start with positional args

    if args.from_file:
        file_path = Path(args.from_file)  # parse file path
        if not file_path.exists():
            logger.error("File not found: %s", file_path)
            sys.exit(1)  # abort on missing file
        lines = file_path.read_text(encoding="utf-8").splitlines()
        op_ids += [line.strip() for line in lines if line.strip() and not line.startswith("#")]

    if args.all_library_funcs:
        op_ids += _collect_library_only_funcs()  # scan library for all known funcs

    seen: set[str] = set()  # deduplicate while preserving order
    deduped = [op for op in op_ids if not (op in seen or seen.add(op))]  # type: ignore[func-returns-value]
    logging.info("Probing %d unique operationIds", len(deduped))
    return deduped  # return deduplicated list


def _collect_library_only_funcs() -> list[str]:
    """Return function names that are in mistapi but not in ENDPOINT_PRIMARY_KEY_STRATEGIES."""
    import pkgutil  # local import

    import mistapi.api.v1 as v1  # mistapi SDK root package  # noqa: I001

    logging.info("Scanning mistapi library for all public function names ...")

    all_lib_funcs: set[str] = set()  # accumulate all SDK function names
    for module_info in pkgutil.walk_packages(v1.__path__, v1.__name__ + "."):
        try:
            mod = importlib.import_module(module_info.name)  # import each sub-module
            for name, _obj in inspect.getmembers(mod, inspect.isfunction):
                if not name.startswith("_"):
                    all_lib_funcs.add(name)  # collect public function names
        except Exception:
            continue  # skip un-importable modules

    # MistHelper.py is too large to import; return all library funcs and
    # let the caller cross-reference against the existing strategy dict manually.

    logging.info("Found %d library functions to consider", len(all_lib_funcs))
    return sorted(all_lib_funcs)  # return sorted list


def main() -> None:
    """Parse args, run probe pipeline, write suggestions."""
    parser = argparse.ArgumentParser(
        description="Probe live Mist API responses to suggest PK strategies for MistHelper.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "op_ids",
        nargs="*",
        metavar="OPERATION_ID",
        help="One or more operationIds to probe (e.g. listOrgDevices)",
    )
    parser.add_argument(
        "--from-file",
        metavar="FILE",
        help="Read operationIds from a file (one per line)",
    )
    parser.add_argument(
        "--all-library-funcs",
        action="store_true",
        default=False,
        help="Probe all public mistapi functions not yet in ENDPOINT_PRIMARY_KEY_STRATEGIES",
    )
    parser.add_argument(
        "--org-id",
        metavar="ORG_ID",
        default=os.environ.get("MIST_ORG_ID", ""),
        help="Org ID for calls that require it (default: MIST_ORG_ID env var)",
    )
    parser.add_argument(
        "--site-id",
        metavar="SITE_ID",
        default=os.environ.get("MIST_SITE_ID", ""),
        help="Site ID for site-scoped calls (default: MIST_SITE_ID env var)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Skip API calls; classify using field names from OpenAPI spec docs instead",
    )
    args = parser.parse_args()

    op_ids = _load_op_ids_from_args(args)  # collect operationIds to probe
    if not op_ids:
        parser.print_help()  # show help if nothing to probe
        sys.exit(0)

    # Build context dict for call argument injection
    context: dict = {}
    if args.org_id:
        context["org_id"] = args.org_id  # inject org_id into all calls
    if args.site_id:
        context["site_id"] = args.site_id  # inject site_id into all calls

    if args.dry_run:
        logger.info("Dry-run mode: no API calls will be made")
        suggestions = _dry_run_classify(op_ids)  # classify from doc field hints
    else:
        mist_session = _load_mist_session()  # authenticate
        context = _enrich_context_from_session(context, mist_session)  # auto-fill org/site ids
        probe = MistApiProbe(mist_session)  # create probe instance
        analyzer = ResponseAnalyzer()  # create analyzer instance
        suggestions: dict[str, dict] = {}  # accumulate results

        logging.info("Beginning probe loop for %d operationIds ...", len(op_ids))
        mutating_skipped = [op for op in op_ids if not MistApiProbe.is_read_only(op)]
        read_only_ops = [op for op in op_ids if MistApiProbe.is_read_only(op)]
        if mutating_skipped:
            logging.warning(
                "Pre-flight: refusing %d mutating operationIds (write-safe probe only): %s",
                len(mutating_skipped),
                mutating_skipped,
            )  # log refused list before any network calls are made
        logging.info("Probing %d read-only operationIds ...", len(read_only_ops))
        for op_id in read_only_ops:
            record = probe.fetch_first_record(op_id, context)  # make live API call
            if record is None:
                logging.warning("Skipping %s — no usable record returned", op_id)
                continue  # skip if probe failed
            suggestions[op_id] = analyzer.classify(record, op_id)  # classify the record

    writer = SuggestionWriter()  # create output writer
    writer.write(suggestions)  # write suggestions file
    writer.print_summary(suggestions)  # print console summary
    print(f"\nSuggestions written to: {SuggestionWriter.OUTPUT_PATH}")


def _dry_run_classify(op_ids: list[str]) -> dict[str, dict]:
    """Classify operationIds by name patterns alone (no API calls)."""
    analyzer = ResponseAnalyzer()  # reuse analyzer class
    suggestions: dict[str, dict] = {}
    for op_id in op_ids:
        name_lower = op_id.lower()
        # Infer likely fields from the operationId verb and noun
        inferred_fields: set[str] = set()
        if any(word in name_lower for word in ("search", "event", "log", "alarm")):
            inferred_fields = {"id", "timestamp", "type", "org_id", "site_id"}  # event-like
        elif any(word in name_lower for word in ("stat", "metric", "usage", "port")):
            inferred_fields = {"timestamp", "rx_bytes", "tx_bytes", "org_id"}  # metrics-like
        elif any(word in name_lower for word in ("list", "get", "count")):
            inferred_fields = {"id", "name", "org_id"}  # entity-like
        else:
            inferred_fields = {"id"}  # default to entity
        suggestions[op_id] = analyzer.classify(
            {f: None for f in inferred_fields}, op_id  # fake record from inferred fields
        )
        suggestions[op_id]["_probe_fields"] = sorted(inferred_fields)  # mark as inferred, not real
        suggestions[op_id]["_dry_run"] = True  # flag that this was not a live call
    return suggestions


if __name__ == "__main__":
    main()
