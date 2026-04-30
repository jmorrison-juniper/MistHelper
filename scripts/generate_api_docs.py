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
import json
import logging
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
                        "responses": self._resolve_responses(
                            op.get("responses", {})
                        ),
                        "deprecated": op.get("deprecated", False),
                        "security": op.get("security"),
                        "category": category,
                        "filename": self._make_filename(
                            method.upper(), path
                        ),
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
            return {
                prop_name: self._resolve_node(prop_schema, visited)
                for prop_name, prop_schema in value.items()
            }
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
            parts.append(
                "> **DEPRECATED** -- This endpoint is deprecated "
                "and may be removed in a future release."
            )
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
        return (
            "## Request Body\n\n"
            "Content-Type: `application/json`\n\n"
            f"```json\n{schema_json}\n```"
        )

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
        schema_raw = content.get("application/json", {}).get(
            "schema"
        ) or content.get("application/vnd.api+json", {}).get("schema")
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
            pagination = (
                "## Pagination\n\n"
                "Supports pagination. Use `limit` and `page` query parameters."
            )
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
# IndexGenerator
# ---------------------------------------------------------------------------
class IndexGenerator:
    """Generate the master INDEX.md grouped by OpenAPI tag."""

    def __init__(self, operations: list[dict]) -> None:
        self.operations = operations

    def generate(self) -> str:
        """Build the full INDEX.md content grouped by tag."""
        tag_groups = self._group_by_tag()
        parts = [
            "# Mist API Endpoint Index",
            "",
            f"> {len(self.operations)} operations across {len(tag_groups)} tags",
            "",
        ]
        for tag_name in sorted(tag_groups.keys()):
            parts.append(
                self._render_tag_section(tag_name, tag_groups[tag_name])
            )
        return "\n".join(parts) + "\n"

    def _group_by_tag(self) -> dict[str, list[dict]]:
        """Group operations by their first tag."""
        groups: dict[str, list[dict]] = {}
        for op in self.operations:
            tag = op.get("tags", ["Utilities"])[0]
            groups.setdefault(tag, []).append(op)
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
            summary = op.get("summary", "").replace("|", "\\|")
            link = f"[{filename}]({category}/{filename})"
            rows.append(
                f"| {op['method']} | {op['path']} | {op['operation_id']} "
                f"| {summary} | {link} |"
            )
        return "\n".join([header, "", table, sep] + rows + [""])


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
    parser = argparse.ArgumentParser(
        description="Generate Mist API endpoint reference docs."
    )
    parser.add_argument(
        "--spec",
        type=Path,
        default=DEFAULT_SPEC,
        help="Path to OpenAPI 3.1 JSON spec file",
    )
    args = parser.parse_args()

    start_time = time.time()

    create_output_directories()

    spec_parser = SpecParser(args.spec)
    resolver = SchemaResolver(spec_parser.schemas)
    renderer = MarkdownRenderer(resolver)

    operations = spec_parser.operations
    category_counts: dict[str, int] = {}

    for operation in operations:
        category = operation["category"]
        filename = operation["filename"]
        content = renderer.render_operation(operation)
        output_path = OUTPUT_DIR / category / filename
        output_path.write_text(content, encoding="utf-8")
        category_counts[category] = category_counts.get(category, 0) + 1

    for category in CATEGORY_DIRS:
        count = category_counts.get(category, 0)
        logger.info("  %s/: %d files", category, count)

    index_gen = IndexGenerator(operations)
    index_content = index_gen.generate()
    (OUTPUT_DIR / "INDEX.md").write_text(index_content, encoding="utf-8")
    logger.info(
        "Generated INDEX.md with %d entries across %d tags",
        len(operations),
        len(spec_parser.tags),
    )

    elapsed = time.time() - start_time
    logger.info("Done in %.1f seconds.", elapsed)


if __name__ == "__main__":
    main()
