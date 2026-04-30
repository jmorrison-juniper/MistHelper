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

import sys
import os
import subprocess
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Tuple


def check_and_install_uv() -> bool:
    """
    Check if UV package manager is installed, and install it if missing.
    UV is preferred over pip for faster package installation.
    
    Returns:
        bool: True if UV is available (either already installed or newly installed)
    """
    try:
        # Check if UV is already installed
        result = subprocess.run(
            ['uv', '--version'],
            capture_output=True,
            text=True,
            timeout=5
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
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'uv'],
            capture_output=True,
            text=True,
            timeout=60
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


def check_and_install_grpcio() -> Tuple[bool, str]:
    """
    Check if grpcio packages are installed, and install them if missing.
    Uses UV if available, otherwise falls back to pip.
    
    Returns:
        Tuple[bool, str]: (Success status, Error message if any)
    """
    try:
        # Try importing grpcio to check if it exists
        import grpc
        import google.protobuf
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
    
    packages = ['grpcio', 'grpcio-tools', 'protobuf']
    
    try:
        if uv_available:
            # Use UV for faster installation
            print("Using UV for faster installation...")
            print(f"Installing: {', '.join(packages)}")
            result = subprocess.run(
                ['uv', 'pip', 'install'] + packages,
                capture_output=False,  # Show progress to user
                timeout=300
            )
        else:
            # Fall back to pip
            print("Using pip for installation...")
            print(f"Installing: {', '.join(packages)}")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install'] + packages,
                capture_output=False,  # Show progress to user
                timeout=300
            )
        
        if result.returncode == 0:
            print("\n" + "="*60)
            print("gRPC packages installed successfully!")
            print("="*60)
            return True, ""
            
        else:
            error_msg = (
                f"\nFailed to install gRPC packages.\n\n"
                f"Please try manual installation:\n"
                f"  pip install grpcio grpcio-tools protobuf\n\n"
                f"Or if using UV:\n"
                f"  uv pip install grpcio grpcio-tools protobuf"
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


def check_and_install_pyqt6() -> Tuple[bool, str]:
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
            result = subprocess.run(
                ['uv', 'pip', 'install', 'PyQt6'],
                capture_output=False,  # Show progress to user
                timeout=300
            )
        else:
            # Fall back to pip
            print("Using pip for installation...")
            print("Please wait, downloading and installing PyQt6 (approximately 50MB)...")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', 'PyQt6'],
                capture_output=False,  # Show progress to user
                timeout=300
            )
        
        if result.returncode == 0:
            print("\n" + "="*60)
            print("PyQt6 installed successfully!")
            print("="*60)
            print("Restarting application with GUI support...\n")
            
            # Restart the script to load the newly installed PyQt6
            os.execv(sys.executable, [sys.executable] + sys.argv)
            
        else:
            error_msg = (
                f"\nFailed to install PyQt6.\n\n"
                f"Please try manual installation:\n"
                f"  pip install PyQt6\n\n"
                f"Or if using UV:\n"
                f"  uv pip install PyQt6"
            )
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        error_msg = (
            "Installation timed out. Please check your internet connection and try:\n"
            "  pip install PyQt6"
        )
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
            qt_plugins = os.path.join(site_path, 'PyQt6', 'Qt6', 'plugins')
            if os.path.exists(qt_plugins):
                os.environ['QT_PLUGIN_PATH'] = qt_plugins
                print(f"Set Qt plugin path to: {qt_plugins}")
                break
    except Exception as error:
        print(f"Warning: Could not set Qt plugin path: {error}")

# Apply Qt plugin path fix
fix_qt_plugin_path()

# Now safe to import PyQt6
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QGroupBox, QGridLayout, QProgressBar,
        QLineEdit, QMessageBox, QStatusBar, QFrame, QComboBox
    )
    from PyQt6.QtCore import QTimer, Qt, QSize
    from PyQt6.QtGui import QFont, QPalette, QColor, QIcon
