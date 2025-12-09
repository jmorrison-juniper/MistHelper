#!/usr/bin/env python3
"""
Starlink Enterprise TUI Monitor
A btop-style terminal user interface for monitoring Starlink Enterprise terminals.

Features:
- Real-time stats display with auto-refresh
- btop-inspired layout with box drawing
- Color-coded status indicators
- Keyboard navigation (q=quit, r=refresh, h=help)
- Progress bars for alignment accuracy
- Beautiful terminal graphics using Rich library

Author: System
Date: 2025-10-20
"""

import sys
import os
import time
import argparse
import logging
from datetime import datetime
from typing import Dict, Optional
from threading import Thread, Event
import platform

# Platform-specific keyboard input handling
IS_WINDOWS = platform.system() == 'Windows'
if IS_WINDOWS:
    try:
        import msvcrt
    except ImportError:
        msvcrt = None
else:
    # Unix/Linux/macOS keyboard input
    try:
        import select
        import tty
        import termios
    except ImportError:
        select = None
        tty = None
        termios = None

# Check and install dependencies
def check_and_install_dependencies():
    """Check for required packages and install if missing."""
    required_packages = {
        'rich': 'rich',
        'grpc': 'grpcio',
    }
    
    missing = []
    for module, package in required_packages.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"Installing missing packages: {', '.join(missing)}")
        import subprocess
        try:
            # Try UV first
            result = subprocess.run(['uv', 'pip', 'install'] + missing, 
                                  capture_output=True, timeout=120)
            if result.returncode != 0:
                # Fallback to pip
                subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing,
                             check=True, timeout=120)
        except (subprocess.SubprocessError, FileNotFoundError):
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing,
                         check=True, timeout=120)
        print("Dependencies installed successfully!")

check_and_install_dependencies()

