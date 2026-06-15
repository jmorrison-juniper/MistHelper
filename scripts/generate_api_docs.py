"""Mist API Endpoint Reference Documentation Generator.

Parses the Juniper Mist OpenAPI 3.1 specification and generates one
markdown file per API operation (~1,013 files) organized by tag category,
plus a master INDEX.md for endpoint discovery.

Source files (already downloaded to documentation/):
    - documentation/mist-api-openapi31json.json  (17MB, OpenAPI 3.1)
    - documentation/mist-api-openapi31yaml.yaml  (11MB, OpenAPI 3.1)

Download URLs for spec updates:
    - JSON: https://doc.mist-lab.fr/openapi/spec/mist-api-openapi31json.json
    - YAML: https://doc.mist-lab.fr/openapi/spec/mist-api-openapi31yaml.yaml

Offline regeneration:
    python scripts/generate_api_docs.py

Two-phase approach (R6):
    Phase 1: This script generates raw markdown from the OpenAPI spec.
    Phase 2: An AI agent rewrites each file with enriched content
             (see documentation/api/ENRICHMENT_GUIDE.md).
"""

import argparse
import dataclasses
import importlib
import inspect
import json
import logging
import pkgutil
import re
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SPEC = REPO_ROOT / "documentation" / "mist-api-openapi31json.json"
OUTPUT_DIR = REPO_ROOT / "documentation" / "api"

CATEGORY_DIRS = [
    "orgs",
    "sites",
    "msps",
    "utilities",
    "constants",
    "installer",
    "self",
    "admins",
]

DEFAULT_AUTH_TEXT = (
    "Requires API token authentication "
    "(`Authorization: Token {api_token}` header "
    "or `X-CSRFToken` cookie). "
    "See Mist API authentication documentation."
)


# ---------------------------------------------------------------------------
# SpecParser
# ---------------------------------------------------------------------------
class SpecParser:
    """Load and extract operations, tags, and schemas from OpenAPI JSON."""

    def __init__(self, spec_path: Path) -> None:
        logger.info("Parsing OpenAPI spec from %s ...", spec_path)
        with open(spec_path, encoding="utf-8") as fh:
            raw = json.load(fh)
        self.schemas: dict = raw.get("components", {}).get("schemas", {})
        self.tags: list[dict] = raw.get("tags", [])
        self.security: list = raw.get("security", [])
        self.response_defs: dict = raw.get("components", {}).get("responses", {})
        self.operations: list[dict] = self._extract_operations(raw)
        logger.info(
            "Extracted %d operations, %d schemas, %d tags",
            len(self.operations),
            len(self.schemas),
            len(self.tags),
        )

    def _extract_operations(self, raw: dict) -> list[dict]:
        """Walk paths and build a flat operation list."""
        methods = ("get", "post", "put", "delete", "patch")
        operations: list[dict] = []
        for path, path_obj in raw.get("paths", {}).items():
            for method in methods:
                if method not in path_obj:
                    continue
                op = path_obj[method]
                tag = op.get("tags", ["Utilities"])[0]
                category = tag.split()[0].lower()
                if category == "msps":
                    category = "msps"
                operations.append(
                    {
                        "method": method.upper(),
                        "path": path,
                        "operation_id": op.get("operationId", ""),
                        "tags": op.get("tags", []),
                        "summary": op.get("summary", ""),
                        "description": op.get("description", ""),
                        "parameters": op.get("parameters", []),
                        "request_body": op.get("requestBody"),
                        "responses": self._resolve_responses(op.get("responses", {})),
                        "deprecated": op.get("deprecated", False),
                        "security": op.get("security"),
                        "category": category,
                        "filename": self._make_filename(method.upper(), path),
                    }
                )
        return operations

    @staticmethod
    def _make_filename(method: str, path: str) -> str:
        """Build filename per R3: {METHOD}_{path_slug}.md."""
        slug = path.replace("/api/v1/", "")
        slug = slug.strip("/")
        slug = re.sub(r"[{}]", "", slug)
        slug = slug.replace("/", "_")
        return f"{method}_{slug}.md"

    def _resolve_responses(self, responses: dict) -> dict:
        """Inline response-level $ref from components/responses."""
        resolved = {}
        for code, resp in responses.items():
            if "$ref" in resp:
                ref_name = resp["$ref"].rsplit("/", 1)[-1]
                resolved[code] = self.response_defs.get(ref_name, resp)
            else:
                resolved[code] = resp
        return resolved


