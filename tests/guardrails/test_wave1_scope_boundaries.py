"""Wave 1 bounded-decomposition scope-audit tests.

Verifies that Wave 1 exclusion constraints were not violated:
1. PacketCaptureManager class was not split out of MistHelper.py.
2. No new packet-capture decomposition source files were added to src/capture/.
3. Menu action key set has not shrunk from the Wave 1 baseline count.
4. All destructive-boundary menu keys (90-100) remain present.
5. Wave-1-touched in-scope classes remain accessible in MistHelper.
6. The bounded-decomposition-checklist.md evidence document exists.
"""

from pathlib import Path  # For cross-platform path resolution

import MistHelper  # Main module under test — must be importable from repo root

# Baseline menu_actions key count as of Wave 1 completion (2026-05-15)
# Any count below this means menu keys were silently removed
_MENU_ACTIONS_BASELINE_COUNT = 178

# Expected filenames in src/capture/ at Wave 1 baseline — no new ones should appear
# Wave 1 exclusion: no packet-capture architecture decomposition
_CAPTURE_MODULE_BASELINE = {"packet_capture.py", "packet_capture_download.py", "__init__.py"}

# Absolute path to src/capture/ for packet-capture decomposition scan
_SRC_CAPTURE_PATH = Path(__file__).resolve().parents[2] / "src" / "capture"

# Wave-1-touched classes that must remain accessible in MistHelper
# These were the in-scope classes modified during Wave 1 safe_input and logging work
_WAVE1_IN_SCOPE_CLASSES = [
    "TroubleshootUtils",  # Touched in safe_input hardening and logging envelope work
    "SSHRunnerManager",  # Touched in safe_input hardening and logging envelope work
    "WAN2MigrationManager",  # Touched in safe_input hardening and logging envelope work
    "InputUtils",  # Core safe_input infrastructure used across all touched paths
    "OperationRegistry",  # Routing/safety classification — US2 guardrail baseline source
    "PacketCaptureManager",  # Wave 1 exclusion: must NOT have been extracted to a new module
]


class TestWave1ScopeBoundaries:
    """Scope-audit checks that Wave 1 bounded-decomposition constraints were not violated."""

    def test_menu_actions_key_count_not_reduced(self) -> None:
        """menu_actions must retain at least the Wave-1 baseline key count."""
        actual_count = len(MistHelper.menu_actions)  # Get current count of all registered menu keys
        assert (
            actual_count >= _MENU_ACTIONS_BASELINE_COUNT
        ), (  # Reduction signals unintended routing removal
            f"menu_actions shrank: expected >= {_MENU_ACTIONS_BASELINE_COUNT}, got {actual_count}"
        )

    def test_destructive_boundary_keys_all_present(self) -> None:
        """All destructive boundary keys 90-100 must exist in menu_actions."""
        for option in [str(i) for i in range(90, 101)]:  # Destructive range fixed by Wave 1 safety baseline
            assert (
                option in MistHelper.menu_actions
            ), (  # Missing key breaks destructive-safety routing
                f"Destructive boundary key '{option}' missing from menu_actions"
            )

    def test_packet_capture_manager_still_in_misthelper(self) -> None:
        """PacketCaptureManager must remain as a class in MistHelper (Wave 1 exclusion: no extraction)."""
        assert hasattr(
            MistHelper, "PacketCaptureManager"
        ), (  # Wave 1 must not extract this class
            "PacketCaptureManager class removed or moved out of MistHelper.py — Wave 1 exclusion violated"
        )

    def test_no_new_packet_capture_files_in_src_capture(self) -> None:
        """src/capture/ must contain only the baseline files — no new Wave-1 decomposition."""
        if not _SRC_CAPTURE_PATH.exists():  # If capture dir is absent, no decomposition possible
            return
        actual_files = {  # Collect all filenames, ignoring compiled bytecode directories
            f.name for f in _SRC_CAPTURE_PATH.iterdir() if not f.name.startswith("__pycache__")
        }
        new_files = actual_files - _CAPTURE_MODULE_BASELINE  # Files beyond baseline are violations
        assert (
            new_files == set()
        ), (  # Any new files indicate unauthorized packet-capture decomposition
            f"New packet-capture decomposition files found in src/capture/: {new_files}"
        )

    def test_wave1_in_scope_classes_still_accessible(self) -> None:
        """All Wave-1-touched in-scope classes must remain accessible in MistHelper."""
        for class_name in _WAVE1_IN_SCOPE_CLASSES:  # Each touched class must be importable from MistHelper
            assert hasattr(
                MistHelper, class_name
            ), (  # Missing class means it was extracted or renamed
                f"Wave-1 in-scope class '{class_name}' is missing from MistHelper module"
            )

    def test_bounded_decomposition_checklist_file_exists(self) -> None:
        """The bounded-decomposition-checklist.md must exist as auditable scope-boundary evidence."""
        checklist_path = (  # Absolute path to the scope-boundary constraints document
            Path(__file__).resolve().parents[2]
            / "specs"
            / "192-compliance-decomposition-wave1"
            / "bounded-decomposition-checklist.md"
        )
        assert (
            checklist_path.exists()
        ), (  # Document must exist for auditors to verify wave-1 boundaries
            f"bounded-decomposition-checklist.md not found at: {checklist_path}"
        )
