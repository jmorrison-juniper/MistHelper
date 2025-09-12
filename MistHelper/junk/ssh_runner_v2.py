#!/usr/bin/env python3
"""
Enhanced SSH Runner - Connect to network devices with advanced command execution

This script provides comprehensive SSH functionality with support for both
direct command execution and interactive shell sessions. It's specifically
designed to work well with network devices that require pseudo-terminals.

Version: 2.1.0
Date: 2025-01-09
"""

import sys
import time
import socket
import argparse
import getpass
import logging
import logging.handlers
import os
import re
import ipaddress
import multiprocessing
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from typing import Tuple, Optional
import paramiko
from paramiko import SSHClient, AutoAddPolicy

# Try to import python-dotenv for .env file support
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("   .env file support will be limited to basic parsing")






class EnhancedSSHRunner:
    """Advanced SSH connection and command execution handler with comprehensive validation"""
    
    def __init__(self, timeout: int = 30, logger: logging.Logger = None):
        """
        Initialize SSH runner
        
        Args:
            timeout: Connection timeout in seconds
            logger: Logger instance
        """
        self.timeout = timeout
        self.client = None
        self.logger = logger or logging.getLogger('ssh_runner_v2')
        self.logger.debug(f"EnhancedSSHRunner initialized with timeout={timeout}")
    
    @staticmethod
    def validate_hostname(hostname: str) -> bool:
        """
        Validate hostname or IP address format
        
        Args:
            hostname: Hostname or IP address to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not hostname or not isinstance(hostname, str):
            return False
        
        # Check length limits
        if len(hostname) > 253:  # RFC 1035 limit
            return False
        
        # Try to parse as IP address first
        try:
            ipaddress.ip_address(hostname)
            return True
        except ValueError:
            pass
        
        # Validate as hostname (RFC 1123 compliant)
        if len(hostname) > 253:
            return False
        
        # Remove trailing dot if present
        hostname = hostname.rstrip('.')
        
        # Check overall format
        hostname_pattern = re.compile(
            r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'
        )
        
        return bool(hostname_pattern.match(hostname))
    
    @staticmethod
    def validate_port(port: int) -> bool:
        """
        Validate port number is in valid range
        
        Args:
            port: Port number to validate
            
        Returns:
            bool: True if valid (1-65535), False otherwise
        """
        return isinstance(port, int) and 1 <= port <= 65535
    
    @staticmethod
    def validate_timeout(timeout: int) -> bool:
        """
        Validate timeout value is reasonable
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            bool: True if valid (1-3600), False otherwise
        """
        return isinstance(timeout, int) and 1 <= timeout <= 3600
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """
        Validate SSH username format
        
        Args:
            username: Username to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not username or not isinstance(username, str):
            return False
        
        # Length check (typical Unix limit is 32 chars)
        if len(username) > 32 or len(username) < 1:
            return False
        
        # Basic character validation (alphanumeric, underscore, hyphen, dot)
        username_pattern = re.compile(r'^[a-zA-Z0-9._-]+$')
        return bool(username_pattern.match(username))
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal and invalid characters
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename safe for filesystem use
        """
        if not filename:
            return "unknown"
        
        # Remove or replace dangerous characters
        # Keep only alphanumeric, underscore, hyphen, and dot
        sanitized = re.sub(r'[^\w\-_\.]', '_', filename)
        
        # Remove leading/trailing dots and dashes
        sanitized = sanitized.strip('.-')
        
        # Ensure filename isn't empty after sanitization
        if not sanitized:
            sanitized = "sanitized_host"
        
        # Limit length to prevent filesystem issues
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        # Prevent reserved filenames on Windows
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]
        if sanitized.upper() in reserved_names:
            sanitized = f"host_{sanitized}"
        
        return sanitized
    
    @staticmethod
    def validate_command(command: str) -> bool:
        """
        Basic validation for SSH commands
        
        Args:
            command: Command to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not command or not isinstance(command, str):
            return False
        
        # Length check (reasonable command length limit)
        if len(command) > 1000:
            return False
        
        # Check for null bytes (can cause issues in some contexts)
        if '\x00' in command:
            return False
        
        return True
    
    @staticmethod
    def validate_thread_count(thread_count: int, max_hosts: int) -> int:
        """
        Validate and adjust thread count to reasonable limits
        
        Args:
            thread_count: Requested thread count
            max_hosts: Maximum number of hosts
            
        Returns:
            int: Validated thread count
        """
        if not isinstance(thread_count, int) or thread_count <= 0:
            return min(max_hosts, multiprocessing.cpu_count())
        
        # Limit to reasonable maximum (don't overwhelm system)
        max_reasonable_threads = min(50, max_hosts * 2)
        return min(thread_count, max_reasonable_threads, max_hosts)
    
    @staticmethod
    def parse_host_list(hosts_str: str) -> list:
        """
        Parse comma-separated host list from .env file with validation
        
        Args:
            hosts_str: String containing comma-separated hosts (e.g., '192.168.1.1,192.168.1.2')
            
        Returns:
            list: List of validated hostnames/IPs
        """
        if not hosts_str or not isinstance(hosts_str, str):
            return []
        
        # Length check to prevent DoS
        if len(hosts_str) > 10000:  # Reasonable limit for host list
            print("⚠️  Host list too long, truncating to first 10000 characters")
            hosts_str = hosts_str[:10000]
        
        # Split by comma and validate each host
        hosts = []
        invalid_hosts = []
        
        for host in hosts_str.split(','):
            host = host.strip()
            if not host:  # Skip empty entries
                continue
                
            # Validate hostname/IP format
            if EnhancedSSHRunner.validate_hostname(host):
                hosts.append(host)
            else:
                invalid_hosts.append(host)
        
        # Warn about invalid hosts
        if invalid_hosts:
            print(f"⚠️  Skipping {len(invalid_hosts)} invalid hosts: {', '.join(invalid_hosts[:5])}")
            if len(invalid_hosts) > 5:
                print(f"    ... and {len(invalid_hosts) - 5} more")
        
        # Limit total number of hosts to prevent resource exhaustion
        max_hosts = 100  # Reasonable limit
        if len(hosts) > max_hosts:
            print(f"⚠️  Too many hosts ({len(hosts)}), limiting to first {max_hosts}")
            hosts = hosts[:max_hosts]
        
        return hosts
    
    @staticmethod
    def parse_command_list(commands_str: str) -> list:
        """
        Parse comma-separated command list from .env file with validation
        
        Args:
            commands_str: String containing comma-separated commands (e.g., 'show ver,show route' or '"show ver","show route"')
            
        Returns:
            list: List of validated commands
        """
        if not commands_str or not isinstance(commands_str, str):
            return []
        
        # Length check to prevent DoS
        if len(commands_str) > 50000:  # Reasonable limit for command string
            print("⚠️  Command list too long, truncating to first 50000 characters")
            commands_str = commands_str[:50000]
        
        # Remove outer quotes if present
        commands_str = commands_str.strip('\'"')
        
        # Split by comma and validate each command
        commands = []
        invalid_commands = []
        
        for cmd in commands_str.split(','):
            # Remove quotes and whitespace
            clean_cmd = cmd.strip().strip('\'"').strip()
            
            if not clean_cmd:  # Skip empty commands
                continue
            
            # Validate command
            if EnhancedSSHRunner.validate_command(clean_cmd):
                commands.append(clean_cmd)
            else:
                invalid_commands.append(clean_cmd[:50] + "..." if len(clean_cmd) > 50 else clean_cmd)
        
        # Warn about invalid commands
        if invalid_commands:
            print(f"⚠️  Skipping {len(invalid_commands)} invalid commands: {', '.join(invalid_commands[:3])}")
            if len(invalid_commands) > 3:
                print(f"    ... and {len(invalid_commands) - 3} more")
        
        # Limit total number of commands to prevent resource exhaustion
        max_commands = 50  # Reasonable limit
        if len(commands) > max_commands:
            print(f"⚠️  Too many commands ({len(commands)}), limiting to first {max_commands}")
            commands = commands[:max_commands]
        
        return commands
    
    @staticmethod
    def load_commands_from_csv(csv_file_path: str = "SSH_COMMANDS.CSV") -> list:
        """
        Load SSH commands from a CSV file as fallback when .env has no commands.
        
        Expected CSV format:
        - First column: command
        - Optional second column: description/comment (ignored)
        - Lines starting with # are treated as comments and ignored
        - Empty lines are ignored
        
        Example CSV content:
        # Network device commands
        show version
        show interfaces,Interface status
        show route,Routing table
        
        Args:
            csv_file_path (str): Path to the CSV file (default: SSH_COMMANDS.CSV)
            
        Returns:
            list: List of validated commands loaded from the CSV file
        """
        import csv
        
        commands = []
        
        if not os.path.exists(csv_file_path):
            return commands
            
        try:
            with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                # Use simple comma delimiter instead of trying to detect dialect
                # This is more reliable for simple CSV files with comments
                reader = csv.reader(csvfile, delimiter=',')
                invalid_commands = []
                
                for row_num, row in enumerate(reader, 1):
                    if not row:  # Skip empty rows
                        continue
                        
                    # Skip comment lines (lines starting with #)
                    first_cell = str(row[0]).strip()
                    if first_cell.startswith('#') or not first_cell:
                        continue
                    
                    # Get the command (first column)
                    command = first_cell
                    
                    # Validate the command
                    if EnhancedSSHRunner.validate_command(command):
                        commands.append(command)
                    else:
                        invalid_cmd = command[:50] + "..." if len(command) > 50 else command
                        invalid_commands.append(f"line {row_num}: {invalid_cmd}")
                
                # Warn about invalid commands
                if invalid_commands:
                    print(f"⚠️  Skipping {len(invalid_commands)} invalid commands from {csv_file_path}:")
                    for invalid_cmd in invalid_commands[:3]:  # Show first 3
                        print(f"    {invalid_cmd}")
                    if len(invalid_commands) > 3:
                        print(f"    ... and {len(invalid_commands) - 3} more")
                
                # Limit total number of commands to prevent resource exhaustion
                max_commands = 50  # Reasonable limit
                if len(commands) > max_commands:
                    print(f"⚠️  Too many commands in {csv_file_path} ({len(commands)}), limiting to first {max_commands}")
                    commands = commands[:max_commands]
                    
        except Exception as e:
            print(f"⚠️  Warning: Could not read {csv_file_path}: {e}")
            return []
            
        return commands
    
    def create_secure_log_file(self, hostname: str) -> tuple:
        """
        Create a secure per-host log file with proper sanitization
        
        Args:
            hostname: Original hostname
            
        Returns:
            tuple: (log_file_path, write_function)
        """
        # Create per-host log file in subfolder with proper sanitization
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_hostname = self.sanitize_filename(hostname)
        
        # Ensure per-host-logs directory exists and is secure
        log_dir = "per-host-logs"
        try:
            os.makedirs(log_dir, exist_ok=True)
            # Set secure permissions on directory (owner read/write/execute only)
            if hasattr(os, 'chmod'):
                os.chmod(log_dir, 0o700)
        except OSError as e:
            self.logger.error(f"Failed to create log directory {log_dir}: {e}")
            # Fallback to current directory
            log_dir = "."
            safe_hostname = f"fallback_{safe_hostname}"
        
        host_log_file = os.path.join(log_dir, f"ssh_output_{safe_hostname}_{timestamp}.log")
        
        def write_to_host_log(message: str):
            """Write message to host-specific log file only (not console)"""
            if not message:
                return
            
            try:
                # Sanitize message to prevent log injection
                safe_message = message.replace('\x00', '').replace('\r\n', '\n')
                
                with open(host_log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{safe_message}\n")
                    f.flush()  # Ensure data is written immediately
            except IOError as e:
                self.logger.error(f"IO error writing to host log {host_log_file}: {e}")
            except UnicodeEncodeError as e:
                self.logger.error(f"Unicode encoding error writing to host log {host_log_file}: {e}")
                # Try writing a sanitized version
                try:
                    safe_message = message.encode('ascii', errors='replace').decode('ascii')
                    with open(host_log_file, 'a', encoding='utf-8') as f:
                        f.write(f"{safe_message}\n")
                        f.flush()
                except Exception:
                    self.logger.error(f"Failed to write sanitized message to host log")
            except Exception as e:
                self.logger.error(f"Unexpected error writing to host log {host_log_file}: {e}")
        
        return host_log_file, write_to_host_log
    
    def connect(self, hostname: str, username: str, password: str, port: int = 22) -> bool:
        """
        Establish SSH connection to remote host with input validation
        
        Args:
            hostname: IP address or hostname
            username: SSH username
            password: SSH password
            port: SSH port (default 22)
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        # Validate inputs before attempting connection
        if not self.validate_hostname(hostname):
            error_msg = f"Invalid hostname format: {hostname}"
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False
        
        if not self.validate_username(username):
            error_msg = f"Invalid username format: {username}"
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False
        
        if not self.validate_port(port):
            error_msg = f"Invalid port number: {port} (must be 1-65535)"
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False
        
        if not password:
            error_msg = "Password cannot be empty"
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return False
        
        try:
            self.logger.info(f"Attempting SSH connection to {hostname}:{port} as {username}")
            print(f"🔌 Connecting to {hostname}:{port} as {username}...")
            
            # Create SSH client
            self.client = SSHClient()
            # Load existing host keys if available
            self.client.load_system_host_keys()  
            try:
                self.client.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
            except FileNotFoundError:
                # known_hosts file doesn't exist yet - that's fine
                pass
            
            # For internal networks: Auto-accept new host keys
            # NOTE: Only use this for trusted internal networks, not internet-facing connections
            self.client.set_missing_host_key_policy(AutoAddPolicy())
            self.logger.debug("SSH client created with AutoAddPolicy for internal network use")
            
            # Attempt connection
            connection_start = time.time()
            self.logger.debug(f"Initiating SSH connection with timeout={self.timeout}s")
            self.client.connect(
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                timeout=self.timeout,
                allow_agent=False,
                look_for_keys=False
            )
            connection_time = time.time() - connection_start
            self.logger.debug(f"SSH connection established in {connection_time:.2f} seconds")
            
            self.logger.info(f"Successfully connected to {hostname} in {connection_time:.2f} seconds")
            print(f"✅ Successfully connected to {hostname}")
            return True
            
        except socket.gaierror as e:
            error_msg = f"DNS Resolution Error for {hostname}: {e}"
            self.logger.error(error_msg)
            print(f"❌ DNS Resolution Error: {e}")
            return False
        except socket.timeout:
            error_msg = f"Connection timeout to {hostname}:{port} after {self.timeout} seconds"
            self.logger.error(error_msg)
            print(f"❌ Connection timeout after {self.timeout} seconds")
            return False
        except paramiko.AuthenticationException as e:
            error_msg = f"Authentication failed for {username}@{hostname}: {e}"
            self.logger.error(error_msg)
            print("❌ Authentication failed - check username and password")
            return False
        except paramiko.SSHException as e:
            error_msg = f"SSH Error connecting to {hostname}: {e}"
            self.logger.error(error_msg)
            print(f"❌ SSH Error: {e}")
            return False
        except Exception as e:
            error_msg = f"Unexpected error connecting to {hostname}: {type(e).__name__}: {e}"
            self.logger.error(error_msg, exc_info=True)
            print(f"❌ Unexpected error: {e}")
            return False
    
    def execute_command(self, command: str, use_shell: bool = False, hostname: str = "unknown") -> Tuple[bool, str, str]:
        """
        Execute command on remote host
        
        Args:
            command: Command to execute
            use_shell: Use interactive shell instead of exec_command (better for network devices)
            hostname: Hostname for display purposes
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        if not self.client:
            error_msg = "No active SSH connection"
            self.logger.error(error_msg)
            return False, "", error_msg
        
        try:
            self.logger.debug(f"Executing command: '{command}' (shell_mode={use_shell})")
            self.logger.debug(f"Command execution method: {'shell' if use_shell else 'direct'}")
            
            command_start = time.time()
            
            if use_shell:
                # Use interactive shell for network devices
                self.logger.debug("Using shell-based execution for network device compatibility")
                return self._execute_with_shell(command, command_start, hostname)
            else:
                # Use direct exec_command (try with PTY first for network devices)
                self.logger.debug("Using direct exec_command execution")
                return self._execute_direct(command, command_start, hostname)
                
        except socket.timeout:
            error_msg = f"Command execution timeout after {self.timeout} seconds"
            self.logger.error(error_msg)
            return False, "", error_msg
        except Exception as e:
            error_msg = f"Execution error: {type(e).__name__}: {e}"
            self.logger.error(error_msg, exc_info=True)
            return False, "", error_msg
    
    def _execute_direct(self, command: str, start_time: float, hostname: str = 'unknown') -> Tuple[bool, str, str]:
        """Execute command using exec_command with PTY support"""
        try:
            # Try with PTY first (better for network devices)
            self.logger.debug("Attempting exec_command with get_pty=True")
            stdin, stdout, stderr = self.client.exec_command(
                command, 
                timeout=self.timeout, 
                get_pty=True
            )
            
            # Get output
            stdout_output = stdout.read().decode('utf-8', errors='ignore')
            stderr_output = stderr.read().decode('utf-8', errors='ignore')
            exit_status = stdout.channel.recv_exit_status()
            command_time = time.time() - start_time
            
            self.logger.debug(f"Command completed in {command_time:.2f} seconds with exit status: {exit_status}")
            # Escape newlines and special characters for clean logging
            stdout_sample = stdout_output[:200].replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            self.logger.debug(f"STDOUT ({len(stdout_output)} chars): {stdout_sample}{'...' if len(stdout_output) > 200 else ''}")
            
            if stderr_output:
                stderr_sample = stderr_output[:200].replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                self.logger.warning(f"STDERR ({len(stderr_output)} chars): {stderr_sample}{'...' if len(stderr_output) > 200 else ''}")
            
            print(f"📊 [{hostname}] Command completed with exit status: {exit_status}")
            return exit_status == 0, stdout_output, stderr_output
            
        except Exception as e:
            # If PTY fails, try without PTY
            self.logger.warning(f"exec_command with PTY failed: {e}, trying without PTY")
            try:
                stdin, stdout, stderr = self.client.exec_command(command, timeout=self.timeout)
                stdout_output = stdout.read().decode('utf-8', errors='ignore')
                stderr_output = stderr.read().decode('utf-8', errors='ignore')
                exit_status = stdout.channel.recv_exit_status()
                command_time = time.time() - start_time
                
                self.logger.debug(f"Command completed (no PTY) in {command_time:.2f} seconds with exit status: {exit_status}")
                print(f"📊 [{hostname}] Command completed with exit status: {exit_status}")
                return exit_status == 0, stdout_output, stderr_output
            except Exception as e2:
                self.logger.error(f"Both PTY and non-PTY exec_command failed: {e2}")
                raise e2
    
    def _execute_with_shell(self, command: str, start_time: float, hostname: str = 'unknown') -> Tuple[bool, str, str]:
        """Execute command using interactive shell with device type detection"""
        try:
            self.logger.debug("Using interactive shell mode")
            
            # Start interactive shell
            shell = self.client.invoke_shell(term='vt100', width=120, height=24)
            shell.settimeout(self.timeout)
            
            # Wait for initial prompt
            max_wait = 3  # Maximum wait time
            wait_increment = 0.2
            total_wait = 0
            
            while total_wait < max_wait:
                    time.sleep(wait_increment)
                    total_wait += wait_increment
                    if shell.recv_ready():
                        initial_output = shell.recv(4096).decode('utf-8', errors='ignore')
                        # Escape newlines and special characters for clean logging
                        initial_sample = initial_output[:100].replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                    self.logger.debug(f"Initial shell output: {initial_sample}...")
                    break
            
            # Send command with improved buffering
            try:
                command_with_newline = command + '\n'
                shell.send(command_with_newline)
                time.sleep(0.1)  # Small delay to ensure command is sent completely
                self.logger.debug(f"Sent command to shell: {command}")
            except Exception as e:
                self.logger.warning(f"Error sending command: {e}")
                return False, "", f"Failed to send command: {e}"
            
            # Wait for command execution with adaptive timing
            max_cmd_wait = 6  # Increased maximum command wait time
            cmd_wait = 0
            
            while cmd_wait < max_cmd_wait:
                time.sleep(wait_increment)
                cmd_wait += wait_increment
                if shell.recv_ready():
                    break            # Collect output with universal timing-based approach
            output = ""
            last_data_time = time.time()
            no_data_timeout = 3.0  # Universal timeout - wait 3 seconds after no new data
            max_total_wait = 120  # Universal maximum wait time (2 minutes) for any command
            
            max_output_size = 100 * 1024 * 1024  # 100MB limit - higher since we now drain properly
            chunk_count = 0
            
            try:
                while (time.time() - start_time) < max_total_wait:
                    current_duration = time.time() - start_time
                    
                    # Hard timeout detection - if we've been running too long, force completion
                    if current_duration > 90:  # 90 second hard timeout
                        print(f"⏰ [{hostname}] HANG DETECTED: Command running for {current_duration:.0f}s, forcing completion")
                        self.logger.warning(f"Command hang detected after {current_duration:.0f}s, forcing completion: {command}")
                        output += f"\n\n[COMMAND TIMEOUT - Forced completion after {current_duration:.0f}s]\n"
                        break
                    
                    # Progress messages for long-running commands
                    if current_duration > 30:  # Show progress after 30 seconds
                        if chunk_count % 150 == 0:  # Every 150 chunks after 30 seconds
                            print(f"⏱️ [{hostname}] Long-running command... {current_duration:.0f}s elapsed (Ctrl+C to interrupt)")
                    
                    if shell.recv_ready():
                        chunk = shell.recv(131072).decode('utf-8', errors='ignore')  # Even larger buffer (128KB) for efficiency
                        output += chunk
                        last_data_time = time.time()  # Reset timer when we get data
                        chunk_count += 1
                        
                        # Log progress every 100 chunks for very large outputs
                        if chunk_count % 100 == 0:
                            output_mb = len(output) / (1024 * 1024)
                            self.logger.debug(f"Receiving data... {chunk_count} chunks, {output_mb:.1f}MB")
                            # Print progress for user feedback on large outputs
                            if output_mb > 5:
                                print(f"📥 [{hostname}] Receiving large output... {output_mb:.1f}MB (Press Ctrl+C to interrupt)")
                        
                        # Check output size limit - but keep draining to prevent blocking
                        if len(output) > max_output_size:
                            self.logger.warning(f"Output size limit ({max_output_size // (1024*1024)}MB) reached, draining remaining data...")
                            output += f"\n\n[OUTPUT TRUNCATED - Size limit of {max_output_size // (1024*1024)}MB reached]\n"
                            print(f"📋 [{hostname}] Output truncated at {max_output_size // (1024*1024)}MB, draining remaining data...")
                            
                            # Continue draining data without storing it to prevent device blocking
                            drain_start = time.time()
                            max_drain_time = 30  # Maximum 30 seconds to drain
                            drained_chunks = 0
                            
                            while (time.time() - drain_start) < max_drain_time:
                                if shell.recv_ready():
                                    shell.recv(262144)  # Large drain buffer (256KB) for maximum efficiency
                                    drained_chunks += 1
                                    last_data_time = time.time()  # Reset timeout
                                    
                                    # Show drain progress
                                    if drained_chunks % 100 == 0:
                                        drain_duration = time.time() - drain_start
                                        print(f"🚰 [{hostname}] Draining excess data... {drain_duration:.0f}s ({drained_chunks} chunks discarded)")
                                        
                                else:
                                    # Check if we've waited long enough since last data
                                    if (time.time() - last_data_time) >= no_data_timeout:
                                        break  # No new data, device finished
                                    time.sleep(0.05)
                            
                            drain_duration = time.time() - drain_start
                            print(f"✅ [{hostname}] Data drain completed in {drain_duration:.1f}s ({drained_chunks} chunks discarded)")
                            break
                        
                        time.sleep(0.01)  # Very small delay for maximum throughput
                    else:
                        # Check if we've waited long enough since last data
                        if (time.time() - last_data_time) >= no_data_timeout:
                            break  # No new data for timeout period, command likely complete
                        time.sleep(0.05)  # Small sleep when no data available
                    
            except KeyboardInterrupt:
                print(f"\n💥 [{hostname}] Ctrl+C detected! Interrupting command: {command}")
                self.logger.warning(f"Command interrupted by user: {command}")
                output += f"\n\n[COMMAND INTERRUPTED BY USER - Ctrl+C pressed during data collection]\n"
                # Don't return here, continue with cleanup and return what we have
            
            # Log command completion status
            command_duration = time.time() - start_time
            output_size_mb = len(output) / (1024 * 1024)
            if output_size_mb > 1:
                self.logger.info(f"Command data collection completed after {command_duration:.2f}s, output size: {output_size_mb:.2f}MB ({chunk_count} chunks)")
            else:
                self.logger.debug(f"Command data collection completed after {command_duration:.2f}s, output size: {len(output)} bytes ({chunk_count} chunks)")
            
            # Fast cleanup - especially important after truncation
            cleanup_start = time.time()
            max_cleanup_time = 2.0  # Maximum 2 seconds for cleanup to prevent hangs
            
            try:
                shell.send('exit\n')
                shell.send('\n')  # Extra newline to ensure command completion
                
                # Quick cleanup collection with timeout
                cleanup_timeout = time.time() + max_cleanup_time
                while time.time() < cleanup_timeout:
                    if shell.recv_ready():
                        try:
                            shell.recv(4096)  # Drain any remaining output quickly
                            time.sleep(0.1)
                        except:
                            break
                    else:
                        time.sleep(0.1)
                        break  # No more data, exit quickly
                        
            except KeyboardInterrupt:
                print(f"💥 [{hostname}] Ctrl+C during cleanup - forcing shell close")
                self.logger.warning("Command cleanup interrupted by user")
            except Exception as e:
                self.logger.debug(f"Warning during cleanup: {e}")
            
            cleanup_duration = time.time() - cleanup_start
            if cleanup_duration > 1.0:
                self.logger.debug(f"Cleanup took {cleanup_duration:.2f}s")
            
            # Force close shell to prevent hangs
            try:
                shell.close()
            except Exception as e:
                self.logger.debug(f"Warning during shell close: {e}")
            command_time = time.time() - start_time
            
            # Enhanced output cleaning to remove shell artifacts and prompts
            lines = output.split('\n')
            cleaned_lines = []
            skip_command = False
            command_found = False
            
            # Common shell prompts and artifacts to filter out
            shell_artifacts = [
                'exit', 'logout', 'Connection to', 'Last login:',
                'Welcome to', 'Match except:', '---(more)---',
                'No next tag', 'press RETURN', 'Invalid command:', 'xit',
                'vyos@vyos:~$', 'Connection closed'
            ]
            
            # Shell prompt patterns (more comprehensive)
            shell_prompt_patterns = [
                r'.*[$#>]\s*$',  # Basic prompts ending with $, #, or >
                r'vyos@.*[$#>]\s*$',  # VyOS prompts
                r'.*@.*:.*[$#>]\s*$',  # Standard user@host:path$ prompts
                r'{master:\d+}',  # Juniper master mode prompts
                r'^\s*$',  # Empty lines (remove excessive whitespace)
                r':+.*\[.*\d+;\d+.*H.*',  # ANSI cursor positioning sequences
                r'^:.*press RETURN.*',  # Pager "press RETURN" prompts
                r'^>vyos@.*\$ xit$',  # VyOS shell prompt with truncated exit
                r'^vyos@.*:~\$.*xit$',  # VyOS shell cleanup with xit
                r'^Invalid command: \[xit\]$',  # VyOS invalid xit command error
                r'^.*Connection to .* closed\.$',  # Connection closed messages
                r'^\s*xit\s*$'  # Standalone truncated exit commands
            ]
            
            import re
            
            for line in lines:
                original_line = line
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Skip command echo (first occurrence of the command)
                if not command_found and command.strip() in line:
                    command_found = True
                    continue
                
                # Skip shell artifacts
                should_skip = False
                for artifact in shell_artifacts:
                    if artifact.lower() in line.lower():
                        should_skip = True
                        break
                
                if should_skip:
                    continue
                
                # Skip shell prompts using regex patterns
                is_prompt = False
                for pattern in shell_prompt_patterns:
                    if re.match(pattern, line):
                        is_prompt = True
                        break
                
                if is_prompt:
                    continue
                
                # Enhanced cleaning for terminal control sequences and VyOS artifacts
                clean_line = re.sub(r'\x1b\[[0-9;]*[mK]', '', line)  # ANSI escape codes
                clean_line = re.sub(r'\x1b\[\?[0-9]+[hl]', '', clean_line)  # ANSI mode changes
                clean_line = re.sub(r'\x1b\[[0-9]+;[0-9]+H', '', clean_line)  # ANSI cursor positioning
                clean_line = re.sub(r':\s*$', '', clean_line)  # Remove trailing colons from pager prompts
                clean_line = clean_line.replace('\r', '').replace('\x08', '').strip()  # Remove carriage returns and backspaces
                
                # Skip VyOS-specific shell artifacts
                vyos_artifacts = [
                    r'^\s*xit\s*$',
                    r'^Invalid command: \[xit\]$',
                    r'^vyos@.*:~\$',
                    r'^Connection.*closed\.$'
                ]
                
                skip_vyos_artifact = False
                for artifact_pattern in vyos_artifacts:
                    if re.match(artifact_pattern, clean_line):
                        skip_vyos_artifact = True
                        break
                
                # Only add non-empty cleaned lines that aren't VyOS artifacts
                if clean_line and not skip_vyos_artifact:
                    cleaned_lines.append(clean_line)
            
            cleaned_output = '\n'.join(cleaned_lines).strip()
            
            self.logger.debug(f"Shell command completed in {command_time:.2f} seconds")
            # Only log output sample for smaller outputs to avoid log spam
            if len(cleaned_output) < 10000:  # Only log sample for outputs under 10KB
                output_sample = cleaned_output[:200].replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                self.logger.debug(f"Shell output ({len(cleaned_output)} chars): {output_sample}{'...' if len(cleaned_output) > 200 else ''}")
            else:
                self.logger.debug(f"Shell output: {len(cleaned_output)} characters (large output, sample not logged)")
            
            # Universal success detection - simple and reliable
            success = len(cleaned_output) > 0
            
            # More intelligent error detection - only flag real command errors
            # Skip error detection for shell cleanup artifacts
            error_patterns = [
                "command not found", "syntax error",
                "permission denied", "authentication failed",
                "connection refused", "host unreachable", "network unreachable",
                "no such file or directory"
            ]
            
            # Exclude patterns that are likely shell cleanup artifacts
            shell_cleanup_indicators = [
                "invalid command: [xit]",
                "unknown command: xit",
                "invalid command: exit",
                "connection to .* closed"
            ]
            
            output_lower = cleaned_output.lower()
            
            # Check for shell cleanup indicators first - if found, don't treat as error
            is_shell_cleanup = False
            for cleanup_pattern in shell_cleanup_indicators:
                if cleanup_pattern in output_lower:
                    is_shell_cleanup = True
                    self.logger.debug(f"Shell cleanup artifact detected, ignoring: {cleanup_pattern}")
                    break
            
            # Only check for real errors if this isn't shell cleanup
            if not is_shell_cleanup:
                for pattern in error_patterns:
                    if pattern in output_lower:
                        success = False
                        self.logger.warning(f"Command error detected: {pattern}")
                        break
            
            self.logger.debug(f"Command success determination: success={success}, output_length={len(cleaned_output)}")
            print(f"📊 [{hostname}] Command completed in {command_time:.2f} seconds")
            return success, cleaned_output, ""
            
        except Exception as e:
            error_msg = f"Shell execution error: {type(e).__name__}: {e}"
            self.logger.error(error_msg, exc_info=True)
            return False, "", error_msg
    
    def disconnect(self):
        """Close SSH connection"""
        if self.client:
            self.logger.debug("Closing SSH connection")
            self.client.close()
            self.client = None
            print("🔌 SSH connection closed")
        else:
            self.logger.debug("No SSH connection to close")
    
    @staticmethod
    def load_ssh_config_from_env(env_file: str = ".env") -> dict:
        """
        Load SSH configuration from .env file with comprehensive validation
        
        Args:
            env_file: Path to the .env file (default: ".env")
            
        Returns:
            dict: SSH configuration with keys: hosts, username, password, commands
        """
        config = {
            'hosts': [],
            'username': None, 
            'password': None,
            'commands': []
        }
        
        # Validate env_file path to prevent directory traversal
        if not env_file or '..' in env_file or env_file.startswith('/') or '\\' in env_file:
            print(f"⚠️  Invalid .env file path: {env_file}")
            return config
        
        if not os.path.exists(env_file):
            return config
        
        # Check file size to prevent DoS
        try:
            file_size = os.path.getsize(env_file)
            if file_size > 1024 * 1024:  # 1MB limit
                print(f"⚠️  .env file too large ({file_size} bytes), skipping")
                return config
        except OSError as e:
            print(f"⚠️  Cannot access .env file: {e}")
            return config
        
        if DOTENV_AVAILABLE:
            # Use python-dotenv for proper parsing
            try:
                load_dotenv(env_file)
                ssh_host = os.getenv('SSH_HOST')
                if ssh_host:
                    config['hosts'] = EnhancedSSHRunner.parse_host_list(ssh_host)
                
                # Validate username
                username = os.getenv('SSH_USER')
                if username and EnhancedSSHRunner.validate_username(username):
                    config['username'] = username
                elif username:
                    print(f"⚠️  Invalid username format in .env file: {username}")
                
                config['password'] = os.getenv('SSH_PASSWORD')
                
                # Parse SSH_COMMANDS
                ssh_commands = os.getenv('SSH_COMMANDS')
                if ssh_commands:
                    config['commands'] = EnhancedSSHRunner.parse_command_list(ssh_commands)
            except Exception as e:
                print(f"⚠️  Error loading .env with python-dotenv: {e}")
        else:
            # Basic manual parsing for .env files with enhanced validation
            try:
                with open(env_file, 'r', encoding='utf-8', errors='ignore') as f:
                    line_count = 0
                    for line in f:
                        line_count += 1
                        
                        # Prevent processing too many lines
                        if line_count > 1000:
                            print("⚠️  .env file has too many lines, stopping at 1000")
                            break
                        
                        line = line.strip()
                        
                        # Skip empty lines and comments
                        if not line or line.startswith('#'):
                            continue
                        
                        # Skip lines without equals sign
                        if '=' not in line:
                            continue
                        
                        # Handle multiple = signs correctly
                        parts = line.split('=', 1)
                        if len(parts) != 2:
                            continue
                        
                        key = parts[0].strip()
                        value = parts[1].strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        # Process known keys with validation
                        if key == 'SSH_HOST':
                            config['hosts'] = EnhancedSSHRunner.parse_host_list(value)
                        elif key == 'SSH_USER':
                            if EnhancedSSHRunner.validate_username(value):
                                config['username'] = value
                            else:
                                print(f"⚠️  Invalid username format in .env file: {value}")
                        elif key == 'SSH_PASSWORD':
                            config['password'] = value
                        elif key == 'SSH_COMMANDS':
                            config['commands'] = EnhancedSSHRunner.parse_command_list(value)
                            
            except UnicodeDecodeError as e:
                print(f"⚠️  .env file encoding error: {e}")
            except IOError as e:
                print(f"⚠️  Error reading {env_file}: {e}")
            except Exception as e:
                print(f"⚠️  Unexpected error reading {env_file}: {e}")
        
        return config
    
    @staticmethod
    def setup_logging(log_level: str = 'INFO') -> logging.Logger:
        """
        Setup comprehensive logging configuration with syslog-style levels
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            logging.Logger: Configured logger instance
        """
        # Create logger
        logger = logging.getLogger('ssh_runner_v2')
        logger.setLevel(getattr(logging, log_level.upper()))
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
        
        # Create formatters - RFC3164 syslog-style format
        # File logging: detailed format with all syslog fields
        detailed_formatter = logging.Formatter(
            '%(asctime)s %(name)s[%(process)d]: %(levelname)s: %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%b %d %H:%M:%S'
        )
        
        # Console logging: simplified format, minimal for per-host operations
        console_formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # File handler with rotation - captures all debug info
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                'ssh_runner_v2.log', 
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)  # Always capture debug in file
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"WARNING: Could not setup file logging: {e}")
        
        # Console handler - only for summary info, not per-host details
        console_handler = logging.StreamHandler(sys.stdout)
        # Set console level higher to reduce noise (WARNING+ unless debug mode)
        console_level = logging.DEBUG if log_level == 'DEBUG' else logging.WARNING
        console_handler.setLevel(console_level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # Log startup at appropriate level
        if log_level == 'DEBUG':
            logger.debug("Enhanced SSH Runner v2 - DEBUG logging initialized")
        else:
            logger.info("Enhanced SSH Runner v2 logging initialized")
        
        return logger
    
    @staticmethod
    def run_multiple_ssh_commands(hostname: str, username: str, password: str, commands: list, 
                                 port: int = 22, timeout: int = 30, use_shell: bool = False) -> bool:
        """
        Connect via SSH and execute multiple commands sequentially
        
        Args:
            hostname: IP address or hostname
            username: SSH username
            password: SSH password
            commands: List of commands to execute
            port: SSH port (default 22)
            timeout: Connection timeout
            use_shell: Use interactive shell mode (better for network devices)
            
        Returns:
            bool: True if all commands successful, False otherwise
        """
        # Get the already-configured logger
        logger = logging.getLogger('ssh_runner_v2')
        logger.debug(f"Starting SSH multi-command execution: {hostname}:{port} - {len(commands)} commands (shell={use_shell})")
        logger.debug(f"Commands to execute: {commands}")
        
        # Create per-host log file in subfolder with proper sanitization
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_hostname = EnhancedSSHRunner.sanitize_filename(hostname)
        
        # Ensure per-host-logs directory exists and is secure
        log_dir = "per-host-logs"
        try:
            os.makedirs(log_dir, exist_ok=True)
            # Set secure permissions on directory (owner read/write/execute only)
            if hasattr(os, 'chmod'):
                os.chmod(log_dir, 0o700)
        except OSError as e:
            logger.error(f"Failed to create log directory {log_dir}: {e}")
            # Fallback to current directory
            log_dir = "."
            safe_hostname = f"fallback_{safe_hostname}"
        
        host_log_file = os.path.join(log_dir, f"ssh_output_{safe_hostname}_{timestamp}.log")
        print(f"🌐 [{hostname}] Logging to: {host_log_file}")
        
        def write_to_host_log(message: str):
            """Write message to host-specific log file only (not console)"""
            if not message:
                return
            
            try:
                # Sanitize message to prevent log injection
                safe_message = message.replace('\x00', '').replace('\r\n', '\n')
                
                with open(host_log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{safe_message}\n")
                    f.flush()  # Ensure data is written immediately
            except IOError as e:
                logger.error(f"IO error writing to host log {host_log_file}: {e}")
            except UnicodeEncodeError as e:
                logger.error(f"Unicode encoding error writing to host log {host_log_file}: {e}")
                # Try writing a sanitized version
                try:
                    safe_message = message.encode('ascii', errors='replace').decode('ascii')
                    with open(host_log_file, 'a', encoding='utf-8') as f:
                        f.write(f"{safe_message}\n")
                        f.flush()
                except Exception:
                    logger.error(f"Failed to write sanitized message to host log")
            except Exception as e:
                logger.error(f"Unexpected error writing to host log {host_log_file}: {e}")
        
        runner = EnhancedSSHRunner(timeout=timeout, logger=logger)
        overall_success = True
        
        # Initialize host log with header
        header = f"""
{'='*80}
SSH Session Log for Host: {hostname}
Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Commands to execute: {len(commands)}
{'='*80}"""
        write_to_host_log(header)
        
        try:
            # Connect once for all commands
            if not runner.connect(hostname, username, password, port):
                error_msg = f"Failed to connect to {hostname}"
                logger.error(f"SSH connection failed: {hostname}:{port}")
                write_to_host_log(f"❌ {error_msg}")
                return False
            
            logger.debug(f"SSH connected to {hostname}, executing {len(commands)} commands")
            connection_msg = f"\n🚀 Executing {len(commands)} commands sequentially..."
            write_to_host_log(connection_msg)
            
            # Execute each command with keyboard interrupt handling
            for i, command in enumerate(commands, 1):
                try:
                    separator = f"\n{'='*60}"
                    command_header = f"📝 Command {i}/{len(commands)}: {command}"
                    separator_line = '='*60
                    
                    write_to_host_log(separator)
                    write_to_host_log(command_header)
                    write_to_host_log(separator_line)
                    
                    print(f"⚡ [{hostname}] Executing command: {command}")
                    success, stdout, stderr = runner.execute_command(command, use_shell=use_shell, hostname=hostname)
                    
                    if stdout:
                        write_to_host_log("📤 OUTPUT:")
                        write_to_host_log(stdout)
                    
                    if stderr:
                        write_to_host_log("📤 ERRORS:")
                        write_to_host_log(stderr)
                    
                    if success:
                        logger.debug(f"[{hostname}] Command {i}/{len(commands)} completed: {command}")
                        success_msg = f"✅ Command {i} executed successfully"
                        write_to_host_log(success_msg)
                    else:
                        logger.warning(f"[{hostname}] Command {i}/{len(commands)} failed: {command[:50]}...")
                        failure_msg = f"❌ Command {i} failed"
                        write_to_host_log(failure_msg)
                        overall_success = False
                    
                    # Small delay between commands for network devices
                    if i < len(commands):
                        time.sleep(0.5)
                        
                except KeyboardInterrupt:
                    print(f"\n💥 [{hostname}] Ctrl+C detected! Skipping remaining commands...")
                    interrupt_msg = f"\n❌ Command {i} interrupted by user (Ctrl+C)\n⏭️ Skipping remaining {len(commands) - i} commands"
                    write_to_host_log(interrupt_msg)
                    logger.warning(f"[{hostname}] Command execution interrupted by user at command {i}/{len(commands)}")
                    overall_success = False
                    break
            
            final_separator = f"\n{'='*60}"
            write_to_host_log(final_separator)
            
            if overall_success:
                logger.info(f"[{hostname}] All {len(commands)} commands completed successfully")
                final_msg = "✅ All commands executed successfully"
                write_to_host_log(final_msg)
            else:
                logger.warning(f"[{hostname}] Some commands failed during execution")
                final_msg = "⚠️  Some commands failed - check output above"
                write_to_host_log(final_msg)
            
            return overall_success
            
        except Exception as e:
            logger.error(f"[{hostname}] Unexpected error during multi-command execution: {type(e).__name__}: {e}", exc_info=True)
            error_msg = f"❌ Unexpected error: {e}"
            write_to_host_log(error_msg)
            return False
        finally:
            runner.disconnect()
            logger.debug(f"[{hostname}] SSH multi-command session completed")
            
            # Write session footer to host log
            footer = f"""
{'='*80}
SSH Session Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: {'SUCCESS' if overall_success else 'FAILED'}
Log file: {host_log_file}
{'='*80}"""
            write_to_host_log(footer)
    
    @staticmethod
    def run_ssh_command(hostname: str, username: str, password: str, command: str, 
                       port: int = 22, timeout: int = 30, use_shell: bool = False) -> bool:
        """
        Connect via SSH and execute a command
        
        Args:
            hostname: IP address or hostname
            username: SSH username
            password: SSH password
            command: Command to execute
            port: SSH port (default 22)
            timeout: Connection timeout
            use_shell: Use interactive shell mode (better for network devices)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Get the already-configured logger
        logger = logging.getLogger('ssh_runner_v2')
        logger.debug(f"Starting SSH command execution: {hostname}:{port} - '{command}' (shell={use_shell})")
        logger.debug(f"Single command details: timeout={timeout}, use_shell={use_shell}")
        
        # Create per-host log file in subfolder with proper sanitization
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_hostname = EnhancedSSHRunner.sanitize_filename(hostname)
        
        # Ensure per-host-logs directory exists and is secure
        log_dir = "per-host-logs"
        try:
            os.makedirs(log_dir, exist_ok=True)
            # Set secure permissions on directory (owner read/write/execute only)
            if hasattr(os, 'chmod'):
                os.chmod(log_dir, 0o700)
        except OSError as e:
            logger.error(f"Failed to create log directory {log_dir}: {e}")
            # Fallback to current directory
            log_dir = "."
            safe_hostname = f"fallback_{safe_hostname}"
        
        host_log_file = os.path.join(log_dir, f"ssh_output_{safe_hostname}_{timestamp}.log")
        print(f"🌐 [{hostname}] Logging to: {host_log_file}")
        
        def write_to_host_log(message: str):
            """Write message to host-specific log file only (not console)"""
            if not message:
                return
            
            try:
                # Sanitize message to prevent log injection
                safe_message = message.replace('\x00', '').replace('\r\n', '\n')
                
                with open(host_log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{safe_message}\n")
                    f.flush()  # Ensure data is written immediately
            except IOError as e:
                logger.error(f"IO error writing to host log {host_log_file}: {e}")
            except UnicodeEncodeError as e:
                logger.error(f"Unicode encoding error writing to host log {host_log_file}: {e}")
                # Try writing a sanitized version
                try:
                    safe_message = message.encode('ascii', errors='replace').decode('ascii')
                    with open(host_log_file, 'a', encoding='utf-8') as f:
                        f.write(f"{safe_message}\n")
                        f.flush()
                except Exception:
                    logger.error(f"Failed to write sanitized message to host log")
            except Exception as e:
                logger.error(f"Unexpected error writing to host log {host_log_file}: {e}")
        
        runner = EnhancedSSHRunner(timeout=timeout, logger=logger)
        
        # Initialize host log with header
        header = f"""
{'='*80}
SSH Single Command Log for Host: {hostname}
Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Command: {command}
{'='*80}"""
        write_to_host_log(header)
        
        try:
            # Connect
            if not runner.connect(hostname, username, password, port):
                error_msg = f"Failed to connect to {hostname}"
                logger.error(f"SSH connection failed: {hostname}:{port}")
                write_to_host_log(f"❌ {error_msg}")
                return False
            
            logger.debug(f"SSH connected to {hostname}, executing single command")
            
            # Execute command
            success, stdout, stderr = runner.execute_command(command, use_shell=use_shell, hostname=hostname)
            
            # Display results
            separator = "\n" + "=" * 60
            output_header = "📋 COMMAND OUTPUT"
            separator_line = "=" * 60
            
            write_to_host_log(separator)
            write_to_host_log(output_header)
            write_to_host_log(separator_line)
            
            if stdout:
                write_to_host_log("📤 STDOUT:")
                write_to_host_log(stdout)
            
            if stderr:
                write_to_host_log("📤 STDERR:")
                write_to_host_log(stderr)
            
            if not stdout and not stderr:
                write_to_host_log("📝 No output returned")
            
            write_to_host_log(separator_line)
            
            if success:
                logger.info(f"[{hostname}] Command completed successfully")
                success_msg = "✅ Command executed successfully"
                write_to_host_log(success_msg)
            else:
                logger.warning(f"[{hostname}] Command failed: {command[:50]}...")
                failure_msg = "❌ Command execution failed or returned non-zero exit status"
                write_to_host_log(failure_msg)
                    
            return success
            
        except Exception as e:
            logger.error(f"[{hostname}] Unexpected error during SSH command execution: {type(e).__name__}: {e}", exc_info=True)
            error_msg = f"❌ Unexpected error: {e}"
            write_to_host_log(error_msg)
            return False
        finally:
            runner.disconnect()
            logger.debug(f"[{hostname}] SSH single command session completed")
            
            # Write session footer to host log
            footer = f"""
{'='*80}
SSH Single Command Session Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: {'SUCCESS' if 'success' in locals() and success else 'FAILED'}
Log file: {host_log_file}
{'='*80}"""
            write_to_host_log(footer)
    
    @staticmethod
    def run_ssh_command_on_host(hostname: str, username: str, password: str, commands: list, 
                               port: int = 22, timeout: int = 30, use_shell: bool = True) -> tuple:
        """
        Run SSH commands on a single host (for multi-threading)
        
        Args:
            hostname: IP address or hostname
            username: SSH username  
            password: SSH password
            commands: List of commands to execute
            port: SSH port
            timeout: Connection timeout
            use_shell: Whether to use shell mode
            
        Returns:
            tuple: (hostname, success, results_summary)
        """
        logger = logging.getLogger(__name__)
        
        try:
            logger.debug(f"[{hostname}] Starting SSH session...")
            
            if len(commands) == 1:
                # Single command
                success = EnhancedSSHRunner.run_ssh_command(hostname, username, password, commands[0], port, timeout, use_shell)
                return (hostname, success, f"Single command: {commands[0]}")
            else:
                # Multiple commands
                success = EnhancedSSHRunner.run_multiple_ssh_commands(hostname, username, password, commands, port, timeout, use_shell)
                return (hostname, success, f"{len(commands)} commands executed")
                
        except Exception as e:
            logger.error(f"[{hostname}] Unexpected error: {type(e).__name__}: {e}", exc_info=True)
            return (hostname, False, f"Error: {e}")
    
    @staticmethod
    def run_ssh_commands_multi_host(hosts: list, username: str, password: str, commands: list,
                                   port: int = 22, timeout: int = 30, use_shell: bool = True,
                                   max_threads: int = 5) -> dict:
        """
        Run SSH commands on multiple hosts concurrently using threading
        
        Args:
            hosts: List of hostnames/IPs
            username: SSH username
            password: SSH password  
            commands: List of commands to execute on each host
            port: SSH port
            timeout: Connection timeout
            use_shell: Whether to use shell mode
            max_threads: Maximum number of concurrent threads
            
        Returns:
            dict: Results summary with success/failure counts per host
        """
        logger = logging.getLogger(__name__)
        
        print(f"\n🚀 Starting SSH execution on {len(hosts)} hosts ({max_threads} threads)")
        logger.info(f"Multi-host SSH execution: {len(hosts)} hosts, {len(commands)} commands, {max_threads} threads")
        logger.debug(f"Target hosts: {hosts}")
        logger.debug(f"Commands: {commands}")
        logger.debug(f"Connection parameters: port={port}, timeout={timeout}, use_shell={use_shell}")
        
        results = {}
        successful_hosts = []
        failed_hosts = []
        
        # Use ThreadPoolExecutor for thread management
        with ThreadPoolExecutor(max_workers=max_threads, thread_name_prefix="SSH") as executor:
            # Submit all host tasks
            future_to_host = {
                executor.submit(EnhancedSSHRunner.run_ssh_command_on_host, host, username, password, commands, 
                               port, timeout, use_shell): host 
                for host in hosts
            }
            
            # Process completed tasks
            for future in as_completed(future_to_host):
                hostname, success, summary = future.result()
                results[hostname] = {
                    'success': success,
                    'summary': summary
                }
                
                if success:
                    successful_hosts.append(hostname)
                    logger.debug(f"[{hostname}] Completed successfully: {summary}")
                else:
                    failed_hosts.append(hostname)
                    logger.error(f"[{hostname}] Failed: {summary}")
        
        # Summary report
        print(f"\n{'='*60}")
        print(f"📊 EXECUTION SUMMARY")
        print(f"{'='*60}")
        print(f"Total hosts: {len(hosts)}")
        print(f"Successful: {len(successful_hosts)} ✅")
        print(f"Failed: {len(failed_hosts)} ❌")
        print(f"Per-host logs: per-host-logs/ssh_output_<hostname>_<timestamp>.log")
        
        if successful_hosts:
            print(f"\n✅ Successful hosts: {', '.join(successful_hosts)}")
        
        if failed_hosts:
            print(f"\n❌ Failed hosts: {', '.join(failed_hosts)}")
        
        logger.info(f"Multi-host execution completed: {len(successful_hosts)}/{len(hosts)} successful")
        
        return {
            'total': len(hosts),
            'successful': len(successful_hosts),
            'failed': len(failed_hosts),
            'successful_hosts': successful_hosts,
            'failed_hosts': failed_hosts,
            'results': results
        }
    
    @staticmethod
    def run_application(args):
        """Main application logic - handles all the SSH runner functionality"""
        # Determine logging level (--debug flag overrides --log-level)
        log_level = 'DEBUG' if args.debug else args.log_level
        
        # Setup logging with specified level
        logger = EnhancedSSHRunner.setup_logging(log_level)
        
        # Interactive mode
        if args.interactive:
            return EnhancedSSHRunner.interactive_mode()
        
        # Determine if we should use .env file (default behavior unless --no-env is specified)
        use_env = not args.no_env
        
        # Try to load .env configuration
        env_config = {}
        if use_env:
            logger.info("Loading SSH credentials from .env file (default behavior)")
            env_config = EnhancedSSHRunner.load_ssh_config_from_env()
            if any([env_config.get('hosts'), env_config['username'], env_config['password']]):
                host_count = len(env_config.get('hosts', []))
                hosts_str = ', '.join(env_config.get('hosts', [])) if host_count <= 3 else f"{host_count} hosts"
                logger.info(f"Found .env credentials - Hosts: {hosts_str}, User: {env_config['username']}, Commands: {len(env_config['commands'])}")
        
        # Determine final connection parameters (command line overrides .env)
        final_hosts = []
        if args.hostname:
            final_hosts = [args.hostname]  # Single host from command line
        elif env_config.get('hosts'):
            final_hosts = env_config['hosts']  # Multiple hosts from .env
        
        final_username = args.username or env_config.get('username') 
        final_password = env_config.get('password')  # Only from .env, never from command line
        
        # Handle secure password input if needed
        if not final_password and not args.secure:
            if final_username and final_hosts:
                host_display = final_hosts[0] if len(final_hosts) == 1 else f"{len(final_hosts)} hosts"
                final_password = getpass.getpass(f"🔒 Enter password for {final_username}@{host_display}: ")
            else:
                print("❌ Password required but not provided")
                return False
        elif args.secure and not final_password:
            host_display = final_hosts[0] if len(final_hosts) == 1 else f"{len(final_hosts)} hosts"
            final_password = getpass.getpass(f"🔒 Enter password for {final_username}@{host_display}: ")
        # SECURITY: Password argument removed - this code block is no longer needed
        
        # Validate final parameters
        validated_hosts = []
        invalid_hosts = []
        
        for host in final_hosts:
            if EnhancedSSHRunner.validate_hostname(host):
                validated_hosts.append(host)
            else:
                invalid_hosts.append(host)
        
        if invalid_hosts:
            print(f"❌ Invalid hosts detected: {', '.join(invalid_hosts)}")
            if not validated_hosts:
                print("❌ No valid hosts remaining")
                return False
            else:
                print(f"⚠️  Proceeding with {len(validated_hosts)} valid hosts")
                final_hosts = validated_hosts
        
        # Validate username
        if final_username and not EnhancedSSHRunner.validate_username(final_username):
            print(f"❌ Invalid username format: {final_username}")
            return False
        
        # Check if we have minimum required parameters
        if not all([final_hosts, final_username, final_password]):
            missing = []
            if not final_hosts: missing.append("hostname/SSH_HOST")
            if not final_username: missing.append("username/SSH_USER") 
            if not final_password: missing.append("password/SSH_PASSWORD")
            
            print(f"❌ Error: Missing required parameters: {', '.join(missing)}")
            if use_env:
                print("💡 Add these to your .env file or provide as command line arguments")
                print("💡 Use --no-env flag to disable .env file loading")
            else:
                print("💡 Provide as command line arguments or remove --no-env flag to use .env file")
                # Since we can't access the parser here, we'll let the caller handle help display
            return False
        
        # Determine commands to execute
        commands_to_run = []
        
        # Priority 1: Command line argument
        if args.command:
            commands_to_run = [args.command]
            logger.info(f"Using command from command line: {args.command}")
        # Priority 2: SSH_COMMANDS from .env file
        elif use_env and env_config.get('commands'):
            commands_to_run = env_config['commands']
            logger.info(f"Using {len(commands_to_run)} commands from .env file: {commands_to_run}")
        # Priority 3: SSH_COMMANDS.CSV file as fallback
        elif not args.command:
            csv_commands = EnhancedSSHRunner.load_commands_from_csv()
            if csv_commands:
                commands_to_run = csv_commands
                logger.info(f"Using {len(commands_to_run)} commands from SSH_COMMANDS.CSV: {commands_to_run}")
                print(f"💡 Loaded {len(commands_to_run)} commands from SSH_COMMANDS.CSV")
        # Priority 4: Interactive input
        else:
            # Check what command sources are available
            env_commands = env_config.get('commands', []) if use_env else []
            csv_commands = EnhancedSSHRunner.load_commands_from_csv() if not commands_to_run else []
            
            if env_commands and csv_commands:
                command = input(f"⚡ Enter command to execute (or press Enter to use {len(env_commands)} commands from .env, or 'csv' for {len(csv_commands)} commands from CSV): ").strip()
                if not command:
                    commands_to_run = env_commands
                    print(f"💡 Using {len(commands_to_run)} commands from .env file: {commands_to_run}")
                elif command.lower() == 'csv':
                    commands_to_run = csv_commands
                    print(f"💡 Using {len(commands_to_run)} commands from SSH_COMMANDS.CSV: {commands_to_run}")
                else:
                    commands_to_run = [command]
            elif env_commands:
                command = input(f"⚡ Enter command to execute (or press Enter to use {len(env_commands)} commands from .env): ").strip()
                if not command:
                    commands_to_run = env_commands
                    print(f"💡 Using {len(commands_to_run)} commands from .env file: {commands_to_run}")
                else:
                    commands_to_run = [command]
            elif csv_commands:
                command = input(f"⚡ Enter command to execute (or press Enter to use {len(csv_commands)} commands from SSH_COMMANDS.CSV): ").strip()
                if not command:
                    commands_to_run = csv_commands
                    print(f"💡 Using {len(commands_to_run)} commands from SSH_COMMANDS.CSV: {commands_to_run}")
                else:
                    commands_to_run = [command]
            else:
                command = input("⚡ Enter command to execute: ").strip()
                if not command:
                    print("❌ No commands specified")
                    return False
                commands_to_run = [command]
        
        # Validate commands
        validated_commands = []
        invalid_commands = []
        
        for cmd in commands_to_run:
            if EnhancedSSHRunner.validate_command(cmd):
                validated_commands.append(cmd)
            else:
                invalid_cmd = cmd[:50] + "..." if len(cmd) > 50 else cmd
                invalid_commands.append(invalid_cmd)
        
        if invalid_commands:
            print(f"❌ Invalid commands detected: {', '.join(invalid_commands)}")
            if not validated_commands:
                print("❌ No valid commands remaining")
                return False
            else:
                print(f"⚠️  Proceeding with {len(validated_commands)} valid commands")
                commands_to_run = validated_commands
        
        if not commands_to_run:
            print("❌ No commands to execute")
            return False
        
        # Determine shell mode (default is True unless --no-shell is specified)
        use_shell_mode = args.shell and not args.no_shell
        
        # Execute SSH commands
        try:
            if len(final_hosts) == 1:
                # Single host execution
                hostname = final_hosts[0]
                if len(commands_to_run) == 1:
                    # Single command on single host
                    success = EnhancedSSHRunner.run_ssh_command(
                        hostname,
                        final_username,
                        final_password,
                        commands_to_run[0],
                        args.port,
                        args.timeout,
                        use_shell_mode
                    )
                else:
                    # Multiple commands on single host
                    success = EnhancedSSHRunner.run_multiple_ssh_commands(
                        hostname,
                        final_username,
                        final_password,
                        commands_to_run,
                        args.port,
                        args.timeout,
                        use_shell_mode
                    )
                
                return success
                
            else:
                # Multiple host execution (multi-threaded)
                default_threads = multiprocessing.cpu_count()
                requested_threads = args.max_threads or default_threads
                max_threads = EnhancedSSHRunner.validate_thread_count(requested_threads, len(final_hosts))
                
                if max_threads != requested_threads:
                    print(f"⚠️  Adjusted thread count from {requested_threads} to {max_threads}")
                
                results = EnhancedSSHRunner.run_ssh_commands_multi_host(
                    final_hosts,
                    final_username,
                    final_password,
                    commands_to_run,
                    args.port,
                    args.timeout,
                    use_shell_mode,
                    max_threads
                )
                
                # Return success if all hosts succeeded
                return results['failed'] == 0
            
        except KeyboardInterrupt:
            print("\n🛑 Operation cancelled by user")
            return False
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            print(f"❌ Fatal error: {e}")
            return False

    @staticmethod
    def create_argument_parser():
        """Create and configure the argument parser"""
        parser = argparse.ArgumentParser(
            description="Enhanced SSH Command Runner v2 - Execute commands on remote hosts via SSH",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
    # Default: Uses .env file and shell mode (recommended)
    python ssh_runner_v2.py
    
    # Override with specific command (still uses shell mode by default)
    python ssh_runner_v2.py "show version"
    
    # Manual SSH connection (uses secure password prompt)
    python ssh_runner_v2.py 192.168.1.1 vyos --secure "show version"
    
    # Use exec_command mode instead of shell mode  
    python ssh_runner_v2.py --no-shell "ls -la"
    
    # Multi-host with custom thread count
    python ssh_runner_v2.py --max-threads 10
    
    # Interactive mode
    python ssh_runner_v2.py --interactive
    
    # Disable .env loading and use exec_command mode with secure password
    python ssh_runner_v2.py --no-env --no-shell --secure 192.168.1.1 vyos "show version"

.env file format (SECURITY: Keep this file private and out of version control):
    SSH_HOST=192.168.1.1,192.168.1.2,192.168.1.3
    SSH_USER=vyos
    SSH_PASSWORD=your_password
    SSH_COMMANDS=show version,show interfaces,show route
    
SECURITY NOTES:
    - Never commit .env files containing passwords to version control
    - Use secure password prompts (--secure flag) when possible
    - Consider using SSH keys instead of passwords for better security
    - Add .env to your .gitignore file
            """
        )
        
        # Interactive mode
        parser.add_argument("--interactive", "-i", action="store_true",
                           help="Run in interactive mode")
        
        # .env file mode controls
        parser.add_argument("--no-env", action="store_true",
                           help="Disable automatic .env file loading (use manual credentials)")
        
        # Connection parameters
        parser.add_argument("hostname", nargs="?", help="Hostname or IP address (overrides SSH_HOST)")
        parser.add_argument("username", nargs="?", help="SSH username (overrides SSH_USER)") 
        parser.add_argument("password", nargs="?", help="SSH password (overrides SSH_PASSWORD)")
        parser.add_argument("command", nargs="?", help="Command to execute (overrides SSH_COMMANDS)")
        
        # Optional parameters with validation
        def validate_port_arg(value):
            ivalue = int(value)
            if not EnhancedSSHRunner.validate_port(ivalue):
                raise argparse.ArgumentTypeError(f"Port must be between 1 and 65535, got {ivalue}")
            return ivalue
        
        def validate_timeout_arg(value):
            ivalue = int(value)
            if not EnhancedSSHRunner.validate_timeout(ivalue):
                raise argparse.ArgumentTypeError(f"Timeout must be between 1 and 3600 seconds, got {ivalue}")
            return ivalue
        
        def validate_threads_arg(value):
            ivalue = int(value)
            if ivalue <= 0 or ivalue > 100:
                raise argparse.ArgumentTypeError(f"Thread count must be between 1 and 100, got {ivalue}")
            return ivalue
        
        parser.add_argument("--port", "-p", type=validate_port_arg, default=22,
                           help="SSH port (default: 22)")
        parser.add_argument("--timeout", "-t", type=validate_timeout_arg, default=30,
                           help="Connection timeout in seconds (default: 30)")
        parser.add_argument("--secure", "-s", action="store_true",
                           help="Prompt for password securely instead of command line")
        parser.add_argument("--shell", action="store_true", default=True,
                           help="Use interactive shell mode (default, recommended for network devices)")
        parser.add_argument("--no-shell", action="store_true",
                           help="Disable shell mode and use exec_command instead")
        parser.add_argument("--log-level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                           default='INFO', help="Set logging level (default: INFO)")
        parser.add_argument("--debug", "-d", action="store_true",
                           help="Enable debug logging (equivalent to --log-level DEBUG)")
        parser.add_argument("--max-threads", type=validate_threads_arg, default=None,
                           help=f"Maximum threads for multi-host execution (default: {multiprocessing.cpu_count()} cores)")
        
        return parser

    @staticmethod
    def interactive_mode():
        """Interactive mode for SSH command execution with input validation"""
        print("🖥️  Enhanced SSH Command Runner v2 - Interactive Mode")
        print("=" * 60)
        
        # Get connection details with validation
        while True:
            hostname = input("🌐 Enter hostname or IP address: ").strip()
            if not hostname:
                print("❌ Hostname is required")
                continue
            if not EnhancedSSHRunner.validate_hostname(hostname):
                print("❌ Invalid hostname or IP address format")
                continue
            break
        
        while True:
            username = input("👤 Enter username: ").strip()
            if not username:
                print("❌ Username is required")
                continue
            if not EnhancedSSHRunner.validate_username(username):
                print("❌ Invalid username format (alphanumeric, underscore, hyphen, dot only)")
                continue
            break
        
        password = getpass.getpass("🔒 Enter password: ")
        if not password:
            print("❌ Password is required")
            return False
        
        # Optional settings with validation
        while True:
            try:
                port_input = input("🔌 Enter SSH port (default 22): ").strip()
                if not port_input:
                    port = 22
                    break
                port = int(port_input)
                if not EnhancedSSHRunner.validate_port(port):
                    print("❌ Port must be between 1 and 65535")
                    continue
                break
            except ValueError:
                print("❌ Port must be a valid number")
        
        while True:
            try:
                timeout_input = input("⏱️  Enter timeout in seconds (default 30): ").strip()
                if not timeout_input:
                    timeout = 30
                    break
                timeout = int(timeout_input)
                if not EnhancedSSHRunner.validate_timeout(timeout):
                    print("❌ Timeout must be between 1 and 3600 seconds")
                    continue
                break
            except ValueError:
                print("❌ Timeout must be a valid number")
        
        # Execution mode
        shell_mode = input("🐚 Use interactive shell mode? (y/N - recommended for network devices): ").strip().lower()
        use_shell = shell_mode in ['y', 'yes', 'true', '1']
        
        # Get command with validation
        while True:
            command = input("⚡ Enter command to execute: ").strip()
            if not command:
                print("❌ Command is required")
                continue
            if not EnhancedSSHRunner.validate_command(command):
                print("❌ Invalid command (too long or contains null bytes)")
                continue
            break
        
        print(f"\n🚀 Starting SSH session (shell_mode={use_shell})...")
        
        # Execute
        return EnhancedSSHRunner.run_ssh_command(hostname, username, password, command, port, timeout, use_shell)



def ssh_runner_main():
    """SSH Runner entry point - delegates to class-based application logic"""
    try:
        # Create argument parser
        parser = EnhancedSSHRunner.create_argument_parser()
        
        # Parse arguments
        args = parser.parse_args()
        
        # Run the application
        success = EnhancedSSHRunner.run_application(args)
        
        # If application returns False and it's likely due to missing parameters, show help
        if not success:
            # Check if we have the basic requirements that would indicate help is needed
            if not any([args.hostname, args.interactive]):
                parser.print_help()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except argparse.ArgumentTypeError as e:
        print(f"❌ Invalid argument: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    ssh_runner_main()