# ---------------------------------------------------------------------------
# SchemaResolver
# ---------------------------------------------------------------------------
class SchemaResolver:
    """Dereference all $ref entries in schemas iteratively."""

    def __init__(self, schemas: dict) -> None:
        self.schemas = schemas

    def resolve(self, schema: dict | None) -> dict | None:
        """Fully resolve a schema, inlining all $ref."""
        if schema is None:
            return None
        return self._resolve_node(schema, set())

    def _resolve_node(self, node: dict, visited: set) -> dict:
        """Resolve a single schema node, flattening allOf inline."""
        if not isinstance(node, dict):
            return node
        if "$ref" in node:
            ref_name = self._ref_name(node["$ref"])
            if ref_name in visited:
                return {"type": "object", "description": f"(circular: {ref_name})"}
            visited = visited | {ref_name}
            target = self.schemas.get(ref_name, {})
            return self._resolve_node(dict(target), visited)
        if "allOf" in node and isinstance(node["allOf"], list):
            merged = self._merge_all_of(node["allOf"], visited)
            for key, value in node.items():
                if key in ("allOf", "contentMediaType"):
                    continue
                resolved = self._resolve_value(key, value, visited)
                if key == "properties" and isinstance(merged.get("properties"), dict):
                    merged["properties"].update(resolved)
                else:
                    merged[key] = resolved
            return merged
        result = {}
        for key, value in node.items():
            if key == "contentMediaType":
                continue
            result[key] = self._resolve_value(key, value, visited)
        return result

    def _resolve_value(self, key: str, value, visited: set):
        """Resolve a single value, handling composition keywords."""
        if key in ("oneOf", "anyOf") and isinstance(value, list):
            return [self._resolve_node(s, visited) for s in value]
        if key == "properties" and isinstance(value, dict):
            return {prop_name: self._resolve_node(prop_schema, visited) for prop_name, prop_schema in value.items()}
        if key == "items" and isinstance(value, dict):
            return self._resolve_node(value, visited)
        if isinstance(value, dict) and "$ref" in value:
            return self._resolve_node(value, visited)
        return value

    def _merge_all_of(self, schemas: list, visited: set) -> dict:
        """Merge allOf schemas into a single object."""
        merged: dict = {"type": "object", "properties": {}, "required": []}
        for sub_schema in schemas:
            resolved = self._resolve_node(sub_schema, visited)
            if "properties" in resolved:
                merged["properties"].update(resolved["properties"])
            if "required" in resolved:
                merged["required"].extend(resolved["required"])
            for merge_key in ("description", "type", "format"):
                if merge_key in resolved:
                    merged[merge_key] = resolved[merge_key]
        if not merged["required"]:
            del merged["required"]
        if not merged["properties"]:
            del merged["properties"]
        return merged

    @staticmethod
    def _ref_name(ref_str: str) -> str:
        """Extract schema name from $ref string."""
        return ref_str.rsplit("/", 1)[-1]


