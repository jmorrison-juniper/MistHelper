"""Wave 1 gate-runner regression tests for stop/go execution semantics.

Verifies that the PowerShell gate runner script at scripts/wave1/run_wave1_gate.ps1
has the structural properties required for correct stop/go gate execution:
- Present at the expected path.
- Sets $ErrorActionPreference to Stop for fail-fast behavior.
- Propagates exit codes via exit $LASTEXITCODE so CI detects failures.
- Contains all 6 CS1 command step names as defined in the spec.
- Contains all 6 CS1 module/tool markers that identify what each step runs.
"""

from pathlib import Path  # For cross-platform path resolution

# Absolute path to the gate runner script, resolved from this test file's location
_GATE_RUNNER_PATH = (
    Path(__file__).resolve().parents[2]  # Navigate up from tests/guardrails/ to repo root
    / "scripts"  # Into the scripts directory
    / "wave1"  # Into the wave1 subdirectory
    / "run_wave1_gate.ps1"  # The PowerShell gate runner script
)

# The 6 CS1 step names as defined in the gate runner $commands array
# Each must be present so the command set is complete and auditable
_CS1_STEP_NAMES = [
    "py_compile",  # Python syntax check step
    "ruff",  # Lint check step
    "black_check",  # Format check step
    "mypy",  # Type check step
    "pytest_cov",  # Test + coverage step
    "misthelper_test",  # Full integration test step
]

# CS1 module/tool markers that must appear in command arguments
# These identify the actual tool invoked in each step
_CS1_MODULE_MARKERS = [
    "py_compile",  # Module invoked for syntax check
    "ruff",  # Ruff linter invocation marker
    "black",  # Black formatter invocation marker
    "mypy",  # Mypy type checker invocation marker
    "pytest",  # Pytest test runner invocation marker
    "MistHelper.py",  # Main script invoked in the integration test step
]


class TestGateRunnerStructure:
    """Verify gate runner script has the required structure for stop/go semantics."""

    def test_gate_runner_script_exists(self) -> None:
        """Gate runner script must be present at the documented path."""
        assert (
            _GATE_RUNNER_PATH.exists()
        ), (  # Script must exist for CI and operators to use
            f"Gate runner not found at expected path: {_GATE_RUNNER_PATH}"
        )

    def test_gate_runner_has_fail_fast_error_preference(self) -> None:
        """Script must set ErrorActionPreference to Stop to halt on any command failure."""
        script_text = _GATE_RUNNER_PATH.read_text(encoding="utf-8")  # Read the PS1 script content
        assert (
            '$ErrorActionPreference = "Stop"' in script_text
        ), (  # Stop semantics required for fail-fast
            "Gate runner must set ErrorActionPreference=Stop for fail-fast stop/go semantics"
        )

    def test_gate_runner_has_exit_code_propagation(self) -> None:
        """Script must propagate non-zero exit codes so CI and callers detect failures."""
        script_text = _GATE_RUNNER_PATH.read_text(encoding="utf-8")  # Read script for exit propagation check
        assert (
            "exit $LASTEXITCODE" in script_text
        ), (  # Exit code propagation required for CI gate blocking
            "Gate runner must forward exit codes via 'exit $LASTEXITCODE'"
        )

    def test_gate_runner_contains_all_six_cs1_step_names(self) -> None:
        """All 6 CS1 step names must appear in the gate runner command array."""
        script_text = _GATE_RUNNER_PATH.read_text(encoding="utf-8")  # Read script once for all assertions
        for step_name in _CS1_STEP_NAMES:  # Each named step in the CS1 set must be present
            assert (
                step_name in script_text
            ), (  # Missing step means CS1 parity is broken
                f"CS1 step '{step_name}' missing from gate runner — CS1 parity broken"
            )

    def test_gate_runner_references_all_cs1_module_markers(self) -> None:
        """All 6 CS1 tool/module markers must appear in the gate runner command arguments."""
        script_text = _GATE_RUNNER_PATH.read_text(encoding="utf-8")  # Read script once for all assertions
        for marker in _CS1_MODULE_MARKERS:  # Each marker must appear as a command argument
            assert (
                marker in script_text
            ), (  # Missing marker means a CS1 command was silently dropped
                f"CS1 module marker '{marker}' missing from gate runner script"
            )

    def test_gate_runner_has_gate_name_parameter(self) -> None:
        """Script must accept a GateName parameter to identify which gate is being run."""
        script_text = _GATE_RUNNER_PATH.read_text(encoding="utf-8")  # Read script for parameter check
        assert (
            "GateName" in script_text
        ), (  # GateName param identifies the tranche in gate logs
            "Gate runner must accept -GateName parameter for tranche log identification"
        )

    def test_gate_runner_has_success_exit_zero(self) -> None:
        """Script must explicitly exit 0 on full success to signal a clean gate pass."""
        script_text = _GATE_RUNNER_PATH.read_text(encoding="utf-8")  # Read script for exit-zero check
        assert (
            "exit 0" in script_text
        ), (  # Explicit 0 required so callers confirm all steps passed
            "Gate runner must have 'exit 0' to signal a clean gate pass"
        )
