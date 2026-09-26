"""The reference data that the analysis reads: the SDK index and the curated rules.

The SDK index holds one row for each public function of the ``mistapi`` package.
Each row names the HTTP method, the request path, and the Juniper API document.
The curated rules name the shared helper classes, the generic method names, the
dynamic calls that static analysis cannot follow, and the reason that a menu
option calls no Mist API.
"""

from __future__ import annotations  # Postponed annotations keep the type hints light.

import ast  # Parses the mistapi source files.
import importlib.metadata  # Reads the installed mistapi version without an import.
import importlib.util  # Finds the installed mistapi folder without an import.
import json  # Reads and writes the two data files.
import logging  # Records each file action for the operator.
import re  # Finds the API document link in a docstring.
from dataclasses import dataclass  # Holds one SDK row as an immutable value.
from pathlib import Path  # Builds the portable data file paths.

LOGGER = logging.getLogger(__name__)  # Keeps the log records tied to this module.

REFERENCE_DIR = Path(__file__).resolve().parents[1] / "reference"  # The folder that holds both data files.
SDK_INDEX_PATH = REFERENCE_DIR / "sdk_index.json"  # The vendored SDK index.
CURATED_PATH = REFERENCE_DIR / "curated.json"  # The curated rules.
DOC_BASE = "https://www.juniper.net/documentation/us/en/software/mist/api/http/api/"  # The shared link prefix.
SDK_NAME_PATTERN = re.compile(r"^[a-z]+[A-Z][A-Za-z0-9]*$")  # An SDK function name, such as listOrgSites.
SDK_INDEX_FIX = "Run python -m tools.menu_api_map --refresh-sdk-index to write the file again."  # The repair.
CURATED_FIX = "Restore tools/menu_api_map/reference/curated.json from git, then apply your change again."  # The repair.


class JsonDataFile:
    """Read one data file, and stop with a clear message when the file cannot give a JSON object."""

    @staticmethod
    def read(path: Path, fix: str) -> dict:
        """Return the JSON object in the file, or stop the command with the reason and the repair."""
        LOGGER.info("Reading the data file %s", path)  # Log before the file read.
        try:  # A missing file is an operator error, not a crash.
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError as error:  # The file does not exist.
            raise SystemExit(f"The data file {path} does not exist. {fix}") from error
        if not text.strip():  # An empty file holds no object.
            raise SystemExit(f"The data file {path} is empty. {fix}")
        try:  # A damaged file must not give a partial map.
            payload = json.loads(text)
        except json.JSONDecodeError as error:  # The text is not JSON.
            raise SystemExit(f"The data file {path} does not hold valid JSON: {error}. {fix}") from error
        if not isinstance(payload, dict):  # The loaders read named fields.
            raise SystemExit(f"The data file {path} does not hold a JSON object. {fix}")
        LOGGER.debug("Read %d fields from %s", len(payload), path)  # Log after the file read.
        return payload


RAW_CALLS = {  # The mistapi session methods, and the HTTP method that each one sends.
    "mist_get": "GET",  # A read request.
    "mist_post": "POST",  # A create request or an action request.
    "mist_put": "PUT",  # A replace request.
    "mist_delete": "DELETE",  # A delete request.
    "mist_post_file": "POST",  # A file upload request.
}


@dataclass(frozen=True)
class SdkEndpoint:
    """One public mistapi function and the HTTP request that it sends."""

    dotted: str  # The dotted name below the package, such as api.v1.orgs.sites.listOrgSites.
    method: str  # The HTTP method, such as GET.
    path: str  # The request path, such as /api/v1/orgs/{org_id}/sites.
    doc: str  # The Juniper API document link, or an empty string.

    @property
    def name(self) -> str:
        """Return the function name without the module path."""
        return self.dotted.rsplit(".", 1)[1]  # The last dotted part is the function name.

    @property
    def module(self) -> str:
        """Return the SDK module below api.v1, such as orgs.sites."""
        return self.dotted.rsplit(".", 1)[0].removeprefix("api.v1.")  # Drop the function and the version prefix.