# ---------------------------------------------------------------------------
# MarkdownRenderer
# ---------------------------------------------------------------------------
class MarkdownRenderer:
    """Render a single operation as a self-contained markdown file."""

    def __init__(self, resolver: SchemaResolver) -> None:
        self.resolver = resolver

    def render_operation(self, operation: dict) -> str:
        """Assemble all R7 template sections into a complete markdown file."""
        sections = [
            self._render_header(operation),
            self.render_parameters(operation.get("parameters", [])),
            self.render_request_body(operation),
            self.render_responses(operation.get("responses", {})),
            self._render_footer(operation),
        ]
        return "\n\n".join(sections) + "\n"

    def _render_header(self, operation: dict) -> str:
        """Build title, deprecated banner, summary, HTTP, description, auth."""
        parts = [f"# {operation['operation_id']}"]
        if operation.get("deprecated"):
            parts.append("> **DEPRECATED** -- This endpoint is deprecated " "and may be removed in a future release.")
        if operation.get("summary"):
            parts.append(f"> {operation['summary']}")
        parts.append(f"## HTTP\n\n`{operation['method']} {operation['path']}`")
        desc = operation.get("description") or "No description available."
        parts.append(f"## Description\n\n{desc}")
        parts.append(f"## Authentication\n\n{DEFAULT_AUTH_TEXT}")
        return "\n\n".join(parts)

    def render_parameters(self, parameters: list[dict]) -> str:
        """Render path, query, header parameter tables per FR-009."""
        if not parameters:
            return "## Parameters\n\nNone."
        groups: dict[str, list] = {"path": [], "query": [], "header": []}
        for param in parameters:
            location = param.get("in", "query")
            if location in groups:
                groups[location].append(param)
        parts = ["## Parameters"]
        for location in ("path", "query", "header"):
            if groups[location]:
                parts.append(self._param_table(location, groups[location]))
        return "\n\n".join(parts)

    def _param_table(self, location: str, params: list[dict]) -> str:
        """Build a markdown table for one parameter location."""
        title = f"### {location.title()} Parameters"
        has_extras = location == "query"
        if has_extras:
            header = "| Name | Type | Required | Default | Enum | Description |"
            sep = "|------|------|----------|---------|------|-------------|"
        else:
            header = "| Name | Type | Required | Description |"
            sep = "|------|------|----------|-------------|"
        rows = [self._param_row(p, has_extras) for p in params]
        return "\n".join([title, "", header, sep] + rows)

    @staticmethod
    def _param_row(param: dict, has_extras: bool) -> str:
        """Format a single parameter as a markdown table row."""
        schema = param.get("schema", {})
        name = param.get("name", "")
        ptype = schema.get("type", "string")
        required = "Yes" if param.get("required") else "No"
        desc = param.get("description", "").replace("\n", " ").replace("|", "\\|")
        if has_extras:
            default = str(schema.get("default", "")) if "default" in schema else ""
            enum = ", ".join(str(e) for e in schema.get("enum", []))
            return f"| {name} | {ptype} | {required} | {default} | {enum} | {desc} |"
        return f"| {name} | {ptype} | {required} | {desc} |"

    def render_request_body(self, operation: dict) -> str:
        """Render request body schema as JSON, or 'None' for GET/DELETE."""
        if operation["method"] in ("GET", "DELETE"):
            return "## Request Body\n\nNone."
        body = operation.get("request_body")
        if not body:
            return "## Request Body\n\nNone."
        content = body.get("content", {})
        schema = content.get("application/json", {}).get("schema")
        if not schema:
            for content_value in content.values():
                if "schema" in content_value:
                    schema = content_value["schema"]
                    break
        if not schema:
            return "## Request Body\n\nNone."
        resolved = self.resolver.resolve(schema)
        schema_json = json.dumps(resolved, indent=2, default=str)
        return "## Request Body\n\n" "Content-Type: `application/json`\n\n" f"```json\n{schema_json}\n```"

    def render_responses(self, responses: dict) -> str:
        """Render success responses with schemas and error table."""
        parts = ["## Response"]
        error_rows: list[str] = []
        for code in sorted(responses.keys()):
            resp = responses[code]
            desc = resp.get("description", "").replace("\n", " ")
            if code.startswith(("4", "5")):
                error_rows.append(f"| {code} | {desc} |")
                continue
            parts.append(self._render_single_response(code, resp))
        errors = "## Errors\n\n"
        if error_rows:
            errors += "| Status | Description |\n|--------|-------------|\n"
            errors += "\n".join(error_rows)
        else:
            errors += "None."
        parts.append(errors)
        return "\n\n".join(parts)

    def _render_single_response(self, code: str, resp: dict) -> str:
        """Render one response status code with its resolved schema."""
        desc = resp.get("description", "")
        content = resp.get("content", {})
        schema_raw = content.get("application/json", {}).get("schema") or content.get(
            "application/vnd.api+json", {}
        ).get("schema")
        if not schema_raw:
            return f"### {code}\n\n{desc}"
        resolved = self.resolver.resolve(schema_raw)
        schema_json = json.dumps(resolved, indent=2, default=str)
        return f"### {code}\n\n{desc}\n\n```json\n{schema_json}\n```"

    def derive_mistapi_path(self, operation: dict) -> str:
        """Map operation tag + operationId to mistapi SDK function path."""
        tag = operation.get("tags", ["Utilities"])[0]
        words = tag.split()
        scope = words[0].lower()
        resource = "_".join(w.lower() for w in words[1:]) if len(words) > 1 else scope
        op_id = operation.get("operation_id", "")
        return f"mistapi.api.v1.{scope}.{resource}.{op_id}()"

    def _render_footer(self, operation: dict) -> str:
        """Build pagination, rate limiting, mistapi, and placeholder sections."""
        param_names = {p.get("name", "") for p in operation.get("parameters", [])}
        if "limit" in param_names or "page" in param_names:
            pagination = "## Pagination\n\n" "Supports pagination. Use `limit` and `page` query parameters."
        else:
            pagination = "## Pagination\n\nNot paginated."
        mistapi_path = self.derive_mistapi_path(operation)
        parts = [
            pagination,
            "## Rate Limiting\n\nStandard Mist API rate limits apply.",
            f"## mistapi SDK\n\n`{mistapi_path}`",
            "## Usage Context\n\n*To be enriched by AI agent.*",
            "## Gotchas\n\n*To be enriched by AI agent.*",
            "## Related Endpoints\n\n*To be enriched by AI agent.*",
            "## MistHelper Notes\n\n*To be enriched by AI agent.*",
        ]
        return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# LibraryFunction dataclass
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class LibraryFunction:
    """Structured record for one public mistapi library function."""

    name: str  # Function name — identical to OpenAPI operationId in the SDK
    module_path: str  # Full dotted module path e.g. mistapi.api.v1.orgs.sites
    category: str  # Top-level category e.g. orgs, sites, msps
    resource: str  # Resource sub-module name e.g. sites, devices
    signature: str  # inspect.signature() string representation
    docstring: str  # Raw function docstring (may be empty)
    parameters: list  # Parameters parsed from docstring PATH/QUERY/BODY sections