except ImportError as import_error:
    print(f"\nERROR: Failed to import PyQt6 even after installation: {import_error}")
    print("Please try reinstalling:")
    print("  pip uninstall PyQt6")
    print("  pip install PyQt6")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('starlink_dashboard')


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
            "background-color: #1E1E1E; color: #E0E0E0; padding: 15px; "
            "border-radius: 5px; line-height: 1.5;"
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
        logger.info(f"Theme changed to: {theme_name}")
        
    def close_application(self):
        """Close the application gracefully."""
        reply = QMessageBox.question(
            self, 'Exit Confirmation',
            'Are you sure you want to exit the Starlink Dashboard?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
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
            value_color = "#1A73E8"
            unit_color = "#80868B"
            good_color = "#137333"
            bad_color = "#C5221F"
            status_bg = "#F8F9FA"
            status_fg = "#202124"
            section_header_color = "#1A73E8"
        elif theme == "TRON":
            title_color = "#00CCCC"
            value_color = "#00FFFF"
            unit_color = "#009999"
            good_color = "#FFD700"
            bad_color = "#FF6600"
            status_bg = "#0A0A0A"
            status_fg = "#00FFFF"
            section_header_color = "#FFD700"
        elif theme == "Hackers":
            title_color = "#00CC00"
            value_color = "#00FF00"
            unit_color = "#009900"
            good_color = "#00FF00"
            bad_color = "#FF0000"
            status_bg = "#001100"
            status_fg = "#00FF00"
            section_header_color = "#00FF00"
        else:  # Dark
            title_color = "#9AA0A6"
            value_color = "#8AB4F8"
            unit_color = "#80868B"
            good_color = "#81C995"
            bad_color = "#F28B82"
            status_bg = "#202124"
            status_fg = "#E8EAED"
            section_header_color = "#8AB4F8"
        
        # Update all metric widgets
        for widget in [self.connection_status, self.service_status, self.hardware_test,
                      self.obstruction_widget, self.terminal_id, self.software_widget,
                      self.hardware_widget, self.utc_offset_widget, self.azimuth_current,
                      self.elevation_current, self.azimuth_target, self.elevation_target]:
            widget.title_label.setStyleSheet(f"color: {title_color};")
            widget.unit_label.setStyleSheet(f"color: {unit_color};")
        
        # Update section header labels
        self.current_position_label.setStyleSheet(
            f"font-weight: bold; color: {section_header_color}; font-size: 11pt;"
        )
        self.target_position_label.setStyleSheet(
            f"font-weight: bold; color: {section_header_color}; font-size: 11pt;"
        )
            
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
                QMessageBox.warning(
                    self, "Invalid Input", 
                    "Please enter a valid Starlink IP address."
                )
                return
                
            self.starlink_ip = ip_address
            logger.info(f"Attempting to connect to Starlink at {self.starlink_ip}")
            
            # Actual gRPC connection
            if self.connect_to_starlink():
                self.connected = True
                self.client_connected = True  # We are now connected to the dish
                self.connect_button.setText("Disconnect")
                self.connect_button.setStyleSheet(
                    "background-color: #D32F2F; color: white; font-weight: bold;"
                )
                self.refresh_button.setEnabled(True)
                self.ip_input.setEnabled(False)
                self.status_bar.showMessage(f"Connected to {self.starlink_ip}")
                self.update_client_status_display()
                
                # Start auto-refresh
                self.timer.start(self.update_interval)
                self.refresh_stats()
            else:
                QMessageBox.critical(
                    self, "Connection Failed",
                    f"Failed to connect to Starlink at {self.starlink_ip}.\n\n"
                    "Please verify:\n"
                    "- IP address is correct\n"
                    "- Device is powered on\n"
                    "- Network connectivity\n"
                    "- gRPC service is accessible"
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
            
            logger.info(f"Connecting to Starlink gRPC service at {self.starlink_ip}:9200")
            
            # Establish gRPC connection to Starlink dish
            # The Starlink dish runs a gRPC service on port 9200
            self.channel = grpc.insecure_channel(
                f'{self.starlink_ip}:9200',
                options=[
                    ('grpc.max_receive_message_length', 1024 * 1024 * 10),  # 10MB
                ]
            )
            
            # Test connection with a timeout
            grpc.channel_ready_future(self.channel).result(timeout=5)
            
            logger.info("Successfully connected to Starlink terminal")
            self.connection_start_time = datetime.now()
            return True
            
        except grpc.FutureTimeoutError:
            logger.error(f"Connection timeout: Could not reach Starlink at {self.starlink_ip}:9200")
            return False
        except Exception as error:
            logger.error(f"Connection failed: {error}")
            return False
    
    def get_starlink_stats(self) -> dict:
        """
        Query Starlink terminal for diagnostics via gRPC.
        
        Returns:
            dict: Statistics dictionary with metrics and status, or default values on error
        """
        default_stats = {
            'connected': False,
            'service_status': 'UNKNOWN',
            'hardware_test': 'UNKNOWN',
            'obstruction_status': 'UNKNOWN',
            'terminal_id': 'N/A',
            'software_version': 'N/A',
            'hardware_version': 'N/A',
            'utc_offset_hours': 0,
            'azimuth_current': 0.0,
            'elevation_current': 0.0,
            'azimuth_target': 0.0,
            'elevation_target': 0.0,
            'status_message': 'Disconnected'
        }
        
        if not self.channel:
            logger.warning("Cannot get stats: Not connected to Starlink terminal")
            return default_stats
        
        try:
            # Import Starlink protobuf modules from the generated files
            # Add the device-api directory to Python path for import
            import sys
            import os
            device_api_path = os.path.join(os.path.dirname(__file__), 'starlink-api-reference', 'device-api')
            if device_api_path not in sys.path:
                sys.path.insert(0, device_api_path)
            
            try:
                import device_pb2  # type: ignore[import]
                import device_pb2_grpc  # type: ignore[import]
            except ImportError as import_error:
                logger.error(f"Starlink protobuf modules not found: {import_error}")
                QMessageBox.critical(
                    self,
                    "Proto Files Missing",
                    "Starlink protobuf modules not found.\n\n"
                    "Please generate them from the Enterprise API repository:\n\n"
                    "1. Navigate to: starlink-api-reference/device-api/\n"
                    "2. Run: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. device.proto\n"
                    "3. Restart the dashboard\n\n"
                    "The files should have been generated already. Check the directory."
                )
                return default_stats
            
            # Create gRPC stub for device service
            stub = device_pb2_grpc.DeviceStub(self.channel)
            
            # Create request for diagnostics information
            request = device_pb2.Request()
            request.get_diagnostics.CopyFrom(device_pb2.GetDiagnosticsRequest())
            
            logger.info("Sending diagnostics request to Starlink terminal...")
            
            # Execute gRPC call with timeout
            response = stub.Handle(request, timeout=10)
            
            logger.info(f"Received response, checking for dish_get_diagnostics field...")
            
            # Extract diagnostics from response
            if response.HasField('dish_get_diagnostics'):
                diag = response.dish_get_diagnostics
                
                logger.info(f"Got diagnostics - ID: {diag.id if hasattr(diag, 'id') else 'N/A'}, "
                           f"Software: {diag.software_version if hasattr(diag, 'software_version') else 'N/A'}, "
                           f"Hardware: {diag.hardware_version if hasattr(diag, 'hardware_version') else 'N/A'}")
                
                # DEBUG: Print full diagnostics object structure
                if logger.isEnabledFor(logging.DEBUG):
                    print("\n" + "="*80)
                    print("FULL DIAGNOSTIC DATA DUMP")
                    print("="*80)
                    print(f"\nRaw protobuf object:\n{diag}")
                    print("\n" + "="*80)
                    print("PARSED FIELDS:")
                    print("="*80)
                    print(f"Terminal ID: {diag.id if hasattr(diag, 'id') else 'N/A'}")
                    print(f"Software Version: {diag.software_version if hasattr(diag, 'software_version') else 'N/A'}")
                    print(f"Hardware Version: {diag.hardware_version if hasattr(diag, 'hardware_version') else 'N/A'}")
                    print(f"UTC Offset: {diag.utc_offset_s if hasattr(diag, 'utc_offset_s') else 'N/A'} seconds")
                    print(f"Hardware Self Test: {diag.hardware_self_test if hasattr(diag, 'hardware_self_test') else 'N/A'}")
                    print(f"Disablement Code: {diag.disablement_code if hasattr(diag, 'disablement_code') else 'N/A'}")
                    print(f"Stowed: {diag.stowed if hasattr(diag, 'stowed') else 'N/A'}")
                    
                    if hasattr(diag, 'alerts'):
                        print("\nALERTS:")
                        print(f"  - Dish Heating: {diag.alerts.dish_is_heating}")
                        print(f"  - Thermal Throttle: {diag.alerts.dish_thermal_throttle}")
                        print(f"  - Thermal Shutdown: {diag.alerts.dish_thermal_shutdown}")
                        print(f"  - Power Supply Throttle: {diag.alerts.power_supply_thermal_throttle}")
                        print(f"  - Motors Stuck: {diag.alerts.motors_stuck}")
                        print(f"  - Mast Not Vertical: {diag.alerts.mast_not_near_vertical}")
                        print(f"  - Slow Ethernet: {diag.alerts.slow_ethernet_speeds}")
                        print(f"  - Software Pending: {diag.alerts.software_install_pending}")
                        print(f"  - Moving Too Fast: {diag.alerts.moving_too_fast_for_policy}")
                        print(f"  - Obstructed: {diag.alerts.obstructed}")
                    
                    if hasattr(diag, 'location') and diag.location.enabled:
                        print(f"\nLOCATION:")
                        print(f"  - Latitude: {diag.location.latitude}")
                        print(f"  - Longitude: {diag.location.longitude}")
                        print(f"  - Altitude: {diag.location.altitude_meters}m")
                        if diag.location.uncertainty_meters_valid:
                            print(f"  - Uncertainty: {diag.location.uncertainty_meters}m")
                    
                    if hasattr(diag, 'alignment_stats'):
                        print(f"\nALIGNMENT:")
                        print(f"  - Boresight Azimuth: {diag.alignment_stats.boresight_azimuth_deg}°")
                        print(f"  - Boresight Elevation: {diag.alignment_stats.boresight_elevation_deg}°")
                        print(f"  - Desired Azimuth: {diag.alignment_stats.desired_boresight_azimuth_deg}°")
                        print(f"  - Desired Elevation: {diag.alignment_stats.desired_boresight_elevation_deg}°")
                    
                    print("="*80 + "\n")
                
                # Parse all available metrics from diagnostics object
                # Map to the keys expected by update_metrics()
                
                # Determine if system is operational
                is_operational = True
                if hasattr(diag, 'alerts'):
                    is_operational = not (diag.alerts.dish_thermal_shutdown or diag.alerts.motors_stuck)
                    logger.debug(f"Alert status: obstructed={diag.alerts.obstructed}, "
                               f"thermal_shutdown={diag.alerts.dish_thermal_shutdown}, "
                               f"motors_stuck={diag.alerts.motors_stuck}")
                
                # Determine obstruction status
                obstruction_status = "CLEAR"
                if hasattr(diag, 'alerts') and diag.alerts.obstructed:
                    obstruction_status = "OBSTRUCTED"
                
                # Determine service status
                service_status = "UNKNOWN"
                if hasattr(diag, 'disablement_code'):
                    if diag.disablement_code == 1:  # OKAY
                        service_status = "ACTIVE"
                    elif diag.disablement_code == 2:
                        service_status = "NO ACCOUNT"
                    elif diag.disablement_code == 3:
                        service_status = "TOO FAR"
                    elif diag.disablement_code == 6:
                        service_status = "BLOCKED"
                    else:
                        service_status = f"CODE {diag.disablement_code}"
                
                # Hardware self test
                hardware_test = "UNKNOWN"
                if hasattr(diag, 'hardware_self_test'):
                    if diag.hardware_self_test == 1:
                        hardware_test = "PASSED"
                    elif diag.hardware_self_test == 2:
                        hardware_test = "FAILED"
                    else:
                        hardware_test = "NO RESULT"
                
                # Alignment data
                azimuth_current = 0.0
                elevation_current = 0.0
                azimuth_target = 0.0
                elevation_target = 0.0
                if hasattr(diag, 'alignment_stats'):
                    azimuth_current = diag.alignment_stats.boresight_azimuth_deg
                    elevation_current = diag.alignment_stats.boresight_elevation_deg
                    azimuth_target = diag.alignment_stats.desired_boresight_azimuth_deg
                    elevation_target = diag.alignment_stats.desired_boresight_elevation_deg
                
                # UTC offset in hours
                utc_offset_hours = 0
                if hasattr(diag, 'utc_offset_s'):
                    utc_offset_hours = diag.utc_offset_s / 3600.0
                
                # Terminal ID (shortened for display)
                terminal_id = diag.id if hasattr(diag, 'id') else 'N/A'
                if len(terminal_id) > 20:
                    terminal_id = terminal_id[:8] + "..." + terminal_id[-8:]
                
                stats = {
                    # Status and Service
                    'connected': is_operational,
                    'service_status': service_status,
                    'hardware_test': hardware_test,
                    'obstruction_status': obstruction_status,
                    
                    # Hardware and Software
                    'terminal_id': terminal_id,
                    'software_version': diag.software_version if hasattr(diag, 'software_version') else 'N/A',
                    'hardware_version': diag.hardware_version if hasattr(diag, 'hardware_version') else 'N/A',
                    'utc_offset_hours': utc_offset_hours,
                    
                    # Alignment
                    'azimuth_current': azimuth_current,
                    'elevation_current': elevation_current,
                    'azimuth_target': azimuth_target,
                    'elevation_target': elevation_target,
                    
                    # Status message with all diagnostic info
                    'status_message': self.format_status_message(diag),
                }
                
                # Update dish connection status based on alerts
                self.dish_connected = is_operational
                
                logger.debug(f"Retrieved Starlink diagnostics: connected={is_operational}, service={service_status}, obstruction={obstruction_status}")
                return stats
            else:
                logger.warning("Response did not contain dish_get_diagnostics field")
                return default_stats
                
        except Exception as error:
            logger.error(f"Error retrieving Starlink diagnostics: {error}")
            import traceback
            logger.error(traceback.format_exc())
            return default_stats
    
    def format_status_message(self, diag) -> str:
        """
        Format detailed status message from Starlink diagnostics object.
        
        Args:
            diag: Protobuf diagnostics object from dish_get_diagnostics
            
        Returns:
            str: Formatted multi-line status message
        """
        try:
            # Build status message with available information from diagnostics
            message_parts = []
            
            # Terminal identification
            if hasattr(diag, 'id') and diag.id:
                message_parts.append(f"Terminal ID: {diag.id}")
            
            # Hardware self-test result
            if hasattr(diag, 'hardware_self_test'):
                test_result = diag.hardware_self_test
                if test_result == 1:  # PASSED
                    message_parts.append("Self Test: PASSED")
                elif test_result == 2:  # FAILED
                    message_parts.append("Self Test: FAILED")
            
            # Disablement code (service status)
            if hasattr(diag, 'disablement_code'):
                code = diag.disablement_code
                if code == 1:  # OKAY
                    message_parts.append("Service: ACTIVE")
                elif code == 2:
                    message_parts.append("Service: NO ACTIVE ACCOUNT")
                elif code == 3:
                    message_parts.append("Service: TOO FAR FROM SERVICE ADDRESS")
                elif code == 6:
                    message_parts.append("Service: BLOCKED COUNTRY")
                elif code > 0:
                    message_parts.append(f"Service: DISABLED (Code {code})")
            
            # Alerts (if any)
            if hasattr(diag, 'alerts'):
                alert_list = []
                if diag.alerts.motors_stuck:
                    alert_list.append("Motors Stuck")
                if diag.alerts.dish_thermal_shutdown:
                    alert_list.append("Thermal Shutdown")
                if diag.alerts.dish_thermal_throttle:
                    alert_list.append("Thermal Throttle")
                if diag.alerts.mast_not_near_vertical:
                    alert_list.append("Mast Not Vertical")
                if diag.alerts.obstructed:
                    alert_list.append("Obstructed")
                if diag.alerts.dish_is_heating:
                    alert_list.append("Heating")
                if diag.alerts.slow_ethernet_speeds:
                    alert_list.append("Slow Ethernet")
                if alert_list:
                    message_parts.append(f"Alerts: {', '.join(alert_list)}")
            
            # Stow status
            if hasattr(diag, 'stowed') and diag.stowed:
                message_parts.append("Status: STOWED")
            
            # Location info (if enabled)
            if hasattr(diag, 'location') and diag.location.enabled:
                loc = diag.location
                message_parts.append(f"Location: {loc.latitude:.4f}, {loc.longitude:.4f}")
            
            # Return formatted message or default
            return '\n'.join(message_parts) if message_parts else "Connected - No issues detected"
            
        except Exception as error:
            logger.error(f"Error formatting status message: {error}")
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
            logger.error(f"Failed to refresh stats: {error}")
            self.status_bar.showMessage(f"Error: {error}")
        
    def update_metrics(self, stats: Dict[str, Any]):
        """Update all metric widgets with new data."""
        # Row 1: Status and Service
        connected = stats.get('connected', False)
        self.connection_status.set_value("ONLINE" if connected else "OFFLINE")
        self.connection_status.set_status_color(connected)
        
        service = stats.get('service_status', 'UNKNOWN')
        self.service_status.set_value(service)
        self.service_status.set_status_color(service == "ACTIVE")
        
        hardware_test = stats.get('hardware_test', 'UNKNOWN')
        self.hardware_test.set_value(hardware_test)
        self.hardware_test.set_status_color(hardware_test == "PASSED")
        
        obstruction = stats.get('obstruction_status', 'UNKNOWN')
        self.obstruction_widget.set_value(obstruction)
        self.obstruction_widget.set_status_color(obstruction == "CLEAR")
        
        # Row 2: Hardware and Software
        self.terminal_id.set_value(stats.get('terminal_id', 'N/A'))
        
        software = stats.get('software_version', 'N/A')
        if len(software) > 20:
            software = software[:17] + "..."
        self.software_widget.set_value(software)
        
        hardware = stats.get('hardware_version', 'N/A')
        self.hardware_widget.set_value(hardware)
        
        utc_offset = stats.get('utc_offset_hours', 0)
        self.utc_offset_widget.set_value(f"{utc_offset:+.1f}")
        
        # Row 3: Alignment
        azimuth_current = stats.get('azimuth_current', 0.0)
        self.azimuth_current.set_value(f"{azimuth_current:.1f}")
        
        elevation_current = stats.get('elevation_current', 0.0)
        self.elevation_current.set_value(f"{elevation_current:.1f}")
        
        azimuth_target = stats.get('azimuth_target', 0.0)
        self.azimuth_target.set_value(f"{azimuth_target:.1f}")
        
        elevation_target = stats.get('elevation_target', 0.0)
        self.elevation_target.set_value(f"{elevation_target:.1f}")
        
        # Calculate alignment accuracy and color code
        azimuth_diff = abs(azimuth_current - azimuth_target)
        elevation_diff = abs(elevation_current - elevation_target)
        well_aligned = azimuth_diff < 5.0 and elevation_diff < 5.0
        
        self.azimuth_current.set_status_color(azimuth_diff < 5.0)
        self.elevation_current.set_status_color(elevation_diff < 5.0)
        
        # Status text
        status_message = stats.get('status_message', 'No status available')
        self.status_text.setText(status_message)


def main():
    """Main entry point for the Starlink Dashboard application."""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Starlink Enterprise Dashboard')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug mode with verbose terminal output')
    args = parser.parse_args()
    
    # Set logging level based on debug flag
    if args.debug:
        logger.setLevel(logging.DEBUG)
        print("\n" + "="*60)
        print("DEBUG MODE ENABLED - Verbose output active")
        print("="*60 + "\n")
    
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


if __name__ == '__main__':
    main()
