#!/usr/bin/env python3
"""
Starlink Stats Dashboard
A modern GUI for monitoring Starlink terminal statistics in real-time.

Author: MistHelper Project
License: MIT
Target Audience: NOC Engineers monitoring Starlink WAN connectivity

Dependencies:
    - PyQt6: Modern GUI framework
    - grpcio: For Starlink device API communication
    - protobuf: Protocol buffer support
"""

import logging
import os
import shutil  # PATH lookup that turns a partial executable name into an absolute path.
import subprocess  # nosec B404 - This is the bootstrap seam, and every call below uses shell=False.
import sys
from datetime import datetime
from typing import Any

# Configure logging first, because the bootstrap below writes DEBUG and INFO records.
# The root logger holds no handler until basicConfig runs, so Python falls back to the
# lastResort handler and drops every record below WARNING. The bootstrap resolves an
# executable on PATH, downloads about 50 MB, and installs two large packages, so the
# operator needs those records when the startup fails. See issue #1721.
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("starlink_dashboard")  # Named logger the whole module shares.

# Default precision for a GPS coordinate the dashboard prints. Three decimal places
# locate a site to about 100 meters, which confirms the right terminal without
# publishing an exact position. See issue #1737.
GPS_PRECISION_DECIMALS = 3
# Environment variable an operator sets to opt in to the exact coordinate.
GPS_EXACT_ENV_VAR = "STARLINK_DASHBOARD_EXACT_GPS"
# Values that count as an opt-in. The set keeps the check to one term per concept.
GPS_EXACT_OPT_IN_VALUES = frozenset({"1", "true", "yes", "on"})


def _exact_gps_enabled() -> bool:
    """Return True when the operator opted in to the exact GPS coordinate.

    Returns:
        bool: True when the opt-in environment variable holds an opt-in value.
        False otherwise, which keeps the reduced precision default.
    """
    raw_value = os.environ.get(GPS_EXACT_ENV_VAR, "")  # An absent variable keeps the safe default.
    enabled = raw_value.strip().lower() in GPS_EXACT_OPT_IN_VALUES  # Accept the common opt-in spellings.
    logging.debug("Exact GPS output opt-in is %s", enabled)  # Record which mode the dump used.
    return enabled


def _format_gps_coordinate(value: Any) -> str:
    """Return the coordinate as text, rounded unless the operator opted in.

    Args:
        value: The latitude or the longitude the Starlink terminal reported.

    Returns:
        str: The exact value when the operator opted in. The rounded value otherwise.
    """
    if _exact_gps_enabled():  # The operator asked for the exact position on purpose.
        return str(value)  # Return the reported value with no change.
    return f"{float(value):.{GPS_PRECISION_DECIMALS}f}"  # Round to about 100 meters.


def _resolve_executable(name: str) -> str:
    """Return the absolute path of *name*, or *name* itself when PATH holds no match.

    Args:
        name: The bare executable name, such as "uv".

    Returns:
        str: The absolute path when PATH holds the program. The bare name otherwise.
        The bare name is safe, because PATH then holds no program that could take its place.
    """
    logging.debug("Resolving the %s executable on PATH", name)  # Log before the PATH lookup runs.
    resolved = shutil.which(name)  # An absolute path stops an earlier PATH entry from supplying another program.
    logging.debug("Resolved the %s executable to %s", name, resolved)  # Log the result of the PATH lookup.
    return resolved or name  # Fall back to the bare name, so the existing FileNotFoundError branch still runs.