# ---------------------------------------------------------------------------
# GapReport dataclass
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class GapReport:
    """Results of comparing OpenAPI spec operations against mistapi functions."""

    matched: list  # operationIds present in both spec and library
    spec_only: list  # operationIds in spec but absent from library (no SDK wrapper)
    library_only: list  # function names in library but absent from spec (undocumented)


# ---------------------------------------------------------------------------
# MistapiLibraryScanner
# ---------------------------------------------------------------------------


class MistapiLibraryScanner:
    """Walk the installed mistapi.api.v1 package and collect all public functions."""

    # Matches each PATH/QUERY/BODY PARAMS section header and its content block
    _SECTION_RE = re.compile(
        r"(PATH PARAMS|QUERY PARAMS|BODY PARAMS|OPTIONAL BODY PARAMS)" r"\s*\n-+\n(.*?)(?=\n[A-Z ]+\n-+|\Z)",
        re.DOTALL,
    )
    # Matches one "name : type_description" line inside a param section
    _PARAM_LINE_RE = re.compile(r"^(\w+)\s*:\s*(.+)$", re.MULTILINE)
    # Maps docstring section headers to OpenAPI parameter location strings
    _SECTION_LOCATION: dict = {
        "PATH PARAMS": "path",
        "QUERY PARAMS": "query",
        "BODY PARAMS": "body",
        "OPTIONAL BODY PARAMS": "body",
    }

    def scan(self) -> dict[str, LibraryFunction]:
        """Walk mistapi.api.v1 and return a dict keyed by function name."""
        import mistapi.api.v1 as v1  # installed mistapi SDK root package

        logging.info("Scanning mistapi.api.v1 for library functions ...")  # log before scan
        functions: dict[str, LibraryFunction] = {}  # accumulator for all discovered functions

        for module_info in pkgutil.walk_packages(v1.__path__, v1.__name__ + "."):
            # Walk every sub-module under mistapi.api.v1 recursively
            discovered = self._scan_module(module_info.name)
            functions.update(discovered)  # merge; last-write wins on name collision

        logging.debug("Found %d library functions total", len(functions))  # log result count
        return functions  # return complete function inventory

    def _scan_module(self, module_name: str) -> dict[str, LibraryFunction]:
        """Import one module and return its public LibraryFunction records."""
        try:
            mod = importlib.import_module(module_name)  # dynamic import of the sub-module
        except Exception as exc:
            logging.warning("Could not import %s: %s", module_name, exc)  # log import failure
            return {}  # skip this module on any import error

        category, resource = self._derive_category_resource(module_name)  # extract from path
        funcs: dict[str, LibraryFunction] = {}  # per-module function accumulator

        for name, obj in inspect.getmembers(mod, inspect.isfunction):
            if name.startswith("_"):
                continue  # skip private/dunder functions — only public API surface wanted
            doc = inspect.getdoc(obj) or ""  # normalize None docstrings to empty string
            funcs[name] = LibraryFunction(
                name=name,
                module_path=module_name,
                category=category,
                resource=resource,
                signature=str(inspect.signature(obj)),  # capture full typed signature string
                docstring=doc,
                parameters=self._parse_docstring_params(doc),  # parse structured params
            )

        return funcs  # return all public functions discovered in this module

    @staticmethod
    def _derive_category_resource(module_name: str) -> tuple[str, str]:
        """Extract (category, resource) from a dotted mistapi module path."""
        parts = module_name.split(".")  # split 'mistapi.api.v1.orgs.sites' into list
        if len(parts) >= 5:
            return parts[3], parts[4]  # 4th=category (orgs), 5th=resource (sites)
        if len(parts) == 4:
            return parts[3], parts[3]  # shallow module: category doubles as resource
        return "utilities", "common"  # fallback for unexpected module depth

    def _parse_docstring_params(self, docstring: str) -> list[dict]:
        """Parse PATH/QUERY/BODY PARAMS sections from a mistapi docstring."""
        params: list[dict] = []  # accumulate parsed parameter dicts
        for match in self._SECTION_RE.finditer(docstring):
            section_name = match.group(1)  # section header e.g. 'PATH PARAMS'
            section_body = match.group(2)  # section content block
            location = self._SECTION_LOCATION.get(section_name, "query")  # map to OpenAPI location
            for line_match in self._PARAM_LINE_RE.finditer(section_body):
                params.append(
                    {
                        "name": line_match.group(1),  # parameter name token
                        "in": location,  # path, query, or body
                        "schema": {"type": line_match.group(2).split(",")[0].strip()},  # first type word
                        "required": location == "path",  # path params are always required by convention
                        "description": "",  # docstring lines lack inline descriptions
                    }
                )
        return params  # return list of parameter dicts in OpenAPI-like shape