from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn
from rich.align import Align
from rich import box
import grpc

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('data/starlink_tui.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class StarlinkTUI:
    """btop-style TUI for Starlink monitoring."""
    
    def __init__(self, ip_address: str = "192.168.100.1", update_interval: int = 5):
        """
        Initialize the Starlink TUI monitor.
        
        Args:
            ip_address: IP address of Starlink terminal (default: 192.168.100.1)
            update_interval: Update interval in seconds (default: 5)
        """
        self.ip_address = ip_address
        self.update_interval = update_interval
        self.console = Console()
        self.channel: Optional[grpc.Channel] = None
        self.connected = False
        self.stop_event = Event()
        self.last_update = datetime.now()
        self.stats: Dict = {}
        
        # Setup protobuf path
        device_api_path = os.path.join(os.path.dirname(__file__), 'starlink-api-reference', 'device-api')
        if device_api_path not in sys.path:
            sys.path.insert(0, device_api_path)
    
    def connect(self) -> bool:
        """
        Establish connection to Starlink terminal.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to Starlink at {self.ip_address}:9200")
            
            self.channel = grpc.insecure_channel(
                f'{self.ip_address}:9200',
                options=[
                    ('grpc.max_receive_message_length', 1024 * 1024 * 10),  # 10MB
                ]
            )
            
            # Test connection with timeout
            grpc.channel_ready_future(self.channel).result(timeout=5)
            
            self.connected = True
            logger.info("Successfully connected to Starlink terminal")
            return True
            
        except grpc.FutureTimeoutError:
            logger.error(f"Connection timeout: Could not reach {self.ip_address}:9200")
            return False
        except Exception as error:
            logger.error(f"Connection failed: {error}")
            return False
    
    def disconnect(self):
        """Close the gRPC channel."""
        if self.channel:
            self.channel.close()
            self.connected = False
            logger.info("Disconnected from Starlink terminal")
    
    def get_stats(self) -> Dict:
        """
        Query Starlink terminal for diagnostics.
        
        Returns:
            dict: Statistics dictionary with metrics
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
            return default_stats
        
        try:
            import device_pb2  # type: ignore[import]
            import device_pb2_grpc  # type: ignore[import]
            
            stub = device_pb2_grpc.DeviceStub(self.channel)
            request = device_pb2.Request()
            request.get_diagnostics.CopyFrom(device_pb2.GetDiagnosticsRequest())
            
            response = stub.Handle(request, timeout=10)
            
            if response.HasField('dish_get_diagnostics'):
                diag = response.dish_get_diagnostics
                
                # Service status based on disablement_code
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
                
                # Obstruction status
                obstruction_status = "CLEAR"
                if hasattr(diag, 'alerts') and diag.alerts.obstructed:
                    obstruction_status = "OBSTRUCTED"
                
                # Terminal info
                terminal_id = getattr(diag, 'id', 'N/A')
                if len(terminal_id) > 30:
                    terminal_id = terminal_id[:12] + "..." + terminal_id[-12:]
                
                software_version = getattr(diag, 'software_version', 'N/A')
                hardware_version = getattr(diag, 'hardware_version', 'N/A')
                
                # UTC offset in hours
                utc_offset_hours = 0
                if hasattr(diag, 'utc_offset_s'):
                    utc_offset_hours = diag.utc_offset_s / 3600.0
                
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
                
                return {
                    'connected': True,
                    'service_status': service_status,
                    'hardware_test': hardware_test,
                    'obstruction_status': obstruction_status,
                    'terminal_id': terminal_id,
                    'software_version': software_version,
                    'hardware_version': hardware_version,
                    'utc_offset_hours': utc_offset_hours,
                    'azimuth_current': azimuth_current,
                    'elevation_current': elevation_current,
                    'azimuth_target': azimuth_target,
                    'elevation_target': elevation_target,
                    'status_message': f"Terminal ID: {terminal_id}\nSelf Test: {hardware_test}\nService: {service_status}"
                }
            
            return default_stats
            
        except Exception as error:
            logger.error(f"Failed to get stats: {error}", exc_info=True)
            return default_stats
    
    def create_header(self) -> Panel:
        """Create the header panel with title and status."""
        header_text = Text()
        header_text.append("S", style="bold cyan")
        header_text.append("tarlink ", style="bold white")
        header_text.append("E", style="bold cyan")
        header_text.append("nterprise ", style="bold white")
        header_text.append("M", style="bold cyan")
        header_text.append("onitor", style="bold white")
        
        # Connection status
        if self.connected:
            status = Text(" [CONNECTED] ", style="bold black on green")
        else:
            status = Text(" [DISCONNECTED] ", style="bold white on red")
        
        # Timestamp
        timestamp = Text(f" Last Update: {self.last_update.strftime('%Y-%m-%d %H:%M:%S')} ", 
                        style="dim white")
        
        header_line = Text.assemble(header_text, " ", status, " ", timestamp)
        
        return Panel(
            Align.center(header_line),
            box=box.DOUBLE,
            style="bold cyan",
            padding=(0, 1)
        )
    
    def create_connection_panel(self) -> Panel:
        """Create connection info panel."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style="cyan", width=20)
        table.add_column("Value", style="bold white")
        
        table.add_row("IP Address", self.ip_address)
        table.add_row("Port", "9200")
        table.add_row("Protocol", "gRPC")
        table.add_row("Update Interval", f"{self.update_interval}s")
        
        return Panel(
            table,
            title="[bold cyan]Connection",
            border_style="cyan",
            box=box.ROUNDED
        )
    
    def create_status_panel(self) -> Panel:
        """Create main status panel with color-coded indicators."""
        table = Table(show_header=True, box=None, padding=(0, 2))
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Status", justify="center", width=15)
        
        stats = self.stats
        
        # Connection
        conn_status = "[bold green]ONLINE[/]" if stats.get('connected') else "[bold red]OFFLINE[/]"
        table.add_row("Connection", conn_status)
        
        # Service
        service = stats.get('service_status', 'UNKNOWN')
        service_color = "green" if service == "ACTIVE" else "red"
        table.add_row("Service Status", f"[bold {service_color}]{service}[/]")
        
        # Hardware Test
        hw_test = stats.get('hardware_test', 'UNKNOWN')
        hw_color = "green" if hw_test == "PASSED" else "red"
        table.add_row("Self Test", f"[bold {hw_color}]{hw_test}[/]")
        
        # Obstructions
        obstruction = stats.get('obstruction_status', 'UNKNOWN')
        obs_color = "green" if obstruction == "CLEAR" else "red"
        table.add_row("Obstructions", f"[bold {obs_color}]{obstruction}[/]")
        
        return Panel(
            table,
            title="[bold green]System Status",
            border_style="green",
            box=box.ROUNDED
        )
    
    def create_info_panel(self) -> Panel:
        """Create terminal info panel."""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style="yellow", width=20)
        table.add_column("Value", style="bold white")
        
        stats = self.stats
        
        table.add_row("Terminal ID", stats.get('terminal_id', 'N/A'))
        table.add_row("Software Version", stats.get('software_version', 'N/A'))
        table.add_row("Hardware Version", stats.get('hardware_version', 'N/A'))
        table.add_row("UTC Offset", f"{stats.get('utc_offset_hours', 0):.1f} hours")
        
        return Panel(
            table,
            title="[bold yellow]Terminal Information",
            border_style="yellow",
            box=box.ROUNDED
        )
    
    def create_alignment_panel(self) -> Panel:
        """Create dish alignment panel with progress bars."""
        stats = self.stats
        
        # Current position
        azimuth_current = stats.get('azimuth_current', 0.0)
        elevation_current = stats.get('elevation_current', 0.0)
        
        # Target position
        azimuth_target = stats.get('azimuth_target', 0.0)
        elevation_target = stats.get('elevation_target', 0.0)
        
        # Calculate alignment deltas
        azimuth_diff = abs(azimuth_current - azimuth_target)
        elevation_diff = abs(elevation_current - elevation_target)
        
        # Calculate accuracy percentage based on Starlink API documented ranges:
        # - Azimuth: 0-360° (compass bearing, 0=North, 90=East, 180=South, 270=West)
        # - Elevation: 0-90° (0=vertical/upright, 90=horizontal/flat)
        # 
        # Accuracy calculation: error% = (angular_diff / total_range) * 100
        # Then: accuracy% = 100 - error%
        
        azimuth_error_pct = (azimuth_diff / 360.0) * 100
        azimuth_accuracy = max(0, min(100, 100 - azimuth_error_pct))
        
        elevation_error_pct = (elevation_diff / 90.0) * 100
        elevation_accuracy = max(0, min(100, 100 - elevation_error_pct))
        
        # Create table
        table = Table(show_header=True, box=None, padding=(0, 1))
        table.add_column("Axis", style="magenta", width=12)
        table.add_column("Current", justify="right", width=10)
        table.add_column("Target", justify="right", width=10)
        table.add_column("Accuracy & Delta", width=40)
        
        # Azimuth row with color based on accuracy percentage
        # Green: >98% accurate (<7.2° error), Yellow: >95% accurate (<18° error), Red: otherwise
        azimuth_color = "green" if azimuth_accuracy > 98 else "yellow" if azimuth_accuracy > 95 else "red"
        azimuth_bar = self.create_progress_bar(azimuth_accuracy, azimuth_color)
        diff_display = f"[dim](Δ {azimuth_diff:.1f}°)[/]" if azimuth_diff > 0.5 else ""
        table.add_row(
            "Azimuth",
            f"[bold cyan]{azimuth_current:6.1f}°[/]",
            f"[bold white]{azimuth_target:6.1f}°[/]",
            f"{azimuth_bar} {diff_display}"
        )
        
        # Elevation row with color based on accuracy percentage
        # Green: >98% accurate (<1.8° error), Yellow: >95% accurate (<4.5° error), Red: otherwise
        elevation_color = "green" if elevation_accuracy > 98 else "yellow" if elevation_accuracy > 95 else "red"
        elevation_bar = self.create_progress_bar(elevation_accuracy, elevation_color)
        diff_display = f"[dim](Δ {elevation_diff:.1f}°)[/]" if elevation_diff > 0.5 else ""
        table.add_row(
            "Elevation",
            f"[bold cyan]{elevation_current:6.1f}°[/]",
            f"[bold white]{elevation_target:6.1f}°[/]",
            f"{elevation_bar} {diff_display}"
        )
        
        return Panel(
            table,
            title="[bold magenta]Dish Alignment",
            border_style="magenta",
            box=box.ROUNDED
        )
    
    def create_progress_bar(self, value: float, color: str) -> str:
        """Create a text-based progress bar."""
        width = 20
        filled = int(value / 100 * width)
        empty = width - filled
        
        bar = "█" * filled + "░" * empty
        return f"[{color}]{bar}[/] [{color}]{value:5.1f}%[/]"
    
    def create_help_panel(self) -> Panel:
        """Create help/keybindings panel."""
        help_text = Text()
        help_text.append("q", style="bold cyan")
        help_text.append(" Quit  ", style="white")
        help_text.append("r", style="bold cyan")
        help_text.append(" Refresh Now  ", style="white")
        help_text.append("h", style="bold cyan")
        help_text.append(" Help", style="white")
        
        return Panel(
            Align.center(help_text),
            box=box.ROUNDED,
            style="dim white"
        )
    
    def create_layout(self) -> Layout:
        """Create the overall btop-style layout."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["left"].split_column(
            Layout(name="connection", size=8),
            Layout(name="status", size=12)
        )
        
        layout["right"].split_column(
            Layout(name="info", size=10),
            Layout(name="alignment", size=10)
        )
        
        # Populate layout
        layout["header"].update(self.create_header())
        layout["connection"].update(self.create_connection_panel())
        layout["status"].update(self.create_status_panel())
        layout["info"].update(self.create_info_panel())
        layout["alignment"].update(self.create_alignment_panel())
        layout["footer"].update(self.create_help_panel())
        
        return layout
    
    def update_stats(self):
        """Update stats from Starlink terminal."""
        self.stats = self.get_stats()
        self.last_update = datetime.now()
    
    def check_keyboard_input(self):
        """Check for keyboard input (cross-platform)."""
        key = None
        
        try:
            if IS_WINDOWS and msvcrt:
                # Windows keyboard input using msvcrt
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
            else:
                # Unix/Linux/macOS keyboard input using select
                if select and sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1).lower()
        except Exception as e:
            logger.debug(f"Keyboard input error: {e}")
            return False
        
        if key:
            if key == 'q':
                logger.info("User pressed 'q' - stopping application")
                self.stop_event.set()
                return True
            elif key == 'r':
                logger.info("User pressed 'r' - refreshing stats")
                self.update_stats()
                return True
            elif key == 'h':
                logger.info("User pressed 'h' - showing help")
                # Help is already shown in footer
                return True
        
        return False
    
    def run(self):
        """Run the TUI application."""
        # Connect to Starlink
        if not self.connect():
            self.console.print("[bold red]Failed to connect to Starlink terminal![/]")
            self.console.print(f"[yellow]Please check that {self.ip_address}:9200 is accessible[/]")
            return
        
        # Initial stats fetch
        self.update_stats()
        
        try:
            with Live(
                self.create_layout(),
                console=self.console,
                screen=True,
                refresh_per_second=2
            ) as live:
                
                last_refresh = time.time()
                
                while not self.stop_event.is_set():
                    # Check for keyboard input
                    if self.check_keyboard_input():
                        if self.stop_event.is_set():
                            break
                    
                    # Check if it's time to refresh
                    current_time = time.time()
                    if current_time - last_refresh >= self.update_interval:
                        self.update_stats()
                        last_refresh = current_time
                    
                    # Update display
                    live.update(self.create_layout())
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            pass
        finally:
            self.disconnect()
            self.console.print("\n[bold cyan]Starlink TUI Monitor stopped.[/]")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Starlink Enterprise TUI Monitor - btop-style interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Connect to default IP (192.168.100.1)
  %(prog)s --ip 10.0.0.1            # Connect to custom IP
  %(prog)s --interval 10            # Update every 10 seconds
  %(prog)s --ip 10.0.0.1 -i 3       # Custom IP with 3s updates

Keyboard Controls:
  q     - Quit the application
  r     - Refresh stats immediately
  h     - Show help
  Ctrl+C - Exit
        """
    )
    
    parser.add_argument(
        '--ip',
        type=str,
        default='192.168.100.1',
        help='Starlink terminal IP address (default: 192.168.100.1)'
    )
    
    parser.add_argument(
        '-i', '--interval',
        type=int,
        default=5,
        help='Update interval in seconds (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Create and run TUI
    tui = StarlinkTUI(ip_address=args.ip, update_interval=args.interval)
    
    try:
        tui.run()
    except Exception as error:
        logger.error(f"Application error: {error}", exc_info=True)
        print(f"\n[ERROR] {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