def check_and_install_uv() -> bool:
    """
    Check if UV package manager is installed, and install it if missing.
    UV is preferred over pip for faster package installation.

    Returns:
        bool: True if UV is available (either already installed or newly installed)
    """
    try:
        # Check if UV is already installed
        uv_path = _resolve_executable("uv")  # Absolute path when uv is installed, bare name otherwise.
        result = subprocess.run(  # nosec B603 - shutil.which resolved the path and the rest are literals.
            [uv_path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            print(f"UV package manager found: {result.stdout.strip()}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # UV not found, attempt to install it
    print("\nUV package manager not found. Installing UV for faster package management...")
    print("This will only take a moment.\n")

    try:
        # Install UV using pip
        result = subprocess.run(  # nosec B603 - Every argument is a literal or the running interpreter.
            [sys.executable, "-m", "pip", "install", "uv"], capture_output=True, text=True, timeout=60
        )

        if result.returncode == 0:
            print("UV installed successfully!")
            return True
        else:
            print(f"Warning: UV installation had issues: {result.stderr}")
            print("Falling back to pip for package installation.")
            return False

    except Exception as error:
        print(f"Warning: Could not install UV: {error}")
        print("Falling back to pip for package installation.")
        return False


def check_and_install_grpcio() -> tuple[bool, str]:
    """
    Check if grpcio packages are installed, and install them if missing.
    Uses UV if available, otherwise falls back to pip.

    Returns:
        Tuple[bool, str]: (Success status, Error message if any)
    """
    try:
        # Try importing grpcio to check if it exists
        import google.protobuf  # noqa: F401
        import grpc

        print(f"gRPC packages found: grpcio {grpc.__version__}")
        return True, ""
    except ImportError:
        pass

    # gRPC not found, attempt to install it
    print("\ngRPC packages not found. Installing grpcio, grpcio-tools, and protobuf...")
    print("These are required for connecting to Starlink terminals.")
    print("This may take a minute or two.\n")

    # Check if UV is available
    uv_available = check_and_install_uv()

    packages = ["grpcio", "grpcio-tools", "protobuf"]

    try:
        if uv_available:
            # Use UV for faster installation
            print("Using UV for faster installation...")
            print(f"Installing: {', '.join(packages)}")
            uv_path = _resolve_executable("uv")  # Absolute path, so PATH order cannot substitute another program.
            result = subprocess.run(  # nosec B603 - shutil.which resolved the path and packages is a module literal.
                [uv_path, "pip", "install"] + packages, capture_output=False, timeout=300  # Show progress to user
            )
        else:
            # Fall back to pip
            print("Using pip for installation...")
            print(f"Installing: {', '.join(packages)}")
            result = subprocess.run(  # nosec B603 - Every argument is a literal or the running interpreter.
                [sys.executable, "-m", "pip", "install"] + packages,
                capture_output=False,  # Show progress to user
                timeout=300,
            )

        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("gRPC packages installed successfully!")
            print("=" * 60)
            return True, ""

        else:
            error_msg = (
                "\nFailed to install gRPC packages.\n\n"
                "Please try manual installation:\n"
                "  pip install grpcio grpcio-tools protobuf\n\n"
                "Or if using UV:\n"
                "  uv pip install grpcio grpcio-tools protobuf"
            )
            return False, error_msg

    except subprocess.TimeoutExpired:
        error_msg = (
            "Installation timed out. Please check your internet connection and try:\n"
            "  pip install grpcio grpcio-tools protobuf"
        )
        return False, error_msg
    except Exception as error:
        error_msg = (
            f"Unexpected error during installation: {error}\n\n"
            f"Please try manual installation:\n"
            f"  pip install grpcio grpcio-tools protobuf"
        )
        return False, error_msg


def check_and_install_pyqt6() -> tuple[bool, str]:
    """
    Check if PyQt6 is installed, and install it if missing.
    Uses UV if available, otherwise falls back to pip.

    Returns:
        Tuple[bool, str]: (Success status, Error message if any)
    """
    try:
        # Try importing PyQt6 to check if it exists
        from PyQt6.QtCore import PYQT_VERSION_STR

        print(f"PyQt6 found: version {PYQT_VERSION_STR}")
        return True, ""
    except ImportError:
        pass

    # PyQt6 not found, attempt to install it
    print("\nPyQt6 GUI framework not found. Installing PyQt6...")
    print("This may take a minute or two depending on your connection.\n")

    # Check if UV is available
    uv_available = check_and_install_uv()

    try:
        if uv_available:
            # Use UV for faster installation
            print("Using UV for faster installation...")
            print("Please wait, downloading and installing PyQt6 (approximately 50MB)...")
            uv_path = _resolve_executable("uv")  # Absolute path, so PATH order cannot substitute another program.
            result = subprocess.run(  # nosec B603 - shutil.which resolved the path and the rest are literals.
                [uv_path, "pip", "install", "PyQt6"], capture_output=False, timeout=300  # Show progress to user
            )
        else:
            # Fall back to pip
            print("Using pip for installation...")
            print("Please wait, downloading and installing PyQt6 (approximately 50MB)...")
            result = subprocess.run(  # nosec B603 - Every argument is a literal or the running interpreter.
                [sys.executable, "-m", "pip", "install", "PyQt6"],
                capture_output=False,  # Show progress to user
                timeout=300,
            )

        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("PyQt6 installed successfully!")
            print("=" * 60)
            print("Restarting application with GUI support...\n")

            # Restart the script to load the newly installed PyQt6
            os.execv(sys.executable, [sys.executable] + sys.argv)  # nosec B606 - The target is the running interpreter.

        else:
            error_msg = (
                "\nFailed to install PyQt6.\n\n"
                "Please try manual installation:\n"
                "  pip install PyQt6\n\n"
                "Or if using UV:\n"
                "  uv pip install PyQt6"
            )
            return False, error_msg

    except subprocess.TimeoutExpired:
        error_msg = "Installation timed out. Please check your internet connection and try:\n" "  pip install PyQt6"
        return False, error_msg
    except Exception as error:
        error_msg = (
            f"Unexpected error during installation: {error}\n\n"
            f"Please try manual installation:\n"
            f"  pip install PyQt6"
        )
        return False, error_msg

    return True, ""


# Check and install dependencies before importing PyQt6
print("Starlink Dashboard - Checking dependencies...")

# Check gRPC first (needed for Starlink connection)
grpc_success, grpc_error = check_and_install_grpcio()
if not grpc_success:
    print(f"\nWARNING: {grpc_error}")
    print("Dashboard will start, but you won't be able to connect to Starlink terminals.")
    print("You can install manually later and restart the dashboard.\n")

# Check PyQt6 (required for GUI)
pyqt_success, pyqt_error = check_and_install_pyqt6()
if not pyqt_success:
    print(f"\nERROR: {pyqt_error}")
    sys.exit(1)


# Fix Qt plugin path issue on Windows
def fix_qt_plugin_path():
    """
    Fix Qt platform plugin path issue on Windows.
    This is a common issue where Qt cannot find the platform plugins.
    """
    try:
        import site

        site_packages = site.getsitepackages()

        for site_path in site_packages:
            qt_plugins = os.path.join(site_path, "PyQt6", "Qt6", "plugins")
            if os.path.exists(qt_plugins):
                os.environ["QT_PLUGIN_PATH"] = qt_plugins
                print(f"Set Qt plugin path to: {qt_plugins}")
                break
    except Exception as error:
        print(f"Warning: Could not set Qt plugin path: {error}")


# Apply Qt plugin path fix
fix_qt_plugin_path()

# Now safe to import PyQt6
try:
    from PyQt6.QtCore import QSize, Qt, QTimer
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import (
        QApplication,
        QComboBox,
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QStatusBar,
        QVBoxLayout,
        QWidget,
    )
except ImportError as import_error:
    print(f"\nERROR: Failed to import PyQt6 even after installation: {import_error}")
    print("Please try reinstalling:")
    print("  pip uninstall PyQt6")
    print("  pip install PyQt6")
    sys.exit(1)

# Logging configuration moved to the top of this module under issue #1721, so the
# bootstrap records above reach a handler.


class MetricWidget(QFrame):
    """Custom widget for displaying a single metric with label and value."""

    def __init__(self, title: str, unit: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.setup_ui()

    def setup_ui(self):
        """Initialize the metric widget UI."""
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        layout = QVBoxLayout()

        # Title label
        self.title_label = QLabel(self.title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(9)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #B0B0B0;")  # Light gray for dark theme

        # Value label
        self.value_label = QLabel("--")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setWordWrap(True)  # Allow wrapping for long values
        value_font = QFont()
        value_font.setPointSize(20)  # Slightly smaller for better fit
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setStyleSheet("color: #64B5F6;")  # Bright blue for dark theme

        # Unit label
        self.unit_label = QLabel(self.unit)
        self.unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        unit_font = QFont()
        unit_font.setPointSize(8)
        self.unit_label.setFont(unit_font)
        self.unit_label.setStyleSheet("color: #909090;")  # Medium gray for dark theme

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.unit_label)
        layout.setSpacing(8)  # Increased spacing
        layout.setContentsMargins(10, 15, 10, 15)  # Add padding inside widget
        self.setLayout(layout)

        # Set minimum height for consistent sizing
        self.setMinimumHeight(120)

    def set_value(self, value: str, color: str = "#64B5F6"):
        """Update the metric value and color."""
        self.value_label.setText(str(value))
        self.value_label.setStyleSheet(f"color: {color};")

    def set_status_color(self, is_good: bool):
        """Set color based on status (green for good, red for bad)."""
        color = "#66BB6A" if is_good else "#EF5350"  # Brighter green/red for dark theme
        self.value_label.setStyleSheet(f"color: {color};")


class StarlinkDashboard(QMainWindow):
    """Main dashboard window for Starlink statistics monitoring."""

    def __init__(self):
        super().__init__()
        self.starlink_ip = "192.168.100.1"  # Default Starlink router IP
        self.update_interval = 5000  # 5 seconds
        self.timer = QTimer()
        self.connected = False
        self.client_connected = False  # Connection status from us to the dish
        self.current_theme = "Dark"  # Default theme
        self.connection_start_time = None  # Track when connection started
        self.simulated_uptime_base = 0  # Base uptime for simulation
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Starlink Enterprise Dashboard")
        self.setMinimumSize(QSize(1100, 800))  # Larger window for better layout
        self.resize(QSize(1200, 850))  # Default size

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)  # Increased spacing
        main_layout.setContentsMargins(25, 25, 25, 25)  # More padding

        # Header section
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)

        # Theme and control section
        control_layout = self.create_control_section()
        main_layout.addLayout(control_layout)

        # Connection section
        connection_group = self.create_connection_section()
        main_layout.addWidget(connection_group)

        # Main metrics grid
        metrics_layout = self.create_metrics_section()
        main_layout.addLayout(metrics_layout)

        # Status section
        status_group = self.create_status_section()
        main_layout.addWidget(status_group)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Not connected")

        # Apply stylesheet
        self.apply_theme(self.current_theme)

        # Setup timer for auto-refresh
        self.timer.timeout.connect(self.refresh_stats)

    def create_header(self) -> QHBoxLayout:
        """Create the header section with title and timestamp."""
        layout = QHBoxLayout()

        # Title
        title = QLabel("Starlink Enterprise Statistics")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #42A5F5;")  # Bright blue for dark theme

        # Timestamp
        self.timestamp_label = QLabel("Last Updated: Never")
        timestamp_font = QFont()
        timestamp_font.setPointSize(10)
        self.timestamp_label.setFont(timestamp_font)
        self.timestamp_label.setStyleSheet("color: #B0B0B0;")  # Light gray for dark theme

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.timestamp_label)

        return layout

    def create_control_section(self) -> QHBoxLayout:
        """Create the theme selector and control buttons section."""
        layout = QHBoxLayout()

        # Theme selector
        theme_label = QLabel("Theme:")
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Light", "Dark", "TRON", "Hackers"])
        self.theme_selector.setCurrentText(self.current_theme)
        self.theme_selector.currentTextChanged.connect(self.change_theme)
        self.theme_selector.setMaximumWidth(150)

        # Client connection status indicator
        self.client_status_label = QLabel("Client: DISCONNECTED")
        client_status_font = QFont()
        client_status_font.setPointSize(10)
        client_status_font.setBold(True)
        self.client_status_label.setFont(client_status_font)
        self.update_client_status_display()

        # Exit button
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close_application)
        self.exit_button.setMaximumWidth(100)

        layout.addWidget(theme_label)
        layout.addWidget(self.theme_selector)
        layout.addSpacing(30)
        layout.addWidget(self.client_status_label)
        layout.addStretch()
        layout.addWidget(self.exit_button)

        return layout

    def create_connection_section(self) -> QGroupBox:
        """Create the connection configuration section."""
        group = QGroupBox("Connection Settings")
        layout = QHBoxLayout()

        # IP Address input
        ip_label = QLabel("Starlink IP:")
        self.ip_input = QLineEdit(self.starlink_ip)
        self.ip_input.setMaximumWidth(200)
        self.ip_input.setPlaceholderText("192.168.100.1")

        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_connection)
        self.connect_button.setMaximumWidth(120)

        # Refresh button
        self.refresh_button = QPushButton("Refresh Now")
        self.refresh_button.clicked.connect(self.refresh_stats)
        self.refresh_button.setMaximumWidth(120)
        self.refresh_button.setEnabled(False)

        layout.addWidget(ip_label)
        layout.addWidget(self.ip_input)
        layout.addWidget(self.connect_button)
        layout.addWidget(self.refresh_button)
        layout.addStretch()

        group.setLayout(layout)
        return group

    def create_metrics_section(self) -> QGridLayout:
        """Create the main metrics display grid with available diagnostic data."""
        layout = QGridLayout()
        layout.setSpacing(15)

        # Set column stretch factors for better proportions
        # Make Terminal ID and Software columns wider
        layout.setColumnStretch(0, 2)  # Terminal ID - wider
        layout.setColumnStretch(1, 2)  # Service/Software - wider
        layout.setColumnStretch(2, 1)  # Status indicators - standard
        layout.setColumnStretch(3, 1)  # Status indicators - standard

        # Row 1: Critical Status (most important info at top)
        self.connection_status = MetricWidget("Connection", "")
        self.service_status = MetricWidget("Service Status", "")
        self.hardware_test = MetricWidget("Self Test", "")
        self.obstruction_widget = MetricWidget("Obstructions", "")

        layout.addWidget(self.connection_status, 0, 0)
        layout.addWidget(self.service_status, 0, 1)
        layout.addWidget(self.hardware_test, 0, 2)
        layout.addWidget(self.obstruction_widget, 0, 3)

        # Row 2: Terminal Identity (full width for long IDs)
        self.terminal_id = MetricWidget("Terminal ID", "")
        self.utc_offset_widget = MetricWidget("UTC Offset", "hours")

        layout.addWidget(self.terminal_id, 1, 0, 1, 2)  # Span 2 columns
        layout.addWidget(self.utc_offset_widget, 1, 2, 1, 2)  # Span 2 columns

        # Row 3: Software and Hardware (firmware tracking)
        self.software_widget = MetricWidget("Software Version", "")
        self.hardware_widget = MetricWidget("Hardware Version", "")

        layout.addWidget(self.software_widget, 2, 0, 1, 2)  # Span 2 columns
        layout.addWidget(self.hardware_widget, 2, 2, 1, 2)  # Span 2 columns

        # Row 4: Dish Alignment - Current Position
        self.current_position_label = QLabel("Current Dish Position")
        self.current_position_label.setStyleSheet("font-weight: bold; color: #00D9FF; font-size: 11pt;")
        self.current_position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.current_position_label, 3, 0, 1, 2)

        self.target_position_label = QLabel("Target Position")
        self.target_position_label.setStyleSheet("font-weight: bold; color: #00D9FF; font-size: 11pt;")
        self.target_position_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.target_position_label, 3, 2, 1, 2)

        # Row 5: Alignment Values
        self.azimuth_current = MetricWidget("Azimuth", "°")
        self.elevation_current = MetricWidget("Elevation", "°")
        self.azimuth_target = MetricWidget("Azimuth", "°")
        self.elevation_target = MetricWidget("Elevation", "°")

        layout.addWidget(self.azimuth_current, 4, 0)
        layout.addWidget(self.elevation_current, 4, 1)
        layout.addWidget(self.azimuth_target, 4, 2)
        layout.addWidget(self.elevation_target, 4, 3)

        return layout

    def create_status_section(self) -> QGroupBox:
        """Create the detailed status section."""
        group = QGroupBox("Detailed Status & Alerts")
        group_font = QFont()
        group_font.setPointSize(11)
        group_font.setBold(True)
        group.setFont(group_font)

        layout = QVBoxLayout()

        # Status text area - larger and more prominent
        self.status_text = QLabel("No data available. Connect to Starlink terminal to view statistics.")
        self.status_text.setWordWrap(True)
        self.status_text.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.status_text.setMinimumHeight(120)  # Taller for better readability
        status_font = QFont("Consolas", 10)  # Slightly larger font
        self.status_text.setFont(status_font)
        self.status_text.setStyleSheet(
            "background-color: #1E1E1E; color: #E0E0E0; padding: 15px; " "border-radius: 5px; line-height: 1.5;"
        )

        layout.addWidget(self.status_text)
        layout.setContentsMargins(10, 15, 10, 10)
        group.setLayout(layout)
        return group

    def apply_theme(self, theme_name: str):
        """Apply the selected theme to the entire application."""
        self.current_theme = theme_name

        if theme_name == "Light":
            self.apply_light_theme()
        elif theme_name == "Dark":
            self.apply_dark_theme()
        elif theme_name == "TRON":
            self.apply_tron_theme()
        elif theme_name == "Hackers":
            self.apply_hackers_theme()

    def change_theme(self, theme_name: str):
        """Handle theme change from dropdown."""
        self.apply_theme(theme_name)
        logger.info("Theme changed to: %s", theme_name)

    def close_application(self):
        """Close the application gracefully."""
        reply = QMessageBox.question(
            self,
            "Exit Confirmation",
            "Are you sure you want to exit the Starlink Dashboard?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            logger.info("Application closed by user")
            self.close()

    def update_client_status_display(self):
        """Update the client connection status indicator."""
        if self.client_connected:
            self.client_status_label.setText("Client: CONNECTED")
            if self.current_theme == "Light":
                self.client_status_label.setStyleSheet("color: #2E7D32; font-weight: bold;")
            elif self.current_theme == "TRON":
                self.client_status_label.setStyleSheet("color: #00FFFF; font-weight: bold;")
            elif self.current_theme == "Hackers":
                self.client_status_label.setStyleSheet("color: #00FF00; font-weight: bold;")
            else:  # Dark
                self.client_status_label.setStyleSheet("color: #66BB6A; font-weight: bold;")
        else:
            self.client_status_label.setText("Client: DISCONNECTED")
            if self.current_theme == "Light":
                self.client_status_label.setStyleSheet("color: #C62828; font-weight: bold;")
            elif self.current_theme == "TRON":
                self.client_status_label.setStyleSheet("color: #FF4444; font-weight: bold;")
            elif self.current_theme == "Hackers":
                self.client_status_label.setStyleSheet("color: #FF0000; font-weight: bold;")
            else:  # Dark
                self.client_status_label.setStyleSheet("color: #EF5350; font-weight: bold;")

    def apply_light_theme(self):
        """Apply light theme stylesheet."""
        stylesheet = """
            QMainWindow {
                background-color: #F0F2F5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #DADCE0;
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 10px;
                background-color: #FFFFFF;
                color: #202124;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px 0 5px;
                color: #1A73E8;
            }
            QPushButton {
                background-color: #1A73E8;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1557B0;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #DADCE0;
                border-radius: 6px;
                background-color: #FFFFFF;
                color: #202124;
                selection-background-color: #1A73E8;
            }
            QLineEdit:focus {
                border: 2px solid #1A73E8;
            }
            QLabel {
                color: #202124;
            }
            QStatusBar {
                background-color: #FFFFFF;
                color: #5F6368;
                border-top: 1px solid #DADCE0;
            }
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #DADCE0;
                border-radius: 10px;
            }
            QComboBox {
                padding: 6px;
                border: 2px solid #DADCE0;
                border-radius: 6px;
                background-color: #FFFFFF;
                color: #202124;
            }
            QComboBox:hover {
                border: 2px solid #1A73E8;
            }
            QComboBox::drop-down {
                border: none;
            }
        """
        self.setStyleSheet(stylesheet)
        self.update_metric_colors_for_theme("Light")
        self.update_header_colors_for_theme("Light")
        self.update_client_status_display()

    def apply_dark_theme(self):
        """Apply dark theme stylesheet."""
        stylesheet = """
            QMainWindow {
                background-color: #181818;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3A3A3A;
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 10px;
                background-color: #242424;
                color: #E8EAED;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px 0 5px;
                color: #8AB4F8;
            }
            QPushButton {
                background-color: #1A73E8;
                color: #FFFFFF;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2196F3;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #3A3A3A;
                color: #707070;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #3A3A3A;
                border-radius: 6px;
                background-color: #242424;
                color: #E8EAED;
                selection-background-color: #1A73E8;
            }
            QLineEdit:focus {
                border: 2px solid #8AB4F8;
            }
            QLabel {
                color: #E8EAED;
            }
            QStatusBar {
                background-color: #202124;
                color: #9AA0A6;
                border-top: 1px solid #3A3A3A;
            }
            QFrame {
                background-color: #242424;
                border: 1px solid #3A3A3A;
                border-radius: 10px;
            }
            QComboBox {
                padding: 6px;
                border: 2px solid #3A3A3A;
                border-radius: 6px;
                background-color: #242424;
                color: #E8EAED;
            }
            QComboBox:hover {
                border: 2px solid #8AB4F8;
            }
            QComboBox::drop-down {
                border: none;
            }
        """
        self.setStyleSheet(stylesheet)
        self.update_metric_colors_for_theme("Dark")
        self.update_header_colors_for_theme("Dark")
        self.update_client_status_display()

    def apply_tron_theme(self):
        """Apply TRON-inspired theme (neon cyan and orange on black)."""
        stylesheet = """
            QMainWindow {
                background-color: #000000;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #00FFFF;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
                background-color: #0A0A0A;
                color: #00FFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px 0 5px;
                color: #00FFFF;
            }
            QPushButton {
                background-color: #003366;
                color: #00FFFF;
                border: 2px solid #00FFFF;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #004488;
            }
            QPushButton:pressed {
                background-color: #001133;
            }
            QPushButton:disabled {
                background-color: #1A1A1A;
                color: #404040;
                border: 2px solid #404040;
            }
            QLineEdit {
                padding: 6px;
                border: 2px solid #00FFFF;
                border-radius: 4px;
                background-color: #0A0A0A;
                color: #00FFFF;
                selection-background-color: #003366;
            }
            QLineEdit:focus {
                border: 2px solid #FFD700;
            }
            QLabel {
                color: #00FFFF;
            }
            QStatusBar {
                background-color: #000000;
                color: #00FFFF;
            }
            QFrame {
                background-color: #0A0A0A;
                border: 1px solid #00FFFF;
                border-radius: 8px;
            }
            QComboBox {
                padding: 6px;
                border: 2px solid #00FFFF;
                border-radius: 4px;
                background-color: #0A0A0A;
                color: #00FFFF;
            }
            QComboBox:hover {
                border: 2px solid #FFD700;
            }
            QComboBox::drop-down {
                border: none;
            }
        """
        self.setStyleSheet(stylesheet)
        self.update_metric_colors_for_theme("TRON")
        self.update_header_colors_for_theme("TRON")
        self.update_client_status_display()

    def apply_hackers_theme(self):
        """Apply Hackers movie theme (green terminal on black)."""
        stylesheet = """
            QMainWindow {
                background-color: #000000;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #00FF00;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 10px;
                background-color: #001100;
                color: #00FF00;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px 0 5px;
                color: #00FF00;
            }
            QPushButton {
                background-color: #003300;
                color: #00FF00;
                border: 2px solid #00FF00;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
            }
            QPushButton:hover {
                background-color: #004400;
            }
            QPushButton:pressed {
                background-color: #001100;
            }
            QPushButton:disabled {
                background-color: #1A1A1A;
                color: #404040;
                border: 2px solid #404040;
            }
            QLineEdit {
                padding: 6px;
                border: 2px solid #00FF00;
                border-radius: 4px;
                background-color: #001100;
                color: #00FF00;
                selection-background-color: #003300;
                font-family: 'Courier New', monospace;
            }
            QLineEdit:focus {
                border: 2px solid #00FF00;
            }
            QLabel {
                color: #00FF00;
                font-family: 'Courier New', monospace;
            }
            QStatusBar {
                background-color: #000000;
                color: #00FF00;
                font-family: 'Courier New', monospace;
            }
            QFrame {
                background-color: #001100;
                border: 1px solid #00FF00;
                border-radius: 8px;
            }
            QComboBox {
                padding: 6px;
                border: 2px solid #00FF00;
                border-radius: 4px;
                background-color: #001100;
                color: #00FF00;
                font-family: 'Courier New', monospace;
            }
            QComboBox:hover {
                border: 2px solid #00FF00;
            }
            QComboBox::drop-down {
                border: none;
            }
        """
        self.setStyleSheet(stylesheet)
        self.update_metric_colors_for_theme("Hackers")
        self.update_header_colors_for_theme("Hackers")
        self.update_client_status_display()

    def update_metric_colors_for_theme(self, theme: str):
        """Update metric widget colors based on theme."""
        if theme == "Light":
            title_color = "#5F6368"
            _value_color = "#1A73E8"
            unit_color = "#80868B"
            _good_color = "#137333"
            _bad_color = "#C5221F"
            status_bg = "#F8F9FA"
            status_fg = "#202124"
            section_header_color = "#1A73E8"
        elif theme == "TRON":
            title_color = "#00CCCC"
            _value_color = "#00FFFF"
            unit_color = "#009999"
            _good_color = "#FFD700"
            _bad_color = "#FF6600"
            status_bg = "#0A0A0A"
            status_fg = "#00FFFF"
            section_header_color = "#FFD700"
        elif theme == "Hackers":
            title_color = "#00CC00"
            _value_color = "#00FF00"
            unit_color = "#009900"
            _good_color = "#00FF00"
            _bad_color = "#FF0000"
            status_bg = "#001100"
            status_fg = "#00FF00"
            section_header_color = "#00FF00"
        else:  # Dark
            title_color = "#9AA0A6"
            _value_color = "#8AB4F8"
            unit_color = "#80868B"
            _good_color = "#81C995"
            _bad_color = "#F28B82"
            status_bg = "#202124"
            status_fg = "#E8EAED"
            section_header_color = "#8AB4F8"

        # Update all metric widgets
        for widget in [
            self.connection_status,
            self.service_status,
            self.hardware_test,
            self.obstruction_widget,
            self.terminal_id,
            self.software_widget,
            self.hardware_widget,
            self.utc_offset_widget,
            self.azimuth_current,
            self.elevation_current,
            self.azimuth_target,
            self.elevation_target,
        ]:
            widget.title_label.setStyleSheet(f"color: {title_color};")
            widget.unit_label.setStyleSheet(f"color: {unit_color};")

        # Update section header labels
        self.current_position_label.setStyleSheet(f"font-weight: bold; color: {section_header_color}; font-size: 11pt;")
        self.target_position_label.setStyleSheet(f"font-weight: bold; color: {section_header_color}; font-size: 11pt;")

        # Update status text with better styling
        self.status_text.setStyleSheet(
            f"background-color: {status_bg}; color: {status_fg}; "
            f"padding: 15px; border-radius: 8px; font-family: 'Consolas', monospace; "
            f"line-height: 1.6; font-size: 10pt;"
        )

    def update_header_colors_for_theme(self, theme: str):
        """Update header colors based on theme."""
        if theme == "Light":
            title_color = "#1976D2"
            timestamp_color = "#757575"
        elif theme == "TRON":
            title_color = "#00FFFF"
            timestamp_color = "#00AAAA"
        elif theme == "Hackers":
            title_color = "#00FF00"
            timestamp_color = "#00AA00"
        else:  # Dark
            title_color = "#42A5F5"
            timestamp_color = "#B0B0B0"

        # Find and update title label
        for widget in self.centralWidget().findChildren(QLabel):
            if "Starlink Enterprise Statistics" in widget.text():
                widget.setStyleSheet(f"color: {title_color};")
            elif "Last Updated:" in widget.text():
                self.timestamp_label.setStyleSheet(f"color: {timestamp_color};")

    def toggle_connection(self):
        """Toggle connection to Starlink terminal."""
        if not self.connected:
            # Attempt connection
            ip_address = self.ip_input.text().strip()
            if not ip_address:
                QMessageBox.warning(self, "Invalid Input", "Please enter a valid Starlink IP address.")
                return

            self.starlink_ip = ip_address
            logger.info("Attempting to connect to Starlink at %s", self.starlink_ip)

            # Actual gRPC connection
            if self.connect_to_starlink():
                self.connected = True
                self.client_connected = True  # We are now connected to the dish
                self.connect_button.setText("Disconnect")
                self.connect_button.setStyleSheet("background-color: #D32F2F; color: white; font-weight: bold;")
                self.refresh_button.setEnabled(True)
                self.ip_input.setEnabled(False)
                self.status_bar.showMessage(f"Connected to {self.starlink_ip}")
                self.update_client_status_display()

                # Start auto-refresh
                self.timer.start(self.update_interval)
                self.refresh_stats()
            else:
                QMessageBox.critical(
                    self,
                    "Connection Failed",
                    f"Failed to connect to Starlink at {self.starlink_ip}.\n\n"
                    "Please verify:\n"
                    "- IP address is correct\n"
                    "- Device is powered on\n"
                    "- Network connectivity\n"
                    "- gRPC service is accessible",
                )
        else:
            # Disconnect
            self.timer.stop()
            self.connected = False
            self.client_connected = False  # We are now disconnected from the dish
            self.connect_button.setText("Connect")
            self.connect_button.setStyleSheet("")
            self.refresh_button.setEnabled(False)
            self.ip_input.setEnabled(True)
            self.status_bar.showMessage("Disconnected")
            self.update_client_status_display()
            logger.info("Disconnected from Starlink")

    def connect_to_starlink(self) -> bool:
        """
        Establish connection to Starlink terminal via gRPC.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            import grpc

            logger.info("Connecting to Starlink gRPC service at %s:9200", self.starlink_ip)

            # Establish gRPC connection to Starlink dish
            # The Starlink dish runs a gRPC service on port 9200
            self.channel = grpc.insecure_channel(
                f"{self.starlink_ip}:9200",
                options=[
                    ("grpc.max_receive_message_length", 1024 * 1024 * 10),  # 10MB
                ],
            )

            # Test connection with a timeout
            grpc.channel_ready_future(self.channel).result(timeout=5)

            logger.info("Successfully connected to Starlink terminal")
            self.connection_start_time = datetime.now()
            return True

        except grpc.FutureTimeoutError:
            logger.error("Connection timeout: Could not reach Starlink at %s:9200", self.starlink_ip)
            return False
        except Exception as error:
            logger.error("Connection failed: %s", error)
            return False

    _DEFAULT_STARLINK_STATS: dict = {  # Returned when terminal cannot be reached
        "connected": False,
        "service_status": "UNKNOWN",
        "hardware_test": "UNKNOWN",
        "obstruction_status": "UNKNOWN",
        "terminal_id": "N/A",
        "software_version": "N/A",
        "hardware_version": "N/A",
        "utc_offset_hours": 0,
        "azimuth_current": 0.0,
        "elevation_current": 0.0,
        "azimuth_target": 0.0,
        "elevation_target": 0.0,
        "status_message": "Disconnected",
    }

    _SERVICE_STATUS_CODES: dict[int, str] = {  # Disablement code -> short status label
        1: "ACTIVE",
        2: "NO ACCOUNT",
        3: "TOO FAR",
        6: "BLOCKED",
    }

    _HARDWARE_TEST_RESULTS: dict[int, str] = {  # Self-test code -> short label
        1: "PASSED",
        2: "FAILED",
    }

    @staticmethod
    def _load_starlink_proto_modules():
        """Load device_pb2 + device_pb2_grpc from local reference dir. Returns (pb2, grpc, error_msg)."""
        import os
        import sys

        device_api_path = os.path.join(
            os.path.dirname(__file__), "starlink-api-reference", "device-api"
        )  # Path to generated proto modules bundled with this repo
        if device_api_path not in sys.path:
            sys.path.insert(0, device_api_path)  # Make protos importable for this process
        try:
            import device_pb2  # type: ignore[import]
            import device_pb2_grpc  # type: ignore[import]

            return device_pb2, device_pb2_grpc, None  # Success path -- modules loaded
        except ImportError as import_error:
            logger.error("Starlink protobuf modules not found: %s", import_error)
            return None, None, str(import_error)  # Caller will show user dialog

    @staticmethod
    def _compute_obstruction_status(diag) -> str:
        """Return CLEAR or OBSTRUCTED for the current diagnostics snapshot."""
        if hasattr(diag, "alerts") and diag.alerts.obstructed:  # Obstruction alert is set
            return "OBSTRUCTED"
        return "CLEAR"  # Default to clear when no obstruction signal

    @classmethod
    def _compute_service_status(cls, diag) -> str:
        """Return human-readable service status from disablement_code."""
        if not hasattr(diag, "disablement_code"):  # Field missing -> unknown
            return "UNKNOWN"
        code = diag.disablement_code  # Numeric disablement code
        if code in cls._SERVICE_STATUS_CODES:  # Mapped to a short label
            return cls._SERVICE_STATUS_CODES[code]
        return f"CODE {code}"  # Unknown code -> show raw value

    @classmethod
    def _compute_hardware_test(cls, diag) -> str:
        """Return PASSED, FAILED, NO RESULT, or UNKNOWN for hardware self-test."""
        if not hasattr(diag, "hardware_self_test"):  # Field missing -> unknown
            return "UNKNOWN"
        return cls._HARDWARE_TEST_RESULTS.get(diag.hardware_self_test, "NO RESULT")

    @staticmethod
    def _compute_alignment(diag) -> tuple[float, float, float, float]:
        """Return (az_current, el_current, az_target, el_target) from alignment_stats, or zeros."""
        if not hasattr(diag, "alignment_stats"):  # No alignment data -> zeros
            return 0.0, 0.0, 0.0, 0.0
        stats = diag.alignment_stats  # Alignment sub-message
        return (
            stats.boresight_azimuth_deg,
            stats.boresight_elevation_deg,
            stats.desired_boresight_azimuth_deg,
            stats.desired_boresight_elevation_deg,
        )

    @staticmethod
    def _compute_utc_offset_hours(diag) -> float:
        """Return UTC offset hours from utc_offset_s, or 0 if unavailable."""
        if not hasattr(diag, "utc_offset_s"):  # Field missing -> default offset
            return 0
        return diag.utc_offset_s / 3600.0  # Convert seconds to hours

    @staticmethod
    def _compute_short_terminal_id(diag) -> str:
        """Return display-friendly terminal ID (shortened with ... if long)."""
        raw = diag.id if hasattr(diag, "id") else "N/A"  # Full ID or N/A placeholder
        if len(raw) > 20:  # IDs longer than 20 chars are abbreviated for the UI
            return raw[:8] + "..." + raw[-8:]
        return raw

    @staticmethod
    def _compute_is_operational(diag) -> bool:
        """Return True if dish is operational (no shutdown/stuck alerts)."""
        if not hasattr(diag, "alerts"):  # No alerts -> assume operational
            return True
        return not (diag.alerts.dish_thermal_shutdown or diag.alerts.motors_stuck)

    @staticmethod
    def _safe_diag_field(diag, attr: str, default="N/A"):
        """Return diag.attr if present, else the supplied default. Avoids `if hasattr` branches."""
        return getattr(diag, attr, default)

    @classmethod
    def _dump_diagnostics_main_fields(cls, diag) -> None:
        """Pretty-print the top-level diagnostic scalar fields under DEBUG logging."""
        print(f"Terminal ID: {cls._safe_diag_field(diag, 'id')}")
        print(f"Software Version: {cls._safe_diag_field(diag, 'software_version')}")
        print(f"Hardware Version: {cls._safe_diag_field(diag, 'hardware_version')}")
        print(f"UTC Offset: {cls._safe_diag_field(diag, 'utc_offset_s')} seconds")
        print(f"Hardware Self Test: {cls._safe_diag_field(diag, 'hardware_self_test')}")
        print(f"Disablement Code: {cls._safe_diag_field(diag, 'disablement_code')}")
        print(f"Stowed: {cls._safe_diag_field(diag, 'stowed')}")

    @classmethod
    def _dump_diagnostics_sub_messages(cls, diag) -> None:
        """Pretty-print any present sub-messages (alerts/location/alignment) under DEBUG logging."""
        if hasattr(diag, "alerts"):
            cls._dump_diagnostics_alerts(diag.alerts)
        if hasattr(diag, "location") and diag.location.enabled:
            cls._dump_diagnostics_location(diag.location)
        if hasattr(diag, "alignment_stats"):
            cls._dump_diagnostics_alignment(diag.alignment_stats)

    def _dump_diagnostics_debug(self, diag) -> None:
        """Pretty-print the full diagnostics object when DEBUG logging is enabled."""
        if not logger.isEnabledFor(logging.DEBUG):  # No-op unless DEBUG is on
            return
        print("\n" + "=" * 80)
        print("FULL DIAGNOSTIC DATA DUMP")
        print("=" * 80)
        print(f"\nRaw protobuf object:\n{diag}")
        print("\n" + "=" * 80)
        print("PARSED FIELDS:")
        print("=" * 80)
        self._dump_diagnostics_main_fields(diag)  # Top-level scalar fields
        self._dump_diagnostics_sub_messages(diag)  # Nested alerts/location/alignment
        print("=" * 80 + "\n")

    @staticmethod
    def _dump_diagnostics_alerts(alerts) -> None:
        """Pretty-print the alerts sub-message for DEBUG diagnostics."""
        print("\nALERTS:")
        print(f"  - Dish Heating: {alerts.dish_is_heating}")
        print(f"  - Thermal Throttle: {alerts.dish_thermal_throttle}")
        print(f"  - Thermal Shutdown: {alerts.dish_thermal_shutdown}")
        print(f"  - Power Supply Throttle: {alerts.power_supply_thermal_throttle}")
        print(f"  - Motors Stuck: {alerts.motors_stuck}")
        print(f"  - Mast Not Vertical: {alerts.mast_not_near_vertical}")
        print(f"  - Slow Ethernet: {alerts.slow_ethernet_speeds}")
        print(f"  - Software Pending: {alerts.software_install_pending}")
        print(f"  - Moving Too Fast: {alerts.moving_too_fast_for_policy}")
        print(f"  - Obstructed: {alerts.obstructed}")

    @staticmethod
    def _dump_diagnostics_location(loc) -> None:
        """Pretty-print the location sub-message for DEBUG diagnostics."""
        logger.debug("Dumping the location sub-message for the diagnostics report")  # Log before the dump.
        print("\nLOCATION:")
        # CodeQL py/clear-text-logging-sensitive-data alert 190 (latitude) and alert 191
        # (longitude). Verdict: fixed. Review date: 2026-08-22. Reason: the two prints
        # sent an exact coordinate pair to stdout, and a redirect or a recorded SSH
        # session can capture that pair into a support bundle. The pair locates a
        # customer site or a vehicle to within meters. The default output now rounds to
        # GPS_PRECISION_DECIMALS, which locates the site to about 100 meters and still
        # confirms the right terminal. An operator who needs the exact value sets
        # GPS_EXACT_ENV_VAR. Next review trigger: a change to _format_gps_coordinate, a
        # change to GPS_PRECISION_DECIMALS, or a new CodeQL alert on either print below.
        print(f"  - Latitude: {_format_gps_coordinate(loc.latitude)}")
        print(f"  - Longitude: {_format_gps_coordinate(loc.longitude)}")
        print(f"  - Altitude: {loc.altitude_meters}m")
        if loc.uncertainty_meters_valid:  # The terminal reports the uncertainty only when it is valid.
            print(f"  - Uncertainty: {loc.uncertainty_meters}m")
        logger.debug("Dumped the location sub-message")  # Log after the dump.

    @staticmethod
    def _dump_diagnostics_alignment(align) -> None:
        """Pretty-print the alignment_stats sub-message for DEBUG diagnostics."""
        print("\nALIGNMENT:")
        print(f"  - Boresight Azimuth: {align.boresight_azimuth_deg}°")
        print(f"  - Boresight Elevation: {align.boresight_elevation_deg}°")
        print(f"  - Desired Azimuth: {align.desired_boresight_azimuth_deg}°")
        print(f"  - Desired Elevation: {align.desired_boresight_elevation_deg}°")

    def _build_starlink_stats_dict(self, diag) -> dict:
        """Assemble the public stats dict from a populated diagnostics object."""
        logger.debug("_build_starlink_stats_dict: parsing diagnostics into stats dict")
        is_operational = self._compute_is_operational(diag)  # Overall connection health flag
        azimuth_current, elevation_current, azimuth_target, elevation_target = self._compute_alignment(
            diag
        )  # Antenna pointing coordinates
        self.dish_connected = is_operational  # Cached side-effect: reflect health on the widget
        stats: dict = {
            "connected": is_operational,
            "service_status": self._compute_service_status(diag),
            "hardware_test": self._compute_hardware_test(diag),
            "obstruction_status": self._compute_obstruction_status(diag),
            "terminal_id": self._compute_short_terminal_id(diag),
            "software_version": (diag.software_version if hasattr(diag, "software_version") else "N/A"),
            "hardware_version": (diag.hardware_version if hasattr(diag, "hardware_version") else "N/A"),
            "utc_offset_hours": self._compute_utc_offset_hours(diag),
            "azimuth_current": azimuth_current,
            "elevation_current": elevation_current,
            "azimuth_target": azimuth_target,
            "elevation_target": elevation_target,
            "status_message": self.format_status_message(diag),
        }
        logger.debug(
            "_build_starlink_stats_dict: connected=%s, service=%s, obstruction=%s",
            is_operational,
            stats["service_status"],
            stats["obstruction_status"],
        )
        return stats

    def _show_proto_files_missing_dialog(self) -> None:
        """Show the 'protobuf modules missing' dialog with regeneration instructions."""
        QMessageBox.critical(
            self,
            "Proto Files Missing",
            "Starlink protobuf modules not found.\n\n"
            "Please generate them from the Enterprise API repository:\n\n"
            "1. Navigate to: starlink-api-reference/device-api/\n"
            "2. Run: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. device.proto\n"
            "3. Restart the dashboard\n\n"
            "The files should have been generated already. Check the directory.",
        )

    def _fetch_diagnostics_from_terminal(self):
        """Send the diagnostics gRPC request and return the raw response, or None on failure."""
        pb2, pb2_grpc, error = self._load_starlink_proto_modules()  # Lazy-load generated proto bindings
        if error is not None:  # Modules missing -> show dialog and bail
            self._show_proto_files_missing_dialog()
            return None
        stub = pb2_grpc.DeviceStub(self.channel)  # gRPC client stub
        request = pb2.Request()  # Top-level wrapper request
        request.get_diagnostics.CopyFrom(pb2.GetDiagnosticsRequest())  # Embed diagnostics sub-request
        logger.info("Sending diagnostics request to Starlink terminal...")
        response = stub.Handle(request, timeout=10)  # Synchronous 10s gRPC call
        logger.info("Received response, checking for dish_get_diagnostics field...")
        return response

    @staticmethod
    def _describe_diagnostics(diag) -> tuple[str, str, str]:
        """Return (id, software_version, hardware_version) safely from a diag proto."""
        return (
            diag.id if hasattr(diag, "id") else "N/A",
            diag.software_version if hasattr(diag, "software_version") else "N/A",
            diag.hardware_version if hasattr(diag, "hardware_version") else "N/A",
        )

    def get_starlink_stats(self) -> dict:
        """Query Starlink terminal for diagnostics via gRPC. Returns default dict on error."""
        if not self.channel:  # Caller hasn't connected to a terminal yet
            logger.warning("Cannot get stats: Not connected to Starlink terminal")
            return dict(self._DEFAULT_STARLINK_STATS)  # Return a fresh copy of the defaults
        try:
            response = self._fetch_diagnostics_from_terminal()  # Delegate gRPC + proto loading
            if response is None or not response.HasField("dish_get_diagnostics"):
                logger.warning("Response did not contain dish_get_diagnostics field")
                return dict(self._DEFAULT_STARLINK_STATS)  # No diagnostics -> defaults
            diag = response.dish_get_diagnostics  # Strongly-typed diagnostics sub-message
            term_id, software_ver, hardware_ver = self._describe_diagnostics(diag)
            logger.info(
                "Got diagnostics - ID: %s, Software: %s, Hardware: %s",
                term_id,
                software_ver,
                hardware_ver,
            )
            self._dump_diagnostics_debug(diag)  # No-op unless DEBUG logging is enabled
            return self._build_starlink_stats_dict(diag)  # Final assembled stats dict
        except Exception as error:
            logger.error("Error retrieving Starlink diagnostics: %s", error)
            import traceback

            logger.error(traceback.format_exc())
            return dict(self._DEFAULT_STARLINK_STATS)  # Failure path -> safe defaults

    _DISABLEMENT_CODE_MESSAGES: dict[int, str] = {
        1: "Service: ACTIVE",
        2: "Service: NO ACTIVE ACCOUNT",
        3: "Service: TOO FAR FROM SERVICE ADDRESS",
        6: "Service: BLOCKED COUNTRY",
    }

    _STATUS_ALERT_FIELDS: tuple[tuple[str, str], ...] = (
        ("motors_stuck", "Motors Stuck"),
        ("dish_thermal_shutdown", "Thermal Shutdown"),
        ("dish_thermal_throttle", "Thermal Throttle"),
        ("mast_not_near_vertical", "Mast Not Vertical"),
        ("obstructed", "Obstructed"),
        ("dish_is_heating", "Heating"),
        ("slow_ethernet_speeds", "Slow Ethernet"),
    )

    @staticmethod
    def _status_part_terminal_id(diag) -> str | None:
        """Return the terminal-ID status line or None if unavailable."""
        if not (hasattr(diag, "id") and diag.id):  # No terminal ID -> nothing to report
            return None
        return f"Terminal ID: {diag.id}"  # Format the human-readable terminal identifier

    @staticmethod
    def _status_part_self_test(diag) -> str | None:
        """Return the hardware self-test status line or None if unavailable."""
        if not hasattr(diag, "hardware_self_test"):  # Field missing -> skip
            return None
        result = diag.hardware_self_test  # Numeric self-test result code
        if result == 1:  # 1 == PASSED per Starlink proto
            return "Self Test: PASSED"
        if result == 2:  # 2 == FAILED per Starlink proto
            return "Self Test: FAILED"
        return None  # Any other code is treated as "no result"

    @classmethod
    def _status_part_disablement(cls, diag) -> str | None:
        """Return the service disablement status line or None if unavailable."""
        if not hasattr(diag, "disablement_code"):  # Field missing -> skip
            return None
        code = diag.disablement_code  # Numeric disablement code from proto
        if code in cls._DISABLEMENT_CODE_MESSAGES:  # Known code -> use mapped message
            return cls._DISABLEMENT_CODE_MESSAGES[code]
        if code > 0:  # Unknown but non-zero -> generic disabled message
            return f"Service: DISABLED (Code {code})"
        return None  # Code 0 (or negative) means no message

    @classmethod
    def _status_part_alerts(cls, diag) -> str | None:
        """Return the active-alerts status line or None if no alerts/field."""
        if not hasattr(diag, "alerts"):  # Alerts sub-message missing -> skip
            return None
        alerts = diag.alerts  # Alerts sub-object from proto
        triggered = [
            label for attr, label in cls._STATUS_ALERT_FIELDS if getattr(alerts, attr, False)
        ]  # Collect human-readable labels for any flag that is True
        return f"Alerts: {', '.join(triggered)}" if triggered else None

    @staticmethod
    def _status_part_stowed(diag) -> str | None:
        """Return the stowed-status line or None if not stowed/unknown."""
        if not (hasattr(diag, "stowed") and diag.stowed):  # Not stowed (or unknown)
            return None
        return "Status: STOWED"

    @staticmethod
    def _status_part_location(diag) -> str | None:
        """Return the location status line or None if disabled/unavailable."""
        if not (hasattr(diag, "location") and diag.location.enabled):  # Location reporting off
            return None
        loc = diag.location  # Location sub-object
        return f"Location: {loc.latitude:.4f}, {loc.longitude:.4f}"

    @classmethod
    def _collect_status_parts(cls, diag) -> list[str]:
        """Run each status part builder and return non-empty results in display order."""
        builders = (
            cls._status_part_terminal_id,
            cls._status_part_self_test,
            cls._status_part_disablement,
            cls._status_part_alerts,
            cls._status_part_stowed,
            cls._status_part_location,
        )  # Ordered tuple of part builders -- evaluation order = display order
        return [part for part in (build(diag) for build in builders) if part]

    def format_status_message(self, diag) -> str:
        """Format detailed status message from Starlink diagnostics object."""
        logger.debug("format_status_message: assembling parts from diagnostics object")
        try:
            parts = self._collect_status_parts(diag)  # Delegate per-part assembly + filtering
            logger.debug("format_status_message: produced %d non-empty parts", len(parts))
            return "\n".join(parts) if parts else "Connected - No issues detected"
        except Exception as error:
            logger.error("Error formatting status message: %s", error)
            import traceback

            logger.error(traceback.format_exc())
            return "Status unavailable"

    def refresh_stats(self):
        """Refresh all statistics from Starlink terminal."""
        if not self.connected:
            return

        try:
            logger.debug("Refreshing Starlink statistics")

            # Get actual statistics from Starlink terminal
            stats = self.get_starlink_stats()

            if stats is None:
                logger.warning("No data received from Starlink terminal")
                self.status_bar.showMessage("Warning: No data received from terminal")
                return

            # Update all widgets
            self.update_metrics(stats)

            # Update timestamp
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.timestamp_label.setText(f"Last Updated: {current_time}")
            self.status_bar.showMessage(
                f"Connected to {self.starlink_ip} - Auto-refresh every {self.update_interval/1000}s"
            )

        except Exception as error:
            logger.error("Failed to refresh stats: %s", error)
            self.status_bar.showMessage(f"Error: {error}")

    def update_metrics(self, stats: dict[str, Any]):
        """Update all metric widgets with new data."""
        # Row 1: Status and Service
        connected = stats.get("connected", False)
        self.connection_status.set_value("ONLINE" if connected else "OFFLINE")
        self.connection_status.set_status_color(connected)

        service = stats.get("service_status", "UNKNOWN")
        self.service_status.set_value(service)
        self.service_status.set_status_color(service == "ACTIVE")

        hardware_test = stats.get("hardware_test", "UNKNOWN")
        self.hardware_test.set_value(hardware_test)
        self.hardware_test.set_status_color(hardware_test == "PASSED")

        obstruction = stats.get("obstruction_status", "UNKNOWN")
        self.obstruction_widget.set_value(obstruction)
        self.obstruction_widget.set_status_color(obstruction == "CLEAR")

        # Row 2: Hardware and Software
        self.terminal_id.set_value(stats.get("terminal_id", "N/A"))

        software = stats.get("software_version", "N/A")
        if len(software) > 20:
            software = software[:17] + "..."
        self.software_widget.set_value(software)

        hardware = stats.get("hardware_version", "N/A")
        self.hardware_widget.set_value(hardware)

        utc_offset = stats.get("utc_offset_hours", 0)
        self.utc_offset_widget.set_value(f"{utc_offset:+.1f}")

        # Row 3: Alignment
        azimuth_current = stats.get("azimuth_current", 0.0)
        self.azimuth_current.set_value(f"{azimuth_current:.1f}")

        elevation_current = stats.get("elevation_current", 0.0)
        self.elevation_current.set_value(f"{elevation_current:.1f}")

        azimuth_target = stats.get("azimuth_target", 0.0)
        self.azimuth_target.set_value(f"{azimuth_target:.1f}")

        elevation_target = stats.get("elevation_target", 0.0)
        self.elevation_target.set_value(f"{elevation_target:.1f}")

        # Calculate alignment accuracy and color code
        azimuth_diff = abs(azimuth_current - azimuth_target)
        elevation_diff = abs(elevation_current - elevation_target)
        _well_aligned = azimuth_diff < 5.0 and elevation_diff < 5.0

        self.azimuth_current.set_status_color(azimuth_diff < 5.0)
        self.elevation_current.set_status_color(elevation_diff < 5.0)

        # Status text
        status_message = stats.get("status_message", "No status available")
        self.status_text.setText(status_message)


def main():
    """Main entry point for the Starlink Dashboard application."""
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Starlink Enterprise Dashboard")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with verbose terminal output")
    args = parser.parse_args()

    # Set logging level based on debug flag
    if args.debug:
        logger.setLevel(logging.DEBUG)
        print("\n" + "=" * 60)
        print("DEBUG MODE ENABLED - Verbose output active")
        print("=" * 60 + "\n")

    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Starlink Enterprise Dashboard")
    app.setOrganizationName("MistHelper Project")
    app.setApplicationVersion("1.0.0")

    # Create and show main window
    dashboard = StarlinkDashboard()
    dashboard.show()

    logger.info("Starlink Dashboard started")

    # Run application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