# ---------------------------------------------------------------------------
# GapAnalyzer
# ---------------------------------------------------------------------------


class GapAnalyzer:
    """Compare the OpenAPI spec operation set against the mistapi library function set."""

    def __init__(self, spec_operations: list[dict], library_functions: dict) -> None:
        self.spec_ids: frozenset[str] = frozenset(  # all operationIds extracted from parsed spec
            op["operation_id"] for op in spec_operations if op.get("operation_id")
        )
        self.lib_ids: frozenset[str] = frozenset(library_functions.keys())  # all SDK function names

    def analyze(self) -> GapReport:
        """Compute matched, spec-only, and library-only sets and return a GapReport."""
        logging.info(
            "Gap analysis: %d spec ops vs %d library functions",
            len(self.spec_ids),
            len(self.lib_ids),
        )  # log before heavy set operations
        matched = sorted(self.spec_ids & self.lib_ids)  # intersection: both sources agree
        spec_only = sorted(self.spec_ids - self.lib_ids)  # in spec but no SDK wrapper
        library_only = sorted(self.lib_ids - self.spec_ids)  # in SDK but absent from spec
        logging.debug(
            "Matched: %d  |  Spec-only: %d  |  Library-only: %d",
            len(matched),
            len(spec_only),
            len(library_only),
        )  # log result counts after set operations
        return GapReport(matched=matched, spec_only=spec_only, library_only=library_only)


# ---------------------------------------------------------------------------
# LibraryStubRenderer
# ---------------------------------------------------------------------------


