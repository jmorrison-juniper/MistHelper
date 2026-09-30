"""Build site variable audit rows from Mist records."""

from __future__ import annotations  # Keep annotations lightweight at import time.

import logging  # Log model transforms for operator traceability.
import re  # Find Mist site variable tokens in template strings.
from dataclasses import dataclass  # Define stable report data contracts.
from typing import Any  # Accept heterogeneous Mist API dictionaries.

logger = logging.getLogger(__name__)  # Keep log records tied to this module.
_TOKEN_PATTERN = re.compile(r"{{\s*([A-Za-z0-9_]+)\s*}}")  # Match valid Mist site variable tokens.
_JOIN_TEXT = ", "  # Keep joined report fields consistent across rows.


@dataclass(frozen=True)
class TemplateReference:
    """Represent one assigned template body."""

    template_id: str  # Preserve the Mist template identifier for stable evidence.
    template_type: str  # Preserve the source type for operators.
    template_name: str  # Preserve the display name for operators.
    body: dict[str, Any] | list[Any]  # Preserve the nested template body for recursive scans.
    site_ids: set[str]  # Preserve each site that receives this template.


@dataclass(frozen=True)
class VariableTokenUse:
    """Represent one variable token found in a template field."""

    variable_name: str  # Store the normalized variable name used for comparisons.
    field_path: str  # Store the JSON path to the string that contains the token.
    template_type: str  # Store the template type for the audit row.
    template_name: str  # Store the template name for the audit row.
    template_id: str  # Store the template ID for the audit row.


@dataclass(frozen=True)
class SiteVariableDefinition:
    """Represent one site variable returned by Mist."""

    site_id: str  # Store the site scope for the variable definition.
    variable_name: str  # Store the normalized variable name.
    source: str = ""  # Preserve optional Mist source data for diagnostics.


@dataclass(frozen=True)
class MissingVariableFinding:
    """Represent one missing variable report row."""

    site_name: str  # Store the site name for operator triage.
    site_id: str  # Store the site ID for duplicate site names.
    template_type: str  # Store the template source type.
    template_name: str  # Store the assigned template name.
    template_id: str  # Store the assigned template ID.
    variable_name: str  # Store the missing variable name.
    field_path: str  # Store the field path that proves the missing use.

    def to_row(self) -> dict[str, Any]:
        """Return the CSV row shape for this finding."""
        return {  # Build a stable dictionary that matches the report contract.
            "site_name": self.site_name,  # Include the operator-readable site name.
            "site_id": self.site_id,  # Include a stable site identifier.
            "template_type": self.template_type,  # Include the template source type.
            "template_name": self.template_name,  # Include the template display name.
            "template_id": self.template_id,  # Include a stable template identifier.
            "variable_name": self.variable_name,  # Include the missing variable name.
            "field_path": self.field_path,  # Include the JSON path to the field.
        }


@dataclass(frozen=True)
class SiteVariableSummary:
    """Represent one per-site summary report row."""

    site_name: str  # Store the site name for operator triage.
    site_id: str  # Store the site ID for duplicate site names.
    assigned_templates: str  # Store joined assigned template names.
    required_variable_count: int  # Store the count of required variable names.
    defined_variable_count: int  # Store the count of defined variable names.
    missing_count: int  # Store the count of missing variable names.
    unused_variable_count: int  # Store the count of unused variable names.
    unused_variable_names: str  # Store joined unused variable names.

    def to_row(self) -> dict[str, Any]:
        """Return the CSV row shape for this summary."""
        return {  # Build a stable dictionary that matches the summary contract.
            "site_name": self.site_name,  # Include the operator-readable site name.
            "site_id": self.site_id,  # Include a stable site identifier.
            "assigned_templates": self.assigned_templates,  # Include sorted assigned template display names.
            "required_variable_count": self.required_variable_count,  # Include the required variable count.
            "defined_variable_count": self.defined_variable_count,  # Include the defined variable count.
            "missing_count": self.missing_count,  # Include the missing variable count.
            "unused_variable_count": self.unused_variable_count,  # Include the unused variable count.
            "unused_variable_names": self.unused_variable_names,  # Include sorted unused variable names.
        }