class SdkSourceReader:
    """Read the installed mistapi source files and build one row for each function."""

    def __init__(self, sdk_dir: Path) -> None:
        """Store the mistapi package folder to read."""
        self.sdk_dir = sdk_dir  # The folder that holds mistapi/__init__.py.

    @staticmethod
    def installed_dir() -> Path:
        """Return the folder of the installed mistapi package without an import."""
        spec = importlib.util.find_spec("mistapi")  # Finds the package and does not run its code.
        if spec is None or not spec.submodule_search_locations:  # The package is not installed.
            raise SystemExit("The mistapi package is not installed. Install the requirements first.")
        return Path(next(iter(spec.submodule_search_locations)))  # The one package folder.

    @staticmethod
    def installed_version() -> str:
        """Return the version of the installed mistapi distribution."""
        return importlib.metadata.version("mistapi")  # Reads the metadata and does not run package code.

    def read(self) -> list[SdkEndpoint]:
        """Return one row for each public function below mistapi/api, sorted by name."""
        LOGGER.info("Reading the mistapi source below %s", self.sdk_dir)  # Log before the file walk.
        rows: list[SdkEndpoint] = []  # Collects the rows from every module.
        for file_path in sorted((self.sdk_dir / "api").rglob("*.py"), key=lambda path: path.as_posix()):
            if file_path.name != "__init__.py":  # A package file holds no endpoint function.
                rows.extend(self.read_module(file_path))  # Adds the rows of one module.
        LOGGER.debug("Read %d SDK functions", len(rows))  # Log the row count after the walk.
        return sorted(rows, key=lambda row: row.dotted)  # A sorted list gives a stable data file.

    def read_module(self, file_path: Path) -> list[SdkEndpoint]:
        """Return the rows of one SDK module file."""
        module = ".".join(file_path.relative_to(self.sdk_dir).with_suffix("").parts)  # For example api.v1.orgs.sites.
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))  # Parse the module.
        rows = [self.read_function(module, node) for node in tree.body if isinstance(node, ast.FunctionDef)]
        return [row for row in rows if row is not None]  # Keep the functions that send a request.

    def read_function(self, module: str, node: ast.FunctionDef) -> SdkEndpoint | None:
        """Return the row of one SDK function, or None when it sends no request."""
        if node.name.startswith("_"):  # A private helper is not part of the public API.
            return None
        uri, method = self.request_of(node)  # The path and the method of the request.
        if uri is None or method is None:  # The function does not send a request.
            return None
        match = re.search(r"API doc:\s*(\S+)", ast.get_docstring(node) or "")  # The document link line.
        doc = match.group(1) if match else ""  # An empty link when the docstring names none.
        return SdkEndpoint(f"{module}.{node.name}", method, uri, doc)  # One complete row.

    @staticmethod
    def request_of(node: ast.FunctionDef) -> tuple[str | None, str | None]:
        """Return the request path and the HTTP method that one SDK function uses."""
        uri: str | None = None  # The value of the uri variable.
        method: str | None = None  # The method of the session call.
        for sub in ast.walk(node):  # Visit every node of the function body.
            if isinstance(sub, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "uri" for t in sub.targets):
                uri = AstTextReader.fstring_text(sub.value)  # The request path with placeholder names.
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) and sub.func.attr in RAW_CALLS:
                method = RAW_CALLS[sub.func.attr]  # The method of the session call.
        return uri, method  # Both values, or None for a missing value.