class LibraryStubRenderer:
    """Render stub markdown for library functions absent from the OpenAPI spec."""

    _DOC_LINK_RE = re.compile(r"API doc:\s*(https?://\S+)")  # extracts upstream reference URL

    def render(self, func: LibraryFunction) -> str:
        """Assemble a complete stub markdown file from a LibraryFunction record."""
        parts = [
            self._render_header(func),
            self._render_parameters(func.parameters),
            "## Request Body\n\nSee mistapi SDK documentation.",
            "## Response\n\nSee mistapi SDK documentation.",
            "## Errors\n\nNone documented.",
            self._render_footer(func),
        ]
        return "\n\n".join(parts) + "\n"  # join sections with blank lines; terminate with newline

    def _render_header(self, func: LibraryFunction) -> str:
        """Build title, source badge, description, module, signature, and auth sections."""
        description = self._extract_description(func.docstring)  # pull first prose paragraph
        doc_match = self._DOC_LINK_RE.search(func.docstring)  # find API doc URL if present
        doc_link = doc_match.group(1) if doc_match else ""  # extract URL or empty string
        parts = [
            f"# {func.name}",
            "> **SOURCE: mistapi SDK only** -- "
            "This endpoint is not described in the current OpenAPI specification. "
            "Documentation generated from the installed `mistapi` Python library.",
        ]
        if doc_link:
            parts.append(f"> API Reference: {doc_link}")  # include upstream link when available
        parts += [
            f"## Module\n\n`{func.module_path}`",
            f"## Signature\n\n```python\n{func.name}{func.signature}\n```",
            f"## Description\n\n{description}",
            f"## Authentication\n\n{DEFAULT_AUTH_TEXT}",
        ]
        return "\n\n".join(parts)  # return assembled header block

    def _render_parameters(self, parameters: list[dict]) -> str:
        """Render a parameter table from parsed docstring params."""
        if not parameters:
            return "## Parameters\n\nNone documented."  # no params found in docstring
        header = "| Name | Location | Type | Required | Description |"
        sep = "|------|----------|------|----------|-------------|"
        rows = [self._param_row(p) for p in parameters]  # build one row per parameter
        return "## Parameters\n\n" + "\n".join([header, sep] + rows)

    @staticmethod
    def _param_row(param: dict) -> str:
        """Format one parameter dict as a markdown table row."""
        name = param.get("name", "")  # parameter name token
        location = param.get("in", "query")  # path, query, or body
        ptype = param.get("schema", {}).get("type", "")  # schema type string
        required = "Yes" if param.get("required") else "No"  # boolean to Yes/No label
        desc = param.get("description", "")  # description (often empty)
        return f"| {name} | {location} | {ptype} | {required} | {desc} |"

    def _render_footer(self, func: LibraryFunction) -> str:
        """Build rate limiting, mistapi SDK path, and placeholder enrichment sections."""
        parts = [
            "## Rate Limiting\n\nStandard Mist API rate limits apply.",
            f"## mistapi SDK\n\n`{func.module_path}.{func.name}()`",
            "## Usage Context\n\n*To be enriched by AI agent.*",
            "## Gotchas\n\n*To be enriched by AI agent.*",
            "## Related Endpoints\n\n*To be enriched by AI agent.*",
            "## MistHelper Notes\n\n*To be enriched by AI agent.*",
        ]
        return "\n\n".join(parts)  # return assembled footer block

    @staticmethod
    def _extract_description(docstring: str) -> str:
        """Pull the first prose paragraph from a mistapi docstring."""
        if not docstring:
            return "No description available."  # guard against empty docstrings
        lines = docstring.strip().splitlines()  # split into individual lines for iteration
        desc_lines: list[str] = []  # accumulate lines of the first prose paragraph
        for line in lines:
            stripped = line.strip()  # remove surrounding whitespace for comparison
            if not stripped:
                if desc_lines:
                    break  # first blank line after content ends the paragraph
                continue  # skip leading blank lines before paragraph starts
            if stripped.isupper() or stripped.startswith("API doc:"):
                break  # stop at ALL CAPS section headers or API doc link
            desc_lines.append(stripped)  # add prose line to description accumulator
        return " ".join(desc_lines) if desc_lines else "No description available."