@dataclass(frozen=True)
class SiteVariableAuditResult:
    """Carry complete audit output to the operation layer."""

    findings: list[MissingVariableFinding]  # Store rows for SiteVariableAudit.csv.
    summaries: list[SiteVariableSummary]  # Store rows for SiteVariableSummary.csv.
    missing_site_count: int  # Store the distinct site count with findings.


class SiteVariableAuditModel:
    """Convert Mist records into site variable audit data."""

    _SITE_TEMPLATE_FIELDS = {  # Map template types to common site reference fields.
        "gateway_template": ("gatewaytemplate_id", "gateway_template_id", "gateway_template_ids"),
        "network_template": ("networktemplate_id", "network_template_id", "network_template_ids"),
        "template": ("template_id", "template_ids", "templates"),
        "wlan": ("wlan_id", "wlan_ids", "wlans"),
        "device_profile": ("deviceprofile_id", "device_profile_id", "device_profile_ids"),
    }

    @classmethod
    def build_result(
        cls,
        records: dict[str, list[dict[str, Any]]],
    ) -> SiteVariableAuditResult:
        """Build the complete audit result from loaded Mist records."""
        logger.info("Building site variable audit model")  # Log before the main transform.
        sites = cls._site_lookup(records.get("sites", []))  # Normalize sites for all row joins.
        templates = cls._template_references(records, sites)  # Normalize assigned templates from each source.
        definitions = cls._definitions_by_site(records.get("site_variables", []))  # Normalize variable definitions.
        token_map = cls._tokens_by_template(templates)  # Scan every assigned template body once.
        findings = cls._missing_findings(sites, templates, definitions, token_map)  # Build detailed audit rows.
        summaries = cls._summaries(sites, templates, definitions, token_map)  # Build per-site summary rows.
        missing_site_count = len({finding.site_id for finding in findings})  # Count sites with any finding.
        logger.debug("Built %s findings and %s summaries", len(findings), len(summaries))  # Log result sizes.
        return SiteVariableAuditResult(findings, summaries, missing_site_count)  # Return all report data.

    @classmethod
    def scan_template(cls, template: TemplateReference) -> list[VariableTokenUse]:
        """Find valid variable tokens at any depth in one template."""
        logger.info("Scanning template %s for variable tokens", template.template_id)  # Log before recursion.
        uses: list[VariableTokenUse] = []  # Collect token evidence before deterministic sorting.
        cls._scan_value(template.body, "$", template, uses)  # Walk mappings, lists, and strings recursively.
        unique = sorted(
            {(use.variable_name, use.field_path, use.template_id): use for use in uses}.values(),
            key=cls._token_sort_key,
        )  # Deduplicate repeated token evidence.
        logger.debug("Found %s token uses in template %s", len(unique), template.template_id)  # Log scan size.
        return unique  # Return deterministic token evidence.

    @staticmethod
    def normalize_variable_name(value: Any) -> str:
        """Normalize one variable name for comparison."""
        if value is None:  # Missing variable fields cannot define a useful variable.
            return ""  # Return empty so callers can reject it.
        normalized = str(value).strip()  # Trim surrounding spaces from Mist values or tokens.
        return normalized if normalized and " " not in normalized else ""  # Reject empty names and embedded spaces.

    @classmethod
    def _site_lookup(cls, sites: list[dict[str, Any]]) -> dict[str, str]:
        """Return a site ID to site name map."""
        logger.info("Normalizing %s sites", len(sites))  # Log before site normalization.
        lookup = {
            str(site["id"]): str(site.get("name") or site["id"]) for site in sites if site.get("id")
        }  # Keep only sites with IDs.
        logger.debug("Normalized %s sites", len(lookup))  # Log normalized site count.
        return lookup  # Return site_id to name mapping.

    @classmethod
    def _template_references(
        cls, records: dict[str, list[dict[str, Any]]], sites: dict[str, str]
    ) -> list[TemplateReference]:
        """Return assigned templates from each supported Mist source."""
        logger.info("Normalizing assigned templates")  # Log before template normalization.
        site_records = records.get("sites", [])  # Keep full site records so site-level assignments are visible.
        sources = (  # Define each Mist source and its normalized type.
            ("gateway_templates", "gateway_template"),
            ("network_templates", "network_template"),
            ("templates", "template"),
            ("wlans", "wlan"),
            ("device_profiles", "device_profile"),
        )
        templates: list[TemplateReference] = []  # Collect assigned template references.
        for record_key, template_type in sources:  # Walk each source once.
            templates.extend(
                cls._references_from_records(records.get(record_key, []), template_type, sites, site_records)
            )  # Add references.
        templates.sort(key=cls._template_sort_key)  # Keep deterministic ordering across runs.
        logger.debug("Normalized %s assigned templates", len(templates))  # Log assigned template count.
        return templates  # Return all assigned template references.

    @classmethod
    def _references_from_records(
        cls,
        records: list[dict[str, Any]],
        template_type: str,
        sites: dict[str, str],
        site_records: list[dict[str, Any]],
    ) -> list[TemplateReference]:
        """Return assigned template references for one source type."""
        references: list[TemplateReference] = []  # Collect references for one source type.
        for index, record in enumerate(records):  # Walk records once for this source.
            template_id = str(record.get("id") or f"{template_type}-{index}")  # Use a stable fallback ID.
            site_ids = cls._record_site_ids(record) | cls._site_references(
                sites, site_records, record, template_type
            )  # Merge record and site assignment evidence.
            if site_ids:  # Only assigned templates can affect a site.
                references.append(
                    TemplateReference(
                        template_id, template_type, str(record.get("name") or template_id), record, site_ids
                    )
                )  # Store scan input.
        return references  # Return references for this source type.

    @classmethod
    def _record_site_ids(cls, record: dict[str, Any]) -> set[str]:
        """Return site IDs embedded directly in one template record."""
        site_ids = set()  # Collect site IDs from record-level assignment fields.
        for field in ("site_id", "site_ids"):  # Support singular and plural Mist fields.
            value = record.get(field)  # Read the candidate assignment field.
            site_ids |= cls._ids_from_value(value)  # Merge IDs from strings, lists, and dictionaries.
        return site_ids  # Return every site ID found on the record.

    @classmethod
    def _site_references(
        cls,
        sites: dict[str, str],
        records: list[dict[str, Any]],
        record: dict[str, Any],
        template_type: str,
    ) -> set[str]:
        """Return site IDs that reference the template through site fields."""
        template_id = str(record.get("id", ""))  # Read the template ID for site reference matching.
        reference_fields = cls._SITE_TEMPLATE_FIELDS.get(template_type, ())  # Read common fields for this type.
        return {
            site_id for site_id in sites if cls._site_has_reference(records, site_id, template_id, reference_fields)
        }  # Match site records.

    @classmethod
    def _site_has_reference(
        cls,
        records: list[dict[str, Any]],
        site_id: str,
        template_id: str,
        reference_fields: tuple[str, ...],
    ) -> bool:
        """Return whether one site record references one template ID."""
        site_record = next(
            (record for record in records if record.get("id") == site_id), {}
        )  # Support sources that are sites.
        return any(
            template_id in cls._ids_from_value(site_record.get(field)) for field in reference_fields
        )  # Test all known fields.

    @classmethod
    def _ids_from_value(cls, value: Any) -> set[str]:
        """Return string IDs found inside common Mist reference shapes."""
        if isinstance(value, str):  # A direct string value can hold one ID.
            return {value} if value else set()  # Return a single non-empty ID.
        if isinstance(value, dict):  # A dictionary can hold an ID or nested values.
            direct = {str(value["id"])} if value.get("id") else set()  # Prefer the dictionary ID when present.
            return direct | set().union(*(cls._ids_from_value(item) for item in value.values()))  # Include nested IDs.
        if isinstance(value, list):  # A list can hold several IDs or objects.
            return set().union(*(cls._ids_from_value(item) for item in value)) if value else set()  # Merge each item.
        return set()  # Ignore unsupported assignment shapes.

    @classmethod
    def _definitions_by_site(cls, variables: list[dict[str, Any]]) -> dict[str, set[str]]:
        """Return defined variable names grouped by site ID."""
        logger.info("Normalizing %s site variable definitions", len(variables))  # Log before variable normalization.
        definitions: dict[str, set[str]] = {}  # Build site_id to defined variable names.
        for variable in variables:  # Walk each searchOrgVars record once.
            site_id = str(variable.get("site_id") or "")  # Read the site scope from Mist.
            name = cls.normalize_variable_name(
                variable.get("var") or variable.get("name") or variable.get("key")
            )  # Normalize known name fields.
            if site_id and name:  # Keep only site-scoped named variables.
                definitions.setdefault(site_id, set()).add(name)  # Add the definition to its site.
        logger.debug("Normalized definitions for %s sites", len(definitions))  # Log site coverage.
        return definitions  # Return normalized definitions.

    @classmethod
    def _tokens_by_template(cls, templates: list[TemplateReference]) -> dict[str, list[VariableTokenUse]]:
        """Return token evidence for each assigned template ID."""
        return {
            template.template_id: cls.scan_template(template) for template in templates
        }  # Scan each assigned template once.

    @classmethod
    def _missing_findings(
        cls,
        sites: dict[str, str],
        templates: list[TemplateReference],
        definitions: dict[str, set[str]],
        token_map: dict[str, list[VariableTokenUse]],
    ) -> list[MissingVariableFinding]:
        """Return one finding for each missing variable use."""
        findings: list[MissingVariableFinding] = []  # Collect missing variable rows.
        for template in templates:  # Walk each assigned template.
            for site_id in sorted(template.site_ids):  # Build rows in deterministic site order.
                defined = definitions.get(site_id, set())  # Read defined variables for this site.
                findings.extend(
                    cls._findings_for_template_site(sites, site_id, defined, token_map.get(template.template_id, []))
                )  # Add missing uses.
        findings.sort(key=cls._finding_sort_key)  # Keep CSV output deterministic.
        return findings  # Return detailed audit rows.

    @classmethod
    def _findings_for_template_site(
        cls,
        sites: dict[str, str],
        site_id: str,
        defined: set[str],
        uses: list[VariableTokenUse],
    ) -> list[MissingVariableFinding]:
        """Return missing variable findings for one site and template."""
        return [  # Build one row for each missing token use.
            MissingVariableFinding(
                sites.get(site_id, site_id),
                site_id,
                use.template_type,
                use.template_name,
                use.template_id,
                use.variable_name,
                use.field_path,
            )  # Preserve evidence.
            for use in uses
            if use.variable_name not in defined
        ]

    @classmethod
    def _summaries(
        cls,
        sites: dict[str, str],
        templates: list[TemplateReference],
        definitions: dict[str, set[str]],
        token_map: dict[str, list[VariableTokenUse]],
    ) -> list[SiteVariableSummary]:
        """Return deterministic summary rows for all sites."""
        summaries = [
            cls._summary_for_site(site_id, site_name, templates, definitions, token_map)
            for site_id, site_name in sites.items()
        ]  # Build every site row.
        summaries.sort(key=lambda summary: (summary.site_name, summary.site_id))  # Keep summary output deterministic.
        return summaries  # Return one summary per site.

    @classmethod
    def _summary_for_site(
        cls,
        site_id: str,
        site_name: str,
        templates: list[TemplateReference],
        definitions: dict[str, set[str]],
        token_map: dict[str, list[VariableTokenUse]],
    ) -> SiteVariableSummary:
        """Return one summary row for one site."""
        assigned = [
            template for template in templates if site_id in template.site_ids
        ]  # Select templates assigned to this site.
        required = {
            use.variable_name for template in assigned for use in token_map.get(template.template_id, [])
        }  # Count unique required names.
        defined = definitions.get(site_id, set())  # Read all variables defined for this site.
        missing = required - defined  # Compute required names that are absent.
        unused = defined - required  # Compute defined names that no assigned template uses.
        assigned_names = sorted(
            f"{template.template_type}:{template.template_name}" for template in assigned
        )  # Build readable template labels.
        return SiteVariableSummary(
            site_name,
            site_id,
            _JOIN_TEXT.join(assigned_names),
            len(required),
            len(defined),
            len(missing),
            len(unused),
            _JOIN_TEXT.join(sorted(unused)),
        )  # Return the summary row.

    @classmethod
    def _scan_value(cls, value: Any, path: str, template: TemplateReference, uses: list[VariableTokenUse]) -> None:
        """Scan one nested value and append token evidence."""
        if isinstance(value, str):  # Strings are the only values that can contain tokens.
            uses.extend(cls._uses_from_string(value, path, template))  # Extract each valid token from this field.
            return  # Stop recursion at the string leaf.
        if isinstance(value, dict):  # Dictionaries can contain nested template fields.
            for key, child in value.items():  # Walk every dictionary field.
                cls._scan_value(child, cls._child_path(path, str(key)), template, uses)  # Recurse into the child field.
            return  # Stop after dictionary children are scanned.
        if isinstance(value, list):  # Lists can contain strings, dictionaries, or more lists.
            for index, child in enumerate(value):  # Walk every list item with its index.
                cls._scan_value(child, f"{path}[{index}]", template, uses)  # Recurse into the list item.

    @classmethod
    def _uses_from_string(cls, value: str, path: str, template: TemplateReference) -> list[VariableTokenUse]:
        """Return valid token uses found in one string field."""
        uses = []  # Collect valid tokens from one string field.
        for match in _TOKEN_PATTERN.finditer(value):  # Find each complete valid token.
            name = cls.normalize_variable_name(match.group(1))  # Normalize the token name before comparing.
            if name:  # Empty or invalid names are ignored.
                uses.append(
                    VariableTokenUse(name, path, template.template_type, template.template_name, template.template_id)
                )  # Preserve token evidence.
        return uses  # Return all valid token uses in the string.

    @staticmethod
    def _child_path(parent: str, key: str) -> str:
        """Return a readable JSON-like child path."""
        return f"{parent}.{key}" if key.isidentifier() else f"{parent}[{key!r}]"  # Use readable JSON-like paths.

    @staticmethod
    def _template_sort_key(template: TemplateReference) -> tuple[str, str, str]:
        """Return the deterministic sort key for a template."""
        return (
            template.template_type,
            template.template_name,
            template.template_id,
        )  # Sort templates deterministically.

    @staticmethod
    def _token_sort_key(use: VariableTokenUse) -> tuple[str, str, str, str]:
        """Return the deterministic sort key for token evidence."""
        return (use.template_type, use.template_name, use.variable_name, use.field_path)  # Sort token evidence.

    @staticmethod
    def _finding_sort_key(finding: MissingVariableFinding) -> tuple[str, str, str, str, str, str]:
        """Return the deterministic sort key for findings."""
        return (
            finding.site_name,
            finding.site_id,
            finding.template_type,
            finding.template_name,
            finding.variable_name,
            finding.field_path,
        )  # Sort findings.
