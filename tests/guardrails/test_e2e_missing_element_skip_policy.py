"""Guardrail: required E2E elements fail instead of reporting a skip.

Why:
    Issue #3380 found 16 browser-test conditions that reported success when
    required interface content or seeded data was absent. This guard keeps the
    measured sites visible and preserves skips for browser capability failures.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # Resolve each approved path from one stable root.


@dataclass(frozen=True)
class RepairSite:
    """Identify one approved missing-element skip repair."""

    repair_id: str  # Keep the issue inventory identifier in each failure.
    path: str  # Name the repository-relative source file.
    owner: str  # Limit the scan to the function that owns the condition.
    message_fragment: str  # Locate the condition through its stable operator message.
    condition: str  # Explain the missing step in the guard output.


REPAIR_SITES = (
    RepairSite(  # R-01 owns the web portal accordion precondition.
        "R-01",
        "tests/e2e/web_portal/test_operations_panel_workflow.py",
        "operations_page",
        "No accordion category revealed an operation row",
        "No accordion category reveals an operation row",
    ),
    RepairSite(  # R-02 owns the browser-token row-prefix precondition.
        "R-02",
        "tests/e2e/upgrade_portal/test_browser_token_signin.py",
        "_first_key",
        "identifier prefix",
        "No element matches the required row prefix",
    ),
    RepairSite(  # R-03 owns the capture site-row precondition.
        "R-03",
        "tests/e2e/upgrade_portal/test_capture.py",
        "_listed_site_id",
        "site picker shows no site row",
        "The site picker has no site row",
    ),
    RepairSite(  # R-04 owns the capture version-control precondition.
        "R-04",
        "tests/e2e/upgrade_portal/test_capture.py",
        "test_walk_from_the_site_list_reaches_the_confirm_page",
        "options page offered no",
        "A required type version control is absent or has no real option",
    ),
    RepairSite(  # R-05 owns the comparison-table row precondition.
        "R-05",
        "tests/e2e/upgrade_portal/test_comparison.py",
        "_assert_row_keys_are_addresses",
        "shows no row",
        "A required comparison table has no row",
    ),
    RepairSite(  # R-06 owns the comparison-render precondition.
        "R-06",
        "tests/e2e/upgrade_portal/test_comparison.py",
        "_skip_without_comparison",
        "picker again rather than a comparison",
        "The expected comparison does not render",
    ),
    RepairSite(  # R-07 owns the stored-capture picker precondition.
        "R-07",
        "tests/e2e/upgrade_portal/test_comparison.py",
        "comparison_page",
        "picker offers no stored capture",
        "The picker has no stored-capture option",
    ),
    RepairSite(  # R-08 owns the History site-row precondition.
        "R-08",
        "tests/e2e/upgrade_portal/test_history.py",
        "site_id",
        "site picker shows no site row",
        "The site picker has no site row",
    ),
    RepairSite(  # R-09 owns the History stored-row precondition.
        "R-09",
        "tests/e2e/upgrade_portal/test_history.py",
        "_stored_rows",
        "capture store holds no stored capture",
        "The seeded store has no history row",
    ),
    RepairSite(  # R-10 owns the History previous-page precondition.
        "R-10",
        "tests/e2e/upgrade_portal/test_history.py",
        "_earlier_page_window",
        "shows no earlier page link",
        "A required previous-page control has no link",
    ),
    RepairSite(  # R-11 owns the sign-in row-prefix precondition.
        "R-11",
        "tests/e2e/upgrade_portal/test_signin.py",
        "_first_row_key",
        "identifier prefix",
        "No element matches the required row prefix",
    ),
    RepairSite(  # R-12 owns the site-selection row-prefix precondition.
        "R-12",
        "tests/e2e/upgrade_portal/test_site_selection.py",
        "_first_row_key",
        "identifier prefix",
        "No element matches the required row prefix",
    ),
    RepairSite(  # R-13 owns the inventory-row precondition.
        "R-13",
        "tests/e2e/upgrade_portal/test_site_selection.py",
        "test_every_device_row_carries_a_mac_address_key",
        "site holds no device",
        "The inventory table has no row",
    ),
    RepairSite(  # R-14 owns the stop site-row precondition.
        "R-14",
        "tests/e2e/upgrade_portal/test_stop.py",
        "_listed_site_id",
        "site picker shows no site row",
        "The site picker has no site row",
    ),
    RepairSite(  # R-15 owns the existing-run site-row precondition.
        "R-15",
        "tests/e2e/upgrade_portal/test_run_controls/test_existing.py",
        "_listed_site_id",
        "site picker shows no site row",
        "The site picker has no site row",
    ),
    RepairSite(  # R-16 owns the two-operator site-row precondition.
        "R-16",
        "tests/e2e/upgrade_portal/test_two_operators.py",
        "_open_site_picker",
        "site picker shows no site row",
        "The site picker has no site row",
    ),
)


def _call_text(call: ast.Call) -> str:
    """Return the literal message text that one call contains."""
    return " ".join(  # Join f-string fragments, so dynamic values do not hide the stable text.
        str(node.value)  # Convert each string constant into scan text.
        for node in ast.walk(call)  # Read each literal below this call.
        if isinstance(node, ast.Constant) and isinstance(node.value, str)  # Ignore numbers and dynamic expressions.
    )


def _call_target(call: ast.Call) -> str:
    """Return the dotted target name of one call."""
    if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name):  # Match module.function calls.
        return f"{call.func.value.id}.{call.func.attr}"  # Preserve the module name for pytest.skip.
    if isinstance(call.func, ast.Name):  # Match direct exception constructor calls.
        return call.func.id  # Return the direct target name.
    return ""  # An indirect call cannot be one approved pytest.skip statement.


def _owner_node(tree: ast.AST, owner: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    """Return the function that owns one approved repair site."""
    matches = [  # Collect functions by name, because class methods also use FunctionDef nodes.
        node  # Keep the node for its calls and source line.
        for node in ast.walk(tree)  # Search module functions, fixtures, and test methods.
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == owner  # Match the manifest owner.
    ]
    assert (
        len(matches) == 1
    ), f"The approved owner {owner!r} has {len(matches)} matches."  # Reject absent or duplicate sites.
    return matches[0]  # The manifest requires one stable owner.


def _matching_calls(source: str, site: RepairSite) -> list[ast.Call]:
    """Return calls in one owner that contain the approved message fragment."""
    tree = ast.parse(source)  # Parse syntax instead of matching comments or documentation text.
    owner = _owner_node(tree, site.owner)  # Restrict the scan to the approved function.
    calls = [  # Keep each call that carries the stable condition text.
        node  # Preserve its target and source line for the finding.
        for node in ast.walk(owner)  # Search each branch of the approved owner.
        if isinstance(node, ast.Call) and site.message_fragment in _call_text(node)  # Locate the measured condition.
    ]
    assert calls, (  # A missing site means a rewrite bypassed the approved policy.
        f"{site.repair_id} could not find {site.message_fragment!r} in "  # Name the inventory record and fragment.
        f"{site.path}:{site.owner}."  # Name the expected file and owner.
    )
    return calls  # The repair can split one condition into several explicit failures.


def _site_findings(source: str, site: RepairSite) -> list[str]:
    """Return one finding for each forbidden skip at an approved site."""
    findings: list[str] = []  # Keep every finding, so one run reports the full repair inventory.
    for call in _matching_calls(source, site):  # Examine each call that carries the measured condition.
        if _call_target(call) == "pytest.skip":  # Missing required content must never report a skip.
            findings.append(  # Give the implementer the exact source and missing step.
                f"{site.repair_id} {site.path}:{call.lineno}: {site.condition}"  # Keep one stable line per finding.
            )
    return findings  # An explicit assertion or pytest.fail produces no finding.


def test_approved_missing_element_sites_do_not_skip() -> None:
    """All 16 approved missing-element sites must use explicit failures."""
    findings: list[str] = []  # Aggregate the full measured result before the assertion.
    for site in REPAIR_SITES:  # Examine each immutable issue inventory record once.
        source = (REPOSITORY_ROOT / site.path).read_text(encoding="utf-8")  # Read the checked-out E2E module.
        findings.extend(_site_findings(source, site))  # Retain every forbidden skip for one complete report.
    print(
        f"Examined {len(REPAIR_SITES)} sites; found {len(findings)} findings."
    )  # Publish the required measured count.
    assert not findings, "Forbidden missing-element skips:\n" + "\n".join(findings)  # Fail with all source locations.


def test_a_forbidden_skip_produces_a_finding() -> None:
    """A skip with the approved condition must fail the policy."""
    site = RepairSite("R-X", "sample.py", "sample", "missing control", "The required control is absent")  # Test data.
    source = "def sample():\n    pytest.skip('missing control')\n"  # Model one forbidden missing-element skip.
    findings = _site_findings(source, site)  # Scan the in-memory example without repository state.
    assert len(findings) == 1, f"The negative example produced {len(findings)} findings."  # Prove the guard can fail.


def test_an_explicit_failure_passes_the_policy() -> None:
    """An explicit failure with the approved condition must pass the policy."""
    site = RepairSite("R-X", "sample.py", "sample", "missing control", "The required control is absent")  # Test data.
    source = "def sample():\n    pytest.fail('missing control')\n"  # Model the required explicit failure.
    findings = _site_findings(source, site)  # Scan the in-memory compliant example.
    assert findings == [], f"The positive example produced findings: {findings}"  # Prove failures stay allowed.


def test_an_absent_approved_site_fails_the_policy() -> None:
    """A missing manifest site must fail instead of reducing scan scope."""
    site = RepairSite("R-X", "sample.py", "sample", "missing control", "The required control is absent")  # Test data.
    source = "def sample():\n    return None\n"  # Model a rewrite that removed the measured condition.
    try:  # Read the assertion text without adding a dependency on a pytest helper.
        _site_findings(source, site)  # The missing message fragment must stop the scan.
    except AssertionError as failure:  # The guard reports the absent inventory record.
        assert "R-X could not find" in str(failure), f"The absent-site error was {failure!s}."  # Verify specificity.
    else:  # A silent scan-scope reduction is a policy failure.
        raise AssertionError("The absent approved site did not fail the policy.")  # Keep the manifest immutable.