class AstTextReader:
    """Read the text of a string node, with a placeholder name for each f-string field."""

    @staticmethod
    def fstring_text(node: ast.AST) -> str | None:
        """Return the text of a string or an f-string, or None for another node."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):  # A plain string.
            return node.value
        if not isinstance(node, ast.JoinedStr):  # Not a string at all.
            return None
        parts: list[str] = []  # Collects the literal text and the placeholders.
        for value in node.values:  # Visit each literal part and each field.
            if isinstance(value, ast.Constant):  # A literal part.
                parts.append(str(value.value))
            elif isinstance(value, ast.FormattedValue):  # A field, such as {org_id} or {self.site_id}.
                parts.append("{" + ast.unparse(value.value).split(".")[-1].split("[")[0] + "}")
        return "".join(parts)  # The text with one placeholder for each field.


class SdkIndex:
    """Look up an SDK function by its dotted name or by its function name."""

    def __init__(self, endpoints: list[SdkEndpoint], version: str) -> None:
        """Index the rows by dotted name and by function name."""
        self.version = version  # The mistapi version that the rows describe.
        self.by_dotted = {row.dotted: row for row in endpoints}  # The primary lookup.
        self.by_name: dict[str, list[str]] = {}  # The function name to its dotted names.
        for row in endpoints:  # Index each row by its function name.
            self.by_name.setdefault(row.name, []).append(row.dotted)

    def __contains__(self, dotted: object) -> bool:
        """Return True when the dotted name is an SDK function."""
        return dotted in self.by_dotted  # A plain dictionary lookup.

    def __len__(self) -> int:
        """Return the number of SDK functions."""
        return len(self.by_dotted)  # One row for each function.

    def get(self, dotted: str) -> SdkEndpoint | None:
        """Return the row of one SDK function, or None."""
        return self.by_dotted.get(dotted)  # None for a name outside the SDK.

    def unique_owner(self, name: str) -> str | None:
        """Return the dotted name of the one SDK function with this name, or None."""
        owners = self.by_name.get(name, [])  # Every SDK function with this name.
        if len(owners) == 1 and SDK_NAME_PATTERN.match(name):  # One owner, and an SDK style name.
            return owners[0]
        return None  # No owner, several owners, or a name in another style.

    @classmethod
    def load(cls, path: Path = SDK_INDEX_PATH) -> SdkIndex:
        """Read the vendored SDK index file."""
        LOGGER.info("Reading the SDK index %s", path)  # Log before the file read.
        payload = JsonDataFile.read(path, SDK_INDEX_FIX)  # The whole index document.
        base = payload["doc_base"]  # The shared prefix of every document link.
        rows = [SdkEndpoint(row[0], row[1], row[2], base + row[3] if row[3] else "") for row in payload["functions"]]
        LOGGER.debug("Read %d SDK rows for mistapi %s", len(rows), payload["mistapi_version"])  # Log the count.
        return cls(rows, payload["mistapi_version"])  # The index for the analysis.

    def render(self) -> str:
        """Return the index file text, with one function on each line."""
        lines = ["{", '  "format": 1,', f'  "mistapi_version": {json.dumps(self.version)},']  # The header.
        lines.append(f'  "doc_base": {json.dumps(DOC_BASE)},')  # The shared link prefix.
        rows = [self.by_dotted[dotted] for dotted in sorted(self.by_dotted)]  # A sorted order for a stable file.
        encoded = [json.dumps([row.dotted, row.method, row.path, row.doc.removeprefix(DOC_BASE)]) for row in rows]
        lines.append('  "functions": [')  # Open the row list.
        lines.extend(f"    {text}," for text in encoded[:-1])  # Every row except the last takes a comma.
        lines.extend(f"    {text}" for text in encoded[-1:])  # JSON does not permit a trailing comma.
        lines.extend(["  ]", "}", ""])  # Close the list and the document.
        return "\n".join(lines)  # One string with Unix line ends.


@dataclass(frozen=True)
class DynamicCall:
    """One call that static analysis cannot follow, and the edges that it adds."""

    function: str  # The key of the function that makes the dynamic call.
    reason: str  # The reason that the analysis cannot follow the call.
    route_handlers_under: str = ""  # Add every route handler below this module prefix.
    sdk_prefix: str = ""  # Add every SDK function below this dotted prefix.


class CuratedRules:
    """The rules that a maintainer writes by hand in reference/curated.json."""

    def __init__(self, payload: dict) -> None:
        """Read the rule tables from the decoded file."""
        self.helper_classes: dict[str, str] = dict(payload["helper_classes"])  # Class name to its purpose.
        self.generic_names = frozenset(payload["generic_names"])  # Method names that match too many classes.
        self.dynamic_calls = {row["function"]: DynamicCall(**row) for row in payload["dynamic_calls"]}
        self.no_endpoint_reasons: dict[str, str] = dict(payload["no_endpoint_reasons"])  # Menu to its reason.

    @classmethod
    def load(cls, path: Path = CURATED_PATH) -> CuratedRules:
        """Read the curated rules file."""
        LOGGER.info("Reading the curated rules %s", path)  # Log before the file read.
        rules = cls(JsonDataFile.read(path, CURATED_FIX))  # Decode and index the tables.
        LOGGER.debug("Read %d helper classes and %d dynamic calls", len(rules.helper_classes), len(rules.dynamic_calls))
        return rules  # The rules for the analysis.

    def helper_of(self, key: str) -> str | None:
        """Return the helper class name when the function key belongs to a helper class."""
        qualified = key.split(":", 1)[1]  # For example DataExporter.write_with_format_selection.
        owner = qualified.split(".", 1)[0]  # The top-level class, or the function name.
        return owner if owner in self.helper_classes else None  # None for a function outside the helpers.