# ---------------------------------------------------------------------------
# IndexGenerator
# ---------------------------------------------------------------------------
class IndexGenerator:
    """Generate the master INDEX.md grouped by OpenAPI tag."""

    def __init__(
        self,
        operations: list[dict],
        library_only_funcs: list[LibraryFunction] | None = None,
    ) -> None:
        self.operations = operations  # spec-derived operations list
        self.library_only = library_only_funcs or []  # SDK-only functions (not in spec)

    def generate(self) -> str:
        """Build the full INDEX.md content grouped by tag."""
        tag_groups = self._group_by_tag()  # group spec ops by tag name
        total = len(self.operations) + len(self.library_only)  # combined entry count
        parts = [
            "# Mist API Endpoint Index",
            "",
            f"> {len(self.operations)} spec operations, "
            f"{len(self.library_only)} library-only stubs "
            f"({total} total)",
            "",
        ]
        for tag_name in sorted(tag_groups.keys()):
            parts.append(self._render_tag_section(tag_name, tag_groups[tag_name]))
        if self.library_only:
            parts.append(self._render_library_only_section())  # append library-only section
        return "\n".join(parts) + "\n"

    def _group_by_tag(self) -> dict[str, list[dict]]:
        """Group operations by their first tag."""
        groups: dict[str, list[dict]] = {}  # tag-name → operations list
        for op in self.operations:
            tag = op.get("tags", ["Utilities"])[0]  # first tag determines grouping
            groups.setdefault(tag, []).append(op)  # append to existing or create
        return groups

    def _render_tag_section(self, tag_name: str, ops: list[dict]) -> str:
        """Render a single tag group as a markdown table."""
        header = f"## {tag_name}"
        table = "| Method | Path | operationId | Summary | File |"
        sep = "|--------|------|-------------|---------|------|"
        rows = []
        for op in ops:
            category = op["category"]
            filename = op["filename"]
            summary = op.get("summary", "").replace("|", "\\|")  # escape pipe chars in cells
            link = f"[{filename}]({category}/{filename})"
            rows.append(f"| {op['method']} | {op['path']} | {op['operation_id']} " f"| {summary} | {link} |")
        return "\n".join([header, "", table, sep] + rows + [""])

    def _render_library_only_section(self) -> str:
        """Render the library-only stub table at the bottom of INDEX.md."""
        header = "## Library-Only (mistapi SDK, not in OpenAPI spec)"
        note = (
            "> The following endpoints exist in the installed `mistapi` Python library "
            "but are absent from the OpenAPI specification. "
            "Stub documentation was auto-generated from the library source."
        )
        table = "| Function | Module | Category | File |"
        sep = "|----------|--------|----------|------|"
        rows = []
        for func in sorted(self.library_only, key=lambda f: f.name):  # sort alphabetically
            filename = f"SDK_{func.name}.md"  # stub filename convention
            link = f"[{filename}]({func.category}/{filename})"
            rows.append(f"| {func.name} | `{func.module_path}` | {func.category} | {link} |")
        return "\n".join([header, "", note, "", table, sep] + rows + [""])


# ---------------------------------------------------------------------------
# Directory creation
# ---------------------------------------------------------------------------
def create_output_directories() -> None:
    """Create documentation/api/ and all 8 category subdirectories."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for category in CATEGORY_DIRS:
        (OUTPUT_DIR / category).mkdir(parents=True, exist_ok=True)
    logger.info("Created output directories under %s", OUTPUT_DIR)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Parse args, run generation pipeline."""
    parser = argparse.ArgumentParser(description="Generate Mist API endpoint reference docs.")
    parser.add_argument(
        "--spec",
        type=Path,
        default=DEFAULT_SPEC,
        help="Path to OpenAPI 3.1 JSON spec file",
    )
    parser.add_argument(
        "--skip-library-scan",
        action="store_true",
        default=False,
        help="Skip mistapi library introspection; generate from OpenAPI spec only",
    )
    args = parser.parse_args()

    start_time = time.time()  # record start for elapsed time reporting

    create_output_directories()  # ensure documentation/api/ and category subdirs exist

    spec_parser = SpecParser(args.spec)  # parse OpenAPI JSON spec
    resolver = SchemaResolver(spec_parser.schemas)  # build schema resolver for $ref expansion
    renderer = MarkdownRenderer(resolver)  # construct markdown renderer

    operations = spec_parser.operations  # flat list of all spec operations
    category_counts: dict[str, int] = {}  # track per-category file count for logging

    logging.info("Writing spec-derived operation files ...")  # log before bulk file write
    for operation in operations:
        category = operation["category"]
        filename = operation["filename"]
        content = renderer.render_operation(operation)  # render markdown for this operation
        output_path = OUTPUT_DIR / category / filename
        _safe_write(output_path, content)  # preserve enriched files; only write if placeholder or new
        category_counts[category] = category_counts.get(category, 0) + 1  # increment count

    for category in CATEGORY_DIRS:
        count = category_counts.get(category, 0)
        logger.info("  %s/: %d files", category, count)  # log per-category file counts

    # --- Library gap analysis phase ---
    library_only_funcs: list[LibraryFunction] = []  # stubs to include in index
    if not args.skip_library_scan:
        library_only_funcs = _run_library_gap_analysis(operations)

    index_gen = IndexGenerator(operations, library_only_funcs)  # pass stubs to index generator
    index_content = index_gen.generate()  # build full INDEX.md content
    (OUTPUT_DIR / "INDEX.md").write_text(index_content, encoding="utf-8")  # write index to disk
    logging.info(
        "Generated INDEX.md: %d spec ops + %d library-only stubs",
        len(operations),
        len(library_only_funcs),
    )  # log final index totals

    elapsed = time.time() - start_time  # compute total elapsed seconds
    logger.info("Done in %.1f seconds.", elapsed)


def _run_library_gap_analysis(operations: list[dict]) -> list[LibraryFunction]:
    """Scan the mistapi library, analyse gaps, write stubs, return library-only list."""
    try:
        scanner = MistapiLibraryScanner()  # create library scanner instance
        logging.info("Starting mistapi library scan ...")  # log before slow scan
        library_funcs = scanner.scan()  # introspect all mistapi.api.v1 funcs
        logging.info("Library scan complete: %d functions found", len(library_funcs))
    except ImportError as exc:
        logging.warning("mistapi not importable, skipping library scan: %s", exc)
        return []  # gracefully degrade if library is not installed

    analyzer = GapAnalyzer(operations, library_funcs)  # build comparator
    logging.info("Running gap analysis ...")  # log before comparison
    report = analyzer.analyze()  # compute matched/spec-only/lib-only
    logging.info(
        "Gap report -- matched: %d  spec-only: %d  library-only: %d",
        len(report.matched),
        len(report.spec_only),
        len(report.library_only),
    )  # log gap report summary for operator visibility

    if report.spec_only:
        logging.info(
            "%d spec operationIds have no mistapi wrapper (spec-only).", len(report.spec_only)
        )  # inform operator about SDK coverage gap

    stub_renderer = LibraryStubRenderer()  # renderer for SDK-only stubs
    library_only_funcs: list[LibraryFunction] = []  # accumulate written stubs

    logging.info("Writing %d library-only stub files ...", len(report.library_only))
    for func_name in report.library_only:
        func = library_funcs[func_name]  # retrieve LibraryFunction record
        _write_library_stub(func, stub_renderer)  # write stub markdown to disk
        library_only_funcs.append(func)  # add to index list

    logging.debug("Wrote %d library-only stub files", len(library_only_funcs))
    return library_only_funcs  # return list for IndexGenerator


_ENRICHMENT_PLACEHOLDER = "*To be enriched by AI agent.*"  # sentinel text written into fresh stub files


def _safe_write(output_path: "Path", content: str) -> None:
    """Write content to output_path only when safe to do so.

    Skips the write if the file already exists and contains content that
    differs from the placeholder template — meaning a human or AI agent
    has already enriched it.  This prevents re-running the script from
    destroying manually curated documentation.

    A file is considered enriched when it exists AND does NOT contain the
    sentinel placeholder string anywhere in its body.
    """
    if output_path.exists():  # only check existing files — new files are always written
        existing = output_path.read_text(encoding="utf-8")  # read current file content
        if _ENRICHMENT_PLACEHOLDER not in existing:  # placeholder absent → file has been enriched
            logging.debug("Skipping enriched file: %s", output_path.name)  # log skip for traceability
            return  # leave enriched content untouched
        logging.debug("Overwriting placeholder file: %s", output_path.name)  # log intentional overwrite
    output_path.write_text(content, encoding="utf-8")  # write fresh or placeholder-only file to disk


def _write_library_stub(func: LibraryFunction, renderer: LibraryStubRenderer) -> None:
    """Render and write one library-only stub markdown file."""
    category = func.category if func.category in CATEGORY_DIRS else "utilities"  # safe fallback
    category_dir = OUTPUT_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)  # ensure dir exists for this category
    filename = f"SDK_{func.name}.md"  # prefix prevents collision with spec files
    output_path = category_dir / filename
    content = renderer.render(func)  # render stub markdown from LibraryFunction
    _safe_write(output_path, content)  # preserve enriched stubs; only write if placeholder or new
    logging.debug("Wrote library stub: %s/%s", category, filename)


if __name__ == "__main__":
    main()
